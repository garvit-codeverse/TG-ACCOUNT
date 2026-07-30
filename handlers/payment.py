from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from utils.qr import make_upi_qr
from keyboards import payment_kb, screenshot_done_kb, admin_approve_kb
from config import ADMIN_IDS

router = Router()


class ScreenshotState(StatesGroup):
    waiting = State()


@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_pay(cq: CallbackQuery, bot: Bot):
    account_id = cq.data.split(":", 1)[1]
    acc        = await db.get_account(account_id)

    if not acc or acc["status"] != "available":
        return await cq.answer("❌ Account no longer available!", show_alert=True)

    u        = cq.from_user
    order_id = await db.create_order(
        u.id, u.username or "", u.full_name or "", account_id, acc["price"]
    )

    qr_bytes, exact, upi_id = await make_upi_qr(acc["price"], order_id[:6])

    caption = (
        f"💳 <b>UPI Payment</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{acc['country_flag']} {acc['country']} Account\n"
        f"💰 Pay EXACTLY: <b>₹{exact:.2f}</b>\n"
        f"🏦 UPI ID: <code>{upi_id}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ Steps:\n"
        f"1️⃣ Exact amount pay karo\n"
        f"2️⃣ Screenshot lo\n"
        f"3️⃣ Upload button dabao\n"
        f"4️⃣ Notify Admin dabao\n\n"
        f"⏰ 15 min mein pay karo!"
    )

    qr_file = BufferedInputFile(qr_bytes, filename="pay.png")
    try:
        await cq.message.answer_photo(
            photo=qr_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=payment_kb(order_id)
        )
    except Exception as e:
        return await cq.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)

    try:
        await cq.message.delete()
    except Exception:
        pass

    for aid in ADMIN_IDS:
        try:
            await bot.send_message(
                aid,
                f"🛎 <b>New Order!</b>\n\n"
                f"👤 @{u.username or 'N/A'} (<code>{u.id}</code>)\n"
                f"{acc['country_flag']} {acc['country']} · <code>{acc['number']}</code>\n"
                f"💸 ₹{exact:.2f}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    await cq.answer("✅ QR generated!")


@router.callback_query(F.data.startswith("upload_ss:"))
async def upload_ss_prompt(cq: CallbackQuery, state: FSMContext):
    order_id = cq.data.split(":", 1)[1]
    order    = await db.get_order(order_id)

    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    if order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)

    await state.set_state(ScreenshotState.waiting)
    await state.update_data(order_id=order_id)
    await cq.message.answer(
        "📸 <b>Payment Screenshot Bhejo</b>\n\n"
        "• Gallery se photo select karo\n"
        "• Direct image send karo (file nahi)\n"
        "• Sirf ek photo bhejo",
        parse_mode="HTML"
    )
    await cq.answer()


@router.message(ScreenshotState.waiting, F.photo)
async def receive_ss(msg: Message, state: FSMContext, bot: Bot):
    data     = await state.get_data()
    order_id = data.get("order_id")
    await state.clear()

    if not order_id:
        return await msg.answer("❌ Session expire. Dobara try karo.")

    file_id = msg.photo[-1].file_id
    await db.set_order_screenshot(order_id, file_id)
    order   = await db.get_order(order_id)

    await msg.answer(
        f"✅ <b>Screenshot Received!</b>\n\n"
        f"💸 ₹{order['amount']:.2f}\n\n"
        f"Ab admin ko notify karo 👇",
        parse_mode="HTML",
        reply_markup=screenshot_done_kb(order_id)
    )


@router.message(ScreenshotState.waiting, F.document)
async def ss_doc(msg: Message):
    await msg.answer("❌ <b>File mat bhejo!</b>\nGallery se photo bhejo.", parse_mode="HTML")


@router.message(ScreenshotState.waiting, ~F.photo)
async def ss_wrong(msg: Message):
    await msg.answer("❌ Sirf photo bhejo!")


@router.callback_query(F.data.startswith("paid_notify:"))
async def paid_notify(cq: CallbackQuery, bot: Bot):
    order_id = cq.data.split(":", 1)[1]
    order    = await db.get_order(order_id)

    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    if order["status"] != "pending":
        return await cq.answer("⚠️ Already processed.", show_alert=True)
    if not order.get("screenshot"):
        return await cq.answer(
            "❌ Pehle screenshot upload karo!",
            show_alert=True
        )

    acc = await db.get_account(order["account_id"])
    try:
        await cq.message.edit_caption(
            caption=(
                "⏳ <b>Verification Pending</b>\n\n"
                "Admin review kar raha hai...\n"
                "5-10 min mein approve hoga! ✅"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

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
                    f"{acc['country_flag'] if acc else ''} {acc['country'] if acc else ''}\n"
                    f"💸 ₹{order['amount']:.2f}"
                ),
                parse_mode="HTML",
                reply_markup=admin_approve_kb(order_id)
            )
        except Exception:
            try:
                await bot.send_message(
                    aid,
                    f"🔔 <b>PAYMENT!</b>\n👤 <code>{order['user_id']}</code>\n💸 ₹{order['amount']:.2f}",
                    parse_mode="HTML",
                    reply_markup=admin_approve_kb(order_id)
                )
            except Exception:
                pass

    await cq.answer("✅ Admin ko notify kar diya!")


@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(cq: CallbackQuery):
    order_id = cq.data.split(":", 1)[1]
    order    = await db.get_order(order_id)

    if not order or order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    if order["status"] != "pending":
        return await cq.answer("⚠️ Cannot cancel.", show_alert=True)

    await db.reject_order(order_id)
    try:
        await cq.message.edit_caption(caption="❌ Order cancelled.", parse_mode="HTML")
    except Exception:
        await cq.message.answer("❌ Order cancelled.")
    await cq.answer("Cancelled.")
