import os, json, base64
from pathlib import Path
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

BROKER = "localhost"
TOPIC = "iot/ecc/encrypted"
KEY_DIR = Path("keys")
SERVER_KEY = KEY_DIR / "server_private.pem"
SERVER_PUB = KEY_DIR / "server_public.pem"

def ensure_server_key():
    KEY_DIR.mkdir(exist_ok=True)
    if not SERVER_KEY.exists():
        priv = ec.generate_private_key(ec.SECP256R1())
        SERVER_KEY.write_bytes(
            priv.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            )
        )
        SERVER_PUB.write_bytes(
            priv.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )
        print("[Server] New ECC key generated.")
    else:
        print("[Server] ECC key found.")

def load_private():
    return serialization.load_pem_private_key(SERVER_KEY.read_bytes(), None)

def derive_aes_key(shared):
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"ecc-iot")
    return hkdf.derive(shared)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        eph_pub = base64.b64decode(data["ephemeral_pub"])
        nonce = base64.b64decode(data["nonce"])
        ct = base64.b64decode(data["ciphertext"])
        eph_pub_obj = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), eph_pub)

        shared = userdata["priv"].exchange(ec.ECDH(), eph_pub_obj)
        key = derive_aes_key(shared)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ct, None)
        print("[Server] Decrypted message:", plaintext.decode())

    except Exception as e:
        print("[Server] Error:", e)

def main():
    ensure_server_key()
    priv = load_private()
    client = mqtt.Client(userdata={"priv": priv})
    client.connect(BROKER)
    client.subscribe(TOPIC)
    client.on_message = on_message
    print("[Server] Listening on topic:", TOPIC)
    client.loop_forever()

if __name__ == "__main__":
    main()
