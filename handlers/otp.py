from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS, DATABASE_URL
from keyboards import otp_kb, admin_otp_kb

router = Router()


class ManualOTPState(StatesGroup):
    waiting = State()


# ── Reveal Account Details ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("reveal:"))
async def reveal_account(cq: CallbackQuery):
    order_id = cq.data.split(":", 1)[1]

    try:
        order = await db.get_order(order_id)
    except Exception:
        return await cq.answer("❌ Order not found!", show_alert=True)

    if not order:
        return await cq.answer("❌ Order not found!", show_alert=True)
    if order["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your order!", show_alert=True)
    if order["status"] != "approved":
        return await cq.answer("⏳ Order approved nahi hua abhi!", show_alert=True)

    try:
        acc = await db.get_account(order["account_id"])
    except Exception:
        return await cq.answer("❌ Account not found!", show_alert=True)

    if not acc:
        return await cq.answer("❌ Account not found!", show_alert=True)

    # Find OTP session
    import aiosqlite
    session = None
    try:
        async with aiosqlite.connect(DATABASE_URL) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute(
                "SELECT * FROM otp_sessions WHERE order_id=? ORDER BY rowid DESC LIMIT 1",
                (order_id,)
            ) as c:
                r = await c.fetchone()
                if r:
                    session = dict(r)
    except Exception:
        pass

    text = (
        f"🎉 <b>Account Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Number:</b>   <code>{acc['number']}</code>\n"
        f"🔑 <b>Password:</b> <code>{acc['password'] or 'Not set'}</code>\n"
        f"🔐 <b>2FA:</b>      <code>{acc['twofa'] or 'Not set'}</code>\n"
        f"{acc['country_flag']} <b>Country:</b> {acc['country']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ ₹{order['amount']:.2f} paid\n\n"
        f"📲 Login karo phir OTP ke liye button dabao 👇"
    )

    kb = otp_kb(session["id"]) if session else None
    await cq.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await cq.answer()


# ── Get Latest OTP ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("get_otp:"))
async def get_otp(cq: CallbackQuery, bot: Bot):
    session_id = cq.data.split(":", 1)[1]

    try:
        session = await db.get_otp_session(session_id)
    except Exception:
        return await cq.answer("❌ Session not found!", show_alert=True)

    if not session:
        return await cq.answer("❌ OTP session not found!", show_alert=True)
    if session["user_id"] != cq.from_user.id:
        return await cq.answer("❌ Not your OTP!", show_alert=True)

    try:
        acc = await db.get_account(session["account_id"])
    except Exception:
        acc = None

    # Already delivered
    if session["status"] == "delivered" and session["otp_code"]:
        await cq.answer(f"🔑 OTP: {session['otp_code']}", show_alert=True)
        await bot.send_message(
            cq.from_user.id,
            f"🔐 <b>Your OTP</b>\n\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"🔑 <b><code>{session['otp_code']}</code></b>\n\n"
            f"⚡ Jaldi use karo!",
            parse_mode="HTML"
        )
        return

    # No session string — notify admin manually
    if not acc or not acc.get("session_str"):
        await cq.answer(
            "⏳ Admin ko notify kar diya!\n5 min mein OTP milega.",
            show_alert=True
        )
        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    f"⚠️ <b>Manual OTP Needed!</b>\n\n"
                    f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
                    f"👤 User: <code>{cq.from_user.id}</code>\n"
                    f"Session string missing — manually bhejo!",
                    parse_mode="HTML",
                    reply_markup=admin_otp_kb(session_id)
                )
            except Exception:
                pass
        return

    # Auto fetch via Telethon
    await cq.answer("⏳ OTP fetch ho raha hai... (90 sec)", show_alert=True)

    status_msg = await bot.send_message(
        cq.from_user.id,
        f"🔄 <b>OTP Auto-Fetching...</b>\n\n"
        f"📱 <code>{acc['number']}</code>\n\n"
        f"Abhi account mein login karo taaki OTP trigger ho!\n"
        f"Bot check karega... ⚡",
        parse_mode="HTML"
    )

    try:
        from utils.otp_fetch import auto_fetch_otp
        otp_code = await auto_fetch_otp(acc["session_str"], timeout=90)
    except Exception:
        otp_code = None

    if otp_code:
        await db.deliver_otp(session_id, otp_code)
        try:
            await bot.edit_message_text(
                f"✅ <b>OTP Delivered!</b>\n\n"
                f"📱 <code>{acc['number']}</code>\n"
                f"🔑 <b><code>{otp_code}</code></b>\n\n"
                f"⚡ 2 min mein expire hoga — jaldi use karo!",
                chat_id=cq.from_user.id,
                message_id=status_msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            await bot.send_message(
                cq.from_user.id,
                f"🔑 OTP: <b><code>{otp_code}</code></b>",
                parse_mode="HTML"
            )
        try:
            from utils.logger import log_otp
            await log_otp(bot, acc["number"], otp_code, cq.from_user.id, cq.from_user.username or "")
        except Exception:
            pass
    else:
        try:
            await bot.edit_message_text(
                f"⚠️ <b>Auto OTP Failed</b>\n\n"
                f"Admin ko manually bhejne ke liye request kar diya!\n\n"
                f"Ya:\n"
                f"• Pehle number se login karo\n"
                f"• Phir dubara button dabao",
                chat_id=cq.from_user.id,
                message_id=status_msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

        for aid in ADMIN_IDS:
            try:
                await bot.send_message(
                    aid,
                    f"⚠️ <b>Auto OTP Timeout!</b>\n\n"
                    f"📱 <code>{acc['number']}</code>\n"
                    f"👤 <code>{cq.from_user.id}</code>",
                    parse_mode="HTML",
                    reply_markup=admin_otp_kb(session_id)
                )
            except Exception:
                pass


# ── Manual OTP Send (Admin) ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("manual_otp:"))
async def manual_otp_start(cq: CallbackQuery, state: FSMContext):
    if cq.from_user.id not in ADMIN_IDS:
        return await cq.answer("❌ Not authorized!", show_alert=True)
    session_id = cq.data.split(":", 1)[1]
    await state.set_state(ManualOTPState.waiting)
    await state.update_data(session_id=session_id)
    await cq.message.answer(f"🔐 OTP enter karo user ke liye:")
    await cq.answer()


@router.message(ManualOTPState.waiting)
async def manual_otp_done(msg: Message, state: FSMContext, bot: Bot):
    if msg.from_user.id not in ADMIN_IDS:
        return
    otp_code   = msg.text.strip()
    data       = await state.get_data()
    session_id = data["session_id"]
    await state.clear()

    session = await db.get_otp_session(session_id)
    if not session:
        return await msg.answer("❌ Session not found!")

    await db.deliver_otp(session_id, otp_code)
    acc = await db.get_account(session["account_id"])

    try:
        await bot.send_message(
            session["user_id"],
            f"🔐 <b>Your OTP</b>\n\n"
            f"📱 <code>{acc['number'] if acc else 'N/A'}</code>\n"
            f"🔑 <b><code>{otp_code}</code></b>\n\n"
            f"⚡ Jaldi use karo!",
            parse_mode="HTML"
        )
    except Exception:
        pass

    try:
        from utils.logger import log_otp
        await log_otp(bot, acc["number"] if acc else "N/A", otp_code, session["user_id"], "")
    except Exception:
        pass

    await msg.answer(f"✅ OTP <code>{otp_code}</code> sent!", parse_mode="HTML")
