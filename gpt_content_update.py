import os
import requests
import base64
from openai import OpenAI

# خواندن متغیرها از محیط
OWNER = os.getenv("OWNERVALUE")
REPO = os.getenv("REPOVALUE")
TOKEN = os.getenv("REPO_TOKENVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")

# --- مرحله 1: چاپ و تست دسترسی ---
print(f"🔍 OWNER: {OWNER}")
print(f"🔍 REPO : {REPO}")
print(f"🔍 Token starts with: {TOKEN[:4]}... (len={len(TOKEN)})")

# تست دسترسی به ریپو
check_url = f"https://api.github.com/repos/{OWNER}/{REPO}"
resp = requests.get(check_url, headers={"Authorization": f"token {TOKEN}"})
print(f"📡 Repo access check → {resp.status_code}")

if resp.status_code != 200:
    print("❌ GitHub access failed. Possible issues:")
    print("   - OWNER or REPO spelling mismatch (case-sensitive)")
    print("   - Token lacks 'repo' and 'workflow' permissions")
    print(f"API Response: {resp.text}")
    exit(1)
else:
    print("✅ Repo is accessible!")

# --- مرحله 2: شروع OpenAI Client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- مرحله 3: تولید محتوا ---
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

# --- مرحله 4: آپلود فایل در GitHub ---
file_path = "content/latest.txt"
get_file_url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{file_path}"

# گرفتن SHA اگر فایل وجود دارد
r = requests.get(get_file_url, headers={"Authorization": f"token {TOKEN}"})
sha = r.json().get("sha") if r.status_code == 200 else None

# آماده کردن JSON
data = {
    "message": "Automated content update",
    "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
}
if sha:
    data["sha"] = sha

# آپلود
put_resp = requests.put(
    get_file_url,
    headers={"Authorization": f"token {TOKEN}"},
    json=data
)

if put_resp.status_code in (200, 201):
    print("✅ File updated successfully!")
else:
    print(f"❌ File update failed ({put_resp.status_code}): {put_resp.text}")
    exit(1)
