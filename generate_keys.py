from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import os

# Create keys directory if it doesn't exist
os.makedirs("keys", exist_ok=True)

# --------- Generate Device Private Key ---------
device_private_key = ec.generate_private_key(ec.SECP256R1())
with open("keys/device_private.pem", "wb") as f:
    f.write(device_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

# --------- Generate Server Private Key ---------
server_private_key = ec.generate_private_key(ec.SECP256R1())
with open("keys/server_private.pem", "wb") as f:
    f.write(server_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

# --------- Extract Server Public Key ---------
server_public_key = server_private_key.public_key()
with open("keys/server_public.pem", "wb") as f:
    f.write(server_public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("ECC keys generated successfully in 'keys/' folder.")
