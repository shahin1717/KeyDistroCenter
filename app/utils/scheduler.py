import logging

from app.core.config import get_settings
from app.models.db import SessionLocal
from app.services.message_service import cleanup_expired_messages

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler = None

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - only triggered when dependency is missing
    BackgroundScheduler = None


def _cleanup_job() -> None:
    """Run cleanup in its own DB session."""
    db = SessionLocal()
    try:
        deleted = cleanup_expired_messages(db)
        if deleted:
            logger.info("Scheduler cleanup removed %d messages", deleted)
    except Exception:
        logger.exception("Scheduled cleanup job failed")
    finally:
        db.close()


def start_scheduler() -> None:
    """Start background scheduler for periodic message cleanup."""
    global _scheduler

    if BackgroundScheduler is None:
        logger.warning(
            "APScheduler is not installed; scheduled cleanup is disabled. "
            "Install it with: pip install apscheduler"
        )
        return

    if _scheduler and _scheduler.running:
        return

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _cleanup_job,
        trigger="interval",
        minutes=settings.CLEANUP_INTERVAL_MINUTES,
        id="message_cleanup",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: cleanup every %d minute(s)",
        settings.CLEANUP_INTERVAL_MINUTES,
    )


def stop_scheduler() -> None:
    """Stop scheduler on application shutdown."""
    global _scheduler
    if not _scheduler:
        return
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("Scheduler stopped")
