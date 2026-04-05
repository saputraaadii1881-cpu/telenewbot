from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DATABASE =================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    stock INTEGER,
    price INTEGER
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    qty INTEGER,
    total INTEGER
)
""")

conn.commit()


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 PRODUK", callback_data="produk")],
        [InlineKeyboardButton("📜 HISTORY ORDER", callback_data="history")],
        [InlineKeyboardButton("📖 PANDUAN ORDER", callback_data="panduan")],
        [InlineKeyboardButton("🛡️ CLAIM GARANSI", callback_data="garansi")]
    ]

    await update.message.reply_text(
        "Selamat datang di Bot Jualan",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= PRODUK =================
async def produk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rows = c.execute("SELECT * FROM products").fetchall()

    keyboard = []
    for r in rows:
        keyboard.append([
            InlineKeyboardButton(f"{r[1]} | Stok: {r[2]}", callback_data=f"item_{r[0]}")
        ])

    await query.edit_message_text(
        "📦 Daftar Produk",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ================= DETAIL =================
async def item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pid = int(query.data.split("_")[1])
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    text = f"""
📦 {r[1]}
💰 Harga: {r[3]}
📦 Stok: {r[2]}
"""

    keyboard = [
        [InlineKeyboardButton("BELI", callback_data=f"buy_{pid}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ================= BELI =================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pid = int(query.data.split("_")[1])
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    if r[2] <= 0:
        await query.edit_message_text("❌ Stok habis")
        return

    c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (pid,))
    c.execute("INSERT INTO orders (user_id, product_id, qty, total) VALUES (?, ?, ?, ?)",
              (query.from_user.id, pid, 1, r[3]))
    conn.commit()

    await query.edit_message_text("✅ Berhasil beli")


# ================= HISTORY =================
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    rows = c.execute("SELECT * FROM orders WHERE user_id=?", (query.from_user.id,)).fetchall()

    if not rows:
        await query.edit_message_text("Belum ada order")
        return

    text = "📜 History:\n"
    for r in rows:
        text += f"Order {r[0]} | Qty {r[3]} | Total {r[4]}\n"

    await query.edit_message_text(text)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("Admin aktif\nGunakan /add nama stok harga")


# ================= ADD ITEM =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        name = context.args[0]
        stock = int(context.args[1])
        price = int(context.args[2])

        c.execute("INSERT INTO products (name, stock, price) VALUES (?, ?, ?)",
                  (name, stock, price))
        conn.commit()

        await update.message.reply_text("✅ Item ditambahkan")

    except:
        await update.message.reply_text("Format: /add nama stok harga")


# ================= BUTTON =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "produk":
        await produk(update, context)
    elif data.startswith("item_"):
        await item(update, context)
    elif data.startswith("buy_"):
        await buy(update, context)
    elif data == "history":
        await history(update, context)
    elif data == "panduan":
        await update.callback_query.edit_message_text("Pilih produk lalu klik beli")
    elif data == "garansi":
        await update.callback_query.edit_message_text("Hubungi admin")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("add", add))
app.add_handler(CallbackQueryHandler(button))

print("BOT RUNNING...")
app.run_polling()
