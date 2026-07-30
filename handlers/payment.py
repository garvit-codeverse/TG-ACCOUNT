# handlers/payment.py – DEVILS WILL RISE EDITION 🔥
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
from utils.qr import make_upi_qr
from config import ADMIN_IDS, UPI_ID
import logging

router = Router()
logger = logging.getLogger(__name__)

class PaymentState(StatesGroup):
    waiting_for_screenshot = State()

# ── CONFIRM PAY ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_pay(cq: CallbackQuery, bot: Bot):
    """HANDLE PAY VIA UPI BUTTON"""
    logger.info(f"🔥 confirm_pay called: {cq.data}")
    
    try:
        account_id = cq.data.split(":", 1)[1]
    except Exception as e:
        logger.error(f"Error parsing: {e}")
        return await cq.answer("❌ Invalid!", show_alert=True)
    
    if not account_id:
        return await cq.answer("❌ Invalid account!", show_alert=True)
    
    acc = await db.get_account(account_id)
    
    if not acc:
        return await cq.answer("❌ Account not found!", show_alert=True)
    
    if acc["status"] != "available":
        return await cq.answer("❌ Already sold!", show_alert=True)
    
    user = cq.from_user
    
    try:
        order_id = await db.create_order(
            user_id=user.id,
            username=user.username or "",
            full_name=user.full_name or "",
            account_id=account_id,
            amount=acc["price"]
        )
        logger.info(f"✅ Order created: {order_id}")
    except Exception as e:
        logger.error(f"Order error: {e}")
        return await cq.answer(f"❌ Error: {str(e)[:40]}", show_alert=True)
    
    try:
        qr_bytes, exact_amount, upi_id = await make_upi_qr(acc["price"], order_id[:6])
        await db.set_order_exact_amount(order_id, exact_amount)
    except Exception as e:
        logger.error(f"QR error: {e}")
        return await cq.answer(f"❌ QR error: {str(e)[:40]}", show_alert=True)
    
    caption = (
        f"💳 <b>Complete Payment</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 {acc.get('country_flag', '🏳️')} {acc.get('country', 'Unknown')}\n"
        f"📱 {acc['number']}\n"
        f"💰 <b>₹{exact_amount:.2f}</b>\n"
        f"🏦 UPI: <code>{UPI_ID}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ 15 min pay\n"
        f"🔄 Auto-check available"
    )
    
    qr_file = BufferedInputFile(qr_bytes, filename="qr.png")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Auto-Check", callback_data=f"auto_check:{order_id}")],
        [InlineKeyboardButton(text="📸 Upload Screenshot", callback_data=f"upload_ss:{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_order:{order_id}")]
    ])
    
    try:
        await cq.message.answer_photo(
            photo=qr_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb
        )
    except Exception as e:
        logger.error(f"Send error: {e}")
        return await cq.answer(f"❌ Send error: {str(e)[:40]}", show_alert=True)
    
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"🛎 <b>New Order!</b>\n👤 @{user.username or 'N/A'} ({user.id})\n📱 {acc['number']}\n💸 ₹{exact_amount:.2f}",
                parse_mode="HTML"
            )
        except:
            pass
    
    await cq.answer("✅ QR ready! Pay karo.")
    logger.info("✅ confirm_pay done")


# ── AUTO CHECK ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("auto_check:"))
async def auto_check(cq: CallbackQuery, bot: Bot):
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("Already processed!", show_alert=True)
    
    await cq.answer("⏳ Checking...", show_alert=False)
    
    exact = order.get("exact_amount") or order["amount"]
    
    from utils.payment_checker import verify_payment
    result = await verify_payment(float(exact), timeout_minutes=15)
    
    if result.get("verified"):
        acc = await db.get_account(order["account_id"])
        await db.approve_order(order_id)
        await db.mark_account_sold(order["account_id"], order["user_id"])
        await db.update_user_stats(order["user_id"], order["amount"])
        
        # SEND ACCOUNT DETAILS
        from handlers.user import send_account_details
        await send_account_details(order["user_id"], acc, bot, order_id)
        
        await cq.message.edit_caption(
            caption=f"✅ <b>Payment Verified!</b>\n💸 ₹{result.get('amount', order['amount']):.2f}\n🔖 UTR: {result.get('utr', 'N/A')}",
            parse_mode="HTML"
        )
    else:
        await cq.message.edit_caption(
            caption=f"❌ <b>Payment Not Found</b>\n💸 ₹{exact:.2f}\n\n{result.get('message', 'Try again')}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Retry", callback_data=f"auto_check:{order_id}")],
                [InlineKeyboardButton(text="📸 Upload Screenshot", callback_data=f"upload_ss:{order_id}")]
            ])
        )


# ── UPLOAD SCREENSHOT ──────────────────────────────────────────────
@router.callback_query(F.data.startswith("upload_ss:"))
async def upload_ss(cq: CallbackQuery, state: FSMContext):
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order or order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not yours!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("Already processed!", show_alert=True)
    
    await state.set_state(PaymentState.waiting_for_screenshot)
    await state.update_data(order_id=order_id)
    await cq.message.answer("📸 Send payment screenshot (photo only)")
    await cq.answer()


@router.message(PaymentState.waiting_for_screenshot, F.photo)
async def recv_ss(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("order_id")
    await state.clear()
    
    if not order_id:
        return await msg.answer("❌ Session expired. Try again.")
    
    file_id = msg.photo[-1].file_id
    await db.set_order_screenshot(order_id, file_id)
    
    await msg.answer(
        f"✅ Screenshot received! Notify admin 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Notify Admin", callback_data=f"paid_notify:{order_id}")]
        ])
    )


@router.message(PaymentState.waiting_for_screenshot, ~F.photo)
async def ss_wrong(msg: Message):
    await msg.answer("❌ Only photo!")


# ── PAID NOTIFY ──────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("paid_notify:"))
async def paid_notify(cq: CallbackQuery, bot: Bot):
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order or order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not yours!", show_alert=True)
    
    if not order.get("screenshot"):
        return await cq.answer("❌ Upload screenshot first!", show_alert=True)
    
    acc = await db.get_account(order["account_id"])
    
    for aid in ADMIN_IDS:
        try:
            await bot.send_photo(
                aid,
                order["screenshot"],
                caption=f"🔔 <b>Payment Claimed!</b>\n👤 @{order['username'] or 'N/A'}\n💸 ₹{order['amount']:.2f}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Approve", callback_data=f"admin_approve:{order_id}")],
                    [InlineKeyboardButton(text="❌ Reject", callback_data=f"admin_reject:{order_id}")]
                ])
            )
        except:
            pass
    
    await cq.answer("✅ Admin notified!")


# ── CANCEL ──────────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(cq: CallbackQuery):
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order or order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not yours!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("Cannot cancel!", show_alert=True)
    
    await db.reject_order(order_id)
    await cq.message.edit_caption(caption="❌ Order cancelled.")
    await cq.answer("✅ Cancelled!")
