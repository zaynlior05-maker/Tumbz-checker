import requests
import time
import logging
import threading

BOT_TOKEN = "8202857061:AAE5htvT0rcSv1vMjk_tM-9ZKZOPbOv4EOQ"
OWNER_TAG = "@TumbzO2"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

FLAG_MAP = {
    "US": "🇺🇸", "GB": "🇬🇧", "PT": "🇵🇹", "DE": "🇩🇪", "FR": "🇫🇷",
    "ES": "🇪🇸", "IT": "🇮🇹", "BR": "🇧🇷", "CA": "🇨🇦", "AU": "🇦🇺",
    "NL": "🇳🇱", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰", "PL": "🇵🇱",
    "RU": "🇷🇺", "IN": "🇮🇳", "CN": "🇨🇳", "JP": "🇯🇵", "MX": "🇲🇽",
    "ZA": "🇿🇦", "NG": "🇳🇬", "GH": "🇬🇭", "KE": "🇰🇪", "AR": "🇦🇷",
}

def get_flag(code):
    return FLAG_MAP.get(code.upper(), "") if code else ""

def send_message(chat_id, text):
    try:
        requests.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

def lookup_bin(bin_number):
    try:
        r = requests.get(
            f"https://lookup.binlist.net/{bin_number}",
            headers={"Accept-Version": "3"},
            timeout=8
        )
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            return "rate_limit"
        return None
    except requests.exceptions.Timeout:
        return "timeout"
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

    if brand:
        category = f"{scheme.upper()} {brand.upper()}".strip()
    elif prepaid:
        category = "PREPAID"
    else:
        category = ""

    lines = [f"💳 *BIN:* `{bin_number}`"]

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

def extract_bins(text):
    """Extract all valid 6-8 digit BINs from a message (one per line)."""
    bins = []
    for line in text.splitlines():
        b = line.strip().replace(" ", "")
        if b.isdigit() and 6 <= len(b) <= 8:
            bins.append(b)
    return bins

def process_single_bin(chat_id, bin_number, index, total):
    """Look up one BIN and send result."""
    data = lookup_bin(bin_number)

    if data == "rate_limit":
        send_message(chat_id,
            f"⏳ *BIN `{bin_number}` — Rate limited.* Try again in a moment.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
    elif data == "timeout":
        send_message(chat_id,
            f"⌛ *BIN `{bin_number}` — Timed out.* Try again.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
    elif data:
        send_message(chat_id, format_result(bin_number, data))
    else:
        send_message(chat_id,
            f"❌ *BIN `{bin_number}` not found.*\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )

    # Small delay between lookups to avoid rate limiting
    if index < total - 1:
        time.sleep(1)

def process_message(message):
    chat_id = message.get("chat", {}).get("id")
    text    = message.get("text", "").strip()

    if not chat_id or not text:
        return

    if text.startswith("/start"):
        send_message(chat_id,
            f"👋 *Welcome to Tumbz BIN Bot!*\n\n"
            f"Send me any 6–8 digit BIN to look it up.\n\n"
            f"You can also send *multiple BINs* at once, one per line:\n"
            f"`535772`\n`465865`\n`411111`\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    if text.startswith("/help"):
        send_message(chat_id,
            f"👋 *Welcome to Tumbz BIN Bot!*\n\n"
            f"Send me any 6–8 digit BIN to look it up.\n\n"
            f"You can also send *multiple BINs* at once, one per line:\n"
            f"`535772`\n`465865`\n`411111`\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    # Handle /bin or /heisen commands
    if text.lower().startswith(("/bin", "/heisen")):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, f"⚠️ Usage: `/bin 535772`\n\n👑 *Owner:* {OWNER_TAG}")
            return
        bins = [parts[1].strip()]
    else:
        bins = extract_bins(text)

    if not bins:
        send_message(chat_id, f"⚠️ Send a valid *6–8 digit* BIN.\n\n👑 *Owner:* {OWNER_TAG}")
        return

    # If multiple BINs, notify how many were found
    if len(bins) > 1:
        send_message(chat_id, f"🔍 Found *{len(bins)} BINs* — looking them all up...")

    # Look up each BIN sequentially in this thread
    for i, bin_number in enumerate(bins):
        process_single_bin(chat_id, bin_number, i, len(bins))

def handle_update(update):
    message = update.get("message")
    if message:
        t = threading.Thread(target=process_message, args=(message,))
        t.daemon = True
        t.start()

def main():
    offset = 0
    print("🤖 Tumbz BIN Bot is running...")
    while True:
        try:
            r = requests.get(
                f"{API}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            updates = r.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                handle_update(update)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
