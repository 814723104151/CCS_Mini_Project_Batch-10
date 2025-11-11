import os, json, time, base64
from pathlib import Path
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configuration
BROKER = "localhost"
TOPIC = "iot/ecc/encrypted"
KEY_DIR = Path("keys")
DEVICE_KEY = KEY_DIR / "device_private.pem"
SERVER_PUB = KEY_DIR / "server_public.pem"

def ensure_key():
    KEY_DIR.mkdir(exist_ok=True)
    if not DEVICE_KEY.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        DEVICE_KEY.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        print("[Device] New ECC key generated.")
    else:
        print("[Device] ECC key found.")

def load_keys():
    device_key = serialization.load_pem_private_key(DEVICE_KEY.read_bytes(), None)
    server_pub = serialization.load_pem_public_key(SERVER_PUB.read_bytes())
    return device_key, server_pub

def derive_aes_key(shared):
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"ecc-iot")
    return hkdf.derive(shared)

def encrypt(pub_key, plaintext):
    eph_priv = ec.generate_private_key(ec.SECP256R1())
    eph_pub = eph_priv.public_key()
    shared = eph_priv.exchange(ec.ECDH(), pub_key)
    key = derive_aes_key(shared)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    eph_pub_bytes = eph_pub.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint
    )
    return eph_pub_bytes, nonce, ct

def main():
    ensure_key()
    device_key, server_pub = load_keys()
    client = mqtt.Client()
    client.connect(BROKER)
    client.loop_start()

    while True:
        sensor = {
            "device": "Node-1",
            "temperature": round(20 + 5 * (os.urandom(1)[0]/255), 2),
            "humidity": round(40 + 20 * (os.urandom(1)[0]/255), 2),
            "time": int(time.time())
        }
        data = json.dumps(sensor).encode()
        eph_pub, nonce, ct = encrypt(server_pub, data)

        packet = {
            "ephemeral_pub": base64.b64encode(eph_pub).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ct).decode()
        }

        client.publish(TOPIC, json.dumps(packet))
        print("[Device] Encrypted & sent:", sensor)
        time.sleep(5)

if __name__ == "__main__":
    main()
