# ==============================================================
# FOLDER: backend-bot
# FILE: telegram_auth.py
# ==============================================================
import os
import hmac
import hashlib
import json
import urllib.parse
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

def verify_telegram_init_data(x_telegram_init_data: str = Header(...)) -> dict:
    """
    Validates HMAC-SHA256 signature of Telegram WebApp initData string.
    Ensures callers are authenticated Telegram users.
    """
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TELEGRAM_BOT_TOKEN is not configured on server"
        )
    try:
        parsed_data = dict(urllib.parse.parse_qsl(x_telegram_init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash parameter")

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode("utf-8"), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram signature")

        return json.loads(parsed_data["user"])
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed Telegram initData")