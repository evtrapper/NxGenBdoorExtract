# modules/encryption.py
from cryptography.fernet import Fernet
import base64
import os
import hashlib
import random
import string
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import json

def generate_key():
    """Generate a random encryption key"""
    return Fernet.generate_key()

def derive_key_from_password(password, salt=None):
    """Derive an encryption key from a password"""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data, key):
    """Encrypt data using Fernet symmetric encryption"""
    if isinstance(data, dict) or isinstance(data, list):
        data = json.dumps(data)
    
    if isinstance(data, str):
        data = data.encode()
    
    f = Fernet(key)
    return f.encrypt(data)

def decrypt_data(encrypted_data, key):
    """Decrypt data using Fernet symmetric encryption"""
    f = Fernet(key)
    decrypted_data = f.decrypt(encrypted_data)
    
    # Try to parse as JSON if possible
    try:
        return json.loads(decrypted_data)
    except:
        # Return as string if not JSON
        return decrypted_data.decode()

def secure_file_encryption(input_file, output_file, key):
    """Encrypt a file with additional security measures"""
    try:
        with open(input_file, 'rb') as f:
            data = f.read()
        
        # Encrypt the data
        encrypted_data = encrypt_data(data, key)
        
        # Add a random padding to obscure the file size
        padding_size = random.randint(1024, 16384)  # 1KB to 16KB padding
        padding = os.urandom(padding_size)
        
        # Create a structure with the encrypted data and padding
        structure = {
            "data": base64.b64encode(encrypted_data).decode(),
            "metadata": {
                "created": int(time.time()),
                "id": ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            }
        }
        
        # Save the structure as JSON
        with open(output_file, 'w') as f:
            json.dump(structure, f)
        
        return True
    except:
        return False

def secure_file_decryption(input_file, output_file, key):
    """Decrypt a file that was encrypted with secure_file_encryption"""
    try:
        with open(input_file, 'r') as f:
            structure = json.load(f)
        
        # Get the encrypted data
        encrypted_data = base64.b64decode(structure["data"])
        
        # Decrypt the data
        decrypted_data = decrypt_data(encrypted_data, key)
        
        # Save the decrypted data
        if isinstance(decrypted_data, (dict, list)):
            with open(output_file, 'w') as f:
                json.dump(decrypted_data, f)
        else:
            mode = 'wb' if isinstance(decrypted_data, bytes) else 'w'
            with open(output_file, mode) as f:
                f.write(decrypted_data)
        
        return True
    except:
        return False