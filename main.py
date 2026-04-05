from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, ADMIN_ID
import database as db

db.init_db()

# ================= MENU =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📦 PRODUK", callback_data="produk")],
        [InlineKeyboardButton("📜 HISTORY ORDER", callback_data="history")],
        [InlineKeyboardButton("📖 PANDUAN ORDER", callback_data="panduan")],
        [InlineKeyboardButton("🛡️ CLAIM GARANSI", callback_data="garansi")]
    ]
    await update.message.reply_text("Selamat datang di Bot Jualan!", reply_markup=InlineKeyboardMarkup(keyboard))


# ================= PRODUK =================
async def produk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    products = db.get_products()

    keyboard = []
    for p in products:
        keyboard.append([InlineKeyboardButton(f"{p[1]} | Stok: {p[2]}", callback_data=f"item_{p[0]}")])

    await query.edit_message_text("📦 Daftar Produk:", reply_markup=InlineKeyboardMarkup(keyboard))


# ================= DETAIL ITEM =================
async def item_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    pid = int(query.data.split("_")[1])
    product = db.get_product(pid)

    text = f"""
📦 {product[1]}
💰 Harga: {product[3]}
📦 Stok: {product[2]}
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
    product = db.get_product(pid)

    if product[2] <= 0:
        await query.edit_message_text("❌ Stok habis")
        return

    db.update_stock(pid, 1)
    db.add_order(query.from_user.id, pid, 1, product[3])

    await query.edit_message_text("✅ Berhasil beli 1 item!")


# ================= HISTORY =================
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    orders = db.get_user_orders(query.from_user.id)

    if not orders:
        await query.edit_message_text("Belum ada transaksi.")
        return

    text = "📜 History:\n"
    for o in orders:
        text += f"Order #{o[0]} | Qty: {o[3]} | Total: {o[4]}\n"

    await query.edit_message_text(text)


# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Tambah Item", callback_data="add_item")],
    ]
    await update.message.reply_text("Admin Panel", reply_markup=InlineKeyboardMarkup(keyboard))


# ================= HANDLER =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "produk":
        await produk(update, context)
    elif data.startswith("item_"):
        await item_detail(update, context)
    elif data.startswith("buy_"):
        await buy(update, context)
    elif data == "history":
        await history(update, context)
    elif data == "panduan":
        await update.callback_query.edit_message_text("Cara order:\n1. Pilih produk\n2. Klik beli")
    elif data == "garansi":
        await update.callback_query.edit_message_text("Hubungi admin untuk claim garansi.")


# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()