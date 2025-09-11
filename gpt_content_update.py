import os
import requests
import subprocess
import tempfile
from openai import OpenAI

# --- تنظیمات ---
OWNER  = os.getenv("OWNERVALUE")
REPO   = os.getenv("REPOVALUE")
TOKEN  = os.getenv("REPO_TOKENVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")
BRANCH = "main"  # اگر سایتت از برنچ دیگری آپلود میشه این رو تغییر بده

# --- مرحله 1: چاپ اطلاعات ---
print(f"🔍 OWNER: {OWNER}")
print(f"🔍 REPO : {REPO}")
print(f"🔍 Token starts with: {TOKEN[:4]}... (len={len(TOKEN)})")

# --- مرحله 2: تست دسترسی GitHub ---
check_url = f"https://api.github.com/repos/{OWNER}/{REPO}"
resp = requests.get(check_url, headers={"Authorization": f"token {TOKEN}"})
print(f"📡 Repo access check → {resp.status_code}")

if resp.status_code != 200:
    print("❌ GitHub access failed. Check OWNER/REPO spelling and token permissions.")
    print(f"API Response: {resp.text}")
    exit(1)
else:
    print("✅ Repo is accessible!")

# --- مرحله 3: تولید محتوا ---
client = OpenAI(api_key=OPENAI_API_KEY)
print("📝 Generating content with OpenAI...")

try:
    response = client.responses.create(
        model="gpt-4o-mini",
        input="Generate a short news update about electronics repair trends in Persian, ~100 words."
    )
    content = response.output[0].content[0].text.strip()
    print("✅ Content generated:", content)
except Exception as e:
    print("❌ OpenAI content generation failed:", str(e))
    exit(1)

# --- مرحله 4: کلون و آپدیت با Force Push ---
temp_dir = tempfile.mkdtemp()
repo_url = f"https://{TOKEN}@github.com/{OWNER}/{REPO}.git"

# کلون برنچ اصلی
subprocess.run(["git", "clone", "--branch", BRANCH, repo_url, temp_dir], check=True)
os.chdir(temp_dir)

# تنظیم هویت گیت برای محیط CI
subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)

# مسیر فایل موردنظر
file_path = "content/latest.txt"
os.makedirs(os.path.dirname(file_path), exist_ok=True)

# ذخیره محتوای جدید
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Commit و Force Push
subprocess.run(["git", "add", file_path], check=True)
subprocess.run(["git", "commit", "-m", "update content"], check=True)
subprocess.run(["git", "push", "--force", "origin", BRANCH], check=True)

print("✅ File updated on main branch with force push - site updated, no commit history bloat!")
