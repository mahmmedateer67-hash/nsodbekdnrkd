from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TOKEN = "7581740731:AAEnmzd06ozI9mmepdOYv3wgNIlehFx88vw"
ADMIN_GROUP_ID = -1002454497050
AUCTION_CHANNEL = "@ieexa" 

pending_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
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
        f"<b>مرحباً {user_name}، أهلاً بك في بوت مزاد 𝗔𝗨𝗖𝗧𝗜𝗢𝗡 𝗪𝗔𝗥𝗙𝗔𝗟𝗜.\nاختر نوع المزاد الذي ترغب في نشره:</b>",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "gift":
        context.user_data['type'] = 'gift'
        await query.edit_message_text(
            "<b>أرسل الآن رابط الهدية مع التأكد من تطبيق الشروط: https://t.me/ieexa/3577</b>",
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
            "<b>اختر نوع النشر للمعرف:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

    elif query.data in ["username_nft", "username_normal"]:
        context.user_data['type'] = 'username'
        context.user_data['username_publish_type'] = "nft" if query.data == "username_nft" else "normal"
        await query.edit_message_text(
            "<b>أرسل المعرف مع علامة @hhh6h6، وتأكد من تطبيق الشروط: https://t.me/ieexa/3577</b>",
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
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"<b>مرحباً {user.first_name}، أهلاً بك في بوت مزاد 𝗔𝗨𝗖𝗧𝗜𝗢𝗡 𝗪𝗔𝗥𝗙𝗔𝗟𝗜.\nاختر نوع المزاد الذي ترغب في نشره:</b>",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    req_type = context.user_data.get('type')
    user = update.effective_user
    text = update.message.text.strip()

    if req_type == "gift":
        if not (text.startswith("t.me/nft/") or text.startswith("http://t.me/nft/") or text.startswith("https://t.me/nft/")):
            await update.message.reply_text("<b>رابط الهدية غير صحيح. تأكد أن يبدأ بـ t.me/nft/ أو http://t.me/nft/ أو https://t.me/nft/</b>", parse_mode="HTML")
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
            text=f"<b>طلب جديد لنشر هدية من: {user.mention_html()}\nرابط الهدية:\n{text}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        await update.message.reply_text("<b>تم إرسال طلبك للمراجعة من قبل الإدارة.</b>", parse_mode="HTML")

    elif req_type == "username":
        if not text.startswith("@"):
            await update.message.reply_text("<b>يرجى كتابة المعرف بشكل صحيح ويبدأ بعلامة @</b>", parse_mode="HTML")
            return

        publish_type = context.user_data.get('username_publish_type', 'normal')
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
            text=f"<b>طلب نشر معرف من: {user.mention_html()}\nالمعرف: {text}\nنوع النشر: {'NFT' if publish_type == 'nft' else 'عادي'}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        await update.message.reply_text("<b>تم إرسال طلبك للمراجعة من قبل الإدارة.</b>", parse_mode="HTML")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith(("approve_", "reject_")):
        request_id = data.split("_", 1)[1]
        request = pending_requests.get(request_id)

        if not request:
            await query.edit_message_text("⚠️ الطلب غير موجود أو تم التعامل معه بالفعل.")
            return

        user_id = request["user_id"]

        if data.startswith("approve_"):
            if request["type"] == "gift":
                gift_link = request["content"]
                msg = f"""<b>Upgraded Gift Soom •</b> <a href="{gift_link}">(Details)</a>

<b>- - - - - - - - - - - - - - - - - - - - - - - 
 - ممنوع الكلام داخل المناقشة . 
- ممنوع تعطي سعر اقل من يلي قبلك . 
- حدد السعر مع العملة .
- - - - - - - - - - - - - - - - - - - - -</b>

<b>Auction channel - {AUCTION_CHANNEL}</b>"""
                sent_message = await context.bot.send_message(chat_id=AUCTION_CHANNEL, text=msg, parse_mode="HTML", disable_web_page_preview=True)
                message_link = f"https://t.me/{AUCTION_CHANNEL.strip('@')}/{sent_message.message_id}"
                await context.bot.send_message(chat_id=user_id, text=f"<b>تمت الموافقة على طلبك ونشر الهدية.\nرابط الرسالة: {message_link}</b>", parse_mode="HTML")

            elif request["type"] == "username":
                content = request["content"]
                publish_type = request.get("publish_type", "normal")

                if publish_type == "nft":
                    msg = f"""<b>Username NFT Soom • {content}</b>

<b>- - - - - - - - - - - - - - - - - - - - - - - 
- ممنوع الكلام داخل المناقشة .
- ممنوع تعطي سعر اقل من يلي قبلك . 
- حدد السعر مع العملة . 
- - - - - - - - - - - - - - - - - - - - -</b>

<b>Auction channel - {AUCTION_CHANNEL}</b>"""
                else:
                    msg = f"""<b>Username Soom • {content}</b>

<b>- - - - - - - - - - - - - - - - - - - - - - - 
- ممنوع الكلام داخل المناقشة  .
 - ممنوع تعطي سعر اقل من يلي قبلك . 
- حدد السعر مع العملة . 
 - - - - - - - - - - - - - - - - - - - - -</b>

<b>Auction channel - {AUCTION_CHANNEL}</b>"""
                sent_message = await context.bot.send_message(chat_id=AUCTION_CHANNEL, text=msg, parse_mode="HTML", disable_web_page_preview=True)
                message_link = f"https://t.me/{AUCTION_CHANNEL.strip('@')}/{sent_message.message_id}"
                await context.bot.send_message(chat_id=user_id, text=f"<b>تمت الموافقة على طلبك ونشر المعرف.\nرابط الرسالة: {message_link}</b>", parse_mode="HTML")

            await query.edit_message_text("<b>تمت الموافقة على الطلب ونشره بنجاح.</b>", parse_mode="HTML")
            del pending_requests[request_id]

        elif data.startswith("reject_"):
            await context.bot.send_message(chat_id=user_id, text="<b>تم رفض طلبك راجع الشروط جيداً https://t.me/ieexa/3577</b>", parse_mode="HTML")
            await query.edit_message_text("<b>تم رفض الطلب.</b>", parse_mode="HTML")
            del pending_requests[request_id]

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler, pattern="^(gift|username|username_nft|username_normal|back)$"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|reject_).+"))

print(". Run .")
app.run_polling()