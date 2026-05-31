import requests
import time
import logging

BOT_TOKEN = "8202857061:AAEwNDBWhTEgqNOT865uHjRhhrImJYgPbpk"
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
    return FLAG_MAP.get(code.upper(), "🏳️") if code else "🏳️"

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
    scheme    = data.get("scheme", "N/A").upper()
    card_type = data.get("type", "N/A").upper()
    brand     = data.get("brand", None)
    prepaid   = data.get("prepaid", False)
    category  = str(brand).upper() if brand else ("PREPAID" if prepaid else "N/A")

    bank      = data.get("bank", {})
    bank_name = bank.get("name", "N/A")
    bank_phone= bank.get("phone", "N/A")
    bank_url  = bank.get("url", "N/A")

    country      = data.get("country", {})
    country_name = country.get("name", "N/A")
    country_code = country.get("alpha2", "")
    currency     = country.get("currency", "N/A")
    flag         = get_flag(country_code)

    return (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🔍 *BIN Lookup Result*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💳 *BIN:* `{bin_number}`\n"
        f"🏦 *Bank:* {bank_name}\n"
        f"🌍 *Country:* {flag} {country_name} ({country_code})\n"
        f"💵 *Currency:* {currency}\n"
        f"🔖 *Brand:* {scheme}\n"
        f"📋 *Type:* {card_type}\n"
        f"🏷️ *Category:* {category}\n"
        f"💰 *Prepaid:* {'✅ Yes' if prepaid else '❌ No'}\n"
        f"📞 *Phone:* {bank_phone}\n"
        f"🌐 *Website:* {bank_url}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Owner:* {OWNER_TAG}"
    )

def handle_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text    = message.get("text", "").strip()

    if not chat_id or not text:
        return

    # Commands
    if text in ("/start", "/start@" + BOT_TOKEN):
        send_message(chat_id,
            f"👋 *Welcome to BIN Checker Bot!*\n\n"
            f"Send me any 6–8 digit BIN to look it up.\n\n"
            f"Example: `535772`\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    if text.startswith("/help"):
        send_message(chat_id,
            f"📖 *How to use:*\n\nSend any 6–8 digit BIN number.\n\n"
            f"Supports: plain `535772`, `/bin 535772`, `/heisen 535772`\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
        return

    # Extract BIN from /bin or /heisen commands
    if text.lower().startswith(("/bin", "/heisen")):
        parts = text.split()
        if len(parts) < 2:
            send_message(chat_id, f"⚠️ Usage: `/bin 535772`\n\n👑 *Owner:* {OWNER_TAG}")
            return
        bin_number = parts[1]
    else:
        bin_number = text.replace(" ", "")

    # Validate
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
    print("🤖 Bot is running...")
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
