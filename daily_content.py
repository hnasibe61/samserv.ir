#!/usr/bin/env python3
"""Generate and publish one original Persian repair article per run."""

import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI

SITE_URL = "https://www.samserv.ir"
TEHRAN_TZ = ZoneInfo("Asia/Tehran")

TOPICS = [
    ("laptop", "تعمیر لپ‌تاپ", "عیب‌یابی روشن نشدن، داغی، خاموشی زیر بار، شارژ و خرابی مدار تغذیه لپ‌تاپ"),
    ("inverter", "تعمیر دستگاه اینورتر", "عیب‌یابی روشن نشدن، خطای خروجی، خرابی MOSFET و مدار قدرت اینورتر"),
    ("bluetooth-speaker", "تعمیر باند بلوتوث", "قطع صدا، روشن نشدن، خرابی باتری، مدار شارژ و آمپلی‌فایر باند بلوتوث"),
    ("powerbank", "تعمیر پاوربانک", "شارژ نشدن، خاموشی، بادکردگی باتری و خرابی برد محافظ پاوربانک"),
    ("modem", "تعمیر مودم", "قطع و وصل شدن، روشن نشدن، داغی و خرابی مدار تغذیه مودم و مودم سیم‌کارتی"),
    ("laptop-adapter", "تعمیر آداپتور لپ‌تاپ", "افت ولتاژ، صدای سوت، داغی و خرابی خازن یا ماسفت آداپتور لپ‌تاپ"),
    ("airpods", "تعمیر ایرپاد", "شارژ نشدن، قطع شدن یک گوشی، خرابی کیس شارژ و افت باتری ایرپاد"),
    ("speaker-headset", "تعمیر اسپیکر و هدفون", "قطع یک کانال، نویز، خرابی جک، کابل، باتری و مدار صوتی"),
    ("monitor", "تعمیر مانیتور", "روشن نشدن، تصویر نداشتن، خطوط تصویر و خرابی برد تغذیه مانیتور"),
    ("receiver-tv", "تعمیر رسیور و تلویزیون", "خاموشی، تصویر نداشتن، خرابی بک‌لایت و برد تغذیه دستگاه"),
    ("switching-power", "تعمیر برد تغذیه سوئیچینگ", "فیوزپریدن، استارت نزدن، ولتاژ خروجی نداشتن و تست بخش اولیه و ثانویه"),
    ("intercom", "تعمیر آیفون دربازکن", "قطع صدا، زنگ نخوردن، باز نکردن در و خرابی منبع تغذیه آیفون"),
    ("pc-power", "تعمیر پاور کامپیوتر", "روشن نشدن PC، ریست زیر بار، افت ریل‌های 12 و 5 ولت و خرابی پاور"),
    ("printer", "تعمیر پرینتر", "چاپ نگرفتن، گیرکردن کاغذ، خطای مکانیکی و خرابی برد تغذیه پرینتر"),
]


def choose_topic(today):
    blog_dir = Path("blog")
    existing_today = list(blog_dir.glob(f"{today.isoformat()}-*.html"))
    if existing_today:
        print(f"Article already published today: {existing_today[0].name}")
        return None
    start = today.toordinal() % len(TOPICS)
    for offset in range(len(TOPICS)):
        topic = TOPICS[(start + offset) % len(TOPICS)]
        if not list(blog_dir.glob(f"*-{topic[0]}.html")):
            return topic
    return TOPICS[start]


def parse_model_json(raw):
    raw = raw.strip()
    fence = chr(96) * 3
    if raw.startswith(fence):
        raw = re.sub(r"^" + fence + r"(?:json)?\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*" + fence + r"$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Model did not return a JSON object")
    return json.loads(raw[start:end + 1])


def required_text(data, key, limit):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing field: {key}")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"Field too long: {key}")
    return value


def safe_body(body):
    if not isinstance(body, str) or not body.strip():
        raise ValueError("Missing body_html")
    if re.search(
        r"<\s*(script|iframe|object|embed|form|input|style)\b|on[a-z]+\s*=|javascript:",
        body,
        re.I,
    ):
        raise ValueError("Unsafe HTML returned by model")
    return body.strip()


def generate_article(topic_label, topic_focus, today):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("GitHub Secret OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)
    prompt = f"""
برای وبلاگ تعمیرگاه سامترونیک در کرج، یک مقاله فارسی کاملاً اصیل و آماده انتشار تولید کن.
موضوع امروز: {topic_label}
تمرکز فنی: {topic_focus}
تاریخ انتشار: {today.isoformat()}

مثل تعمیرکار حرفه‌ای و باتجربه بنویس، نه مدرس تئوری. از کلی‌گویی و ادعاهای بی‌پشتوانه پرهیز کن.
ترتیب مطلب: علائم واقعی، محتمل‌ترین علت‌ها، تست‌های سریع، قطعات مشکوک،
ولتاژها یا نقاط اندازه‌گیری مهم، اقدام مرحله‌ای و هشدار ایمنی.
مخاطب هم مشتری محلی کرج است و هم فردی که دنبال عیب‌یابی کاربردی است.
در پایان دعوت طبیعی به مراجعه به سامترونیک بیاور.
از محتوای Reddit یا هر سایت دیگری کپی نکن؛ متن باید تازه و مخصوص سامترونیک باشد.

فقط یک JSON معتبر و بدون Markdown برگردان، با این کلیدها:
- title: عنوان جذاب فارسی، حداکثر 110 نویسه
- description: متادیسکریپشن فارسی، 120 تا 160 نویسه
- excerpt: خلاصه 1 تا 2 جمله‌ای برای کارت وبلاگ، حداکثر 300 نویسه
- keywords: آرایه‌ای از 6 تا 10 کلمه یا عبارت کلیدی فارسی
- body_html: متن مقاله فقط با تگ‌های h2، h3، p، ul، ol، li و strong؛
  بدون script، style، iframe، فرم یا لینک خارجی
- image_alt: پیشنهاد alt فارسی برای تصویر مقاله
"""
    response = client.responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
        input=prompt,
        max_output_tokens=5000,
    )
    data = parse_model_json(response.output_text)
    title = required_text(data, "title", 180)
    description = required_text(data, "description", 220)
    excerpt = required_text(data, "excerpt", 360)
    body = safe_body(data.get("body_html"))
    image_alt = required_text(data, "image_alt", 220)
    keywords = data.get("keywords")
    if isinstance(keywords, str):
        keywords = [x.strip() for x in keywords.split(",") if x.strip()]
    if not isinstance(keywords, list) or not keywords:
        raise ValueError("Missing keywords")
    keywords = [str(x).strip() for x in keywords if str(x).strip()][:10]
    return title, description, excerpt, keywords, body, image_alt


def write_article(slug, title, description, keywords, body, image_alt):
    title_e = html.escape(title, quote=True)
    desc_e = html.escape(description, quote=True)
    keywords_e = html.escape(", ".join(keywords), quote=True)
    canonical = f"{SITE_URL}/blog/{slug}.html"
    schema = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": title,
            "description": description,
            "author": {"@type": "Organization", "name": "سامترونیک"},
            "publisher": {
                "@type": "Organization",
                "name": "سامترونیک",
                "url": SITE_URL,
            },
            "mainEntityOfPage": canonical,
            "image": {"@type": "ImageObject", "caption": image_alt},
        },
        ensure_ascii=False,
    )
    article = f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title_e} | سامترونیک</title>
  <meta name="description" content="{desc_e}">
  <meta name="keywords" content="{keywords_e}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
  <link rel="stylesheet" href="../assets/css/style.css">
  <link rel="stylesheet" href="../assets/css/vazirmatn.css">
  <style>
    .article-content h2 {{ font-size: 1.5rem; font-weight: 700; color: #1e40af; margin: 2rem 0 .75rem; }}
    .article-content h3 {{ font-size: 1.25rem; font-weight: 700; color: #1d4ed8; margin: 1.5rem 0 .5rem; }}
    .article-content p {{ margin: .75rem 0; }}
    .article-content ul, .article-content ol {{ padding-right: 1.5rem; margin: 1rem 0; }}
    .article-content li {{ margin: .35rem 0; }}
  </style>
  <script type="application/ld+json">{schema}</script>
</head>
<body class="bg-gray-50 text-gray-800">
  <header class="bg-blue-800 text-white py-5">
    <div class="container mx-auto px-4 flex justify-between items-center">
      <a href="../index.html" class="text-2xl font-bold">سامترونیک</a>
      <a href="../contact.html" class="bg-white text-blue-800 px-4 py-2 rounded-lg">تماس با تعمیرگاه</a>
    </div>
  </header>
  <main class="container mx-auto px-4 py-10 max-w-4xl">
    <article class="bg-white rounded-xl shadow-md p-6 md:p-10 leading-8">
      <nav class="text-sm text-blue-700 mb-6">
        <a href="../index.html">خانه</a> /
        <a href="index.html">وبلاگ</a> /
        {title_e}
      </nav>
      <h1 class="text-3xl md:text-4xl font-bold text-blue-900 mb-6">{title_e}</h1>
      <div class="article-content text-gray-700">{body}</div>
      <div class="bg-yellow-50 border-r-4 border-yellow-500 p-5 mt-8 rounded-lg">
        <strong>هشدار ایمنی:</strong>
        اندازه‌گیری روی برد روشن و کار با منبع تغذیه نیاز به تجربه دارد؛
        اگر ابزار و تجربه کافی ندارید، تعمیر را به متخصص بسپارید.
      </div>
      <p class="mt-8">
        برای عیب‌یابی و تعمیر تخصصی این دستگاه در کرج، از
        <a href="../services.html" class="text-blue-700 underline">خدمات سامترونیک</a>
        استفاده کنید یا از
        <a href="../contact.html" class="text-blue-700 underline">صفحه تماس با ما</a>
        با تعمیرگاه هماهنگ شوید.
      </p>
    </article>
  </main>
  <footer class="bg-blue-800 text-white text-center py-6">
    <a href="../index.html">سامترونیک</a> |
    تعمیر تخصصی لپ‌تاپ و تجهیزات الکترونیکی در کرج
  </footer>
</body>
</html>
"""
    Path("blog", f"{slug}.html").write_text(article, encoding="utf-8")


def update_site(slug, title, excerpt, today):
    title_e = html.escape(title, quote=True)
    excerpt_e = html.escape(excerpt, quote=True)

    blog_index_path = Path("blog/index.html")
    blog_index = blog_index_path.read_text(encoding="utf-8")
    entry = f"""        <article style="background:#f6f8fa;padding:20px;border-radius:12px;">
            <a href="{slug}.html" style="font-size:1.2rem;font-weight:700;color:#125;text-decoration:none;">{title_e}</a>
            <p style="color:#444;margin:8px 0 0 0;">{excerpt_e}
            <a href="{slug}.html" style="color:#2a76d2;text-decoration:underline;">[مطالعه کامل]</a></p>
        </article>
"""
    marker = "<!-- Latest Article Section -->"
    if marker in blog_index:
        blog_index = blog_index.replace(marker, entry + "        " + marker, 1)
    else:
        blog_index = blog_index.replace("</section>", entry + "    </section>", 1)
    blog_index_path.write_text(blog_index, encoding="utf-8")

    home_path = Path("index.html")
    home = home_path.read_text(encoding="utf-8")
    home_section = f"""<!-- Latest Article Section -->
<section id="latest-article-section" class="py-16 bg-yellow-50">
    <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-8 text-yellow-800">آخرین مقاله</h2>
        <article class="bg-white p-6 rounded-xl shadow-md text-gray-700 leading-relaxed">
            <h3 class="text-2xl font-bold text-blue-800 mb-3">
                <a href="blog/{slug}.html" class="hover:text-blue-600">{title_e}</a>
            </h3>
            <p class="text-lg mb-4">{excerpt_e}</p>
            <a href="blog/{slug}.html" class="inline-block bg-blue-700 text-white px-5 py-2 rounded-lg hover:bg-blue-800">مطالعه مقاله</a>
        </article>
    </div>
</section>"""
    if re.search(r"<!-- Latest Article Section -->[\s\S]*?</section>", home):
        home = re.sub(
            r"<!-- Latest Article Section -->[\s\S]*?</section>",
            home_section,
            home,
            count=1,
        )
    else:
        home = home.replace("</main>", home_section + "\n</main>", 1)
    home_path.write_text(home, encoding="utf-8")

    sitemap_path = Path("sitemap.xml")
    sitemap = sitemap_path.read_text(encoding="utf-8")
    url = f"{SITE_URL}/blog/{slug}.html"
    if f"<loc>{url}</loc>" not in sitemap:
        sitemap = sitemap.replace(
            "</urlset>",
            f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{today.isoformat()}</lastmod>\n    <priority>0.80</priority>\n  </url>\n</urlset>",
        )
    sitemap_path.write_text(sitemap, encoding="utf-8")

    Path("content/latest.txt").write_text(
        f"آخرین مقاله سامترونیک: {title}. {excerpt}",
        encoding="utf-8",
    )


def main():
    today = datetime.now(TEHRAN_TZ).date()
    chosen = choose_topic(today)
    if chosen is None:
        return
    topic_slug, topic_label, topic_focus = chosen
    slug = f"{today.isoformat()}-{topic_slug}"
    title, description, excerpt, keywords, body, image_alt = generate_article(
        topic_label, topic_focus, today
    )
    write_article(slug, title, description, keywords, body, image_alt)
    update_site(slug, title, excerpt, today)

    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "add", "blog", "index.html", "sitemap.xml", "content/latest.txt"],
        check=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if not status.stdout.strip():
        print("No changes to publish")
        return
    subprocess.run(
        ["git", "commit", "-m", f"Publish daily repair article {slug}"],
        check=True,
    )
    subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
    print(f"Published {slug}.html")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Daily publishing failed: {exc}", file=sys.stderr)
        raise
