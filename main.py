from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ================= DB =================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER, price INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, qty INTEGER, total INTEGER, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
conn.commit()

# ================= MENU =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 PRODUK", callback_data="produk")],
        [InlineKeyboardButton("📜 HISTORY", callback_data="history")],
        [InlineKeyboardButton("📖 PANDUAN", callback_data="panduan")],
        [InlineKeyboardButton("🛡️ GARANSI", callback_data="garansi")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 TRANSAKSI", callback_data="admin_transaksi")],
        [InlineKeyboardButton("📦 ITEM", callback_data="admin_item")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu Utama", reply_markup=menu())

# ================= PRODUK =================
async def produk(q):
    rows = c.execute("SELECT * FROM products").fetchall()

    kb = [[InlineKeyboardButton(f"{r[1]} | {r[2]}", callback_data=f"item_{r[0]}")] for r in rows]
    kb.append([InlineKeyboardButton("🔙", callback_data="back_menu")])

    await q.edit_message_text("📦 Produk", reply_markup=InlineKeyboardMarkup(kb))

# ================= ITEM =================
async def item(q, pid):
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    kb = [
        [InlineKeyboardButton("BELI", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton("🔙", callback_data="produk")]
    ]

    await q.edit_message_text(f"{r[1]}\nHarga: {r[3]}\nStok: {r[2]}", reply_markup=InlineKeyboardMarkup(kb))

# ================= BELI =================
async def beli(q, pid):
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    if r[2] <= 0:
        await q.edit_message_text("❌ Stok habis", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="produk")]]))
        return

    c.execute("UPDATE products SET stock=stock-1 WHERE id=?", (pid,))
    c.execute("INSERT INTO orders (user_id, product_id, qty, total) VALUES (?, ?, ?, ?)", (q.from_user.id, pid, 1, r[3]))
    conn.commit()

    await q.edit_message_text("✅ Berhasil", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="produk")]]))

# ================= HISTORY =================
async def history(q):
    rows = c.execute("SELECT * FROM orders WHERE user_id=?", (q.from_user.id,)).fetchall()

    text = "History:\n" if rows else "Belum ada"
    for r in rows:
        text += f"\n#{r[0]} qty:{r[3]} total:{r[4]}"

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back_menu")]]))

# ================= ADMIN =================
async def admin_panel(q):
    if q.from_user.id != ADMIN_ID:
        return
    await q.edit_message_text("ADMIN PANEL", reply_markup=admin_menu())

# ================= TRANSAKSI =================
async def transaksi(q):
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    h = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{today}%",)).fetchone()[0] or 0
    b = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{month}%",)).fetchone()[0] or 0

    th = c.execute("SELECT COUNT(*) FROM orders WHERE date LIKE ?", (f"{today}%",)).fetchone()[0]
    tb = c.execute("SELECT COUNT(*) FROM orders WHERE date LIKE ?", (f"{month}%",)).fetchone()[0]

    await q.edit_message_text(
        f"Harian: {h}\nBulanan: {b}\n\nTransaksi Hari: {th}\nTransaksi Bulan: {tb}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="admin")]])
    )

# ================= ITEM ADMIN =================
async def admin_item(q):
    kb = [
        [InlineKeyboardButton("➕ Tambah", callback_data="dummy")],
        [InlineKeyboardButton("➕ Stok", callback_data="dummy")],
        [InlineKeyboardButton("➖ Stok", callback_data="dummy")],
        [InlineKeyboardButton("✏️ Edit", callback_data="dummy")],
        [InlineKeyboardButton("🗑️ Hapus", callback_data="dummy")],
        [InlineKeyboardButton("🔙", callback_data="admin")]
    ]
    await q.edit_message_text("Menu Item", reply_markup=InlineKeyboardMarkup(kb))

# ================= CALLBACK =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()

    if data == "produk":
        await produk(q)
    elif data.startswith("item_"):
        await item(q, int(data.split("_")[1]))
    elif data.startswith("buy_"):
        await beli(q, int(data.split("_")[1]))
    elif data == "history":
        await history(q)
    elif data == "panduan":
        await q.edit_message_text("Cara order", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back_menu")]]))
    elif data == "garansi":
        await q.edit_message_text("Hubungi admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back_menu")]]))
    elif data == "back_menu":
        await q.edit_message_text("Menu Utama", reply_markup=menu())

    # ADMIN FIX
    elif data == "admin":
        await admin_panel(q)
    elif data == "admin_transaksi":
        await transaksi(q)
    elif data == "admin_item":
        await admin_item(q)

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))  # masuk admin via command
app.add_handler(CallbackQueryHandler(button))

print("RUNNING...")
app.run_polling()
