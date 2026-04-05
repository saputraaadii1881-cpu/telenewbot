import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================= ENV =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DB =================
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
    total INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ================= KEYBOARD =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 PRODUK", callback_data="produk")],
        [InlineKeyboardButton("📜 HISTORY", callback_data="history")],
        [InlineKeyboardButton("📖 PANDUAN", callback_data="panduan")],
        [InlineKeyboardButton("🛡️ GARANSI", callback_data="garansi")],
    ])

def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 TRANSAKSI", callback_data="admin_transaksi")],
        [InlineKeyboardButton("📦 ITEM", callback_data="admin_item")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="menu")],
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📌 MENU UTAMA", reply_markup=main_menu())

# ================= PRODUK =================
async def show_produk(query):
    rows = c.execute("SELECT * FROM products").fetchall()

    if not rows:
        await query.edit_message_text("Belum ada produk", reply_markup=back_menu())
        return

    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(f"{r[1]} | stok: {r[2]}", callback_data=f"item_{r[0]}")])

    buttons.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu")])

    await query.edit_message_text("📦 PRODUK", reply_markup=InlineKeyboardMarkup(buttons))

# ================= ITEM =================
async def show_item(query, pid):
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    if not r:
        await query.edit_message_text("Produk tidak ditemukan", reply_markup=back_menu())
        return

    buttons = [
        [InlineKeyboardButton("🛒 BELI", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]
    ]

    await query.edit_message_text(
        f"📦 {r[1]}\n💰 Harga: {r[3]}\n📊 Stok: {r[2]}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ================= BELI =================
async def buy(query, pid):
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    if not r or r[2] <= 0:
        await query.edit_message_text("❌ Stok habis", reply_markup=back_menu())
        return

    c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (pid,))
    c.execute(
        "INSERT INTO orders (user_id, product_id, qty, total) VALUES (?, ?, ?, ?)",
        (query.from_user.id, pid, 1, r[3]),
    )
    conn.commit()

    await query.edit_message_text("✅ Pembelian berhasil", reply_markup=back_menu())

# ================= HISTORY =================
async def show_history(query):
    rows = c.execute(
        "SELECT * FROM orders WHERE user_id=?", (query.from_user.id,)
    ).fetchall()

    text = "📜 HISTORY:\n"
    if not rows:
        text += "Belum ada transaksi"
    else:
        for r in rows:
            text += f"\n#{r[0]} | qty: {r[3]} | total: {r[4]}"

    await query.edit_message_text(text, reply_markup=back_menu())

# ================= ADMIN =================
async def admin_panel(query):
    if query.from_user.id != ADMIN_ID:
        return

    await query.edit_message_text("🛠 ADMIN PANEL", reply_markup=admin_menu())

# ================= TRANSAKSI =================
async def transaksi(query):
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    harian = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{today}%",)).fetchone()[0] or 0
    bulanan = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{month}%",)).fetchone()[0] or 0

    await query.edit_message_text(
        f"💰 TRANSAKSI\n\nHarian: {harian}\nBulanan: {bulanan}",
        reply_markup=back_menu()
    )

# ================= ITEM ADMIN =================
async def admin_item(query):
    await query.edit_message_text(
        "📦 ITEM ADMIN (dummy UI)\n\nTambah/Edit stok via DB/manual",
        reply_markup=back_menu()
    )

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "menu":
        await q.edit_message_text("📌 MENU UTAMA", reply_markup=main_menu())

    elif data == "produk":
        await show_produk(q)

    elif data.startswith("item_"):
        await show_item(q, int(data.split("_")[1]))

    elif data.startswith("buy_"):
        await buy(q, int(data.split("_")[1]))

    elif data == "history":
        await show_history(q)

    elif data == "panduan":
        await q.edit_message_text("📖 Panduan: pilih produk lalu klik beli", reply_markup=back_menu())

    elif data == "garansi":
        await q.edit_message_text("🛡️ Hubungi admin jika ada masalah", reply_markup=back_menu())

    # ADMIN
    elif data == "admin":
        await admin_panel(q)

    elif data == "admin_transaksi":
        await transaksi(q)

    elif data == "admin_item":
        await admin_item(q)

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(callback))

print("BOT RUNNING...")
app.run_polling()
