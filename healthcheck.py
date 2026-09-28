import urllib.request
import os

url = f"http://127.0.0.1:{os.getenv('PORT', '8000')}/health"
with urllib.request.urlopen(url, timeout=5) as response:
    if response.status != 200:
        raise SystemExit(1)
print(response.read().decode())
