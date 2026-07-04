from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from db import add_user, get_user, user_exists, update_username
from solana_utils import (
    create_wallet,
    get_balance,
    transfer_sol_to_user,
    request_airdrop,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user_exists(user.id):
        pubkey, _ = get_user(user.id)
        await update.message.reply_text(
            f"Welcome back! Your wallet: `{pubkey}`\n\n"
            f"Commands:\n"
            f"/balance - Check your SOL balance\n"
            f"/tip @user <amount> - Send SOL to another user\n"
            f"/deposit - Show your deposit address\n"
            f"/wallet - Show your wallet info",
            parse_mode="Markdown",
        )
        return

    wallet = create_wallet()
    add_user(user.id, str(wallet.pubkey()), str(wallet), user.username)
    update_username(user.id, user.username)

    airdrop_msg = ""
    try:
        sig = await request_airdrop(str(wallet.pubkey()), 2.0)
        airdrop_msg = f"\nAirdrop requested: `{sig[:8]}...`"
    except Exception:
        pass

    await update.message.reply_text(
        f"Welcome! Your Solana wallet has been created.\n\n"
        f"Address: `{wallet.pubkey()}`\n\n"
        f"Get free devnet SOL at https://faucet.solana.com{airdrop_msg}\n\n"
        f"Commands:\n"
        f"/balance - Check your SOL balance\n"
        f"/tip @user <amount> - Send SOL to another user\n"
        f"/deposit - Show your deposit address",
        parse_mode="Markdown",
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user_exists(user.id):
        await update.message.reply_text("You don't have a wallet yet. Use /start to create one.")
        return

    pubkey, _ = get_user(user.id)
    bal = await get_balance(pubkey)
    await update.message.reply_text(
        f"Your balance: `{bal:.4f} SOL`\nAddress: `{pubkey}`",
        parse_mode="Markdown",
    )


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user_exists(user.id):
        await update.message.reply_text("You don't have a wallet yet. Use /start to create one.")
        return

    pubkey, _ = get_user(user.id)
    await update.message.reply_text(
        f"Send SOL to this address:\n\n`{pubkey}`\n\n"
        f"Only send on **Solana Devnet**!",
        parse_mode="Markdown",
    )


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user_exists(user.id):
        await update.message.reply_text("You don't have a wallet yet. Use /start to create one.")
        return

    pubkey, privkey = get_user(user.id)
    await update.message.reply_text(
        f"**Your Wallet**\n\n"
        f"Public Key: `{pubkey}`\n"
        f"Private Key: `{privkey}`\n\n"
        f"⚠️ Keep your private key secret!",
        parse_mode="Markdown",
    )


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender = update.effective_user
    if not user_exists(sender.id):
        await update.message.reply_text("You don't have a wallet yet. Use /start to create one.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /tip @username <amount>")
        return

    target_text = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Invalid amount. Usage: /tip @username <amount>")
        return

    if amount <= 0:
        await update.message.reply_text("Amount must be positive.")
        return

    if not update.message.reply_to_message and not update.message.entities:
        await update.message.reply_text("Please reply to a user's message or mention them with @username")
        return

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif update.message.entities:
        for entity in update.message.entities:
            if entity.type == "mention" and entity.user:
                target_user = entity.user
                break

    if not target_user:
        await update.message.reply_text("Could not identify the target user.")
        return

    if target_user.id == sender.id:
        await update.message.reply_text("You can't tip yourself!")
        return

    if not user_exists(target_user.id):
        await update.message.reply_text("That user doesn't have a wallet yet. They need to /start first.")
        return

    sender_pubkey, sender_privkey = get_user(sender.id)
    target_pubkey, _ = get_user(target_user.id)

    sender_bal = await get_balance(sender_pubkey)
    if sender_bal < amount:
        await update.message.reply_text(
            f"Insufficient balance. You have `{sender_bal:.4f} SOL` but tried to send `{amount} SOL`.",
            parse_mode="Markdown",
        )
        return

    try:
        tx_sig = await transfer_sol_to_user(sender_privkey, target_pubkey, amount)
        await update.message.reply_text(
            f"✅ Sent `{amount} SOL` to {target_user.mention_html()}!\n"
            f"Tx: `{tx_sig[:8]}...`",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(f"Transfer failed: {e}")


def run_bot(token: str):
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("tip", tip))

    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
