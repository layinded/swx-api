import secrets
import string

def generate_api_key(length: int = 40, prefix: str = "pk_") -> str:
    """Generate a secure random API key."""
    chars = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(length))
    return f"{prefix}{random_part}"

