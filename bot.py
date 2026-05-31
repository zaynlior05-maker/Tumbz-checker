

import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8202857061:AAEwNDBWhTEgqNOT865uHjRhhrImJYgPbpk"
OWNER_TAG = "@TumbzO2"

logging.basicConfig(level=logging.INFO)

FLAG_MAP = {
    "US": "🇺🇸", "GB": "🇬🇧", "PT": "🇵🇹", "DE": "🇩🇪", "FR": "🇫🇷",
    "ES": "🇪🇸", "IT": "🇮🇹", "BR": "🇧🇷", "CA": "🇨🇦", "AU": "🇦🇺",
    "NL": "🇳🇱", "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰", "PL": "🇵🇱",
    "RU": "🇷🇺", "IN": "🇮🇳", "CN": "🇨🇳", "JP": "🇯🇵", "MX": "🇲🇽",
    "ZA": "🇿🇦", "NG": "🇳🇬", "GH": "🇬🇭", "KE": "🇰🇪", "AR": "🇦🇷",
}

def get_flag(country_code: str) -> str:
    return FLAG_MAP.get(country_code.upper(), "🏳️") if country_code else "🏳️"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 *Welcome to BIN Checker Bot!*\n\n"
        f"Just send me a BIN (first 6–8 digits of a card) and I'll look it up.\n\n"
        f"Example: `535772`\n\n"
        f"👑 *Owner:* {OWNER_TAG}",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📖 *How to use:*\n\n"
        f"Simply type any 6–8 digit BIN number.\n\n"
        f"I'll return:\n"
        f"• 🏦 Bank name\n"
        f"• 🌍 Country\n"
        f"• 💳 Card brand & type\n"
        f"• 📋 Category\n"
        f"• 📞 Bank phone & website\n\n"
        f"👑 *Owner:* {OWNER_TAG}",
        parse_mode="Markdown"
    )

def lookup_bin(bin_number: str):
    try:
        headers = {"Accept-Version": "3"}
        response = requests.get(
            f"https://lookup.binlist.net/{bin_number}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def format_result(bin_number: str, data: dict) -> str:
    scheme    = data.get("scheme", "N/A").upper()
    card_type = data.get("type", "N/A").upper()

    brand = data.get("brand", None)
    prepaid_raw = data.get("prepaid", None)
    if brand:
        category = str(brand).upper()
    elif isinstance(prepaid_raw, bool) and prepaid_raw:
        category = "PREPAID"
    else:
        category = "N/A"

    bank_info  = data.get("bank", {})
    bank_name  = bank_info.get("name", "N/A")
    bank_phone = bank_info.get("phone", "N/A")
    bank_url   = bank_info.get("url", "N/A")

    country_info  = data.get("country", {})
    country_name  = country_info.get("name", "N/A")
    country_code  = country_info.get("alpha2", "")
    flag          = get_flag(country_code)
    currency      = country_info.get("currency", "N/A")

    prepaid = "✅ Yes" if prepaid_raw else "❌ No"

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
        f"💰 *Prepaid:* {prepaid}\n"
        f"📞 *Phone:* {bank_phone}\n"
        f"🌐 *Website:* {bank_url}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👑 *Owner:* {OWNER_TAG}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # Support /bin 535772 , /heisen 535772, or plain 535772
    if text.lower().startswith(("/bin", "/heisen")):
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text(
                f"⚠️ Please provide a BIN.\nExample: `/bin 535772`\n\n👑 *Owner:* {OWNER_TAG}",
                parse_mode="Markdown"
            )
            return
        bin_number = parts[1].strip()
    else:
        bin_number = text.replace(" ", "")

    if not bin_number.isdigit() or not (6 <= len(bin_number) <= 8):
        await update.message.reply_text(
            f"⚠️ Please send a valid *6–8 digit* BIN number.\n\n👑 *Owner:* {OWNER_TAG}",
            parse_mode="Markdown"
        )
        return

    loading_msg = await update.message.reply_text("🔍 Looking up BIN, please wait...")

    data = lookup_bin(bin_number)

    if data:
        result = format_result(bin_number, data)
        await loading_msg.edit_text(result, parse_mode="Markdown")
    else:
        await loading_msg.edit_text(
            f"❌ *BIN `{bin_number}` not found.*\n\nThis BIN may not be in the database.\n\n👑 *Owner:* {OWNER_TAG}",
            parse_mode="Markdown"
        )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("bin", handle_message))
    app.add_handler(CommandHandler("heisen", handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
