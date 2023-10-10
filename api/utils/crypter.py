# from Crypto.Cipher import AES
from Cryptodome.Cipher import AES
from core import settings
import base64


def encrypt(plaintext):
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    final_chipper = cipher.nonce + ciphertext + tag
    base64_encoded = base64.b64encode(final_chipper)
    final_string = base64_encoded.decode("utf-8")
    return final_string


def decrypt(ciphertext):
    key = settings.ENCRYPTION_KEY.encode("utf-8")
    base64_decoded = base64.b64decode(ciphertext)
    nonce = base64_decoded[:16]
    tag = base64_decoded[-16:]
    ciphertext = base64_decoded[16:-16]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    return decrypted_data.decode("utf-8")
