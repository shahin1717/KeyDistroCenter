"""
crypto.py — RSA + Caesar cipher hybrid encryption.

Improvements over v1:
- Miller-Rabin primality test (probabilistic, much faster for larger primes)
- Extended Euclidean algorithm for mod_inverse (replaces brute-force loop)
- Larger prime range (1000–9999) for stronger keys
- Clean type annotations throughout
"""

import random
import math
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

PublicKey = Tuple[int, int]   # (e, n)
PrivateKey = Tuple[int, int]  # (d, n)


# ---------------------------------------------------------------------------
# Primality
# ---------------------------------------------------------------------------

def _miller_rabin(n: int, k: int = 8) -> bool:
    """Miller-Rabin probabilistic primality test with k rounds."""
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def is_prime(n: int) -> bool:
    return _miller_rabin(n)


def generate_prime(min_value: int, max_value: int) -> int:
    """Generate a random prime in [min_value, max_value]."""
    candidate = random.randrange(min_value | 1, max_value, 2)  # odd numbers only
    while not is_prime(candidate):
        candidate = random.randrange(min_value | 1, max_value, 2)
    return candidate


# ---------------------------------------------------------------------------
# Modular arithmetic
# ---------------------------------------------------------------------------

def _extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """Return (gcd, x, y) such that a*x + b*y = gcd."""
    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = _extended_gcd(b % a, a)
    return gcd, y1 - (b // a) * x1, x1


def mod_inverse(e: int, phi: int) -> int:
    """Compute modular inverse of e mod phi using extended Euclidean algorithm."""
    gcd, x, _ = _extended_gcd(e % phi, phi)
    if gcd != 1:
        raise ValueError(f"Modular inverse does not exist (gcd={gcd})")
    return x % phi


# ---------------------------------------------------------------------------
# RSA
# ---------------------------------------------------------------------------

def generate_keypair(
    prime_min: int = 1000,
    prime_max: int = 9999,
) -> Tuple[PublicKey, PrivateKey]:
    """
    Generate an RSA keypair.

    Returns:
        ((e, n), (d, n)) — public key and private key
    """
    p = generate_prime(prime_min, prime_max)
    q = generate_prime(prime_min, prime_max)
    while q == p:
        q = generate_prime(prime_min, prime_max)

    n = p * q
    phi = (p - 1) * (q - 1)

    # Choose e: small public exponent, coprime with phi
    e = 65537  # standard choice; fall back to search if needed
    if math.gcd(e, phi) != 1:
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2

    d = mod_inverse(e, phi)
    logger.debug("Generated keypair: public=(%d, %d), private=(%d, %d)", e, n, d, n)
    return (e, n), (d, n)


def rsa_encrypt(plaintext: int, public_key: PublicKey) -> int:
    e, n = public_key
    if plaintext >= n:
        raise ValueError(f"Plaintext {plaintext} must be < n ({n})")
    return pow(plaintext, e, n)


def rsa_decrypt(ciphertext: int, private_key: PrivateKey) -> int:
    d, n = private_key
    return pow(ciphertext, d, n)


# ---------------------------------------------------------------------------
# Caesar cipher
# ---------------------------------------------------------------------------

def caesar_encrypt(message: str, key: int) -> str:
    """Encrypt alphabetic characters; leave others unchanged."""
    result = []
    for ch in message:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + key) % 26 + base))
        else:
            result.append(ch)
    return "".join(result)


def caesar_decrypt(ciphertext: str, key: int) -> str:
    return caesar_encrypt(ciphertext, -key)