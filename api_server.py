"""
Lightweight HTTP server running on Oracle Cloud.
The Vercel dashboard calls this to trigger TikTok uploads,
because Vercel serverless cannot spawn Python processes.

Setup:
  pip install flask
  export API_SECRET=<strong-random-secret>   # same value as ORACLE_API_SECRET on Vercel
  python api_server.py

Or with gunicorn for production:
  gunicorn -w 2 -b 0.0.0.0:8080 api_server:app
"""

import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

from tiktok.manual_upload import upload_video_by_id

app = Flask(__name__)

_API_SECRET = os.environ.get("API_SECRET", "")


def _check_auth() -> bool:
    if not _API_SECRET:
        return False
    return request.headers.get("X-API-Secret", "") == _API_SECRET


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.route("/api/upload/<int:video_id>", methods=["POST"])
def upload(video_id: int):
    if not _check_auth():
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    try:
        result = upload_video_by_id(video_id)
        return jsonify({"ok": True, "result": result})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 500


if __name__ == "__main__":
    if not _API_SECRET:
        raise SystemExit("ERROR: API_SECRET env var is required.")
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
