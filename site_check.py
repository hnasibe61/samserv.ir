import requests

url = "https://samserv.ir"
try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        print(f"✅ Site is up: {url}")
    else:
        print(f"⚠️ Site returned status code {response.status_code}")
except Exception as e:
    print(f"❌ Error checking site: {e}")
