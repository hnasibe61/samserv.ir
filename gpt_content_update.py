import os
import openai
import requests
import sys

# خواندن اطلاعات از متغیرهای محیطی
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")
REPO_TOKEN = os.getenv("REPO_TOKENVALUE")
OWNER = os.getenv("OWNERVALUE")
REPO = os.getenv("REPOVALUE")

# ست کردن کلید API
openai.api_key = OPENAI_API_KEY

# مدل پیش‌فرض و پشتیبان
PRIMARY_MODEL = "gpt-4.1"
FALLBACK_MODEL = "gpt-4o-mini"


def generate_content(prompt, model_name):
    """
    تولید محتوا با مدل دلخواه
    """
    try:
        resp = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert content generator for an electronics repair shop website."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return resp.choices[0].message["content"]

    except openai.error.RateLimitError as e:
        if "insufficient_quota" in str(e):
            raise RuntimeError("Quota exhausted")
        else:
            raise


def update_github_content(filename, content):
    """
    آپدیت فایل در مخزن GitHub
    """
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {REPO_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # خواندن SHA فایل فعلی
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": "Auto update site content",
        "content": content.encode("utf-8").decode("utf-8"),
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=payload)

    if res.status_code not in (200, 201):
        print(f"GitHub update failed: {res.text}")
        sys.exit(1)


if __name__ == "__main__":
    prompt_text = "Write an SEO-optimized blog post about repairing a laptop power adapter."
    try:
        final_content = generate_content(prompt_text, PRIMARY_MODEL)
    except RuntimeError:
        print(f"⚠️ Quota issue in {PRIMARY_MODEL}, switching to {FALLBACK_MODEL}...")
        final_content = generate_content(prompt_text, FALLBACK_MODEL)

    update_github_content("content/latest.txt", final_content)
    print("✅ Content update completed.")
