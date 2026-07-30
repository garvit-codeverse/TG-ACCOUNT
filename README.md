# 🤖 EVILTALKS AccountBot

> Professional Telegram Account Seller Bot — MongoDB · Auto OTP · UPI Payment · Wallet System

---

## ✨ Features

| Feature | Details |
|---|---|
| 🌍 Country Filter | Browse by country, live stock count |
| 💳 UPI QR Payment | Unique paise per order for identification |
| 📸 Screenshot Upload | Payment proof before admin approval |
| ✅ Admin Approval | One-tap approve/reject |
| 🔐 Auto OTP | Telethon session se automatic OTP |
| 💰 Wallet System | Deposit → Buy directly from balance |
| 📢 Log Channel | Every sale logged (half number only) |
| 📣 Broadcast | Message all users at once |
| 🔧 Maintenance Mode | One-click ON/OFF with custom message |
| 🚫 Ban/Unban | Via commands — instant |
| 📊 Statistics | Revenue, stock, users dashboard |
| 🔒 Force Join | Users must join channel before using |
| 🗄️ MongoDB | Data persists across Railway restarts |

---

## ⚙️ Environment Variables

```env
BOT_TOKEN=YOUR_BOT_TOKEN
ADMIN_IDS=8066849679
ADMIN_USERNAME=@EVILTALKS
LOG_CHANNEL_ID=-1003773215198
LOG_CHANNEL_LINK=https://t.me/ACCOUNT_SELLER_PRO
SUPPORT_GROUP=@ACCSPRO_SUPPORT
UPI_ID=das20@fam
UPI_NAME=EVILTALKS Store
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
MONGO_URI=mongodb+srv://EVILTALKS:PASSWORD@cluster0.czrm1wk.mongodb.net/accountbot?appName=Cluster0
FORCE_JOIN_CHANNELS=-1003773215198:https://t.me/ACCOUNT_SELLER_PRO
```

---

## 🚀 Deploy on Railway

### Step 1 — Bot Token
@BotFather → `/newbot` → Token copy karo

### Step 2 — API ID & Hash (Auto OTP)
1. `my.telegram.org` → Login
2. **API Development Tools**
3. `api_id` aur `api_hash` copy karo

### Step 3 — MongoDB Atlas (Free)
1. `mongodb.com/atlas` → Free account banao
2. Free cluster banao
3. **Database Access** → User banao → Password note karo
4. **Network Access** → `0.0.0.0/0` allow karo
5. **Connect** → Connection string copy karo
6. String mein `accountbot` database naam add karo

### Step 4 — GitHub Push
```bash
git init
git add .
git commit -m "EVILTALKS AccountBot"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

### Step 5 — Railway Deploy
1. `railway.app` → New Project → GitHub repo select karo
2. **Variables** tab → Upar wale sab variables add karo
3. Auto deploy hoga ✅

---

## 📁 File Structure

```
evbot/
├── bot.py                  ← Main entry point
├── config.py               ← All config & env vars
├── database.py             ← MongoDB — all DB functions
├── keyboards.py            ← All keyboards
├── session_gen.py          ← Session string generator (run locally)
├── requirements.txt        ← Dependencies
├── Procfile                ← Railway worker
├── railway.toml            ← Railway config
├── .env.example            ← Environment template
├── handlers/
│   ├── user.py             ← User panel
│   ├── admin.py            ← Admin panel
│   ├── payment.py          ← UPI payment flow
│   ├── deposit.py          ← Wallet deposit flow
│   └── otp.py              ← Auto OTP
└── utils/
    ├── qr.py               ← UPI QR generator
    ├── logger.py           ← Log channel
    ├── otp_fetch.py        ← Telethon OTP fetch
    └── force_join.py       ← Force join checker
```

---

## 📱 Bot Flow

```
USER FLOW
──────────────────────────────────────
/start → Force Join Check
  └─ Browse Accounts → Country Select
      └─ Buy via UPI QR
          └─ Upload Screenshot → Notify Admin
              └─ [Admin Approves]
                  └─ Reveal Account → Get OTP ⚡

      OR

  └─ Deposit → UPI QR → Screenshot → Admin Approve
      └─ Wallet Balance Added
          └─ Buy via Wallet → Instant! ⚡

ADMIN FLOW
──────────────────────────────────────
➕ Add Account → Number → Country → Price → Password → 2FA → Session → Done
⏳ Pending Orders → Screenshot dekho → ✅ Approve / ❌ Reject
💳 Pending Deposits → Screenshot → ✅ Approve → Balance add
👥 User Management → Full list → /ban ID reason → /unban ID
🔧 Maintenance → ON/OFF in one tap
📢 Broadcast → Sab users ko message
```

---

## 🔐 Session String (Auto OTP)

Har account ke liye locally run karo:

```bash
pip install telethon
python session_gen.py
```

1. API ID & Hash daalo
2. Account number daalo
3. OTP enter karo
4. Session string copy karo
5. Bot mein **➕ Add Account** → Step 6 mein paste karo ✅

---

## 🛡️ Admin Commands

```
/ban USER_ID reason     ← User ban karo
/unban USER_ID          ← User unban karo
/msg USER_ID text       ← User ko message bhejo
```

---

## ⚠️ Important Notes

- Bot ko **Log Channel** mein Admin banao
- MongoDB Atlas → **Network Access** → `0.0.0.0/0` allow karo
- `session_gen.py` sirf **locally** chalao
- **BOT_TOKEN** kabhi share mat karo

---

Made with ❤️ by [@EVILTALKS](https://t.me/EVILTALKS)
