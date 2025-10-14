from cryptography.fernet import Fernet
from urllib.parse import quote, unquote
from app.core.config import settings

# Generate a key once and store it securely (e.g., in settings or env)
# key = Fernet.generate_key()
# Save it and reuse it
fernet = Fernet(settings.SECRETE_KEY)

def encrypt_for_url(data: str) -> str:
    # Encrypt
    encrypted_bytes = fernet.encrypt(data.encode())
    # Convert to URL-safe string
    return quote(encrypted_bytes.decode())

def decrypt_from_url(data: str) -> str:
    # Decode from URL encoding
    encrypted_bytes = unquote(data).encode()
    # Decrypt back to original
    return fernet.decrypt(encrypted_bytes).decode()
