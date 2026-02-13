"""
Adyen Client-Side Encryption (CSE)

Encrypts payment card data using Adyen's public key format.
Used by Footsites (Foot Locker, Champs, Eastbay, Finish Line) and other
sites that use Adyen as their payment processor.

Spec reference: Adyen CSE v0_1_25
Encryption scheme: RSA-OAEP (SHA-1) wrapping AES-256-CBC

Dependencies: ``cryptography`` (already in requirements.txt)
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
import structlog

logger = structlog.get_logger()

# Adyen CSE version identifier embedded in every encrypted payload
_ADYEN_VERSION = "0_1_25"
_PREFIX = f"adyenjs_{_ADYEN_VERSION}$"


class AdyenEncryptor:
    """
    Encrypts card fields per Adyen's CSE specification.

    Usage::

        enc = AdyenEncryptor(public_key_hex)
        encrypted = enc.encrypt_card(
            number="4111111111111111",
            expiry_month="03",
            expiry_year="2030",
            cvv="737",
        )
        # → "adyenjs_0_1_25$..."
    """

    def __init__(self, public_key_hex: str) -> None:
        """
        Parameters
        ----------
        public_key_hex:
            The Adyen public key in ``"<exponent>|<modulus>"`` hex format,
            e.g. ``"10001|BB2..."`` (found in the site's JS payment config).
        """
        self._rsa_key = self._parse_adyen_key(public_key_hex)
        logger.debug("AdyenEncryptor initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encrypt_card(
        self,
        number: str,
        expiry_month: str,
        expiry_year: str,
        cvv: str,
        holder_name: str = "",
    ) -> str:
        """Encrypt all card fields into a single Adyen CSE payload.

        Returns the ``adyenjs_0_1_25$...`` string that goes into the
        ``encryptedCardData`` / ``encryptedSecurityCode`` payment field.
        """
        generation_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

        data: Dict[str, str] = {
            "number": number.replace(" ", "").replace("-", ""),
            "cvc": cvv,
            "expiryMonth": expiry_month.zfill(2),
            "expiryYear": str(expiry_year),
            "generationtime": generation_time,
        }
        if holder_name:
            data["holderName"] = holder_name

        return self._encrypt_field(data)

    def encrypt_field(self, field_name: str, value: str) -> str:
        """Encrypt a single field (e.g. ``encryptedSecurityCode``)."""
        generation_time = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
        return self._encrypt_field(
            {field_name: value, "generationtime": generation_time}
        )

    # ------------------------------------------------------------------
    # Internal crypto
    # ------------------------------------------------------------------

    def _encrypt_field(self, data: dict) -> str:
        """Core encryption: AES-256-CBC payload wrapped with RSA-OAEP."""
        plaintext = json.dumps(data, separators=(",", ":")).encode()

        # 1 — Generate random AES-256 key + IV
        aes_key = os.urandom(32)  # 256 bits
        iv = os.urandom(16)  # 128 bits

        # 2 — AES-256-CBC encrypt the JSON payload (PKCS7 padded)
        cipher = Cipher(algorithms.AES(aes_key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        padded = self._pkcs7_pad(plaintext, 16)
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        # 3 — RSA-OAEP encrypt the AES key
        encrypted_aes_key = self._rsa_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA1(),
                label=None,
            ),
        )

        # 4 — Assemble: prefix$b64(rsa_enc_key)$b64(iv + ciphertext)
        b64_key = base64.b64encode(encrypted_aes_key).decode()
        b64_payload = base64.b64encode(iv + ciphertext).decode()

        return f"{_PREFIX}{b64_key}${b64_payload}"

    @staticmethod
    def _pkcs7_pad(data: bytes, block_size: int) -> bytes:
        pad_len = block_size - (len(data) % block_size)
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _parse_adyen_key(hex_key: str):
        """Parse ``"exponent_hex|modulus_hex"`` into an RSA public key."""
        parts = hex_key.split("|")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid Adyen public key format — expected 'exp|mod', got {len(parts)} parts"
            )

        exponent = int(parts[0], 16)
        modulus = int(parts[1], 16)

        public_numbers = RSAPublicNumbers(exponent, modulus)
        return public_numbers.public_key()
