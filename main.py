from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import pymongo

# استبدل برمز التوكن الخاص بك
TOKEN = '7331778477:AAG0iLffb5EA7O_T6yrrSv3FA_yPITTHXPc'

# توصيل MongoDB
client = pymongo.MongoClient("mongodb+srv://TelegramBot:XshSRgwp0g6vbwPN@curiox.ttgbp.mongodb.net/?retryWrites=true&w=majority&appName=CurioX")
db = client['telegram_bot']
users_collection = db['users']

countries = ['السعودية', 'مصر', 'تركيا', 'إندونيسيا', 'الجزائر']

# وظيفة بدء اللعبة
async def start(update: Update, context):
    user_id = update.message.from_user.id

    # التحقق من وجود اللاعب في قاعدة البيانات
    user = users_collection.find_one({'user_id': user_id})
    if not user:
        # إضافة اللاعب إلى قاعدة البيانات إذا لم يكن موجوداً
        users_collection.insert_one({'user_id': user_id, 'balance': 0, 'mosques_built': 0})
    
    # إرسال رسالة ترحيبية مع شرح للعبة وأزرار اختيار الدولة
    keyboard = [
        [InlineKeyboardButton("السعودية", callback_data='السعودية'),
         InlineKeyboardButton("مصر", callback_data='مصر')],
        [InlineKeyboardButton("تركيا", callback_data='تركيا'),
         InlineKeyboardButton("إندونيسيا", callback_data='إندونيسيا')],
        [InlineKeyboardButton("الجزائر", callback_data='الجزائر')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🕌 *مرحبًا بك في لعبة بناء المساجد!*\n"
        "🌍 في هذه اللعبة، هدفك هو جمع التبرعات لبناء المساجد في مختلف الدول. اختر الدولة التي ترغب في بدء بناء المسجد فيها.\n\n"
        "💡 طريقة اللعب:\n"
        "1️⃣ اختر دولة لبناء المسجد فيها.\n"
        "2️⃣ اختر المبلغ الذي ترغب في جمعه.\n"
        "3️⃣ سيتم بناء المسجد وزيادة رصيدك.\n\n"
        "🔗 لمتابعة المطور، اضغط على القناة: [قناة المطور](https://t.me/SAYVEN_X)",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# اختيار الدولة
async def choose_country(update: Update, context):
    user_id = update.message.from_user.id
    if users_collection.count_documents({'user_id': user_id}) == 0:
        await update.message.reply_text("يرجى كتابة /start للبدء أولاً.")
        return

    country_choice = update.callback_query.data
    if country_choice not in countries:
        await update.message.reply_text("❌ الرجاء اختيار دولة صحيحة من القائمة!")
        return

    # تحديث الدولة التي اختارها اللاعب
    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'current_country': country_choice}}
    )

    await update.callback_query.message.edit_text(
        f"✅ لقد اخترت {country_choice} لبناء المسجد.\n"
        "💸 اختر المبلغ الذي ترغب في جمعه:\n"
        "1️⃣ 1000 دينار\n"
        "2️⃣ 5000 دينار\n"
        "3️⃣ 10000 دينار"
    )

# اختيار التبرعات
async def donate(update: Update, context):
    user_id = update.message.from_user.id
    user = users_collection.find_one({'user_id': user_id})
    
    if not user or 'current_country' not in user:
        await update.message.reply_text("يرجى اختيار دولة أولاً باستخدام /start.")
        return

    donation_amount = update.message.text.strip()
    if donation_amount == "1000 دينار":
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'balance': 1000, 'mosques_built': 1}}
        )
    elif donation_amount == "5000 دينار":
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'balance': 5000, 'mosques_built': 1}}
        )
    elif donation_amount == "10000 دينار":
        users_collection.update_one(
            {'user_id': user_id},
            {'$inc': {'balance': 10000, 'mosques_built': 1}}
        )
    else:
        await update.message.reply_text("❌ اختيار غير صحيح. حاول مرة أخرى.")
        return

    user = users_collection.find_one({'user_id': user_id})
    await update.message.reply_text(
        f"🎉 تم بناء المسجد بنجاح في {user['current_country']}! "
        f"\n💰 رصيدك الحالي: {user['balance']} دينار.\n"
        "🔄 هل ترغب في بناء مسجد آخر؟\n"
        "اكتب اسم دولة جديدة للمتابعة أو اكتب /leaderboard لعرض أفضل اللاعبين."
    )

# عرض قائمة أفضل اللاعبين
async def leaderboard(update: Update, context):
    # استرجاع قائمة اللاعبين وترتيبهم
    leaderboard = users_collection.find().sort('mosques_built', -1).limit(10)
    message = "🏆 *أفضل اللاعبين في بناء المساجد:*\n"
    for idx, user in enumerate(leaderboard):
        message += f"{idx+1}. 🕌 - {user['mosques_built']} مساجد\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# تهيئة البوت
async def main():
    # تهيئة التطبيق
    application = Application.builder().token(TOKEN).build()

    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Regex(f"^({'|'.join(countries)})$"), choose_country))
    application.add_handler(MessageHandler(filters.Regex("^(1000 دينار|5000 دينار|10000 دينار)$"), donate))
    application.add_handler(CommandHandler('leaderboard', leaderboard))

    # تشغيل البوت
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
