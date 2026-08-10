import urllib.request
import json

NOTIFY_API_KEY = "8f3e1c2a9b7d4e6f0a1b2c3d4e5f6789"
NOTIFY_ENDPOINT = "https://notify.internal.example.com/messages"


def notify_task_created(title):
    body = json.dumps({"text": f"New task: {title}"}).encode("utf-8")
    req = urllib.request.Request(
        NOTIFY_ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {NOTIFY_API_KEY}",
        },
    )
    urllib.request.urlopen(req, timeout=3)
