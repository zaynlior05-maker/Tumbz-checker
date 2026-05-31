import requests
import time
import logging
import threading

BOT_TOKEN = "8202857061:AAGiHhKPux9sdwVRAmCQzs1OcnlcRNL5heA"
OWNER_TAG = "@TumbzO2"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(level=logging.INFO)

COUNTRY_MAP = {
    "US": ("United States", "🇺🇸"),
    "GB": ("United Kingdom", "🇬🇧"),
    "PT": ("Portugal", "🇵🇹"),
    "DE": ("Germany", "🇩🇪"),
    "FR": ("France", "🇫🇷"),
    "ES": ("Spain", "🇪🇸"),
    "IT": ("Italy", "🇮🇹"),
    "BR": ("Brazil", "🇧🇷"),
    "CA": ("Canada", "🇨🇦"),
    "AU": ("Australia", "🇦🇺"),
    "NL": ("Netherlands", "🇳🇱"),
    "SE": ("Sweden", "🇸🇪"),
    "NO": ("Norway", "🇳🇴"),
    "DK": ("Denmark", "🇩🇰"),
    "PL": ("Poland", "🇵🇱"),
    "RU": ("Russia", "🇷🇺"),
    "IN": ("India", "🇮🇳"),
    "CN": ("China", "🇨🇳"),
    "JP": ("Japan", "🇯🇵"),
    "MX": ("Mexico", "🇲🇽"),
    "ZA": ("South Africa", "🇿🇦"),
    "NG": ("Nigeria", "🇳🇬"),
    "GH": ("Ghana", "🇬🇭"),
    "KE": ("Kenya", "🇰🇪"),
    "AR": ("Argentina", "🇦🇷"),
    "IE": ("Ireland", "🇮🇪"),
    "CH": ("Switzerland", "🇨🇭"),
    "AT": ("Austria", "🇦🇹"),
    "BE": ("Belgium", "🇧🇪"),
    "GR": ("Greece", "🇬🇷"),
    "TR": ("Turkey", "🇹🇷"),
    "SA": ("Saudi Arabia", "🇸🇦"),
    "AE": ("UAE", "🇦🇪"),
    "SG": ("Singapore", "🇸🇬"),
    "HK": ("Hong Kong", "🇭🇰"),
    "NZ": ("New Zealand", "🇳🇿"),
    "PH": ("Philippines", "🇵🇭"),
    "MY": ("Malaysia", "🇲🇾"),
    "ID": ("Indonesia", "🇮🇩"),
    "TH": ("Thailand", "🇹🇭"),
    "PK": ("Pakistan", "🇵🇰"),
    "BD": ("Bangladesh", "🇧🇩"),
    "EG": ("Egypt", "🇪🇬"),
    "MA": ("Morocco", "🇲🇦"),
    "TZ": ("Tanzania", "🇹🇿"),
    "UG": ("Uganda", "🇺🇬"),
    "ET": ("Ethiopia", "🇪🇹"),
    "CO": ("Colombia", "🇨🇴"),
    "VE": ("Venezuela", "🇻🇪"),
    "CL": ("Chile", "🇨🇱"),
    "PE": ("Peru", "🇵🇪"),
    "UA": ("Ukraine", "🇺🇦"),
    "CZ": ("Czech Republic", "🇨🇿"),
    "HU": ("Hungary", "🇭🇺"),
    "RO": ("Romania", "🇷🇴"),
    "FI": ("Finland", "🇫🇮"),
    "SK": ("Slovakia", "🇸🇰"),
    "HR": ("Croatia", "🇭🇷"),
    "RS": ("Serbia", "🇷🇸"),
    "IL": ("Israel", "🇮🇱"),
    "KW": ("Kuwait", "🇰🇼"),
    "QA": ("Qatar", "🇶🇦"),
    "BH": ("Bahrain", "🇧🇭"),
    "JO": ("Jordan", "🇯🇴"),
    "LB": ("Lebanon", "🇱🇧"),
    "ZW": ("Zimbabwe", "🇿🇼"),
    "ZM": ("Zambia", "🇿🇲"),
    "SN": ("Senegal", "🇸🇳"),
    "CI": ("Ivory Coast", "🇨🇮"),
    "CM": ("Cameroon", "🇨🇲"),
}

def get_country(code):
    if not code:
        return "", ""
    code = code.upper()
    if code in COUNTRY_MAP:
        return COUNTRY_MAP[code]
    return code, ""  # fallback to just showing the code

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
            timeout=5
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
    country_code = country.get("alpha2", "")

    country_name, flag = get_country(country_code)

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
        lines.append(f"🌍 *Country:* {country_name} {flag}".strip())
    if scheme:
        lines.append(f"🔖 *Brand:* {scheme.upper()}")
    if card_type:
        lines.append(f"📋 *Type:* {card_type.upper()}")
    if category:
        lines.append(f"🏷️ *Category:* {category}")

    lines.append(f"――――――――――――――")
    lines.append(f"👑 *Owner:* {OWNER_TAG}")

    return "\n".join(lines)

def process_message(message):
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

    data = lookup_bin(bin_number)

    if data == "rate_limit":
        send_message(chat_id,
            f"⏳ *Too many requests.* Please wait a moment and try again.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
    elif data == "timeout":
        send_message(chat_id,
            f"⌛ *Lookup timed out.* Please try again.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )
    elif data:
        send_message(chat_id, format_result(bin_number, data))
    else:
        send_message(chat_id,
            f"❌ *BIN `{bin_number}` not found.*\n\n"
            f"This BIN may not be in the database.\n\n"
            f"👑 *Owner:* {OWNER_TAG}"
        )

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
