from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import os
from datetime import datetime

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
    total INTEGER,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 PRODUK", callback_data="produk")],
        [InlineKeyboardButton("📜 HISTORY ORDER", callback_data="history")],
        [InlineKeyboardButton("📖 PANDUAN ORDER", callback_data="panduan")],
        [InlineKeyboardButton("🛡️ CLAIM GARANSI", callback_data="garansi")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Menu Utama", reply_markup=main_menu())

# ================= PRODUK =================
async def produk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rows = c.execute("SELECT * FROM products").fetchall()

    keyboard = [[InlineKeyboardButton(f"{r[1]} | Stok: {r[2]}", callback_data=f"item_{r[0]}")] for r in rows]
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")])

    await q.edit_message_text("📦 Daftar Produk", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= DETAIL =================
async def item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    pid = int(q.data.split("_")[1])
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    keyboard = [
        [InlineKeyboardButton("BELI", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]
    ]

    await q.edit_message_text(
        f"📦 {r[1]}\n💰 {r[3]}\n📦 Stok: {r[2]}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= BELI =================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    pid = int(q.data.split("_")[1])
    r = c.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()

    if r[2] <= 0:
        await q.edit_message_text("❌ Stok habis", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]
        ]))
        return

    c.execute("UPDATE products SET stock = stock - 1 WHERE id=?", (pid,))
    c.execute("INSERT INTO orders (user_id, product_id, qty, total) VALUES (?, ?, ?, ?)",
              (q.from_user.id, pid, 1, r[3]))
    conn.commit()

    await q.edit_message_text("✅ Berhasil beli", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data="produk")]
    ]))

# ================= HISTORY =================
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    rows = c.execute("SELECT * FROM orders WHERE user_id=?", (q.from_user.id,)).fetchall()

    text = "📜 History:\n" if rows else "Belum ada order"
    for r in rows:
        text += f"\nOrder {r[0]} | Qty {r[3]} | Rp{r[4]}"

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_menu")]
    ]))

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("💰 TRANSAKSI", callback_data="admin_transaksi")],
        [InlineKeyboardButton("📦 ITEM", callback_data="admin_item")]
    ]

    await update.message.reply_text("👨‍💼 ADMIN PANEL", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= ADMIN TRANSAKSI =================
async def admin_transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    harian = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{today}%",)).fetchone()[0] or 0
    bulanan = c.execute("SELECT SUM(total) FROM orders WHERE date LIKE ?", (f"{month}%",)).fetchone()[0] or 0

    total_harian = c.execute("SELECT COUNT(*) FROM orders WHERE date LIKE ?", (f"{today}%",)).fetchone()[0]
    total_bulanan = c.execute("SELECT COUNT(*) FROM orders WHERE date LIKE ?", (f"{month}%",)).fetchone()[0]

    text = f"""
💰 TRANSAKSI

📅 Harian: Rp{harian}
📆 Bulanan: Rp{bulanan}

🧾 Total Harian: {total_harian}
🧾 Total Bulanan: {total_bulanan}
"""

    await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin")]
    ]))

# ================= ADMIN ITEM =================
async def admin_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("➕ Tambah Item", callback_data="add_item")],
        [InlineKeyboardButton("➕ Tambah Stok", callback_data="add_stock")],
        [InlineKeyboardButton("➖ Kurangi Stok", callback_data="min_stock")],
        [InlineKeyboardButton("✏️ Edit Stok", callback_data="set_stock")],
        [InlineKeyboardButton("🗑️ Hapus Item", callback_data="del_item")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="admin")]
    ]

    await q.edit_message_text("📦 MENU ITEM", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= BACK =================
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
        await update.callback_query.edit_message_text("Cara order", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back_menu")]]))
    elif data == "garansi":
        await update.callback_query.edit_message_text("Hubungi admin", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back_menu")]]))
    elif data == "back_menu":
        await update.callback_query.edit_message_text("Menu Utama", reply_markup=main_menu())

    # ADMIN
    elif data == "admin":
        await admin(update, context)
    elif data == "admin_transaksi":
        await admin_transaksi(update, context)
    elif data == "admin_item":
        await admin_item(update, context)

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(button))

print("BOT RUNNING...")
app.run_polling()
