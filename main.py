from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters
import pymongo
from bson.objectid import ObjectId
import nest_asyncio  # إضافة هذه المكتبة لتطبيق الحلقات المتداخلة

# تطبيق nest_asyncio لتفعيل دعم الحلقات المتداخلة
nest_asyncio.apply()

# إعدادات MongoDB
client = pymongo.MongoClient("mongodb+srv://TelegramBot:XshSRgwp0g6vbwPN@curiox.ttgbp.mongodb.net/?retryWrites=true&w=majority&appName=CurioX")
db = client['telegram_bot']
users_collection = db['users']
questions_collection = db['questions']
pending_requests_collection = db['pending_requests']

# المالك الأساسي
OWNER_ID = 5247871063
admins = [OWNER_ID]
required_channel = "@SAYVEN_X"
applicants = {}

# وظيفة الاشتراك الإجباري
async def check_subscription(user_id, bot):
    if required_channel:
        try:
            # محاولة الحصول على حالة الاشتراك
            status = await bot.get_chat_member(required_channel, user_id).status
            # إذا كان المستخدم عضوًا أو مسؤولًا أو منشئًا، يتم التحقق بنجاح
            if status in ["member", "administrator", "creator"]:
                return True
            else:
                return False
        except Exception as e:
            # طباعة رسالة الخطأ إذا حدث استثناء
            print(f"Error checking subscription for user {user_id}: {e}")
            return False
    return True

# بدء التسجيل
async def start(update: Update, context):
    user = update.effective_user
    if not await check_subscription(user.id, context.bot):
        await update.message.reply_text(f"يرجى الاشتراك في القناة أولاً: {required_channel}")
        return
    applicants[user.id] = {"answers": [], "step": 0}
    question = await get_question_by_index(0)
    await update.message.reply_text(question)
    return 1

# جلب السؤال من MongoDB
async def get_question_by_index(index):
    question = questions_collection.find_one({"index": index})
    return question['text'] if question else "لا يوجد سؤال في هذه الفئة."

# التعامل مع الإجابات
async def handle_answer(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in applicants:
        return
    applicants[user_id]["answers"].append(update.message.text)
    applicants[user_id]["step"] += 1

    question = await get_question_by_index(applicants[user_id]["step"])
    if question:
        await update.message.reply_text(question)
        return 1
    else:
        # إرسال الإجابات للإدارة
        await send_to_admins(user_id, applicants[user_id]["answers"], context.bot)
        del applicants[user_id]
        await update.message.reply_text("تم إرسال طلبك للإدارة.")
        return ConversationHandler.END

# إرسال الطلبات للمشرفين
async def send_to_admins(user_id, answers, bot):
    pending_requests_collection.insert_one({"user_id": user_id, "answers": answers})
    buttons = [
        [InlineKeyboardButton("✅ قبول", callback_data=f"accept_{user_id}"),
         InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")]
    ]
    text = f"طلب جديد من المستخدم {user_id}:\n" + "\n".join(
        [f"{i + 1}. {q}: {a}" for i, (q, a) in enumerate(zip(answers))])
    for admin in admins:
        await bot.send_message(admin, text, reply_markup=InlineKeyboardMarkup(buttons))

# التعامل مع قرار المشرف
async def handle_decision(update: Update, context):
    query = update.callback_query
    decision, user_id = query.data.split("_")
    user_id = int(user_id)
    await query.answer()

    if decision == "accept":
        await context.bot.send_message(user_id, "تهانينا! تم قبولك.")
    else:
        await context.bot.send_message(user_id, "نعتذر، تم رفض طلبك.")
    pending_requests_collection.delete_one({"user_id": user_id})
    await query.edit_message_text("تم تنفيذ القرار.")

# لوحة تحكم المشرف
async def admin_panel(update: Update, context):
    if update.effective_user.id not in admins:
        return
    buttons = [
        [InlineKeyboardButton("➕ إضافة سؤال", callback_data="add_question"),
         InlineKeyboardButton("➖ حذف سؤال", callback_data="remove_question")],
        [InlineKeyboardButton("📢 تحديد قناة", callback_data="set_channel")],
        [InlineKeyboardButton("👤 إضافة أدمن", callback_data="add_admin")]
    ]
    await update.message.reply_text("لوحة تحكم الأدمن:", reply_markup=InlineKeyboardMarkup(buttons))

# إضافة سؤال
async def add_question(update: Update, context):
    if update.effective_user.id not in admins:
        return
    new_question = ' '.join(context.args)
    if new_question:
        questions_collection.insert_one({"text": new_question, "index": questions_collection.count_documents({})})
        await update.message.reply_text(f"تم إضافة السؤال: {new_question}")
    else:
        await update.message.reply_text("يرجى إرسال السؤال الذي تريد إضافته.")

# حذف سؤال
async def remove_question(update: Update, context):
    if update.effective_user.id not in admins:
        return
    try:
        index = int(context.args[0])
        questions_collection.delete_one({"index": index})
        await update.message.reply_text(f"تم حذف السؤال برقم {index}")
    except (IndexError, ValueError):
        await update.message.reply_text("يرجى إرسال الرقم الصحيح للسؤال الذي تريد حذفه.")

# إضافة أدمن
async def add_admin(update: Update, context):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        new_admin = int(context.args[0])
        admins.append(new_admin)
        await update.message.reply_text(f"تم إضافة {new_admin} كأدمن.")
    except (IndexError, ValueError):
        await update.message.reply_text("يرجى إرسال معرف الأدمن.")

# إعداد التطبيق
async def main():
    application = Application.builder().token("7495429621:AAF0UDFQxVPkJphrdU0RALSHL7Je65giXiQ").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer)]},
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_decision, pattern="^(accept|reject)_"))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("add_question", add_question))
    application.add_handler(CommandHandler("remove_question", remove_question))
    application.add_handler(CommandHandler("add_admin", add_admin))

    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("تم إيقاف البرنامج بواسطة المستخدم.")
    finally:
        if not loop.is_closed():
            loop.close()
