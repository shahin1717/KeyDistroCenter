# Key Distribution Center (KDC)

A secure messaging app using RSA + Caesar cipher hybrid encryption.

## Installation

1. Create and activate a virtual environment.
2. Choose one dependency install method:

- Using `requirements.txt`:
  - `pip install -r requirements.txt`
- Using `pyproject.toml`:
  - `pip install -e .`

3. Create `.env` with your settings:
   - `DATABASE_URL=...`
   - `PRIVATE_KEY_ENCRYPTION_KEY=...` (Fernet key)
4. Run the app:
   - `python -m app.main`

## Project Structure

```
kdc/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py          # POST /auth/register, POST /auth/login, POST /auth/logout
│   │       ├── messages.py      # GET /messages, POST /messages/send
│   │       └── users.py         # GET /users/me, GET /users/{username}/pubkey
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── security.py          # Session helpers, password hashing
│   │   └── crypto.py            # RSA + Caesar cipher (upgraded)
│   ├── models/
│   │   ├── __init__.py
│   │   └── db.py                # SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py              # RegisterRequest, LoginRequest
│   │   ├── message.py           # SendMessageRequest, MessageResponse
│   │   └── user.py              # UserProfile, PublicKeyResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # register, login logic
│   │   ├── message_service.py   # send, fetch, cleanup logic
│   │   └── user_service.py      # get user, get pubkey
│   ├── utils/
│   │   ├── __init__.py
│   │   └── scheduler.py         # APScheduler message cleanup
│   ├── __init__.py
│   └── main.py                  # App factory, middleware, router registration
├── templates/                   # Jinja2 HTML templates
├── static/css/                  # Stylesheets
├── tests/
│   ├── test_crypto.py
│   ├── test_auth.py
│   └── test_messages.py
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

## REST API Design

| Method | Endpoint                      | Description                        |
|--------|-------------------------------|------------------------------------|
| POST   | /api/v1/auth/register         | Register new user                  |
| POST   | /api/v1/auth/login            | Login                              |
| POST   | /api/v1/auth/logout           | Logout                             |
| GET    | /api/v1/users/me              | Get current user profile           |
| GET    | /api/v1/users/{username}/pubkey | Get a user's public key          |
| GET    | /api/v1/messages              | Get received messages              |
| POST   | /api/v1/messages              | Send a message                     |
| DELETE | /api/v1/messages/{id}         | Delete a specific message          |

Page routes (HTML) stay at top level: `/`, `/login`, `/register`, `/profile`, `/send`, `/messages`

## Key Features

- **Modular structure** — each concern in its own file
- **Proper REST** — GET retrieves, POST creates, DELETE removes
- **Schemas** — Pydantic models for all request/response validation
- **Service layer** — business logic separated from route handlers
- **Config** — all settings in one place via `.env`
- **Upgraded crypto** — Miller-Rabin primality, larger primes, extended Euclidean for mod_inverse