from cryptography.fernet import Fernet

# generate secret key (bytes)
key = Fernet.generate_key()

# decode bytes to str to remove the b'...' when printing
key_str = key.decode('utf-8')

print(f"Secret key (string): {key_str}")# prints: ... (no b' and no trailing ')
