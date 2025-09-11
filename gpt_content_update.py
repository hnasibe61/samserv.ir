import os
import base64
import requests
import subprocess

OWNER = os.environ["OWNER"]
REPO = os.environ["REPO"]
TOKEN = os.environ["REPO_TOKEN"]

BRANCH = "content-update"
FILE_PATH = "content/latest.txt"

# مسیر کاری موقت
WORK_DIR = "/tmp/repo"

# Clone شناسنامه‌دار
subprocess.run([
    "git", "clone", f"https://{TOKEN}@github.com/{OWNER}/{REPO}.git", WORK_DIR
], check=True)

os.chdir(WORK_DIR)

# سوییچ به برنچ یا ساختش
subprocess.run(["git", "checkout", "-B", BRANCH], check=True)

# تولید محتوا (اینجا جای خروجی GPT)
content = "متن جدید از GPT..."
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

# Stage + commit
subprocess.run(["git", "add", FILE_PATH], check=True)
subprocess.run(["git", "commit", "-m", "update content"], check=True)

# Force push
subprocess.run([
    "git", "push", "--force", "origin", BRANCH
], check=True)
