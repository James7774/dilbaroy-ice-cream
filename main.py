#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖✨ NOVA.X - RAQAMLI YECHIMLAR BOTI ✨🤖
🎯 To'liq Admin Panel + CRM tizimi
"""

import logging
import json
import os
import re
import csv
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==================== WEB SERVER (RENDER KEEP-ALIVE) ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "NOVA.X Bot is alive!", 200

@web_app.route('/health')
def health():
    return "OK", 200

def run_web_server():
    # Render avtomatik PORT beradi, agar bo'lmasa 8080 ishlatiladi
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Web server {port}-portda ishga tushmoqda...")
    try:
        web_app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Web serverda xato: {e}")

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    logger.info("Keep-alive tizimi yoqildi.")

# ==================== KONFIGURATSIYA ====================
# Render Environment Variables-dan o'qiydi, agar bo'lmasa pastdagini ishlatadi
BOT_TOKEN = os.environ.get('BOT_TOKEN', "7753850166:AAHjbo_ziGmhfitrfkm6NjbWHbMtXyZah20")
ADMIN_PHONE = "+998997236222"
ADMIN_TELEGRAM = "@nnoovvaaxx"
ADMIN_IDS = [6616832324]  # O'z ID ingizni qo'ying

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('nova_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

print("=" * 70)
print("✨🤖 NOVA.X BOT ISHGA TUSHMOQDA... 🤖✨")
print("=" * 70)

# ==================== DATABASE ====================
class NovaDatabase:
    """Ma'lumotlar bazasi"""
    
    def __init__(self):
        self.data_file = "nova_x_database.json"
        self.backup_dir = "backups"
        self.load_data()
    
    def load_data(self):
        """Ma'lumotlarni yuklash"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = {
                    "applications": [],
                    "contacts": [],
                    "ratings": [],
                    "users": {},
                    "stats": {
                        "total_applications": 0,
                        "total_contacts": 0,
                        "total_ratings": 0,
                        "average_rating": 0,
                        "today_applications": 0,
                        "weekly_applications": 0,
                        "monthly_applications": 0
                    }
                }
                self.save_data()
        except Exception as e:
            logger.error(f"Ma'lumotlarni yuklashda xato: {e}")
            self.data = {
                "applications": [],
                "contacts": [],
                "ratings": [],
                "users": {},
                "stats": {
                    "total_applications": 0,
                    "total_contacts": 0,
                    "total_ratings": 0,
                    "average_rating": 0,
                    "today_applications": 0,
                    "weekly_applications": 0,
                    "monthly_applications": 0
                }
            }
    
    def save_data(self):
        """Ma'lumotlarni saqlash"""
        try:
            self.update_stats()
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Ma'lumotlarni saqlashda xato: {e}")
            return False
    
    def update_stats(self):
        """Statistikani yangilash"""
        today = datetime.now().strftime("%d.%m.%Y")
        
        # Bugungi arizalar
        today_apps = [app for app in self.data["applications"] if app["date"].startswith(today)]
        
        # Reytinglar
        ratings = self.data.get("ratings", [])
        total_ratings = len(ratings)
        avg_rating = 0
        if total_ratings > 0:
            avg_rating = sum(r["rating"] for r in ratings) / total_ratings
        
        self.data["stats"] = {
            "total_applications": len(self.data["applications"]),
            "total_contacts": len(self.data["contacts"]),
            "total_ratings": total_ratings,
            "average_rating": round(avg_rating, 1),
            "today_applications": len(today_apps),
            "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
    
    def add_application(self, user_id: int, name: str, phone: str, service: str, message: str = ""):
        """Yangi ariza qo'shish"""
        app_id = len(self.data["applications"]) + 1
        
        application = {
            "id": app_id,
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "service": service,
            "message": message,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "status": "yangi",
            "updated_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        
        self.data["applications"].append(application)
        self.save_data()
        return application
    
    def update_application_status(self, app_id: int, status: str):
        """Ariza holatini yangilash"""
        for app in self.data["applications"]:
            if app["id"] == app_id:
                app["status"] = status
                app["updated_at"] = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                self.save_data()
                return True
        return False
    
    def add_contact(self, user_id: int, name: str, phone: str, message: str = ""):
        """Yangi kontakt qo'shish"""
        contact_id = len(self.data["contacts"]) + 1
        
        contact = {
            "id": contact_id,
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "message": message,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "contacted": False
        }
        
        self.data["contacts"].append(contact)
        self.save_data()
        return contact
    
    def add_rating(self, user_id: int, rating: int, feedback: str = ""):
        """Yangi baho qo'shish"""
        rating_id = len(self.data["ratings"]) + 1
        
        rating_data = {
            "id": rating_id,
            "user_id": user_id,
            "rating": rating,
            "feedback": feedback,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        }
        
        self.data["ratings"].append(rating_data)
        self.save_data()
        return rating_data
    
    def get_all_applications(self):
        """Barcha arizalarni olish"""
        return self.data["applications"]
    
    def get_applications_by_status(self, status: str):
        """Holat bo'yicha arizalarni olish"""
        if status == "all":
            return self.data["applications"]
        return [app for app in self.data["applications"] if app.get("status") == status]
    
    def get_today_applications(self):
        """Bugungi arizalarni olish"""
        today = datetime.now().strftime("%d.%m.%Y")
        return [app for app in self.data["applications"] if app["date"].startswith(today)]
    
    def get_all_contacts(self):
        """Barcha kontaktlarni olish"""
        return self.data["contacts"]
    
    def get_all_ratings(self):
        """Barcha baholarni olish"""
        return self.data["ratings"]
    
    def get_stats(self):
        """Statistikani olish"""
        return self.data["stats"]

# Global database obyekti
db = NovaDatabase()

# ==================== MENYULAR ====================
def get_main_menu(is_admin: bool = False):
    """Asosiy menyu"""
    if is_admin:
        buttons = [
            ["📊 STATISTIKA", "📋 ARIZALAR"],
            ["📅 BUGUNGI", "📞 KONTAKTLAR"],
            ["⭐ BAHOLAR", "📤 EXPORT"],
            ["⚙️ SOZLAMALAR", "🏠 ASOSIY MENYU"]
        ]
    else:
        buttons = [
            # ["ℹ️ BIZ HAQIMIZDA", "🛠️ XIZMATLAR", "💰 NARXLAR"],
            # ["📝 ARIZA QOLDIRISH", "📱 TELEFON QOLDIRISH", "⭐ BAHO BERISH"],
            # ["📞 ALOQA", "❓ YORDAM"]

            ["ℹ️ BIZ HAQIMIZDA", "🛠️ XIZMATLAR"],
            ["💰 NARXLAR", "📝 ARIZA QOLDIRISH"],
            ["📱 TELEFON QOLDIRISH", "⭐ BAHO BERISH"],
            ["📞 ALOQA", "❓ YORDAM"]
            
           
        ]
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_admin_applications_menu():
    """Admin arizalar menyusi"""
    keyboard = [
        [InlineKeyboardButton("🆕 Yangi arizalar", callback_data="admin_apps_new")],
        [InlineKeyboardButton("⏳ Jarayonda", callback_data="admin_apps_progress")],
        [InlineKeyboardButton("✅ Bajarilgan", callback_data="admin_apps_completed")],
        [InlineKeyboardButton("❌ Bekor qilingan", callback_data="admin_apps_cancelled")],
        [InlineKeyboardButton("📊 Barchasi", callback_data="admin_apps_all")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_export_menu():
    """Admin export menyusi"""
    keyboard = [
        [InlineKeyboardButton("📋 Arizalar (CSV)", callback_data="export_apps_csv")],
        [InlineKeyboardButton("📞 Kontaktlar (CSV)", callback_data="export_contacts_csv")],
        [InlineKeyboardButton("⭐ Baholar (CSV)", callback_data="export_ratings_csv")],
        [InlineKeyboardButton("📊 Statistika (TXT)", callback_data="export_stats_txt")],
        [InlineKeyboardButton("📁 Hammasi (ZIP)", callback_data="export_all_zip")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_application_actions(app_id: int):
    """Ariza uchun amallar"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Bajarildi", callback_data=f"app_complete_{app_id}"),
            InlineKeyboardButton("⏳ Jarayonda", callback_data=f"app_progress_{app_id}")
        ],
        [
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"app_cancel_{app_id}"),
            InlineKeyboardButton("📞 Bog'lanish", callback_data=f"app_contact_{app_id}")
        ],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_apps_all")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_rating_keyboard():
    """Baho berish uchun inline keyboard"""
    keyboard = []
    for i in range(1, 6):
        stars = "⭐" * i
        keyboard.append([InlineKeyboardButton(f"{stars} ({i}/5)", callback_data=f"rate_{i}")])
    
    keyboard.append([InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_rate")])
    return InlineKeyboardMarkup(keyboard)

def get_service_keyboard():
    """Xizmatlar uchun inline keyboard"""
    buttons = [
        [InlineKeyboardButton("🌐 Veb-sayt yaratish", callback_data="service_website")],
        [InlineKeyboardButton("📱 Mobil ilova", callback_data="service_mobile")],
        [InlineKeyboardButton("🎨 UI/UX Dizayn", callback_data="service_design")],
        [InlineKeyboardButton("🔍 SEO Optimizatsiya", callback_data="service_seo")],
        [InlineKeyboardButton("☁️ Hosting va Server", callback_data="service_hosting")],
        [InlineKeyboardButton("⚡ Boshqa xizmat", callback_data="service_other")]
    ]
    return InlineKeyboardMarkup(buttons)

# ==================== USER FUNCTIONS ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user = update.effective_user
    user_id = user.id
    
    welcome_message = f"""
✨✨✨✨✨✨✨✨✨✨✨✨✨✨✨
🤖 *NOVA.X GA XUSH KELIBSIZ, {user.first_name}!* 🎉

🚀 *Raqamli Transformatsiya* sarguzashtingiz boshlanishi!

👇 *Quyidagi menyudan kerakli bo'limni tanlang:*
    """
    
    # Admin tekshiruvi
    is_admin = user_id in ADMIN_IDS
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu(is_admin)
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Biz haqimizda"""
    about_text = f"""
🏢✨ *NOVA.X - RAQAMLI YECHIMLAR JAMOASI* ✨🏢

🌟 *BIZ KIMMIZ?*
NOVA.X - bu zamonaviy texnologiyalar va kreativ yondashuvlar orqali biznes va shaxsiy brendlarni raqamli dunyoga olib chiqishga ixtisoslashgan yuqori malakali mutaxassislar jamoasi.

📞 *ALOQA:*
Telefon: {ADMIN_PHONE}
Telegram: {ADMIN_TELEGRAM}
    """
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xizmatlar"""
    services_text = """
🛠️✨ *NOVA.X XIZMATLARI* ✨🛠️

🎨 *1. DIZAYN XIZMATLARI:*
• UI/UX Dizayn
• Logo va brend identifikatsiyasi
• Veb va mobil dizayn

🌐 *2. VEB-DASTURLASH:*
• Landing Page
• Korporativ veb-saytlar
• Onlayn do'konlar
• Portfoliolar

📱 *3. MOBIL DASTURLASH:*
• iOS va Android ilovalari
• Kross-platform ilovalar

🔍 *4. SEO VA MARKETING:*
• SEO Optimizatsiya
• Digital Marketing

☁️ *5. HOSTING VA SERVER:*
• Domen va hosting
• VPS va Cloud serverlar

🛡️ *6. XAVFSIZLIK VA SUPPORT:*
• 24/7 texnik yordam
• Xavfsizlik himoyasi

👇 *Xizmat turini tanlang:*
    """
    
    await update.message.reply_text(
        services_text, 
        parse_mode='Markdown',
        reply_markup=get_service_keyboard()
    )

async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Narxlar"""
    prices_text = f"""
💰✨ *NOVA.X NARXLARI* ✨💰

📊 *ASOSIY PAKETLAR:*

🎯 *STARTUP PAKETI - 1 500 000 – 2 000 000 so‘m*
• Responsive veb-sayt (5 sahifa)
• Domain va hosting (1 yil)
• SSL sertifikati

🚀 *BUSINESS PAKETI - 4 000 000 – 6 000 000 so‘m*
• Full functional veb-sayt (10 sahifa)
• Admin panel
• CRM tizimi

🏆 *PREMIUM PAKETI - 8 000 000 – 12 000 000 so‘m*
• Maxsus veb-ilova
• Full CMS yoki CRM
• Mobil ilova

📞 *BATAFSIL MALUMMOT VA BEPUL MASLAHAT:*
{ADMIN_PHONE}
    """
    
    await update.message.reply_text(prices_text, parse_mode='Markdown')

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aloqa"""
    contact_text = f"""
📞✨ *NOVA.X BILAN ALOQA* ✨📞

📱 *ASOSIY TELEFON:*
{ADMIN_PHONE}

(24/7 qo'llab-quvvatlash)

💬 *TELEGRAM:*
{ADMIN_TELEGRAM}

🎯 *TEZKOR JAVOB:*
Har qanday savolga 15 daqiqa ichida javob beramiz
    """
    
    await update.message.reply_text(contact_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    help_text = f"""
❓✨ *YORDAM VA KO'P BERILADIGAN SAVOLLAR* ✨❓

🤔 *QANDAY ARIZA QOLDIRISH MUMKIN?*
1. "📝 Ariza qoldirish" tugmasini bosing
2. Ma'lumotlarni to'ldiring
3. Xizmat turini tanlang

📞 *QANCHADA JAVOB BERASIZLAR?*
• Ish vaqtida: 15 daqiqa ichida

💰 *TO'LOV QANDAY AMALGA OSHIRILADI?*
1. 30% avans to'lov
2. 40% ish davomida
3. 30% topshirilganda

⏰ *LOYIHA QANCHADA TAYYOR BO'LADI?*
• Landing Page: 3-7 kun
• Veb-sayt: 7-14 kun
• Mobil ilova: 14-30 kun

📱 *QAYSI TELEFON RAQAMLARIGA MUROJAAT QILISH KERAK?*
Asosiy raqam: {ADMIN_PHONE}

💬 *TELEGRAMDA QAYSI PROFILLAR ORQALI BOG'LANISH MUMKIN?*
{ADMIN_TELEGRAM} - Asosiy profil

⭐ *QANDAY BAHO BERISH MUMKIN?*
"⭐ Baho berish" tugmasini bosing va 1 dan 5 gacha baholang

👇 *SAVOLINGIZ QAOLSA, HOZIR BOG'LANING!*
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ==================== APPLICATION FUNCTIONS ====================
async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ariza boshlash"""
    application_text = """
📝✨ *ARIZA QOLDIRISH* ✨📝

🚀 *LOYIHANGIZNI BOSHLANG!*

📋 *KERAKLI MA'LUMOTLAR:*

👤 *SHU FORMATDA YUBORING:*
Ism:     [To'liq ismingiz]
Telefon: [998 XX YYY YY YY]
Xizmat: [Xizmat turi]

👇 *MA'LUMOTLARINGIZNI YUBORING:*
    """
    
    await update.message.reply_text(application_text, parse_mode='Markdown')
    context.user_data['awaiting_application'] = True

async def handle_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ariza ma'lumotlarini qayta ishlash"""
    if not context.user_data.get('awaiting_application'):
        return
    
    user = update.effective_user
    text = update.message.text
    
    # Ma'lumotlarni ajratish
    name = user.first_name or "Noma'lum"
    phone = ""
    service = "Noma'lum"
    
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if 'ism' in key:
                name = value
            elif 'tel' in key or 'phone' in key:
                phone = value
            elif 'xizmat' in key:
                service = value
    
    # Raqamni topish
    if not phone:
        numbers = re.findall(r'[\+\d\s\-\(\)]{10,}', text)
        if numbers:
            phone = numbers[0]
        elif text.replace('+', '').replace(' ', '').isdigit():
            phone = text
    
    if not phone:
        await update.message.reply_text("❌ Telefon raqami aniqlanmadi. Iltimos, qayta yuboring.")
        return
    
    # Saqlash
    app = db.add_application(user.id, name, phone, service, text)
    
    # Foydalanuvchiga javob
    await update.message.reply_text(
        f"✅ *Arizangiz qabul qilindi!*\n\n"
        f"🆔 *ID:* {app['id']}\n"
        f"👤 *Ism:* {name}\n"
        f"📞 *Telefon:* {phone}\n"
        f"🛠️ *Xizmat:* {service}\n\n"
        f"⏰ *Operator 1 soat ichida aloqaga chiqadi.*\n"
        f"📞 *Tezkor javob:* {ADMIN_PHONE}",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )
    
    # Adminlarga xabar
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📥 *YANGI ARIZA #{app['id']}*\n\n"
                     f"👤 *Ism:* {name}\n"
                     f"📞 *Telefon:* {phone}\n"
                     f"🛠️ *Xizmat:* {service}\n"
                     f"📅 *Vaqt:* {app['date']}\n"
                     f"🆔 *User ID:* {user.id}",
                parse_mode='Markdown'
            )
        except:
            pass
    
    context.user_data.pop('awaiting_application', None)

# ==================== PHONE CONTACT FUNCTIONS ====================
async def start_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon qoldirish"""
    phone_text = """
📱✨ *TELEFON RAQAMINGIZNI QOLDIRING* ✨📱

🎯 *BU NIMA UCHUN KERAK?*
• Siz bilan bog'lanish
• Bepul konsultatsiya
• Aksiya va chegirmalar haqida xabar berish

📞 *QANDAY QOLDIRISH MUMKIN?*
Oddiygina telefon raqamingizni yuboring:

    +998 XX XXX XX XX
    YOKI
    +998 XX XXX XX XX

👇 *TELEFON RAQAMINGIZNI YUBORING:*
    """
    
    await update.message.reply_text(phone_text, parse_mode='Markdown')
    context.user_data['awaiting_phone'] = True

async def handle_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon kontaktini qayta ishlash"""
    if not context.user_data.get('awaiting_phone'):
        return
    
    user = update.effective_user
    text = update.message.text
    
    # Telefon raqamini topish
    phone = ""
    numbers = re.findall(r'[\+\d\s\-\(\)]{10,}', text)
    if numbers:
        phone = numbers[0]
    elif text.replace('+', '').replace(' ', '').isdigit():
        phone = text
    
    if not phone:
        await update.message.reply_text("❌ Telefon raqami aniqlanmadi. Iltimos, raqamingizni yuboring.")
        return
    
    name = user.first_name or "Noma'lum"
    
    # Saqlash
    contact = db.add_contact(user.id, name, phone, text)
    
    # Foydalanuvchiga javob
    await update.message.reply_text(
        f"✅ *Raqamingiz qabul qilindi!*\n\n"
        f"👤 *Ism:* {name}\n"
        f"📞 *Telefon:* {phone}\n\n"
        f"⏰ *Operator 15 daqiqa ichida aloqaga chiqadi.*\n"
        f"📞 *Tezkor javob:* {ADMIN_PHONE}",
        parse_mode='Markdown',
        reply_markup=get_main_menu()
    )
    
    # Adminlarga xabar
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📞 *YANGI TELEFON*\n\n"
                     f"👤 *Ism:* {name}\n"
                     f"📞 *Telefon:* {phone}\n"
                     f"📅 *Vaqt:* {contact['date']}\n"
                     f"🆔 *User ID:* {user.id}",
                parse_mode='Markdown'
            )
        except:
            pass
    
    context.user_data.pop('awaiting_phone', None)

# ==================== RATING FUNCTIONS ====================
async def start_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baho berishni boshlash"""
    rating_text = """
⭐✨ *BAHO BERISH* ✨⭐

🎯 *BIZNING ISHIMIZNI BAHOLANG!*

5 yulduz tizimi orqali bizning xizmatlarimizni baholang:

⭐⭐⭐⭐⭐ (5) - A'lo, juda mamnun
⭐⭐⭐⭐ (4) - Yaxshi, mamnun
⭐⭐⭐ (3) - O'rtacha, yaxshi
⭐⭐ (2) - Qoniqarsiz, yaxshilash kerak
⭐ (1) - Yomon, juda norozi

👇 *1 DAN 5 GACHA BAHOLANG:*
    """
    
    await update.message.reply_text(
        rating_text,
        parse_mode='Markdown',
        reply_markup=get_rating_keyboard()
    )

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baho berish callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_rate":
        await query.edit_message_text(
            "❌ *Baho berish bekor qilindi.*\n\n"
            "Istalgan vaqtda qayta baho berishingiz mumkin.",
            parse_mode='Markdown'
        )
        return
    
    if query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])
        
        # Bahoni saqlash
        user = query.from_user
        db.add_rating(user.id, rating)
        
        # Bahoga javob
        stars = "⭐" * rating
        empty_stars = "☆" * (5 - rating)
        
        await query.edit_message_text(
            f"{stars}{empty_stars}\n\n"
            f"✅ *{rating} yulduzli baho qoldirdingiz!*\n\n"
            f"🎯 *Rahmat, qadringizni bildirganingiz uchun!*\n"
            f"💫 Bahoingiz bizni yanada yaxshilanishimizga yordam beradi.\n\n"
            f"📞 Agar takliflaringiz bo'lsa: {ADMIN_PHONE}",
            parse_mode='Markdown'
        )
        
        # Adminlarga xabar
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"⭐ *YANGI BAHO: {rating}/5*\n\n"
                         f"👤 *Foydalanuvchi:* {user.first_name}\n"
                         f"🆔 *User ID:* {user.id}\n"
                         f"📅 *Vaqt:* {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                         f"📊 *O'rtacha reyting:* {db.get_stats()['average_rating']}/5",
                    parse_mode='Markdown'
                )
            except:
                pass

# ==================== YANGI ADMIN FUNCTIONS ====================
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin statistikasi"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    stats = db.get_stats()
    
    # Baholarni hisoblash
    ratings = db.get_all_ratings()
    rating_counts = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for rating in ratings:
        r = rating.get("rating", 0)
        if r in rating_counts:
            rating_counts[r] += 1
    
    text = f"""
📊✨ *ADMIN STATISTIKASI* ✨📊

📈 *UMUMIY KO'RSATKICHLAR:*
📋 Arizalar: {stats['total_applications']} ta
📞 Kontaktlar: {stats['total_contacts']} ta
⭐ Baholar: {stats['total_ratings']} ta
🌟 O'rtacha baho: {stats['average_rating']}/5

📅 *BUGUNGI STATISTIKA:*
📥 Yangi arizalar: {stats['today_applications']} ta

📊 *HOLATLAR BO'YICHA:*
🆕 Yangi: {len([a for a in db.get_all_applications() if a.get('status') == 'yangi'])} ta
⏳ Jarayonda: {len([a for a in db.get_all_applications() if a.get('status') == 'jarayonda'])} ta
✅ Bajarilgan: {len([a for a in db.get_all_applications() if a.get('status') == 'completed'])} ta
❌ Bekor: {len([a for a in db.get_all_applications() if a.get('status') == 'cancelled'])} ta

📊 *BAHOLAR TAQSIMOTI:*
"""
    
    for stars in range(5, 0, -1):
        count = rating_counts[stars]
        percentage = (count / len(ratings) * 100) if ratings else 0
        text += f"⭐{'⭐' * (stars-1)} {stars}/5: {count} ta ({percentage:.1f}%)\n"
    
    text += f"\n🕒 *Oxirgi yangilanish:* {stats['last_updated']}"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_applications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Arizalar menyusi"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    await update.message.reply_text(
        "📋✨ *ARIZALAR BOSHQARUVI* ✨📋\n\nHolat bo'yicha tanlang:",
        parse_mode='Markdown',
        reply_markup=get_admin_applications_menu()
    )

async def admin_show_applications(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str):
    """Holat bo'yicha arizalarni ko'rsatish"""
    query = update.callback_query
    await query.answer()
    
    if status == "all":
        applications = db.get_all_applications()
    else:
        applications = [app for app in db.get_all_applications() if app.get("status") == status]
    
    status_names = {
        "new": "🆕 Yangi arizalar",
        "progress": "⏳ Jarayonda",
        "completed": "✅ Bajarilgan",
        "cancelled": "❌ Bekor qilingan",
        "all": "📊 Barcha arizalar"
    }
    
    if not applications:
        await query.edit_message_text(
            f"{status_names.get(status, 'Arizalar')}\n\n📭 Hech qanday ariza topilmadi.",
            parse_mode='Markdown',
            reply_markup=get_admin_applications_menu()
        )
        return
    
    text = f"{status_names.get(status, 'Arizalar')} ({len(applications)} ta)\n\n"
    
    # So'nggi 10 ta ariza
    for app in applications[-10:]:
        status_emoji = {
            "yangi": "🆕",
            "jarayonda": "⏳",
            "completed": "✅",
            "cancelled": "❌"
        }.get(app.get("status", "yangi"), "📝")
        
        text += f"""
{status_emoji} *#{app['id']}* - {app['name']}
📞 {app['phone']}
🛠️ {app['service']}
📅 {app['date']}
{'='*30}
"""
    
    if len(applications) > 10:
        text += f"\n... va yana {len(applications) - 10} ta ariza"
    
    # Inline tugmalar
    keyboard = []
    for app in applications[-5:]:
        keyboard.append([
            InlineKeyboardButton(
                f"#{app['id']} - {app['name'][:15]}...", 
                callback_data=f"admin_app_detail_{app['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="admin_apps_all")])
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_application_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, app_id: int):
    """Ariza tafsilotlari"""
    query = update.callback_query
    await query.answer()
    
    applications = db.get_all_applications()
    app = next((a for a in applications if a["id"] == app_id), None)
    
    if not app:
        await query.edit_message_text("❌ Ariza topilmadi!")
        return
    
    status_emoji = {
        "yangi": "🆕",
        "jarayonda": "⏳",
        "completed": "✅",
        "cancelled": "❌"
    }.get(app.get("status", "yangi"), "📝")
    
    text = f"""
{status_emoji} *ARIZA #{app['id']}*

👤 *MIJOZ:*
• Ism: {app['name']}
• Telefon: {app['phone']}
• User ID: {app.get('user_id', 'N/A')}

🎯 *LOYIHA:*
• Xizmat: {app['service']}
• Holat: {app.get('status', 'yangi')}
• Vaqt: {app['date']}
• Yangilangan: {app.get('updated_at', 'N/A')}

📝 *XABAR:*
{app.get('message', 'Izoh yo\'q')}

👇 *AMALLAR:*
"""
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_application_actions(app_id)
    )

async def admin_today_apps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bugungi arizalar"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    today_apps = db.get_today_applications()
    
    if not today_apps:
        await update.message.reply_text("📭 Bugun hali ariza yo'q")
        return
    
    text = f"📅 *BUGUNGI ARIZALAR* ({len(today_apps)} ta)\n\n"
    
    for app in today_apps:
        text += f"""
🆔 #{app['id']} - {app['name']}
📞 {app['phone']}
🛠️ {app['service']}
⏰ {app['date'][11:16]}
{'─'*25}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kontaktlarni ko'rsatish"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    contacts = db.get_all_contacts()
    
    if not contacts:
        await update.message.reply_text("📭 Hozircha kontaktlar yo'q")
        return
    
    text = f"📞 *KONTAKTLAR* ({len(contacts)} ta)\n\n"
    
    for contact in contacts[-15:]:
        text += f"""
👤 {contact['name']}
📞 {contact['phone']}
📅 {contact['date']}
{'─'*25}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_ratings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baholarni ko'rsatish"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    ratings = db.get_all_ratings()
    
    if not ratings:
        await update.message.reply_text("⭐ Hozircha baholar yo'q")
        return
    
    stats = db.get_stats()
    
    text = f"""
⭐✨ *BAHOLAR* ✨⭐

📊 *UMUMIY:*
• Jami baholar: {stats['total_ratings']} ta
• O'rtacha baho: {stats['average_rating']}/5
• Mijoz mamnuniyati: {stats['average_rating'] * 20:.0f}%

📋 *SO'NGI 10 BAHO:*
"""
    
    for rating in ratings[-10:]:
        stars = "⭐" * rating['rating']
        empty_stars = "☆" * (5 - rating['rating'])
        text += f"""
{stars}{empty_stars} ({rating['rating']}/5)
👤 ID: {rating.get('user_id', 'Noma\'lum')}
📅 {rating['date']}
{'─'*20}
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def admin_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export menyusi"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    await update.message.reply_text(
        "📤✨ *MA'LUMOTLAR EXPORTI* ✨📤\n\nEksport qilmoqchi bo'lgan ma'lumotlarni tanlang:",
        parse_mode='Markdown',
        reply_markup=get_admin_export_menu()
    )

async def admin_export_data(update: Update, context: ContextTypes.DEFAULT_TYPE, export_type: str):
    """Ma'lumotlarni export qilish"""
    query = update.callback_query
    await query.answer()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if export_type == "apps_csv":
            filename = f"arizalar_{timestamp}.csv"
            applications = db.get_all_applications()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Ism', 'Telefon', 'Xizmat', 'Holat', 'Sana', 'Xabar'])
                for app in applications:
                    writer.writerow([
                        app['id'],
                        app['name'],
                        app['phone'],
                        app['service'],
                        app.get('status', 'yangi'),
                        app['date'],
                        app.get('message', '')[:100]
                    ])
            
            await query.message.reply_document(
                document=open(filename, 'rb'),
                caption=f"📋 Arizalar ro'yxati ({len(applications)} ta)"
            )
            os.remove(filename)
        
        elif export_type == "contacts_csv":
            filename = f"kontaktlar_{timestamp}.csv"
            contacts = db.get_all_contacts()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Ism', 'Telefon', 'Sana', 'Xabar'])
                for contact in contacts:
                    writer.writerow([
                        contact['id'],
                        contact['name'],
                        contact['phone'],
                        contact['date'],
                        contact.get('message', '')[:100]
                    ])
            
            await query.message.reply_document(
                document=open(filename, 'rb'),
                caption=f"📞 Kontaktlar ro'yxati ({len(contacts)} ta)"
            )
            os.remove(filename)
        
        elif export_type == "ratings_csv":
            filename = f"baholar_{timestamp}.csv"
            ratings = db.get_all_ratings()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'User ID', 'Baho', 'Sana', 'Izoh'])
                for rating in ratings:
                    writer.writerow([
                        rating['id'],
                        rating.get('user_id', ''),
                        rating['rating'],
                        rating['date'],
                        rating.get('feedback', '')
                    ])
            
            await query.message.reply_document(
                document=open(filename, 'rb'),
                caption=f"⭐ Baholar ro'yxati ({len(ratings)} ta)"
            )
            os.remove(filename)
        
        elif export_type == "stats_txt":
            filename = f"statistika_{timestamp}.txt"
            stats = db.get_stats()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("="*50 + "\n")
                f.write("NOVA.X STATISTIKA\n")
                f.write("="*50 + "\n\n")
                f.write(f"📅 Export vaqti: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
                f.write(f"📋 Jami arizalar: {stats['total_applications']} ta\n")
                f.write(f"📞 Jami kontaktlar: {stats['total_contacts']} ta\n")
                f.write(f"⭐ Jami baholar: {stats['total_ratings']} ta\n")
                f.write(f"🌟 O'rtacha baho: {stats['average_rating']}/5\n")
                f.write(f"📅 Bugungi arizalar: {stats['today_applications']} ta\n")
                f.write(f"🕒 Oxirgi yangilanish: {stats['last_updated']}\n")
            
            await query.message.reply_document(
                document=open(filename, 'rb'),
                caption=f"📊 Statistika hisoboti"
            )
            os.remove(filename)
        
        elif export_type == "all_zip":
            # ZIP fayl yaratish
            import zipfile
            
            zip_filename = f"nova_export_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                # Arizalar
                apps_file = f"arizalar_{timestamp}.csv"
                applications = db.get_all_applications()
                with open(apps_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Ism', 'Telefon', 'Xizmat', 'Holat', 'Sana', 'Xabar'])
                    for app in applications:
                        writer.writerow([
                            app['id'],
                            app['name'],
                            app['phone'],
                            app['service'],
                            app.get('status', 'yangi'),
                            app['date'],
                            app.get('message', '')[:100]
                        ])
                zipf.write(apps_file)
                os.remove(apps_file)
                
                # Kontaktlar
                contacts_file = f"kontaktlar_{timestamp}.csv"
                contacts = db.get_all_contacts()
                with open(contacts_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'Ism', 'Telefon', 'Sana', 'Xabar'])
                    for contact in contacts:
                        writer.writerow([
                            contact['id'],
                            contact['name'],
                            contact['phone'],
                            contact['date'],
                            contact.get('message', '')[:100]
                        ])
                zipf.write(contacts_file)
                os.remove(contacts_file)
                
                # Baholar
                ratings_file = f"baholar_{timestamp}.csv"
                ratings = db.get_all_ratings()
                with open(ratings_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['ID', 'User ID', 'Baho', 'Sana', 'Izoh'])
                    for rating in ratings:
                        writer.writerow([
                            rating['id'],
                            rating.get('user_id', ''),
                            rating['rating'],
                            rating['date'],
                            rating.get('feedback', '')
                        ])
                zipf.write(ratings_file)
                os.remove(ratings_file)
                
                # Statistika
                stats_file = f"statistika_{timestamp}.txt"
                stats = db.get_stats()
                with open(stats_file, 'w', encoding='utf-8') as f:
                    f.write("="*50 + "\n")
                    f.write("NOVA.X STATISTIKA\n")
                    f.write("="*50 + "\n\n")
                    f.write(f"📅 Export vaqti: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
                    for key, value in stats.items():
                        f.write(f"{key}: {value}\n")
                zipf.write(stats_file)
                os.remove(stats_file)
            
            await query.message.reply_document(
                document=open(zip_filename, 'rb'),
                caption="📁 Barcha ma'lumotlar"
            )
            os.remove(zip_filename)
        
        await query.message.reply_text(
            "✅ Export muvaffaqiyatli yakunlandi!",
            reply_markup=get_main_menu(is_admin=True)
        )
    
    except Exception as e:
        logger.error(f"Exportda xato: {e}")
        await query.message.reply_text(
            f"❌ Exportda xato: {str(e)}",
            reply_markup=get_main_menu(is_admin=True)
        )

async def admin_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sozlamalar"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    text = f"""
⚙️ *ADMIN PANEL SOZLAMALARI*

👑 *Adminlar:* {len(ADMIN_IDS)} ta
📊 *Ma'lumotlar bazasi:* {os.path.getsize('nova_x_database.json') if os.path.exists('nova_x_database.json') else 0} bayt
🕒 *Server vaqti:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
📈 *Bot holati:* 🟢 Faol

🔧 *SOZLAMALAR:*
• Bildirishnomalar: Yoqilgan
• Avtomatik backup: Yoqilgan
• Logging: INFO
"""
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ==================== CALLBACK HANDLER ====================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback query larni qayta ishlash"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Admin callback lar
    if data.startswith("admin_"):
        if data == "admin_back":
            await admin_stats(update, context)
        
        elif data.startswith("admin_apps_"):
            status = data.split("_")[2]
            await admin_show_applications(update, context, status)
        
        elif data.startswith("admin_app_detail_"):
            app_id = int(data.split("_")[3])
            await admin_application_detail(update, context, app_id)
        
        elif data.startswith("app_complete_"):
            app_id = int(data.split("_")[2])
            db.update_application_status(app_id, "completed")
            await query.edit_message_text(
                f"✅ Ariza #{app_id} bajarildi deb belgilandi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("app_progress_"):
            app_id = int(data.split("_")[2])
            db.update_application_status(app_id, "jarayonda")
            await query.edit_message_text(
                f"⏳ Ariza #{app_id} jarayonda deb belgilandi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("app_cancel_"):
            app_id = int(data.split("_")[2])
            db.update_application_status(app_id, "cancelled")
            await query.edit_message_text(
                f"❌ Ariza #{app_id} bekor qilindi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("app_contact_"):
            app_id = int(data.split("_")[2])
            apps = db.get_all_applications()
            app = next((a for a in apps if a["id"] == app_id), None)
            if app:
                await query.edit_message_text(
                    f"📞 *QO'NG'IROQ QILISH:*\n\n"
                    f"👤 Mijoz: {app['name']}\n"
                    f"📞 Telefon: {app['phone']}\n\n"
                    f"💬 Ish turi: {app['service']}",
                    parse_mode='Markdown'
                )
    
    # Export callback lar
    elif data.startswith("export_"):
        export_type = data.split("_")[1]
        await admin_export_data(update, context, export_type)
    
    # User rating callback
    elif data.startswith("rate_"):
        await handle_rating_callback(update, context)
    
    elif data.startswith("service_"):
        service_names = {
            "website": "🌐 Veb-sayt yaratish",
            "mobile": "📱 Mobil ilova",
            "design": "🎨 UI/UX Dizayn",
            "seo": "🔍 SEO Optimizatsiya",
            "hosting": "☁️ Hosting va Server",
            "other": "⚡ Boshqa xizmat"
        }
        service_type = data.split("_")[1]
        name = service_names.get(service_type, "Noma'lum xizmat")
        
        await query.message.reply_text(
            f"🎯 *Siz tanlagan xizmat:* {name}\n\n"
            "Ushbu xizmat bo'yicha ariza qoldirish uchun quyidagi tugmani bosing yoki ma'lumotlaringizni yuboring.",
            parse_mode='Markdown',
            reply_markup=get_main_menu()
        )
        # Arizani boshlash
        await start_application(update, context)

    elif data == "cancel_rate":
        await query.edit_message_text(
            "❌ *Baho berish bekor qilindi.*\n\n"
            "Istalgan vaqtda qayta baho berishingiz mumkin.",
            parse_mode='Markdown'
        )

# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni qayta ishlash"""
    user = update.effective_user
    text = update.message.text
    
    # Admin bo'lsa
    if user.id in ADMIN_IDS:
        if text == "📊 STATISTIKA":
            await admin_stats(update, context)
        elif text == "📋 ARIZALAR":
            await admin_applications(update, context)
        elif text == "📅 BUGUNGI":
            await admin_today_apps(update, context)
        elif text == "📞 KONTAKTLAR":
            await admin_contacts(update, context)
        elif text == "⭐ BAHOLAR":
            await admin_ratings(update, context)
        elif text == "📤 EXPORT":
            await admin_export(update, context)
        elif text == "⚙️ SOZLAMALAR":
            await admin_settings(update, context)
        elif text == "🏠 ASOSIY MENYU":
            await start_command(update, context)
    
    # Oddiy foydalanuvchi bo'lsa
    else:
        if text == "ℹ️ BIZ HAQIMIZDA":
            await about_command(update, context)
        elif text == "🛠️ XIZMATLAR":
            await services_command(update, context)
        elif text == "💰 NARXLAR":
            await prices_command(update, context)
        elif text == "📝 ARIZA QOLDIRISH":
            await start_application(update, context)
        elif text == "📱 TELEFON QOLDIRISH":
            await start_phone_contact(update, context)
        elif text == "⭐ BAHO BERISH":
            await start_rating(update, context)
        elif text == "📞 ALOQA":
            await contact_command(update, context)
        elif text == "❓ YORDAM":
            await help_command(update, context)
        else:
            # Agar ariza yoki telefon kutilayotgan bo'lsa
            if context.user_data.get('awaiting_application'):
                await handle_application(update, context)
            elif context.user_data.get('awaiting_phone'):
                await handle_phone_contact(update, context)
            else:
                # Boshqa har qanday xabar uchun
                await update.message.reply_text(
                    "🤖 *Iltimos, menyudan variant tanlang.*\n\n"
                    "Ariza yoki telefon qoldirish uchun tegishli tugmalarni bosing.\n\n"
                    f"📞 *Yordam:* {ADMIN_PHONE}",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu()
                )

# ==================== MAIN FUNCTION ====================
def main():
    """Asosiy funksiya"""
    print(f"📞 Admin telefon: {ADMIN_PHONE}")
    print(f"💬 Telegram: {ADMIN_TELEGRAM}")
    print(f"👑 Adminlar soni: {len(ADMIN_IDS)}")
    print("=" * 60)
    print("✅ Bot konfiguratsiyasi muvaffaqiyatli!")
    
    # Botni yaratish
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("📱 Telegramda botni oching va /start buyrug'ini yuboring")
    print("=" * 60)
    
    # Render uchun web serverni ishga tushirish
    keep_alive()
    
    # Botni ishga tushirish
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()