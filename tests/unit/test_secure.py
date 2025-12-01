# -*- coding: utf-8 -*-

"""
Unit tests for migasfree_client.secure module
"""

import json
import pytest
from unittest.mock import patch

from migasfree_client import secure
from jwcrypto import jwk, jws, jwe


class TestKeyManagement:
    """Tests for JWK key loading"""

    def test_load_jwk_private_key(self, private_key_path):
        """Test loading private key from PEM file"""
        key = secure.load_jwk(private_key_path)
        assert isinstance(key, jwk.JWK)
        assert key.has_private is True

    def test_load_jwk_public_key(self, public_key_path):
        """Test loading public key from PEM file"""
        key = secure.load_jwk(public_key_path)
        assert isinstance(key, jwk.JWK)
        assert key.has_private is False


class TestSigningAndVerification:
    """Tests for signing and verification operations"""

    def test_sign_dict_claims(self, private_key_path):
        """Test signing dictionary claims"""
        claims = {"user": "test", "action": "login"}
        result = secure.sign(claims, private_key_path)

        assert isinstance(result, str)
        assert len(result) > 0
        # JWS tokens are serialized as JSON by default in this implementation
        assert "{" in result
        assert "signature" in result

    def test_sign_string_claims(self, private_key_path):
        """Test signing string claims"""
        claims = "test message"
        result = secure.sign(claims, private_key_path)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_verify_valid_signature(self, private_key_path, public_key_path):
        """Test verifying valid signature"""
        claims = {"user": "test", "data": "important"}
        signed = secure.sign(claims, private_key_path)

        result = secure.verify(signed, public_key_path)
        verified_data = json.loads(result)

        assert verified_data == claims

    def test_verify_invalid_signature(self, public_key_path):
        """Test verifying invalid signature raises exception"""
        # Invalid JSON structure
        invalid_token = "invalid.token"

        with pytest.raises((jws.InvalidJWSObject, ValueError)):
            secure.verify(invalid_token, public_key_path)

    def test_sign_verify_roundtrip(self, private_key_path, public_key_path):
        """Test complete sign and verify cycle"""
        original_data = {"message": "Hello, World!", "timestamp": 12345}

        # Sign
        signed = secure.sign(original_data, private_key_path)

        # Verify
        verified = secure.verify(signed, public_key_path)
        result = json.loads(verified)

        assert result == original_data


class TestEncryptionAndDecryption:
    """Tests for encryption and decryption operations"""

    def test_encrypt_claims(self, public_key_path):
        """Test encrypting claims"""
        claims = {"secret": "data", "value": 42}
        result = secure.encrypt(claims, public_key_path)

        assert isinstance(result, str)
        assert len(result) > 0
        # JWE tokens are serialized as JSON
        assert "{" in result
        assert "ciphertext" in result

    def test_decrypt_encrypted_data(self, private_key_path, public_key_path):
        """Test decrypting encrypted data"""
        claims = {"secret": "confidential", "level": "top"}
        encrypted = secure.encrypt(claims, public_key_path)

        result = secure.decrypt(encrypted, private_key_path)
        decrypted_data = json.loads(result)

        assert decrypted_data == claims

    def test_decrypt_invalid_data(self, private_key_path):
        """Test decrypting invalid data raises exception"""
        invalid_token = "invalid.encrypted.data.token.here"

        with pytest.raises(jwe.InvalidJWEData):
            secure.decrypt(invalid_token, private_key_path)

    def test_encrypt_decrypt_roundtrip(self, private_key_path, public_key_path):
        """Test complete encrypt and decrypt cycle"""
        original_data = {"password": "secret123", "user": "admin"}

        # Encrypt
        encrypted = secure.encrypt(original_data, public_key_path)

        # Decrypt
        decrypted = secure.decrypt(encrypted, private_key_path)
        result = json.loads(decrypted)

        assert result == original_data


class TestWrapAndUnwrap:
    """Tests for high-level wrap and unwrap operations"""

    def test_wrap_data(self, private_key_path, public_key_path):
        """Test wrapping data (sign + encrypt)"""
        data = {"message": "secure data"}
        result = secure.wrap(data, private_key_path, public_key_path)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should be a JWE token (JSON serialized)
        assert "{" in result
        assert "ciphertext" in result

    def test_unwrap_data(self, private_key_path, public_key_path):
        """Test unwrapping data (decrypt + verify)"""
        original_data = {"important": "information", "id": 123}
        wrapped = secure.wrap(original_data, private_key_path, public_key_path)

        result = secure.unwrap(wrapped, private_key_path, public_key_path)

        assert result == original_data

    def test_wrap_unwrap_roundtrip(self, private_key_path, public_key_path):
        """Test complete wrap and unwrap cycle"""
        original_data = {
            "user": "testuser",
            "permissions": ["read", "write"],
            "timestamp": 1234567890,
        }

        # Wrap
        wrapped = secure.wrap(original_data, private_key_path, public_key_path)

        # Unwrap
        unwrapped = secure.unwrap(wrapped, private_key_path, public_key_path)

        assert unwrapped == original_data

    @patch("migasfree_client.secure.gettext", side_effect=lambda x: x)
    def test_unwrap_invalid_jwe_data(
        self, mock_gettext, private_key_path, public_key_path
    ):
        """Test unwrapping invalid JWE data returns error message"""
        invalid_data = "not.valid.jwe.data.here"

        result = secure.unwrap(invalid_data, private_key_path, public_key_path)

        # Should return error message, not raise exception
        assert isinstance(result, str)
        assert "Invalid" in result

    @patch("migasfree_client.secure.gettext", side_effect=lambda x: x)
    def test_unwrap_invalid_signature(
        self, mock_gettext, private_key_path, public_key_path
    ):
        """Test unwrapping data with invalid signature"""
        # Create data with valid encryption but invalid signature
        # We need to manually construct a valid JWE that contains an invalid JWS

        # 1. Create a fake JWS (just a dict, not signed properly)
        fake_jws = {"sign": "invalid_signature", "data": {"message": "test"}}

        # 2. Encrypt this fake JWS
        encrypted = secure.encrypt(fake_jws, public_key_path)

        # 3. Try to unwrap
        # unwrap will decrypt it (success), then try to verify 'sign' (fail)

        # Note: secure.verify expects a serialized JWS. 'invalid_signature' is not.
        # secure.verify raises InvalidJWSObject if format is wrong, or InvalidJWSSignature if sig is wrong.
        # secure.unwrap catches InvalidJWSSignature.
        # If we pass a string that isn't a valid JWS structure, verify might raise InvalidJWSObject.
        # Let's mock verify to raise InvalidJWSSignature to test the exception handling in unwrap.

        with patch("migasfree_client.secure.verify") as mock_verify:
            mock_verify.side_effect = jws.InvalidJWSSignature("Invalid signature")
            result = secure.unwrap(encrypted, private_key_path, public_key_path)

        # Should return error message
        assert isinstance(result, str)
        assert "Invalid" in result

    def test_wrap_unwrap_with_complex_data(self, private_key_path, public_key_path):
        """Test wrap/unwrap with complex nested data structures"""
        complex_data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "roles": ["admin", "user"],
            },
            "metadata": {"created": "2024-01-01", "version": 2},
            "items": [1, 2, 3, 4, 5],
        }

        wrapped = secure.wrap(complex_data, private_key_path, public_key_path)
        unwrapped = secure.unwrap(wrapped, private_key_path, public_key_path)

        assert unwrapped == complex_data


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_sign_empty_dict(self, private_key_path):
        """Test signing empty dictionary"""
        result = secure.sign({}, private_key_path)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encrypt_empty_dict(self, public_key_path):
        """Test encrypting empty dictionary"""
        result = secure.encrypt({}, public_key_path)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_wrap_empty_data(self, private_key_path, public_key_path):
        """Test wrapping empty data"""
        result = secure.wrap({}, private_key_path, public_key_path)
        assert isinstance(result, str)

    def test_sign_large_data(self, private_key_path):
        """Test signing large data structure"""
        large_data = {"items": list(range(1000)), "text": "x" * 10000}
        result = secure.sign(large_data, private_key_path)
        assert isinstance(result, str)
