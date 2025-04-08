from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import sqlite3

# 📌 اتصال به دیتابیس و ایجاد جدول‌ها
conn = sqlite3.connect("payments.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS record (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, total REAL)")
conn.commit()

# 📌 بررسی و دریافت نام کاربر
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if user_data is None:
        cursor.execute("INSERT INTO users (user_id, name) VALUES (?, ?)", (user_id, text))
        conn.commit()
        await update.message.reply_text(f"✅ اسمت ثبت شد: {text}\nحالا مبلغ واریزی رو بفرست.")
    else:
        await add_payment(update, context, user_data[0])

# 📌 ثبت و نمایش واریزی
async def add_payment(update: Update, context: CallbackContext, user_name: str) -> None:
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    try:
        amount = float(text)
        cursor.execute("INSERT INTO payments (user_id, amount) VALUES (?, ?)", (user_id, amount))
        conn.commit()

        cursor.execute("SELECT SUM(amount) FROM payments WHERE user_id=?", (user_id,))
        total_amount = cursor.fetchone()[0] or 0

        # 📌 بررسی رکورددار جدید
        cursor.execute("SELECT user_id, name, total FROM record WHERE id=1")
        record_data = cursor.fetchone()

        if record_data is None or total_amount > record_data[2]:  # اگر رکورد جدید زده شود
            cursor.execute("INSERT OR REPLACE INTO record (id, user_id, name, total) VALUES (1, ?, ?, ?)", (user_id, user_name, total_amount))
            conn.commit()
            record_holder = user_name
            record_amount = total_amount
        else:
            record_holder = record_data[1]
            record_amount = record_data[2]

        message = f"""👑 {user_name}


واریزی: {amount:,.0f} تومن

جمع واریزی تا این لحظه: {total_amount:,.0f} تومن🔥

🏆 رکورد واریزی در دست: {record_holder} (‼️{record_amount:,.0f}‼️)"""
        
        await update.message.reply_text(message)
    except ValueError:
        await update.message.reply_text("❌ لطفاً فقط مبلغ را به عدد ارسال کنید.")

# 📌 نمایش مجموع واریزی‌ها
async def get_total(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        await update.message.reply_text("❗️ لطفاً اول اسمت رو بفرست تا ثبت بشه.")
        return

    user_name = user_data[0]

    cursor.execute("SELECT SUM(amount) FROM payments WHERE user_id=?", (user_id,))
    total_amount = cursor.fetchone()[0] or 0

    cursor.execute("SELECT user_id, name, total FROM record WHERE id=1")
    record_data = cursor.fetchone()
    record_holder = record_data[1] if record_data else "نامشخص"
    record_amount = record_data[2] if record_data else 0

    message = f"""👑 {user_name}

جمع واریزی تا این لحظه: {total_amount:,.0f} تومن🔥

🏆 رکورد واریزی در دست: {record_holder} (‼️{record_amount:,.0f}‼️)"""
    
    await update.message.reply_text(message)

# 📌 ریست کردن واریزی‌ها (رکورد و نام کاربر حفظ می‌شود)
async def reset_payments(update: Update, context: CallbackContext) -> None:
    cursor.execute("DELETE FROM payments")
    conn.commit()
    await update.message.reply_text("🔄 مجموع واریزی‌ها ریست شد، اما رکورد و نام کاربر حفظ شده است.")

# 📌 شروع ربات
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    cursor.execute("SELECT name FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        await update.message.reply_text(f"👋 خوش اومدی {user_data[0]}!\nمبلغ واریزی رو بفرست تا ذخیره کنم.")
    else:
        await update.message.reply_text("👋 سلام! لطفاً اسم خودت رو بفرست تا ثبت بشه.")

# 📌 اجرای ربات
def main():
    TOKEN = "7641478550:AAHvsWrNhZJTdb4SPkO7UyJiQZ778wvpyFU"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("total", get_total))
    application.add_handler(CommandHandler("reset", reset_payments))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 ربات در حال اجرا است...")
    application.run_polling()

if __name__ == '__main__':
    main()
