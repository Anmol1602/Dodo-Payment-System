import hashlib
import hmac
import secrets
import time
from typing import Tuple


def generate_api_key(is_test: bool = False) -> Tuple[str, str, str]:
    """
    Generates a secure API key with prefix.
    Returns: (raw_key, key_prefix, key_hash)
    Raw key is displayed only once to the client.
    """
    prefix = "dodo_test_" if is_test else "dodo_live_"
    random_hex = secrets.token_hex(20)  # 40 chars
    raw_key = f"{prefix}{random_hex}"
    key_hash = hash_api_key(raw_key)
    return raw_key, prefix, key_hash


def hash_api_key(raw_key: str) -> str:
    """Computes SHA-256 hex digest of the raw API key."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Performs constant-time comparison against stored SHA-256 hash."""
    computed_hash = hash_api_key(raw_key)
    return hmac.compare_digest(computed_hash, stored_hash)


def generate_webhook_secret() -> str:
    """Generates a high-entropy secret for HMAC-SHA256 signing."""
    return f"whsec_{secrets.token_hex(24)}"


def sign_webhook_payload(secret: str, payload_bytes: bytes, timestamp: int) -> str:
    """
    Signs webhook payload: HMAC-SHA256(secret, f"{timestamp}.{payload}")
    Returns header string: "t={timestamp},v1={hex_signature}"
    """
    to_sign = f"{timestamp}.".encode("utf-8") + payload_bytes
    signature = hmac.new(
        secret.encode("utf-8"),
        to_sign,
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={signature}"


def verify_webhook_signature(secret: str, payload_bytes: bytes, signature_header: str, tolerance_seconds: int = 300) -> bool:
    """
    Verifies incoming webhook signature and prevents replay attacks.
    Header format: "t={timestamp},v1={signature}"
    """
    try:
        parts = dict(item.split("=", 1) for item in signature_header.split(","))
        timestamp_str = parts.get("t")
        expected_sig = parts.get("v1")
        if not timestamp_str or not expected_sig:
            return False

        timestamp = int(timestamp_str)
        now = int(time.time())

        # Enforce tolerance window against replay attacks
        if abs(now - timestamp) > tolerance_seconds:
            return False

        to_sign = f"{timestamp}.".encode("utf-8") + payload_bytes
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            to_sign,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_sig, expected_sig)
    except Exception:
        return False
