import os
import requests
from datetime import datetime
from openai import OpenAI
import base64
import sys

# ==== خواندن متغیرها از Environment ====
GITHUB_TOKEN = os.getenv("REPO_TOKENVALUE")
GITHUB_OWNER = os.getenv("OWNERVALUE")
GITHUB_REPO = os.getenv("REPOVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")

# ==== چک کردن اینکه همه متغیرها مقدار دارند ====
missing_vars = []
if not GITHUB_TOKEN:
    missing_vars.append("REPO_TOKENVALUE")
if not GITHUB_OWNER:
    missing_vars.append("OWNERVALUE")
if not GITHUB_REPO:
    missing_vars.append("REPOVALUE")
if not OPENAI_API_KEY:
    missing_vars.append("OPENAI_API_KEYVALUE")

if missing_vars:
    print(f"❌ خطا: این متغیرها مقدار ندارند: {', '.join(missing_vars)}")
    sys.exit(1)

# ==== پیکربندی GitHub API ====
BASE_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ==== اتصال به OpenAI ====
client = OpenAI(api_key=OPENAI_API_KEY)

# ==== توابع کار با GitHub ====
def get_file_content(path, branch="main"):
    """دریافت محتوای فایل و sha از main"""
    url = f"{BASE_URL}/contents/{path}?ref={branch}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 404:
        return "", None  # فایل جدید است
    res = res.json()
    return base64.b64decode(res["content"]).decode(), res["sha"]

def update_file(path, content, sha=None, branch="main", message="update file"):
    """آپلود یا به‌روزرسانی فایل در main"""
    encoded = base64.b64encode(content.encode()).decode()
    data = {
        "message": message,
        "content": encoded,
        "branch": branch
    }
    if sha:
        data["sha"] = sha
    res = requests.put(f"{BASE_URL}/contents/{path}", headers=HEADERS, json=data)
    res.raise_for_status()
    print(f"✅ {path} updated on {branch}")

# ==== توابع مرتبط با OpenAI ====
def gpt_generate_blog():
    prompt = """
    تولید یک مقاله وبلاگی جذاب، تخصصی و سئو شده درباره یکی از موضوعات تعمیرات لپ‌تاپ، پاوربانک، اسپیکر یا سایر خدمات
    سام‌ترونیک. طول مقاله بین ۷۰۰ تا ۱۰۰۰ کلمه باشد، شامل تیتر H1, H2 و پاراگراف‌های منسجم باشد.
    بنویس به زبان فارسی و لحن کارشناس فنی.
    """
    resp = client.responses.create(model="gpt-4.1", input=prompt)
    return resp.output_text

def gpt_optimize_site(content):
    prompt = f"""
    این متن از سایتی خدمات تعمیرات است. آن را بررسی و بهینه کن برای سئو و خوانایی. فقط بخش‌های لازم را تغییر بده.
    ---
    {content}
    """
    resp = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return resp.output_text

# ==== وظایف اصلی ====
def add_blog_post():
    today = datetime.now().strftime("%Y-%m-%d")
    file_path = f"blog/{today}.html"
    blog_content = gpt_generate_blog()
    html = f"<html><body>{blog_content}</body></html>"
    _, sha = get_file_content(file_path, "main")
    update_file(file_path, html, sha, "main", f"Add blog post {today}")

def daily_site_check():
    file_path = "index.html"
    old_content, sha = get_file_content(file_path, "main")
    new_content = gpt_optimize_site(old_content)
    update_file(file_path, new_content, sha, "main", "Daily site optimization")
