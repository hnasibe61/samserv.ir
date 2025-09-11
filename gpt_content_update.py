import os
import base64
import json
import requests
from openai import OpenAI

# خواندن متغیرهای محیطی
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")
OWNER = os.getenv("OWNERVALUE")
REPO = os.getenv("REPOVALUE")
REPO_TOKEN = os.getenv("REPO_TOKENVALUE")

# ستاپ کلاینت
client = OpenAI(api_key=OPENAI_API_KEY)

PRIMARY_MODEL = "gpt-4.1"
FALLBACK_MODEL = "gpt-4o-mini"

def generate_content(prompt, model_name):
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert content generator for an electronics repair website."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return resp.choices[0].message.content
    except Exception as e:
        if "insufficient_quota" in str(e):
            raise RuntimeError("Quota exhausted")
        else:
            raise

def update_github_file(path, content):
    """
    آپدیت یا ساخت فایل در ریپو
    اگر مسیر وجود نداشت، فایل جدید ایجاد می‌شود
    """
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {REPO_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # گِت برای پیدا کردن SHA (اگر فایل موجود بود)
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    # ساختن پوشه به صورت پیش‌فرض به GitHub API مربوط نیست — نیازی به ساخت پوشه جدا نداریم،
    # فقط با PUT می‌تونیم فایل توی مسیر جدید درست کنیم
    payload = {
        "message": "Auto update site content",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
    }
    if sha:
        payload["sha"] = sha  # آپدیت فایل موجود

    print(f"Owner={OWNER}, Repo={REPO}, Token starts with: {REPO_TOKEN[:4]}... length={len(REPO_TOKEN)}")
    print(f"Target path: {path}, Existing file: {'YES' if sha else 'NO'}")

    res = requests.put(url, headers=headers, json=payload)

    if res.status_code not in (200, 201):
        raise Exception(
            f"GitHub update failed ({res.status_code}): {res.text}"
        )

if __name__ == "__main__":
    prompt_text = "Write an SEO-optimized blog post about repairing laptop power adapters."

    try:
        text = generate_content(prompt_text, PRIMARY_MODEL)
    except RuntimeError:
        print(f"⚠️ Quota issue in {PRIMARY_MODEL}, switching to {FALLBACK_MODEL}...")
        text = generate_content(prompt_text, FALLBACK_MODEL)

    # این مسیر اگر فولدر content وجود نداشته باشه، خود GitHub فایل رو میسازه
    update_github_file("content/latest.txt", text)
    print("✅ Content update completed.")
