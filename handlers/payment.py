# handlers/payment.py – DEVILS WILL RISE EDITION 🔥
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys
import os
import logging
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database as db
from utils.qr import make_upi_qr
from config import ADMIN_IDS, UPI_ID, GMAIL_AVAILABLE

router = Router()
logger = logging.getLogger(__name__)

# ── STATES ──────────────────────────────────────────────────────────
class PaymentState(StatesGroup):
    waiting_for_screenshot = State()


# ═══════════════════════════════════════════════════════════════════
# 🔥 1. CONFIRM PAY – QR GENERATE KARO
# ═══════════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_pay(cq: CallbackQuery, bot: Bot):
    """
    Jab user "Pay via UPI" click kare
    """
    logger.info(f"🔥 confirm_pay called: {cq.data}")
    
    # ── ACCOUNT ID NIKAL ──────────────────────────────────────────
    try:
        account_id = cq.data.split(":", 1)[1]
    except Exception as e:
        logger.error(f"Error parsing account_id: {e}")
        return await cq.answer("❌ Invalid account!", show_alert=True)
    
    if not account_id:
        return await cq.answer("❌ Invalid account!", show_alert=True)
    
    # ── ACCOUNT CHECK ─────────────────────────────────────────────
    acc = await db.get_account(account_id)
    
    if not acc:
        return await cq.answer("❌ Account not found!", show_alert=True)
    
    if acc["status"] != "available":
        return await cq.answer("❌ Account already sold!", show_alert=True)
    
    # ── ORDER CREATE ──────────────────────────────────────────────
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
        logger.error(f"Order creation error: {e}")
        return await cq.answer(f"❌ Order error: {str(e)[:40]}", show_alert=True)
    
    # ── QR GENERATE ────────────────────────────────────────────────
    try:
        qr_bytes, exact_amount, upi_id = await make_upi_qr(acc["price"], order_id[:6])
        await db.set_order_exact_amount(order_id, exact_amount)
        logger.info(f"✅ QR generated: ₹{exact_amount}")
    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return await cq.answer(f"❌ QR error: {str(e)[:40]}", show_alert=True)
    
    # ── CAPTION ────────────────────────────────────────────────────
    caption = (
        f"💳 <b>Complete Your Payment</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌍 {acc.get('country_flag', '🏳️')} {acc.get('country', 'Unknown')}\n"
        f"📱 <code>{acc['number']}</code>\n"
        f"💰 Pay <b>₹{exact_amount:.2f}</b>\n"
        f"🏦 UPI ID: <code>{UPI_ID}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏳ 15 min mein pay karo!\n"
        f"🔄 Auto-check available"
    )
    
    qr_file = BufferedInputFile(qr_bytes, filename="qr.png")
    
    # ── KEYBOARD ────────────────────────────────────────────────────
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚡ Auto-Check Payment",
            callback_data=f"auto_check:{order_id}"
        )],
        [InlineKeyboardButton(
            text="📸 Upload Screenshot",
            callback_data=f"upload_ss:{order_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Cancel Order",
            callback_data=f"cancel_order:{order_id}"
        )]
    ])
    
    # ── SEND QR ────────────────────────────────────────────────────
    try:
        await cq.message.answer_photo(
            photo=qr_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb
        )
        logger.info("✅ QR message sent")
    except Exception as e:
        logger.error(f"Send error: {e}")
        return await cq.answer(f"❌ Send error: {str(e)[:40]}", show_alert=True)
    
    # ── ADMIN NOTIFY ──────────────────────────────────────────────
    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"🛎 <b>New Order!</b>\n\n"
                f"👤 @{user.username or 'N/A'} (<code>{user.id}</code>)\n"
                f"📱 <code>{acc['number']}</code>\n"
                f"💸 ₹{exact_amount:.2f}",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Admin notify error: {e}")
    
    await cq.answer("✅ QR ready! Pay karo.")
    logger.info("✅ confirm_pay completed")


# ═══════════════════════════════════════════════════════════════════
# 🔥 2. AUTO-CHECK PAYMENT – GMAIL SCAN
# ═══════════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("auto_check:"))
async def auto_check(cq: CallbackQuery, bot: Bot):
    """
    Auto-Check button – Gmail scan karega
    """
    order_id = cq.data.split(":", 1)[1]
    logger.info(f"🔥 auto_check called: {order_id}")
    
    # ── ORDER CHECK ────────────────────────────────────────────────
    order = await db.get_order(order_id)
    
    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer(
            "✅ Already processed!" if order["status"] == "approved" else "❌ Cancelled.",
            show_alert=True
        )
    
    await cq.answer("⏳ Checking... 30 sec wait", show_alert=False)
    
    # ── UPDATE CAPTION ─────────────────────────────────────────────
    try:
        await cq.message.edit_caption(
            caption=(
                f"🔄 <b>Checking Payment...</b>\n\n"
                f"💸 ₹{order.get('exact_amount', order['amount']):.2f}\n\n"
                f"📧 Scanning Gmail inbox...\n"
                f"⏳ Please wait 30 seconds"
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Caption update error: {e}")
    
    # ── CHECK GMAIL ────────────────────────────────────────────────
    from utils.payment_checker import verify_payment
    exact = order.get("exact_amount") or order["amount"]
    
    try:
        logger.info(f"🔍 Checking payment: ₹{exact}")
        result = await verify_payment(float(exact), timeout_minutes=15)
        logger.info(f"✅ Result: {result}")
    except Exception as e:
        logger.error(f"Payment check error: {e}")
        result = {"verified": False, "message": str(e)}
    
    # ════════════════════════════════════════════════════════════════
    # ✅ IF PAYMENT VERIFIED
    # ════════════════════════════════════════════════════════════════
    if result.get("verified"):
        acc = await db.get_account(order["account_id"])
        
        if not acc:
            return await cq.answer("❌ Account not found!", show_alert=True)
        
        # ── APPROVE ORDER ──────────────────────────────────────────
        await db.approve_order(order_id)
        await db.mark_account_sold(order["account_id"], order["user_id"])
        await db.update_user_stats(order["user_id"], order["amount"])
        
        utr = result.get("utr", "N/A")
        amt = result.get("amount", order["amount"])
        
        # ── SEND ACCOUNT DETAILS ──────────────────────────────────
        from handlers.user import send_account_details
        await send_account_details(order["user_id"], acc, bot, order_id)
        
        # ── UPDATE MESSAGE ─────────────────────────────────────────
        try:
            await cq.message.edit_caption(
                caption=(
                    f"✅ <b>Payment Verified!</b>\n\n"
                    f"💸 ₹{amt:.2f} received\n"
                    f"🔖 UTR: <code>{utr}</code>\n\n"
                    f"📬 Account details sent in DM!"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Final caption error: {e}")
        
        # ── ADMIN NOTIFY ───────────────────────────────────────────
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    f"✅ <b>Auto-Payment Verified!</b>\n\n"
                    f"👤 @{order['username'] or 'N/A'}\n"
                    f"📱 <code>{acc['number']}</code>\n"
                    f"💸 ₹{amt:.2f} · UTR: <code>{utr}</code>",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Admin notify error: {e}")
        
        await cq.answer("✅ Payment verified! Account sent.")
    
    # ════════════════════════════════════════════════════════════════
    # ❌ IF PAYMENT NOT FOUND
    # ════════════════════════════════════════════════════════════════
    else:
        msg_text = result.get("message", "Payment nahi mila")
        
        try:
            await cq.message.edit_caption(
                caption=(
                    f"❌ <b>Payment Not Found</b>\n\n"
                    f"💸 ₹{exact:.2f} abhi nahi mila\n\n"
                    f"ℹ️ {msg_text}\n\n"
                    f"• Pay kiya? 2-3 min baad dobara check karo\n"
                    f"• Ya screenshot upload karo"
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="🔄 Check Again",
                        callback_data=f"auto_check:{order_id}"
                    )],
                    [InlineKeyboardButton(
                        text="📸 Upload Screenshot",
                        callback_data=f"upload_ss:{order_id}"
                    )]
                ])
            )
        except Exception as e:
            logger.error(f"Error caption update: {e}")
        
        await cq.answer("❌ Payment not found", show_alert=True)


# ═══════════════════════════════════════════════════════════════════
# 🔥 3. UPLOAD SCREENSHOT
# ═══════════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("upload_ss:"))
async def upload_ss(cq: CallbackQuery, state: FSMContext):
    """
    Upload screenshot button
    """
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)
    
    await state.set_state(PaymentState.waiting_for_screenshot)
    await state.update_data(order_id=order_id)
    
    await cq.message.answer(
        "📸 <b>Send Payment Screenshot</b>\n\n"
        "Gallery se photo select karo (file nahi)",
        parse_mode="HTML"
    )
    await cq.answer()


@router.message(PaymentState.waiting_for_screenshot, F.photo)
async def recv_ss(msg: Message, state: FSMContext):
    """
    Receive screenshot photo
    """
    data = await state.get_data()
    order_id = data.get("order_id")
    await state.clear()
    
    if not order_id:
        return await msg.answer("❌ Session expired. Dobara try karo.")
    
    file_id = msg.photo[-1].file_id
    await db.set_order_screenshot(order_id, file_id)
    
    await msg.answer(
        f"✅ <b>Screenshot Received!</b>\n\n"
        f"Click below to notify admin 👇",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📢 Notify Admin",
                callback_data=f"paid_notify:{order_id}"
            )]
        ])
    )


@router.message(PaymentState.waiting_for_screenshot, ~F.photo)
async def ss_wrong(msg: Message):
    """
    Wrong input (not photo)
    """
    await msg.answer("❌ Sirf photo bhejo! File ya text nahi.")


# ═══════════════════════════════════════════════════════════════════
# 🔥 4. PAID NOTIFY – ADMIN KO BHEJO
# ═══════════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("paid_notify:"))
async def paid_notify(cq: CallbackQuery, bot: Bot):
    """
    Notify admin that user paid (screenshot uploaded)
    """
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)
    
    if not order.get("screenshot"):
        return await cq.answer("❌ Pehle screenshot upload karo!", show_alert=True)
    
    acc = await db.get_account(order["account_id"])
    
    # ── UPDATE CAPTION ─────────────────────────────────────────────
    try:
        await cq.message.edit_caption(
            caption="⏳ <b>Admin ko notify kar diya!</b>\n5-10 min mein approve hoga.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Caption update error: {e}")
    
    # ── SEND TO ALL ADMINS ─────────────────────────────────────────
    for aid in ADMIN_IDS:
        try:
            await bot.send_photo(
                aid,
                order["screenshot"],
                caption=(
                    f"🔔 <b>PAYMENT CLAIMED!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 @{order['username'] or 'N/A'} · <code>{order['user_id']}</code>\n"
                    f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
                    f"💸 ₹{order['amount']:.2f}"
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="✅ Approve",
                        callback_data=f"admin_approve:{order_id}"
                    )],
                    [InlineKeyboardButton(
                        text="❌ Reject",
                        callback_data=f"admin_reject:{order_id}"
                    )]
                ])
            )
        except Exception as e:
            logger.error(f"Admin send error: {e}")
            try:
                await bot.send_message(
                    aid,
                    f"🔔 <b>PAYMENT!</b>\n<code>{order['user_id']}</code>\n₹{order['amount']:.2f}",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text="✅ Approve",
                            callback_data=f"admin_approve:{order_id}"
                        )],
                        [InlineKeyboardButton(
                            text="❌ Reject",
                            callback_data=f"admin_reject:{order_id}"
                        )]
                    ])
                )
            except Exception as e2:
                logger.error(f"Admin text send error: {e2}")
    
    await cq.answer("✅ Admin notify kiya!")


# ═══════════════════════════════════════════════════════════════════
# 🔥 5. CANCEL ORDER
# ═══════════════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(cq: CallbackQuery):
    """
    Cancel pending order
    """
    order_id = cq.data.split(":", 1)[1]
    order = await db.get_order(order_id)
    
    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    
    if order["status"] != "pending":
        return await cq.answer("⚠️ Cannot cancel.", show_alert=True)
    
    await db.reject_order(order_id)
    
    try:
        await cq.message.edit_caption(
            caption="❌ <b>Order Cancelled.</b>",
            parse_mode="HTML"
        )
    except Exception:
        await cq.message.answer("❌ Cancelled.")
    
    await cq.answer("✅ Cancelled!")
