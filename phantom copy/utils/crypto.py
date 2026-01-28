"""
Cryptographic utilities for Phantom Bot
Handles encryption/decryption of sensitive data like payment info
"""

import os
import base64
import secrets
import hashlib
from pathlib import Path
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog

logger = structlog.get_logger()


class CryptoManager:
    """Manages encryption/decryption of sensitive data"""
    
    _instance: Optional['CryptoManager'] = None
    _fernet: Optional[Fernet] = None
    _key_file: Path = Path("data/.phantom_key")
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._fernet is None:
            self._initialize_key()
    
    def _initialize_key(self):
        """Initialize or load the encryption key"""
        self._key_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self._key_file.exists():
            # Load existing key
            with open(self._key_file, 'rb') as f:
                key = f.read()
            logger.debug("Loaded existing encryption key")
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self._key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(self._key_file, 0o600)
            logger.info("Generated new encryption key")
        
        self._fernet = Fernet(key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data and return base64 encoded string"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        encrypted = self._fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 encoded encrypted data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise ValueError("Failed to decrypt data - invalid key or corrupted data")
    
    def encrypt_card(self, card_number: str) -> str:
        """Encrypt a credit card number"""
        # Remove spaces and dashes
        clean_number = card_number.replace(' ', '').replace('-', '')
        return self.encrypt(clean_number)
    
    def decrypt_card(self, encrypted_card: str) -> str:
        """Decrypt a credit card number and format it"""
        decrypted = self.decrypt(encrypted_card)
        # Format as groups of 4
        return ' '.join(decrypted[i:i+4] for i in range(0, len(decrypted), 4))
    
    def encrypt_cvv(self, cvv: str) -> str:
        """Encrypt CVV"""
        return self.encrypt(cvv)
    
    def decrypt_cvv(self, encrypted_cvv: str) -> str:
        """Decrypt CVV"""
        return self.decrypt(encrypted_cvv)
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Hash a password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        
        key = kdf.derive(password.encode('utf-8'))
        
        return (
            base64.urlsafe_b64encode(key).decode('utf-8'),
            base64.urlsafe_b64encode(salt).decode('utf-8')
        )
    
    def verify_password(self, password: str, hashed: str, salt: str) -> bool:
        """Verify a password against its hash"""
        salt_bytes = base64.urlsafe_b64decode(salt.encode('utf-8'))
        new_hash, _ = self.hash_password(password, salt_bytes)
        return secrets.compare_digest(new_hash, hashed)
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def generate_task_id(self) -> str:
        """Generate a unique task ID"""
        return secrets.token_hex(16)
    
    def mask_card(self, card_number: str) -> str:
        """Mask a card number for display (show last 4 digits)"""
        clean = card_number.replace(' ', '').replace('-', '')
        if len(clean) >= 4:
            return f"**** **** **** {clean[-4:]}"
        return "****"
    
    def mask_email(self, email: str) -> str:
        """Mask an email for display"""
        if '@' in email:
            local, domain = email.split('@')
            if len(local) > 2:
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
            else:
                masked_local = '*' * len(local)
            return f"{masked_local}@{domain}"
        return '***@***'


# Global crypto instance
crypto = CryptoManager()


def encrypt(data: Union[str, bytes]) -> str:
    """Encrypt data"""
    return crypto.encrypt(data)


def decrypt(data: str) -> str:
    """Decrypt data"""
    return crypto.decrypt(data)


def mask_sensitive(data: str, data_type: str = "generic") -> str:
    """Mask sensitive data for logging/display"""
    if data_type == "card":
        return crypto.mask_card(data)
    elif data_type == "email":
        return crypto.mask_email(data)
    elif data_type == "phone":
        if len(data) >= 4:
            return f"***-***-{data[-4:]}"
        return "***"
    else:
        # Generic masking
        if len(data) > 4:
            return data[:2] + '*' * (len(data) - 4) + data[-2:]
        return '*' * len(data)
