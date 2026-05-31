import requests
import time
import logging

BOT_TOKEN = "8202857061:AAE5htvT0rcSv1vMjk_tM-9ZKZOPbOv4EOQ"
OWNER_TAG = "@TumbzO2"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

FLAG_MAP = {
    "US": "🇺🇸", "GB": "🇬🇧", "PT": "🇵🇹", "DE": "🇩🇪", "FR": "🇫🇷",
    "ES": "🇪🇸", "IT": "🇮🇹", "BR": "🇧🇷", "CA": "🇨🇦", "AU": "🇦🇺",
    "NL": "🇳🇱", "SE": "🇸🇪", "NO": "🇳", "DK": "🇩🇰", "PL": "🇵🇱",
    "RU": "🇷🇺", "IN": "🇮🇳", "CN": "🇨🇳", "JP": "🇯🇵", "MX": "🇲🇽",
    "ZA": "🇿🇦", "NG": "🇳🇬", "GH": "🇬🇭", "KE": "🇰🇪", "AR": "🇦🇷",
}

def get_flag(code):
    return FLAG_MAP.get(code.upper(), "") if code else ""

def send_message(chat_id, text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

def lookup_bin(bin_number):
    try:
        r = requests.get(
            f"https://lookup.binlist.net/{bin_number}",
            headers={"Accept-Version": "3"},
            timeout=10
        )
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None

def format_result(bin_number, data):
    bank         = data.get("bank", {})
    country      = data.get("country", {})
    scheme       = data.get("scheme", "")
    card_type    = data.get("type", "")
    brand        = data.get("brand", "")
    prepaid      = data.get("prepaid", False)

    bank_name    = bank.get("name", "")
    country_name = country.get("name", "")
    country_code = country.get("alpha2", "")
    flag         = get_flag(country_code)

    # Build category: prefer brand, fallback to prepaid label
    if brand:
        category = f"{scheme.upper()} {brand.upper()}".strip()
    elif prepaid:
        category = "PREPAID"
    else:
        category = ""

    lines = [
        f"💳 *BIN:* `{bin_number}`",
    ]

    if bank_name:
        lines.append(f"🏦 *Bank:* {bank_name.title()}")

    if country_name:
        lines.append(f"🌍 *Country:* {country_name} {flag}")

    if scheme:
        lines.append(f"🔖 *Brand:* {scheme.upper()}")

    if card_type:
        lines.append(f"📋 *Type:* {card_type.upper()}")

    if category:
        lines.append(f"🏷️ *Category:* {category}")

    lines.append(f"――――――――――――――")
    lines.append(f"👑 *Owner:* {OWNER_TAG}")

    return "\n".join(lines)

def handle_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text    = message.get("text", "").strip()

    if not chat_id or not text:
        return

    if text.startswith("/start"):
        send_message(chat_id,
            f"👋 *Welcome to Tumbz BIN Bot!*\n\n"
            f"Send me any 6–8 digit BIN to look it up.\n\n"
            f"Example: `535772` & get full info\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    if text.startswith("/help"):
        send_message(chat_id,
            f"👋 *Welcome to Tumbz BIN Bot!*\n\n"
            f"Send me any 6–8 digit BIN to look it up.\n\n"
            f"Example: `535772` & get full info\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    if text.lower().startswith(("/bin", "/heisen")):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, f"⚠️ Usage: `/bin 535772`\n\n👑 *Owner:* {OWNER_TAG}")
            return
        bin_number = parts[1]
    else:
        bin_number = text.replace(" ", "")

    if not bin_number.isdigit() or not (6 <= len(bin_number) <= 8):
        send_message(chat_id, f"⚠️ Send a valid *6–8 digit* BIN.\n\n👑 *Owner:* {OWNER_TAG}")
        return

    send_message(chat_id, "🔍 Looking up BIN, please wait...")

    data = lookup_bin(bin_number)
    if data:
        send_message(chat_id, format_result(bin_number, data))
    else:
        send_message(chat_id,
            f"❌ *BIN `{bin_number}` not found.*\n\n"
            f"This BIN may not be in the database.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )

def main():
    offset = 0
    print("🤖 Tumbz BIN Bot is running...")
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=35)
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                handle_update(update)
        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
