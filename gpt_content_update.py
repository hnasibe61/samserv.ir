import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import base64

load_dotenv()

GITHUB_TOKEN = os.getenv("REPO_TOKENVALUE")
GITHUB_OWNER = os.getenv("OWNERVALUE")
GITHUB_REPO = os.getenv("REPOVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")

BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

client = OpenAI(api_key=OPENAI_KEY)

def create_branch(branch_name):
    main_branch = requests.get(BASE_URL, headers=HEADERS).json()["default_branch"]
    sha = requests.get(f"{BASE_URL}/git/refs/heads/{main_branch}", headers=HEADERS).json()["object"]["sha"]
    requests.post(f"{BASE_URL}/git/refs", headers=HEADERS, json={
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    })

def get_file_content(path, branch):
    res = requests.get(f"{BASE_URL}/contents/{path}?ref={branch}", headers=HEADERS).json()
    return base64.b64decode(res["content"]).decode(), res["sha"]

def update_file(path, content, sha, branch, message):
    encoded = base64.b64encode(content.encode()).decode()
    requests.put(f"{BASE_URL}/contents/{path}", headers=HEADERS, json={
        "message": message,
        "content": encoded,
        "sha": sha,
        "branch": branch
    })

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

def add_blog_post():
    today = datetime.now().strftime("%Y-%m-%d")
    branch = f"blog-{today}"
    create_branch(branch)
    blog_content = gpt_generate_blog()

    file_path = f"blog/{today}.html"
    html = f"<html><body>{blog_content}</body></html>"

    update_file(file_path, html, None, branch, f"Add blog post {today}")
    print(f"Blog post added for {today}")

def daily_site_check():
    branch = f"site-update-{datetime.now().strftime('%Y-%m-%d')}"
    create_branch(branch)
    file_path = "index.html"  # صفحه اصلی سایت
    old_content, sha = get_file_content(file_path, branch)

    new_content = gpt_optimize_site(old_content)
    update_file(file_path, new_content, sha, branch, "Daily site optimization")
    print("Site optimization done.")

if __name__ == "__main__":
    task = os.getenv("TASK", "blog")
    if task == "blog":
        add_blog_post()
    elif task == "update":
        daily_site_check()
