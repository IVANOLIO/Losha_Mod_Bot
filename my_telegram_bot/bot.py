from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from datetime import datetime

# استبدل هذا بـ Token الخاص بك من BotFather
TOKEN = "5606703935:AAE4xTqwD48cMPte26Se9zghUHINhZ_aPg4"

# دالة استقبال أمر /start
async def start(update: Update, context):
    await update.message.reply_text('مرحبًا! أنا بوت **CurioX** الشخصي! كيف يمكنني مساعدتك اليوم؟')

# دالة عرض الوقت الحالي
async def time(update: Update, context):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await update.message.reply_text(f'الوقت الحالي: {current_time}')

# دالة الرد على الرسائل
async def echo(update: Update, context):
    await update.message.reply_text(f'أنت قلت: {update.message.text}')

# إعداد البوت
async def main():
    application = Application.builder().token(TOKEN).build()

    # إضافة الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("time", time))

    # إضافة Handler للرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # بدء البوت
    await application.run_polling()

if __name__ == '__main__':
    # قم بتشغيل البوت مباشرة
    import asyncio
    asyncio.run(main())
