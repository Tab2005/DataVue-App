from cryptography.fernet import Fernet
import os

key = Fernet.generate_key().decode()
env_file = ".env"

content = ""
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        content = f.read()

if "ENCRYPTION_KEY" not in content:
    with open(env_file, "a") as f:
        # Ensure newline if file is not empty and doesn't end with one
        if content and not content.endswith("\n"):
            f.write("\n")
        f.write(f"ENCRYPTION_KEY={key}\n")
    print(f"Key generated and added to {env_file}")
else:
    print("ENCRYPTION_KEY already exists in .env")
