# update_version.py
import os
import datetime

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
VERSION_FILE = os.path.join(FRONTEND_DIR, "version.txt")

timestamp = datetime.datetime.now().strftime("%Y.%m.%d.%H%M%S")

with open(VERSION_FILE, "w", encoding="utf-8") as f:
    f.write(timestamp)

print(f"✅ Updated version.txt → {timestamp}")
