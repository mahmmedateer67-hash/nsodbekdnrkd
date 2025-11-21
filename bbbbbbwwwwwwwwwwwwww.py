from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from telegram.constants import ChatType

TOKEN = "7581740731:AAEnmzd06ozI9mmepdOYv3wgNIlehFx88vw"
ADMIN_GROUP_ID = -1002454497050
AUCTION_CHANNEL = "@ieexa"

pending_requests = {}

# ---------------------- START ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != ChatType.PRIVATE:
        return

    user_name = update.effective_user.first_name

    keyboard = [
        [
            InlineKeyboardButton("نشر هدية", callback_data="gift"),
            InlineKeyboardButton("نشر معرف", callback_data="username")
        ],
        [InlineKeyboardButton("قناة المزاد", url="https://t.me/ieexa")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"<b>مرحباً {user_name} أهلاً بك في بوت المزاد\nاختر نوع النشر</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# ------------------ USER BUTTONS -------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gift":
        context.user_data['type'] = 'gift'
        await query.edit_message_text(
            "<b>أرسل رابط الهدية وفق الشروط</b>\nhttps://t.me/ieexa/3577",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back")]]),
            parse_mode="HTML"
        )

    elif query.data == "username":
        keyboard = [
            [
                InlineKeyboardButton("NFT", callback_data="username_nft"),
                InlineKeyboardButton("عادي", callback_data="username_normal")
            ],
            [InlineKeyboardButton("رجوع", callback_data="back")]
        ]
        await query.edit_message_text(
            "<b>اختر نوع النشر للمعرف</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data in ["username_nft", "username_normal"]:
        context.user_data['type'] = 'username'
        context.user_data['username_publish_type'] = (
            "nft" if query.data == "username_nft" else "normal"
        )
        await query.edit_message_text(
            "<b>أرسل المعرف ويبدأ بـ @</b>\nتطبيق الشروط\nhttps://t.me/ieexa/3577",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع", callback_data="back")]]),
            parse_mode="HTML"
        )

    elif query.data == "back":
        user = query.from_user
        keyboard = [
            [
                InlineKeyboardButton("نشر هدية", callback_data="gift"),
                InlineKeyboardButton("نشر معرف", callback_data="username")
            ],
            [InlineKeyboardButton("قناة المزاد", url="https://t.me/ieexa")]
        ]
        await query.edit_message_text(
            f"<b>مرحباً {user.first_name} اختر نوع النشر</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

# ---------------- USER MESSAGE HANDLER ----------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != ChatType.PRIVATE:
        return

    req_type = context.user_data.get("type")
    if not req_type:
        return

    user = update.effective_user
    text = update.message.text.strip()

    # ---------- GIFT ----------
    if req_type == "gift":
        if not (
            text.startswith("t.me/nft/") or
            text.startswith("http://t.me/nft/") or
            text.startswith("https://t.me/nft/")
        ):
            await update.message.reply_text(
                "<b>رابط الهدية غير صحيح</b>",
                parse_mode="HTML"
            )
            return

        request_id = str(update.message.message_id)
        pending_requests[request_id] = {
            "user_id": user.id,
            "content": text,
            "type": "gift"
        }

        keyboard = [
            [
                InlineKeyboardButton("موافقة", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton("رفض", callback_data=f"reject_{request_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=f"<b>طلب نشر هدية من</b> {user.mention_html()}\n{text}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text(
            "<b>تم إرسال طلبك للمراجعة</b>",
            parse_mode="HTML"
        )

    # ---------- USERNAME ----------
    elif req_type == "username":
        if not text.startswith("@"):
            await update.message.reply_text("<b>يجب أن يبدأ المعرف بـ @</b>", parse_mode="HTML")
            return

        publish_type = context.user_data.get("username_publish_type", "normal")

        request_id = str(update.message.message_id)
        pending_requests[request_id] = {
            "user_id": user.id,
            "content": text,
            "type": "username",
            "publish_type": publish_type
        }

        keyboard = [
            [
                InlineKeyboardButton("موافقة", callback_data=f"approve_{request_id}"),
                InlineKeyboardButton("رفض", callback_data=f"reject_{request_id}")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                f"<b>طلب نشر معرف من</b> {user.mention_html()}\n"
                f"المعرف: {text}\n"
                f"نوع النشر: {'NFT' if publish_type=='nft' else 'عادي'}"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text(
            "<b>تم إرسال طلبك للمراجعة</b>",
            parse_mode="HTML"
        )

# ---------------- ADMIN CALLBACK --------------------

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    request_id = data.split("_", 1)[1]

    request = pending_requests.get(request_id)
    if not request:
        await query.edit_message_text("<b>هذا الطلب غير موجود</b>")
        return

    user_id = request["user_id"]

    # -------- APPROVE --------
    if data.startswith("approve_"):
        if request["type"] == "gift":
            gift_link = request["content"]
            msg = f"""<b>Upgraded Gift Soom</b> <a href="{gift_link}">(Details)</a>

<b>قوانين المزاد</b>
- ممنوع الكلام داخل المناقشة
- ممنوع سعر أقل من السابق
- حدد السعر مع العملة

<b>Auction channel - {AUCTION_CHANNEL}</b>"""

        else:
            content = request["content"]
            publish_type = request["publish_type"]

            if publish_type == "nft":
                title = f"Username NFT Soom • {content}"
            else:
                title = f"Username Soom • {content}"

            msg = f"""<b>{title}</b>

<b>قوانين المزاد</b>
- ممنوع الكلام داخل المناقشة
- ممنوع سعر أقل من السابق
- حدد السعر مع العملة

<b>Auction channel - {AUCTION_CHANNEL}</b>"""

        sent_msg = await context.bot.send_message(
            chat_id=AUCTION_CHANNEL,
            text=msg,
            parse_mode="HTML",
            disable_web_page_preview=True
        )

        message_link = f"https://t.me/{AUCTION_CHANNEL.strip('@')}/{sent_msg.message_id}"

        await context.bot.send_message(
            chat_id=user_id,
            text=f"<b>تمت الموافقة على طلبك\nالرابط\n{message_link}</b>",
            parse_mode="HTML"
        )

        await query.edit_message_text("<b>تمت الموافقة على الطلب</b>")
        del pending_requests[request_id]

    # -------- REJECT --------
    elif data.startswith("reject_"):
        await context.bot.send_message(
            chat_id=user_id,
            text="<b>تم رفض الطلب\nراجع الشروط https://t.me/ieexa/3577</b>",
            parse_mode="HTML"
        )
        await query.edit_message_text("<b>تم الرفض</b>")
        del pending_requests[request_id]

# ---------------- RUN APP ----------------------

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CallbackQueryHandler(button_handler, pattern="^(gift|username|username_nft|username_normal|back)$"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|reject_).+"))

print("Bot is running")
app.run_polling()
