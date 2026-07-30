# handlers/browse.py – DEVILS WILL RISE EDITION 🔥
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db

router = Router()

# ── BROWSE COMMAND ──────────────────────────────────────────────────
@router.message(F.text == "/browse")
async def browse_cmd(msg: Message):
    accounts = await db.get_available_accounts()
    
    if not accounts:
        return await msg.answer("❌ No accounts available right now!")
    
    text = "📱 <b>Available Accounts</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    for acc in accounts[:10]:
        text += f"{acc['country_flag']} {acc['country']} – ₹{acc['price']}\n"
    
    text += f"\nTotal: {len(accounts)} accounts"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="👀 View All Accounts",
            callback_data="view_all"
        )]
    ])
    
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


# ── VIEW ALL ACCOUNTS ──────────────────────────────────────────────
@router.callback_query(F.data == "view_all")
async def view_all(cq: CallbackQuery):
    accounts = await db.get_available_accounts()
    
    if not accounts:
        return await cq.answer("❌ No accounts!", show_alert=True)
    
    # Show as buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for acc in accounts[:20]:  # Max 20 per page
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{acc['country_flag']} {acc['country']} – ₹{acc['price']}",
                callback_data=f"view_acc:{acc['_id']}"
            )
        ])
    
    kb.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Back", callback_data="browse_back")
    ])
    
    await cq.message.edit_text(
        f"📱 <b>Select Account</b>\n━━━━━━━━━━━━━━━━━━━━\nTotal: {len(accounts)} accounts",
        parse_mode="HTML",
        reply_markup=kb
    )
    await cq.answer()


# ── ACCOUNT DETAILS (VIEW ACCOUNT) ────────────────────────────────
@router.callback_query(F.data.startswith("view_acc:"))
async def view_account(cq: CallbackQuery):
    account_id = cq.data.split(":", 1)[1]
    acc = await db.get_account(account_id)
    
    if not acc:
        return await cq.answer("❌ Account not found!", show_alert=True)
    
    if acc["status"] != "available":
        return await cq.answer("❌ Already sold!", show_alert=True)
    
    text = (
        f"📱 <b>Account Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 {acc['country_flag']} {acc['country']}\n"
        f"📱 {acc['number']}\n"
        f"💰 Price: ₹{acc['price']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔥 Pay via UPI to unlock!"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 Pay via UPI - ₹{acc['price']}",
            callback_data=f"confirm_pay:{account_id}"  # ← YAHAN CALLBACK
        )],
        [InlineKeyboardButton(
            text="🔙 Back to Accounts",
            callback_data="view_all"
        )]
    ])
    
    await cq.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cq.answer()


# ── BACK ────────────────────────────────────────────────────────────
@router.callback_query(F.data == "browse_back")
async def browse_back(cq: CallbackQuery):
    await browse_cmd(cq.message)
    await cq.answer()
