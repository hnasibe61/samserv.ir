import os
import sys
import base64
import requests
from datetime import datetime
from openai import OpenAI

# --- خواندن متغیرهای محیطی ---
GITHUB_TOKEN = os.getenv("REPO_TOKENVALUE")
GITHUB_OWNER = os.getenv("OWNERVALUE")
GITHUB_REPO = os.getenv("REPOVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")

# --- بررسی متغیرهای ضروری ---
missing = [name for name, val in {
    "REPO_TOKENVALUE": GITHUB_TOKEN,
    "OWNERVALUE": GITHUB_OWNER,
    "REPOVALUE": GITHUB_REPO,
    "OPENAI_API_KEYVALUE": OPENAI_API_KEY
}.items() if not val]

if missing:
    print(f"❌ خطا: متغیرهای محیطی زیر مقدار ندارند: {', '.join(missing)}")
    sys.exit(1)

print("✅ متغیرهای محیطی لازم مقدار دارند (منتشر نشود):", bool(OPENAI_API_KEY))

# --- تنظیم GitHub API ---
BASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# --- کلاینت OpenAI ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- توابع کمکی ---

def get_file_content(path, branch="main"):
    url = f"{BASE_URL}/contents/{path}?ref={branch}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 404:
        return "", None
    res.raise_for_status()
    data = res.json()
    return base64.b64decode(data["content"]).decode(), data["sha"]


def update_file(path, content, sha=None, branch="main", message="update file"):
    encoded = base64.b64encode(content.encode()).decode()
    payload = {"message": message, "content": encoded, "branch": branch}
    if sha:
        payload["sha"] = sha
    res = requests.put(f"{BASE_URL}/contents/{path}", headers=HEADERS, json=payload)
    res.raise_for_status()
    print(f"✅ فایل {path} روی {branch} بروزرسانی شد")

# --- GPT ---

def gpt_generate_blog():
    prompt = (
        "یک مقاله وبلاگی تخصصی و سئو شده برای وب‌سایت سام‌ترونیک بنویس، "
        "درباره یکی از موضوعات تعمیرات لپ‌تاپ، پاوربانک، اسپیکر یا هدست، "
        "بین ۷۰۰ تا ۱۰۰۰ کلمه، همراه با تیترهای H1 و H2، زبان فارسی و لحن کارشناس فنی."
    )
    resp = client.responses.create(model="gpt-4.1", input=prompt)
    return resp.output_text


def gpt_optimize_content(content):
    if not content or not content.strip():
        print("index.html خالی است — بهینه‌سازی انجام نشد")
        return content
    prompt = f"""
    محتوای زیر مربوط به وب‌سایت خدماتی است، آن را از نظر سئو و خوانایی بهینه کن:
    ---
    {content}
    """
    resp = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return resp.output_text

# --- کارهای اصلی ---

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
    if new_content != old_content:
        update_file(path, new_content, sha, "main", "Daily site optimization")
    else:
        print("هیچ تغییری در index.html ایجاد نشد؛ آپدیتی انجام نشد")


if __name__ == "__main__":
    add_blog_post()
    daily_site_check()
