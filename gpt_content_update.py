import os
import json
import glob
import shutil
import requests
import subprocess
import tempfile
from datetime import datetime
from openai import OpenAI

# --- تنظیمات ---
OWNER  = os.getenv("OWNERVALUE")
REPO   = os.getenv("REPOVALUE")
TOKEN  = os.getenv("REPO_TOKENVALUE")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEYVALUE")
BRANCH = "main"
UPLOADS_DIR = "assets/images/uploads"
PROCESSED_FILE = "processed_images.json"

# --- تست دسترسی GitHub ---
print(f"🔍 OWNER: {OWNER}")
print(f"🔍 REPO : {REPO}")
print(f"🔍 Token starts with: {TOKEN[:4]}...")

resp = requests.get(
    f"https://api.github.com/repos/{OWNER}/{REPO}",
    headers={"Authorization": f"token {TOKEN}"}
)
if resp.status_code != 200:
    print(f"❌ GitHub access failed → {resp.text}")
    exit(1)
print("✅ Repo is accessible!")

# --- آماده‌سازی کلاینت OpenAI ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- کلون ریپو ---
temp_dir = tempfile.mkdtemp()
repo_url = f"https://{TOKEN}@github.com/{OWNER}/{REPO}.git"
subprocess.run(["git", "clone", "--branch", BRANCH, repo_url, temp_dir], check=True)
os.chdir(temp_dir)

# --- بارگذاری لیست پردازش‌شده‌ها ---
if os.path.exists(PROCESSED_FILE):
    with open(PROCESSED_FILE, "r") as f:
        processed_images = json.load(f)
else:
    processed_images = []

# --- پیدا کردن عکس‌های جدید ---
new_images = [img for img in glob.glob(f"{UPLOADS_DIR}/*")
              if os.path.basename(img) not in processed_images]

if new_images:
    image_path = new_images[0]
    image_name = os.path.basename(image_path)
    print(f"🖼 پردازش عکس جدید: {image_name}")

    # --- ارسال به GPT Vision ---
    try:
        vision_resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "image_url": f"file://{os.path.abspath(image_path)}"},
                        {"type": "text", "text": """
شما یک تعمیرکار حرفه‌ای الکترونیک هستید. این عکس را تحلیل کنید و یک متن تخصصی پیشرفته
(حدود 500 کلمه) مرتبط با تعمیرات این قطعه/دستگاه بنویسید. متن باید شامل مراحل عیب‌یابی،
جزئیات فنی ولتاژها و قطعات، ابزار لازم و نکات ایمنی باشد.
                        """}
                    ]
                }
            ]
        )
        article_content = vision_resp.output[0].content[0].text.strip()
    except Exception as e:
        print("❌ Vision processing failed:", e)
        exit(1)

    # --- ساخت فایل HTML مطلب ---
    slug = datetime.now().strftime("%Y%m%d") + "-" + os.path.splitext(image_name)[0]
    blog_filename = f"blog/{slug}.html"
    os.makedirs("blog", exist_ok=True)

    html_template = f"""<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>{slug}</title>
<link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
<h1>{slug}</h1>
<img src="../{UPLOADS_DIR}/{image_name}" alt="Repair Image" style="max-width:600px;">
<article>
{article_content}
</article>
</body>
</html>"""
    with open(blog_filename, "w", encoding="utf-8") as f:
        f.write(html_template)

    # --- اضافه کردن به blog/index.html ---
    index_path = "blog/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index_html = f.read()
        new_entry = f'\n<div class="blog-item"><a href="{slug}.html"><img src="../{UPLOADS_DIR}/{image_name}" alt=""><h2>{slug}</h2></a></div>\n'
        index_html = index_html.replace("# وبلاگ سامترونیک", "# وبلاگ سامترونیک\n" + new_entry)
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_html)

    # --- ثبت عکس به پردازش‌شده‌ها ---
    processed_images.append(image_name)
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed_images, f, ensure_ascii=False, indent=2)

else:
    print("📄 عکس جدید پیدا نشد → تولید مطلب متنی با عکس AI")
    prompt = """
یک مقاله تخصصی سطح پیشرفته در یکی از حوزه‌های زیر بنویس (~500 کلمه):
- تعمیرات لپ‌تاپ سطح برد
- تعمیر پاور کامپیوتر
- تعمیر هندزفری بلوتوثی
- تعمیر مودم (سیمکارتی و ADSL)
- تعمیر باند بلوتوثی
جزئیات فنی و مراحل تعمیر را کامل توضیح بده.
"""
    response = client.responses.create(model="gpt-4o-mini", input=prompt)
    article_content = response.output[0].content[0].text.strip()

    # این بخش می‌تواند با generate_image یک عکس AI هم بسازد

# --- کانفیگ گیت ---
subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=True)
subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)

# --- کامیت و پوش ---
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "auto blog update"], check=True)
subprocess.run(["git", "push", "--force", "origin", BRANCH], check=True)
print("✅ Blog updated successfully!")
