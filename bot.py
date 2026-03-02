"""
EUNIQUE WORLD OF CREATION — Telegram Chatbot
Covers: Eunique Cake & More + Eunique Food
Features: Button menus + AI free chat (Claude-powered)
"""

import os
import logging
import anthropic
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config (set via environment variables) ───────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]        # from @BotFather
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]    # from console.anthropic.com
OWNER_CHAT_ID    = os.environ.get("OWNER_CHAT_ID", "") # your personal Telegram chat ID
OWNER_PHONE      = "07036717932 / 07054382079"

# ── Anthropic client ──────────────────────────────────────────────────────────
ai = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── Business knowledge base (used by AI) ────────────────────────────────────
SYSTEM_PROMPT = """
You are EuniqueBot, the friendly and professional AI assistant for EUNIQUE WORLD OF CREATION,
a food & catering business based in Benin City, Nigeria.

BUSINESS OVERVIEW:
Eunique has two divisions:
1. Eunique Cake & More — premium cakes, small chops, snacks & catering
2. Eunique Food — 100% whole grain millet flour (natural, nutritious, pure)

CONTACT:
- Phone/WhatsApp: 07036717932 / 07054382079
- Email: euniquefood@gmail.com
- Address: No. 31 Erediauwa Street, Off Erodiuwa Road, Sapele Road, Benin City
- Hours: Monday–Saturday 8am–7pm, Sunday 10am–4pm

PRODUCTS & PRICES:

CAKES (Eunique Cake & More):
- Single-Tier Cake: from ₦15,000
- Two-Tier Cake: from ₦30,000
- Three-Tier Wedding Cake: from ₦55,000
- Custom Design Cake: price on request

SMALL CHOPS:
- Samosa (per dozen): ₦3,500
- Spring Rolls (per dozen): ₦3,500
- Puff Puff (per 50 pcs): ₦4,500
- Small Chops Platter (combo): from ₦12,000

SNACKS:
- Meat Pie: ₦700 each
- Egg Roll: ₦600 each
- Doughnuts (per 6): ₦2,500
- Chin Chin (per 200g): ₦1,500
- Fish Roll: ₦700 each
- Sausage Rolls: ₦600 each

CATERING SERVICES:
- Small Event (up to 50 guests): from ₦80,000
- Medium Event (51–150 guests): from ₦150,000
- Large/Corporate Event (150+ guests): price on request

MILLET FLOUR (Eunique Food):
- 500g: ₦1,800
- 1 kg: ₦3,200
- 2 kg: ₦6,000
- 5 kg: ₦14,000
- 10 kg Trade Pack: from ₦26,000
Ingredient: 100% whole grain millet. Store in airtight container after opening.

MILLET FLOUR PREPARATION:
1. Boil water, add cold water
2. Gradually add millet flour while stirring
3. Cover and cook 5 minutes
4. Stir to desired texture
5. Serve with any soup of your choice

HEALTH BENEFITS OF MILLET FLOUR:
Rich in fibre, high in protein, supports heart health, helps regulate blood sugar, aids weight loss.

ORDERING:
- Call or WhatsApp: 07036717932 or 07054382079
- Advance booking required for event catering
- Bulk/wholesale discounts available

YOUR PERSONALITY:
- Warm, friendly, professional
- Use Nigerian-friendly language (you can say "Oga", "Madam" etc. where appropriate)
- Always end with an invitation to order or ask more questions
- Keep responses concise and helpful
- Use ₦ for Naira prices
- If asked something outside your knowledge, offer to connect them to the owner

IMPORTANT: Never make up prices or information not listed above. For custom orders or unlisted items, always direct to the phone number.
"""

# ── In-memory order storage ────────────────────────────────────────────────
user_orders: dict[int, dict] = {}
user_chat_history: dict[int, list] = {}

# ═══════════════════════════════════════════════════════════════════════════
#  KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════
def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 Cake & More",      callback_data="menu_cake"),
         InlineKeyboardButton("🌾 Millet Flour",     callback_data="menu_flour")],
        [InlineKeyboardButton("📋 Place an Order",   callback_data="order_start"),
         InlineKeyboardButton("📍 Location & Hours", callback_data="info_location")],
        [InlineKeyboardButton("📞 Contact Us",       callback_data="info_contact"),
         InlineKeyboardButton("💬 Chat with AI",     callback_data="ai_chat")],
    ])

def cake_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 Cakes",        callback_data="sub_cakes"),
         InlineKeyboardButton("🥟 Small Chops",  callback_data="sub_chops")],
        [InlineKeyboardButton("🍩 Snacks",       callback_data="sub_snacks"),
         InlineKeyboardButton("🍽️ Catering",    callback_data="sub_catering")],
        [InlineKeyboardButton("⬅️ Back",         callback_data="back_main")],
    ])

def flour_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Prices & Sizes",     callback_data="sub_flour_prices"),
         InlineKeyboardButton("❤️ Health Benefits",    callback_data="sub_flour_health")],
        [InlineKeyboardButton("👩‍🍳 How to Prepare",    callback_data="sub_flour_prep"),
         InlineKeyboardButton("🛒 Order Now",           callback_data="order_flour")],
        [InlineKeyboardButton("⬅️ Back",               callback_data="back_main")],
    ])

def order_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎂 Cakes & Chops",   callback_data="order_cake"),
         InlineKeyboardButton("🌾 Millet Flour",    callback_data="order_flour")],
        [InlineKeyboardButton("🍽️ Event Catering", callback_data="order_catering")],
        [InlineKeyboardButton("⬅️ Back",            callback_data="back_main")],
    ])

def confirm_order_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm & Send",  callback_data="order_confirm"),
         InlineKeyboardButton("❌ Cancel",          callback_data="order_cancel")],
    ])

def back_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")],
    ])

# ═══════════════════════════════════════════════════════════════════════════
#  WELCOME / START
# ═══════════════════════════════════════════════════════════════════════════
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "there"
    text = (
        f"🌟 *Welcome to Eunique World of Creation, {name}!*\n\n"
        "We bring you:\n"
        "🎂 *Eunique Cake & More* — Cakes, Small Chops, Snacks & Catering\n"
        "🌾 *Eunique Food* — 100% Whole Grain Millet Flour\n\n"
        "_A World of Creativity & A Quest for Quality_\n\n"
        "How can we serve you today? 👇"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=main_menu_keyboard())

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Available commands:*\n\n"
        "/start — Main menu\n"
        "/order — Place an order\n"
        "/contact — Contact & location\n"
        "/menu — View all products\n"
        "/chat — Chat with our AI assistant\n"
        "/cancel — Cancel current action",
        parse_mode=ParseMode.MARKDOWN
    )

# ═══════════════════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER (button clicks)
# ═══════════════════════════════════════════════════════════════════════════
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # ── Navigation ──────────────────────────────────────────────────────────
    if data == "back_main":
        await query.edit_message_text(
            "🏠 *Main Menu*\n\nHow can we help you today?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard()
        )

    # ── Cake & More section ──────────────────────────────────────────────────
    elif data == "menu_cake":
        await query.edit_message_text(
            "🎂 *Eunique Cake & More*\n\n"
            "_Celebrations Made Sweeter_\n\n"
            "What would you like to see?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=cake_menu_keyboard()
        )

    elif data == "sub_cakes":
        await query.edit_message_text(
            "🎂 *CAKES*\n\n"
            "┌ Single-Tier Cake ............... from *₦15,000*\n"
            "├ Two-Tier Cake .................. from *₦30,000*\n"
            "├ Three-Tier Wedding Cake ........ from *₦55,000*\n"
            "└ Custom Design Cake ............. *Price on request*\n\n"
            "🎨 All cakes are fully customised — any flavour, theme or size!\n\n"
            "📞 Call/WhatsApp: *07036717932*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order a Cake", callback_data="order_cake")],
                [InlineKeyboardButton("⬅️ Back",        callback_data="menu_cake")],
            ])
        )

    elif data == "sub_chops":
        await query.edit_message_text(
            "🥟 *SMALL CHOPS*\n\n"
            "┌ Samosa (per dozen) ............. *₦3,500*\n"
            "├ Spring Rolls (per dozen) ....... *₦3,500*\n"
            "├ Puff Puff (per 50 pcs) ......... *₦4,500*\n"
            "└ Small Chops Platter (combo) .... from *₦12,000*\n\n"
            "🎉 Perfect for parties, events & celebrations!\n\n"
            "📞 Call/WhatsApp: *07036717932*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order Small Chops", callback_data="order_cake")],
                [InlineKeyboardButton("⬅️ Back",             callback_data="menu_cake")],
            ])
        )

    elif data == "sub_snacks":
        await query.edit_message_text(
            "🍩 *SNACKS*\n\n"
            "┌ Meat Pie ...................... *₦700* each\n"
            "├ Egg Roll ...................... *₦600* each\n"
            "├ Doughnuts (per 6) ............. *₦2,500*\n"
            "├ Chin Chin (per 200g) .......... *₦1,500*\n"
            "├ Fish Roll ..................... *₦700* each\n"
            "└ Sausage Rolls ................. *₦600* each\n\n"
            "🛍️ Bulk orders available at discounted rates!\n\n"
            "📞 Call/WhatsApp: *07036717932*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order Snacks", callback_data="order_cake")],
                [InlineKeyboardButton("⬅️ Back",        callback_data="menu_cake")],
            ])
        )

    elif data == "sub_catering":
        await query.edit_message_text(
            "🍽️ *INDOOR & OUTDOOR CATERING*\n\n"
            "┌ Small Event (up to 50 guests) .. from *₦80,000*\n"
            "├ Medium Event (51–150 guests) ... from *₦150,000*\n"
            "└ Large/Corporate (150+ guests) .. *Price on request*\n\n"
            "✅ Includes setup & serving staff\n"
            "✅ Customised menu for your event\n"
            "✅ Indoor & outdoor coverage\n\n"
            "⚠️ _Advance booking required_\n\n"
            "📞 Call/WhatsApp: *07036717932*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Book Catering", callback_data="order_catering")],
                [InlineKeyboardButton("⬅️ Back",         callback_data="menu_cake")],
            ])
        )

    # ── Millet Flour section ─────────────────────────────────────────────────
    elif data == "menu_flour":
        await query.edit_message_text(
            "🌾 *Eunique Food — Millet Flour*\n\n"
            "_Natural • Nutritious • Pure_\n\n"
            "100% Whole Grain Millet Flour — packed with essential nutrients.\n\n"
            "What would you like to know?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=flour_menu_keyboard()
        )

    elif data == "sub_flour_prices":
        await query.edit_message_text(
            "🌾 *MILLET FLOUR — PRICES & SIZES*\n\n"
            "┌ 500g .......................... *₦1,800*\n"
            "├ 1 kg .......................... *₦3,200*\n"
            "├ 2 kg .......................... *₦6,000*\n"
            "├ 5 kg .......................... *₦14,000*\n"
            "└ 10 kg (Trade Pack) ............. from *₦26,000*\n\n"
            "💡 Bulk & wholesale discounts available!\n\n"
            "📞 Call/WhatsApp: *07036717932*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order Now",  callback_data="order_flour")],
                [InlineKeyboardButton("⬅️ Back",      callback_data="menu_flour")],
            ])
        )

    elif data == "sub_flour_health":
        await query.edit_message_text(
            "❤️ *HEALTH BENEFITS OF MILLET FLOUR*\n\n"
            "✅ Rich in Fibre\n"
            "✅ High in Protein\n"
            "✅ Supports Heart Health\n"
            "✅ Helps Regulate Blood Sugar\n"
            "✅ Aids Weight Loss\n"
            "✅ 100% Natural — No additives\n\n"
            "_Great for the whole family including diabetics & those on a healthy diet!_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order Now", callback_data="order_flour")],
                [InlineKeyboardButton("⬅️ Back",     callback_data="menu_flour")],
            ])
        )

    elif data == "sub_flour_prep":
        await query.edit_message_text(
            "👩‍🍳 *HOW TO PREPARE MILLET SWALLOW*\n\n"
            "1️⃣ Boil some quantity of water\n"
            "2️⃣ Add in some cold water\n"
            "3️⃣ Gradually add your millet flour and stir\n"
            "4️⃣ Cover and cook for about 5 minutes\n"
            "5️⃣ Stir again very well to desired texture\n"
            "6️⃣ Serve with any soup of your choice 🍲\n\n"
            "_Storage: Keep in an airtight container once opened_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛒 Order Flour", callback_data="order_flour")],
                [InlineKeyboardButton("⬅️ Back",       callback_data="menu_flour")],
            ])
        )

    # ── Location & Contact ───────────────────────────────────────────────────
    elif data == "info_location":
        await query.edit_message_text(
            "📍 *OUR LOCATION*\n\n"
            "No. 31 Erediauwa Street,\n"
            "Off Erodiuwa Road, Sapele Road,\n"
            "*Benin City*\n\n"
            "🕐 *Business Hours:*\n"
            "Monday – Saturday: 8:00am – 7:00pm\n"
            "Sunday: 10:00am – 4:00pm\n\n"
            "📞 *Call/WhatsApp:* 07036717932\n"
            "📧 *Email:* euniquefood@gmail.com",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_main_keyboard()
        )

    elif data == "info_contact":
        await query.edit_message_text(
            "📞 *CONTACT EUNIQUE*\n\n"
            "📱 *WhatsApp/Call:*\n"
            "• 07036717932\n"
            "• 07054382079\n\n"
            "📧 *Email:* euniquefood@gmail.com\n\n"
            "📍 *Address:*\nNo. 31 Erediauwa Street, Off Erodiuwa Road,\nSapele Road, Benin City\n\n"
            "_Our team will respond as quickly as possible!_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_main_keyboard()
        )

    # ── AI Chat mode ─────────────────────────────────────────────────────────
    elif data == "ai_chat":
        ctx.user_data["mode"] = "ai_chat"
        await query.edit_message_text(
            "💬 *AI Chat Mode Activated!*\n\n"
            "You can now ask me anything about Eunique — prices, products, how to order, recipes and more!\n\n"
            "Just type your question below 👇\n\n"
            "_Type /menu to go back to the menu_",
            parse_mode=ParseMode.MARKDOWN
        )

    # ── Order flows ──────────────────────────────────────────────────────────
    elif data == "order_start":
        await query.edit_message_text(
            "🛒 *PLACE AN ORDER*\n\nWhat would you like to order?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=order_type_keyboard()
        )

    elif data in ("order_cake", "order_flour", "order_catering"):
        product_map = {
            "order_cake":     "Cakes / Small Chops / Snacks",
            "order_flour":    "Millet Flour",
            "order_catering": "Event Catering",
        }
        product = product_map[data]
        user_orders[query.from_user.id] = {"type": product, "step": "name"}
        ctx.user_data["ordering"] = True
        ctx.user_data["order_product"] = product
        await query.edit_message_text(
            f"🛒 *Order: {product}*\n\n"
            "Let's get your order ready! 📝\n\n"
            "First, please type your *full name*:",
            parse_mode=ParseMode.MARKDOWN
        )

    elif data == "order_confirm":
        order = user_orders.get(query.from_user.id, {})
        await query.edit_message_text(
            "✅ *Order Received!*\n\n"
            "Thank you! Our team will contact you shortly to confirm your order and arrange payment/delivery.\n\n"
            f"📞 *Contact us directly:* {OWNER_PHONE}\n\n"
            "_Your Satisfaction Is Our Utmost Priority_ 🌟",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_main_keyboard()
        )
        # Notify owner
        if OWNER_CHAT_ID:
            try:
                summary = "\n".join([f"• {k.title()}: {v}" for k, v in order.items() if k != "step"])
                await ctx.bot.send_message(
                    chat_id=OWNER_CHAT_ID,
                    text=f"🔔 *NEW ORDER RECEIVED!*\n\n{summary}\n\n⚡ Please follow up with the customer.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.warning(f"Could not notify owner: {e}")
        user_orders.pop(query.from_user.id, None)
        ctx.user_data.pop("ordering", None)

    elif data == "order_cancel":
        user_orders.pop(query.from_user.id, None)
        ctx.user_data.pop("ordering", None)
        await query.edit_message_text(
            "❌ Order cancelled. No worries — come back anytime!\n\n"
            "🏠 Back to main menu?",
            reply_markup=back_main_keyboard()
        )

# ═══════════════════════════════════════════════════════════════════════════
#  MESSAGE HANDLER (free text)
# ═══════════════════════════════════════════════════════════════════════════
async def message_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    text     = update.message.text.strip()

    # ── Order collection flow ────────────────────────────────────────────────
    if ctx.user_data.get("ordering") and user_id in user_orders:
        order = user_orders[user_id]
        step  = order.get("step")

        if step == "name":
            order["name"] = text
            order["step"] = "phone"
            await update.message.reply_text(
                f"👍 Got it, *{text}*!\n\nNow please enter your *phone number* (WhatsApp preferred):",
                parse_mode=ParseMode.MARKDOWN
            )

        elif step == "phone":
            order["phone"] = text
            order["step"] = "details"
            product = order.get("type", "")
            extra = ""
            if "Catering" in product:
                extra = "\n\n_Please include: event date, venue, number of guests & menu preferences._"
            elif "Flour" in product:
                extra = "\n\n_Please include: size (500g / 1kg / 2kg / 5kg / 10kg) & quantity._"
            else:
                extra = "\n\n_Please include: item(s), quantity, flavour/design preferences & delivery date._"
            await update.message.reply_text(
                f"📝 *Order Details*\n\nPlease describe what you want to order:{extra}",
                parse_mode=ParseMode.MARKDOWN
            )

        elif step == "details":
            order["details"] = text
            order["step"] = "address"
            await update.message.reply_text(
                "📍 Finally, please provide your *delivery address* (or type *pickup* if you'll collect):",
                parse_mode=ParseMode.MARKDOWN
            )

        elif step == "address":
            order["address"] = text
            order["step"] = "done"
            # Show order summary
            summary = (
                f"📋 *ORDER SUMMARY*\n\n"
                f"• Product: {order.get('type')}\n"
                f"• Name: {order.get('name')}\n"
                f"• Phone: {order.get('phone')}\n"
                f"• Details: {order.get('details')}\n"
                f"• Delivery: {order.get('address')}\n\n"
                f"Is everything correct?"
            )
            await update.message.reply_text(
                summary,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_order_keyboard()
            )
        return

    # ── AI Chat mode ─────────────────────────────────────────────────────────
    if ctx.user_data.get("mode") == "ai_chat" or not ctx.user_data.get("ordering"):
        # Always try AI for natural language (unless actively ordering)
        await update.message.chat.send_action("typing")

        # Keep conversation history (last 10 turns)
        history = user_chat_history.setdefault(user_id, [])
        history.append({"role": "user", "content": text})
        if len(history) > 20:
            history = history[-20:]
            user_chat_history[user_id] = history

        try:
            response = ai.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=history
            )
            reply = response.content[0].text
            history.append({"role": "assistant", "content": reply})

            await update.message.reply_text(
                reply,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏠 Main Menu",    callback_data="back_main"),
                     InlineKeyboardButton("🛒 Place Order",  callback_data="order_start")],
                ])
            )
        except Exception as e:
            logger.error(f"AI error: {e}")
            await update.message.reply_text(
                "😅 I'm having a little trouble right now. Please contact us directly:\n\n"
                f"📞 *{OWNER_PHONE}*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard()
            )

# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND SHORTCUTS
# ═══════════════════════════════════════════════════════════════════════════
async def menu_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("mode", None)
    ctx.user_data.pop("ordering", None)
    await update.message.reply_text(
        "🏠 *Main Menu*\n\nHow can we help you today?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )

async def order_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 *Place an Order*\n\nWhat would you like to order?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=order_type_keyboard()
    )

async def contact_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Contact Eunique*\n\n"
        "📱 WhatsApp/Call:\n• 07036717932\n• 07054382079\n\n"
        "📧 euniquefood@gmail.com\n\n"
        "📍 No. 31 Erediauwa Street, Off Erodiuwa Road,\nSapele Road, Benin City",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )

async def chat_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["mode"] = "ai_chat"
    await update.message.reply_text(
        "💬 *AI Chat Mode*\n\nAsk me anything about Eunique! 👇",
        parse_mode=ParseMode.MARKDOWN
    )

async def cancel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_orders.pop(update.effective_user.id, None)
    ctx.user_data.clear()
    await update.message.reply_text(
        "✅ Cancelled. Back to the main menu!",
        reply_markup=main_menu_keyboard()
    )

# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("menu",    menu_cmd))
    app.add_handler(CommandHandler("order",   order_cmd))
    app.add_handler(CommandHandler("contact", contact_cmd))
    app.add_handler(CommandHandler("chat",    chat_cmd))
    app.add_handler(CommandHandler("cancel",  cancel_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 EuniqueBot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
