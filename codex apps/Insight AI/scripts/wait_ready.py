import time
import urllib.error
import urllib.request

for _ in range(120):
    try:
        with urllib.request.urlopen("http://127.0.0.1:3000", timeout=2) as response:
            if response.status == 200:
                break
    except (urllib.error.URLError, TimeoutError):
        time.sleep(1)
else:
    raise SystemExit("Local web server did not become ready within the startup window")
