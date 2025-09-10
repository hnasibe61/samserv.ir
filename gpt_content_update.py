import os
import requests
from datetime import datetime
from openai import OpenAI
import base64
import sys

# ===== خواندن متغیرهای محیطی =====
GITHUB_TOKEN = os.getenv("REPO_TOKENVALUE")
GITHUB_OWNER = os.getenv("OWNERVALUE")
GITHUB_REPO = os.getenv("REPOVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")

# ===== بررسی وجود متغیرها =====
missing = [
    name for name, val in {
        "REPO_TOKENVALUE": GITHUB_TOKEN,
        "OWNERVALUE": GITHUB_OWNER,
        "REPOVALUE": GITHUB_REPO,
        "OPENAI_API_KEYVALUE": OPENAI_API_KEY
    }.items() if not val
]

if missing:
    print(f"❌ خطا: این متغیرها مقدار ندارند: {', '.join(missing)}")
    sys.exit(1)

# ===== پیکربندی GitHub API =====
BASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ===== اتصال OpenAI =====
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== توابع کار با GitHub =====
def get_file_content(path, branch="main"):
    """برگشت محتوای فایل و sha از شاخه main"""
    url = f"{BASE_URL}/contents/{path}?ref={branch}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 404:
        return "", None
    res.raise_for_status()
    data = res.json()
    return base64.b64decode(data["content"]).decode(), data["sha"]

def update_file(path, content, sha=None, branch="main", message="update file"):
    """ایجاد یا بروزرسانی فایل روی main"""
    encoded = base64.b64encode(content.encode()).decode()
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha
    res = requests.put(f"{BASE_URL}/contents/{path}", headers=HEADERS, json=payload)
    res.raise_for_status()
    print(f"✅ فایل {path} با موفقیت روی {branch} تغییر کرد")

# ===== تولید محتوا با GPT =====
def gpt_generate_blog():
    prompt = """
    یک مقاله وبلاگی تخصصی و سئو شده برای وب‌سایت سام‌ترونیک بنویس، 
    درباره یکی از موضوعات تعمیرات لپ‌تاپ، پاوربانک، اسپیکر یا هدست، 
    بین ۷۰۰ تا ۱۰۰۰ کلمه، همراه با تیترهای H1 و H2، زبان فارسی و لحن کارشناس فنی.
    """
    resp = client.responses.create(model="gpt-4.1", input=prompt)
    return resp.output_text

def gpt_optimize_content(content):
    prompt = f"""
    محتوای زیر مربوط به وب‌سایت خدماتی است، آن را از نظر سئو و خوانایی بهینه کن:
    ---
    {content}
    """
    resp = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return resp.output_text

# ===== وظایف اصلی =====
def add_blog_post():
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"blog/{today}.html"
    blog_html = f"<html><body>{gpt_generate_blog()}</body></html>"
    _, sha = get_file_content(path)
    update_file(path, blog_html, sha, "main", f"Add blog post {today}")

def daily_site_check():
    path = "index.html"
    old_content, sha = get_file_content(path)
    new_content = gpt_optimize_content(old_content)
    update_file(path, new_content, sha, "main", "Daily site optimization")

# ===== اجرای مستقیم =====
if __name__ == "__main__":
    add_blog_post()
    daily_site_check()
