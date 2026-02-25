#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🍦✨ DILBAR OY ICE CREAM - MUZQAYMOQ BUYURTMA BOTI ✨🍦
🎯 To'liq Admin Panel + Buyurtmalar tizimi
"""

import logging
import json
import os
import re
import csv
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ==================== WEB SERVER (RENDER KEEP-ALIVE) ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Dilbar Oy Ice Cream Bot is alive!", 200

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
    """Web serverni alohida threadda ishga tushirish"""
    try:
        t = Thread(target=run_web_server)
        t.daemon = True
        t.start()
        logger.info("Keep-alive tizimi (Flask) muvaffaqiyatli ishga tushirildi.")
    except Exception as e:
        logger.error(f"Keep-alive tizimini ishga tushirishda xato: {e}")

# ==================== KONFIGURATSIYA ====================
# Render Environment Variables-dan o'qiydi, agar bo'lmasa pastdagini ishlatadi
BOT_TOKEN = os.environ.get('BOT_TOKEN', "7562958417:AAFjmA8XLYSQco0pbNmWUZ-otqe9JsKsDmY")
ADMIN_PHONE = "990330606 / 992300606"
ADMIN_TELEGRAM = "@sh715aa"
ADMIN_IDS = [7150278934]  # O'z ID ingizni qo'ying

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

# ==================== TRANSLATIONS ====================
TRANSLATIONS = {
    'uz_lat': {
        'select_lang': "🌍 Iltimos, tilni tanlang:\n🇷🇺 Пожалуйста, выберите язык:\n🇺🇸 Please select a language:",
        'welcome': "�✨ **ASSALOMU ALAYKUM, {name} {username}!** 👋✨\n\n🎉 **Dilbar Oy Ice Cream — Muzqaymoqlar dunyosiga xush kelibsiz!**\nSizni bu yerda ko‘rib turganimizdan behad mamnunmiz! 🤩 Bugun shirin muzqaymoq tanovul qilish uchun ajoyib kun.\n\n🚀 **Eng mazali va sifatli muzqaymoqlar faqat bizda!**\nBiz shunchaki muzqaymoq sotmaymiz, biz sizga quvonch va huzurbaxsh ta'mni ulashamiz! �\n\n❄️ **Bizning afzalliklarimiz:**\n• 🍨 _Tabiiy mahsulotlar_ — Faqat suti va yangi mevalar.\n• ⚡️ _Tezkor yetkazib berish_ — Muzqaymoq erishga ulgurmaydi!\n• 🤝 _Hamyonbop narxlar_ — Maza va narx uyg'unligi.\n\n🔥 *Keling, hoziroq buyurtma bering va mazali ta'mdan bahra oling!*\n\n👇 **Marhamat, quyidagi menyudan kerakli bo'limni tanlang:**",
        'menu_about': "ℹ️ BIZ HAQIMIZDA",
        'menu_services': "🍨 ASSORTIMENT",
        'menu_prices': "💰 NARXLAR",
        'menu_apply': "📝 BUYURTMA BERISH",
        'menu_phone': "📱 RAQAM QOLDIRISH",
        'menu_rate': "⭐ BAHO BERISH",
        'menu_contact': "📞 ALOQA",
        'menu_help': "❓ YORDAM",
        'menu_main': "🏠 ASOSIY MENYU",
        'about_text': "�✨ *DILBAR OY ICE CREAM - MAZALI LAHZALAR* ✨�\n\n🌟 *BIZ KIMMIZ?*\nDilbar Oy Ice Cream - bu ko'p yillik tajribaga ega bo'lgan, faqat tabiiy mahsulotlardan tayyorlanuvchi muzqaymoqlar ishlab chiqaruvchi brend.\n\n📞 *ALOQA:*\nTelefon: {phone}\nTelegram: {telegram}",
        'services_text': "🍨✨ *BIZNING ASSORTIMENT* ✨🍨\n\n� *1. KLASSIK MUZQAYMOQLAR:*\n• Shokoladli\n• Vanilli\n• Qaymoqli (Plombir)\n\n� *2. MEVALI MUZQAYMOQLAR:*\n• Qulupnayli\n• Bananli\n• Malinali\n\n🥜 *3. PLUMLI VA YONG'OQLI:*\n• Pistali\n• Yong'oqli mix\n\n🍰 *4. MAXSUS TORT-MUZQAYMOQLAR:*\n• Bayramona tortlar\n• Mevali kompozitsiyalar\n\n🥤 *5. MUZQAYMOQLI KOKTEYLLAR:*\n• Milkshake\n• Muzli kofe\n\n👇 *Turini tanlang:*",
        'prices_text': "💰✨ *MUZQAYMOQ NARXLARI* ✨💰\n\n📊 *NARXLAR RO'YXATI:*\n\n🎯 *DONALI (IDIShDA) - 5 000 – 15 000 so‘m*\n🚀 *KATTA KG-DA - 40 000 – 65 000 so‘m*\n🏆 *MAXSUS TORTLAR - 80 000 – 250 000 so‘m*\n\n📞 *BATAFSIL MALUMMOT VA BUYURTMA:* \n{phone}",
        'contact_text': "📞✨ *DILBAR OY ALOQA* ✨📞\n\n📱 *ASOSIY TELEFONLAR:*\n{phone}\n\n💬 *TELEGRAM:*\n{telegram}\n\n🎯 *TEZKOR JAVOB:*\nBuyurtmalar bo'yicha 10 daqiqa ichida bog'lanamiz",
        'help_text': "❓✨ *YORDAM VA SAVOLLAR* ✨❓\n\n🤔 *BUYURTMA QANDAY BERILADI?*\n1. \"📝 Buyurtma berish\" tugmasini bosing\n2. Ma'lumotlarni to'ldiring\n3. Muzqaymoq turini ayting\n\n� *YETKAZIB BERISh QANCHA VAQT OLADI?*\n• 30-60 daqiqa ichida manzilga yetkaziladi\n\n💰 *TO'LOV USULLARI:*\n• Naqd pul yoki Click/Payme orqali\n\n� *ADMIN BILAN ALOQA:*\n{phone}\n\n👇 *SAVOLINGIZ BO'LSA, MUROJAAT QILING!*",
        'app_start_text': "📝✨ *BUYURTMA BERISH* ✨📝\n\n🚀 *MAZALI MUZQAYMOQNI TANLANG!*\n\n📋 *BUYURTMA FORMATI:*\n\n👤 *SHU KO'RINISHDA YUBORING:*\nIsm:     [Ismingiz]\nTelefon: [998 XX YYY YY YY]\nMuzqaymoq turi: [Nomi va soni]\nManzil: [Uy yoki ofis manzili]\n\n👇 *MA'LUMOTLARINGIZNI YUBORING:*",
        'app_success': "✅ *Buyurtmangiz qabul qilindi!*\n\n🆔 *ID:* {id}\n👤 *Ism:* {name}\n📞 *Telefon:* {phone}\n🍨 *Muzqaymoq:* {service}\n\n⏰ *Operator 10 daqiqa ichida tasdiqlash uchun aloqaga chiqadi.*\n📞 *Admin:* {admin_phone}",
        'phone_start_text': "📱✨ *RAQAMINGIZNI QOLDIRING* ✨📱\n\n🎯 *BIZ SIZGA QO'NG'IROQ QILAMIZ!*\n• Buyurtmani aniqlashtirish\n• Yangi turdagi muzqaymoqlar haqida xabar berish\n\n👇 *TELEFON RAQAMINGIZNI YUBORING:*",
        'phone_success': "✅ *Raqamingiz qabul qilindi!*\n\n👤 *Ism:* {name}\n📞 *Telefon:* {phone}\n\n⏰ *Operator tez orada aloqaga chiqadi.*",
        'rating_start_text': "⭐✨ *BAHO BERISH* ✨⭐\n\n🎯 *MUZQAYMOQLARIMIZ SIZGA YOQDIMI?*\n\nBizning mahsulot va xizmatimizni baholang:\n\n👇 *1 DAN 5 GACHA BAHOLANG:*",
        'rating_success': "✅ *Rahmat! Siz {rating} yulduzli baho berdingiz!*\n\nIste'molingiz shirin bo'lsin! 🍦",
        'error_no_phone': "❌ Telefon raqami xato kiritildi. Iltimos, qayta yuboring.",
        'service_selected': "🎯 *Tanlangan tur:* {name}\n\nBuyurtma qilish uchun ma'lumotlaringizni yuboring.",
        'cancel_btn': "❌ Bekor qilish",
        'back_btn': "🔙 Orqaga",
        'service_website': "� Klassik (Plombir)",
        'service_mobile': "🍓 Mevali muzqaymoq",
        'service_design': "� Muzqaymoqli tort",
        'service_seo': "🥤 Milkshake / Kokteyllar",
        'service_hosting': "🍨 Idishdagi muzqaymoq",
        'service_other': "✨ Boshqa buyurtma",
        'lang_changed': "✅ Til o'zgartirildi!",
        'menu_lang': "🌐 Tilni tanlash"
    },
    'uz_cyr': {
        'select_lang': "🌍 Илтимос, тилни танланг:",
        'welcome': "🍦✨ **АССАЛОМУ АЛАЙКУМ, {name} {username}!** 👋✨\n\n🎉 **Dilbar Oy Ice Cream — Музқаймоқлар дунёсига хуш келибсиз!**\nСизни бу ерда кўриб турганимиздан беҳад мамнунмиз! 🤩 Бугун ширин музқаймоқ тановул қилиш учун ажойиб кун.\n\n🚀 **Энг мазали ва сифатли музқаймоқлар фақат бизда!**\n\n❄️ **Бизнинг афзалликларимиз:**\n• 🍨 _Табиий маҳсулотлар_\n• ⚡️ _Тезкор етказиб бериш_\n• 🤝 _Ҳамёнбоп нархлар_\n\n👇 **Марҳамат, қуйидаги менюдан керакли бўлимни танланг:**",
        'menu_about': "ℹ️ БИЗ ҲАҚИМИЗДА",
        'menu_services': "🍨 АССОРТИМЕНТ",
        'menu_prices': "💰 НАРХЛАР",
        'menu_apply': "📝 БУЮРТМА БЕРИШ",
        'menu_phone': "📱 РАҚАМ ҚОЛДИРИШ",
        'menu_rate': "⭐ БАҲО БЕРИШ",
        'menu_contact': "📞 АЛОҚА",
        'menu_help': "❓ ЁРДАМ",
        'menu_main': "🏠 АСОСИЙ МЕНЮ",
        'about_text': "🍦✨ *DILBAR OY ICE CREAM* ✨🍦\n\n🌟 *БИЗ КИММИЗ?*\nФақат табиий маҳсулотлардан тайёрланувчи музқаймоқлар бренди.\n\n📞 *АЛОҚА:*\nТелефон: {phone}\nТелеграм: {telegram}",
        'services_text': "🍨✨ *БИЗНИНГ АССОРТИМЕНТ* ✨🍨\n\n👇 *Турини танланг:*",
        'prices_text': "💰✨ *МУЗҚАЙМОҚ НАРХЛАРИ* ✨💰\n\n📞 *БУЮРТМА:* {phone}",
        'contact_text': "📞✨ *АЛОҚА* ✨📞\n\n📱 *ТЕЛЕФОНЛАР:* {phone}",
        'help_text': "❓✨ *ЁРДАМ* ✨❓\n\n📱 *АДМИН:* {phone}",
        'app_start_text': "📝✨ *БУЮРТМА БЕРИШ* ✨📝\n\n👤 *ШУ ФОРМАТДА ЮБОРИНГ:*\nИсм:     [Исмонгиз]\nТелефон: [998 XX YYY YY YY]\nМузқаймоқ тури: [Номи ва сони]\nМанзил: [Манзилингиз]",
        'app_success': "✅ *Буюртмангиз қабул қилинди!*\n\n🆔 *ＩＤ:* {id}\n👤 *Исм:* {name}\n📞 *Телефон:* {phone}\n🍨 *Музқаймоқ:* {service}\n\n⏰ *Оператор 10 дақиқа ичида алоқага чиқади.*",
        'phone_start_text': "📱✨ *РАҚАМИНГИЗНИ ҚОЛДИРИНГ* ✨📱\n\n👇 *ТЕЛЕФОН РАҚАМИНГИЗНИ ЮБОРИНГ:*",
        'phone_success': "✅ *Рақамингиз қабул қилинди!*",
        'rating_start_text': "⭐✨ *БАҲО БЕРИШ* ✨⭐\n\n👇 *1 ДАН 5 ГАЧА БАҲОЛАНГ:*",
        'rating_success': "✅ *Раҳмат! Сиз {rating} юлдузли баҳо бердингиз!*",
        'error_no_phone': "❌ Телефон рақами хато. Қайта юборинг.",
        'service_selected': "🎯 *Танланган тур:* {name}",
        'cancel_btn': "❌ Бекор қилиш",
        'back_btn': "🔙 Орқага",
        'service_website': "🍦 Классик (Пломбир)",
        'service_mobile': "🍓 Мевали музқаймоқ",
        'service_design': "🎂 Музқаймоқли торт",
        'service_seo': "🥤 Милкшейк",
        'service_hosting': "🍨 Идишдаги музқаймоқ",
        'service_other': "✨ Бошқа буюртма",
        'lang_changed': "✅ Тил ўзгартирилди!",
        'menu_lang': "🌐 Тилни танлаш"
    },
    'ru': {
        'select_lang': "🌍 Пожалуйста, выберите язык:",
        'welcome': "🍦✨ **ПРИВЕТСТВУЕМ ВАС, {name} {username}!** 👋✨\n\n🎉 **Добро пожаловать в мир Dilbar Oy Ice Cream!**\nМы рады видеть вас здесь! 🤩 Сегодня прекрасный день для вкусного мороженого.\n\n🚀 **Самое вкусное мороженое только у нас!**\n\n❄️ **Наши преимущества:**\n• 🍨 _Натуральные продукты_\n• ⚡️ _Быстрая доставка_\n• 🤝 _Доступные цены_\n\n👇 **Пожалуйста, выберите раздел:**",
        'menu_about': "ℹ️ О НАС",
        'menu_services': "🍨 АССОРТИМЕНТ",
        'menu_prices': "💰 ЦЕНЫ",
        'menu_apply': "📝 ЗАКАЗАТЬ",
        'menu_phone': "📱 ОСТАВИТЬ НОМЕР",
        'menu_rate': "⭐ ОЦЕНИТЬ",
        'menu_contact': "📞 КОНТАКТЫ",
        'menu_help': "❓ ПОМОЩЬ",
        'menu_main': "🏠 ГЛАВНОЕ МЕНЮ",
        'about_text': "🍦✨ *DILBAR OY ICE CREAM* ✨🍦\n\n🌟 *КТО МЫ?*\nБренд мороженого из натуральных продуктов.\n\n📞 *КОНТАКТЫ:*\nТелефон: {phone}\nTelegram: {telegram}",
        'services_text': "🍨✨ *НАШ АССОРТИМЕНТ* ✨🍨\n\n👇 *Выберите тип:*",
        'prices_text': "💰✨ *ЦЕНЫ НА МОРОЖЕНОЕ* ✨💰\n\n📞 *ЗАКАЗ:* {phone}",
        'contact_text': "📞✨ *СВЯЗЬ* ✨📞\n\n📱 *ТЕЛЕФОН:* {phone}",
        'help_text': "❓✨ *ПОМОЩЬ* ✨❓\n\n📱 *АДМИН:* {phone}",
        'app_start_text': "📝✨ *ОСТАВИТЬ ЗАЯВКУ* ✨📝\n\n👤 *ОТПРАВЬТЕ В ФОРМАТЕ:*\nИмя:     [Ваше имя]\nТелефон: [998 XX YYY YY YY]\nВид мороженого: [Название и количество]\nАдрес: [Ваш адрес]",
        'app_success': "✅ *Ваш заказ принят!*\n\n🆔 *ＩＤ:* {id}\n👤 *Имя:* {name}\n📞 *Телефон:* {phone}\n🍨 *Мороженое:* {service}\n\n⏰ *Оператор свяжется с вами в течение 10 минут.*",
        'phone_start_text': "📱✨ *ОСТАВЬТЕ СВОЙ НОМЕР* ✨📱\n\n👇 *ОТПРАВЬТЕ ВАШ НОМЕР ТЕЛЕФОНА:*",
        'phone_success': "✅ *Ваш номер принят!*",
        'rating_start_text': "⭐✨ *ОЦЕНКА* ✨⭐\n\n👇 *ОЦЕНИТЕ ОТ 1 ДО 5:*",
        'rating_success': "✅ *Вы оставили оценку {rating} звезд! Приятного аппетита! 🍦*",
        'error_no_phone': "❌ Номер телефона не определен. Пожалуйста, отправьте еще раз.",
        'service_selected': "🎯 *Выбранный вид:* {name}",
        'cancel_btn': "❌ Отмена",
        'back_btn': "🔙 Назад",
        'service_website': "🍦 Классическое",
        'service_mobile': "🍓 Фруктовое мороженое",
        'service_design': "🎂 Торт-мороженое",
        'service_seo': "🥤 Милкшейки",
        'service_hosting': "🍨 Мороженое в посуде",
        'service_other': "✨ Другой заказ",
        'lang_changed': "✅ Язык успешно изменен!",
        'menu_lang': "🌐 Изменить язык"
    },
    'en': {
        'select_lang': "🌍 Please select a language:",
        'welcome': "🍦✨ **HELLO, {name} {username}!** 👋✨\n\n🎉 **Welcome to Dilbar Oy Ice Cream!**\nWe are absolutely thrilled to have you here! 🤩 Today is a wonderful day for delicious ice cream.\n\n🚀 **The most delicious ice cream is only with us!**\n\n❄️ **Our Advantages:**\n• 🍨 _Natural Products_\n• ⚡️ _Fast Delivery_\n• 🤝 _Affordable Prices_\n\n👇 **Please, select a section:**",
        'menu_about': "ℹ️ ABOUT US",
        'menu_services': "🍨 ASSORTMENT",
        'menu_prices': "💰 PRICES",
        'menu_apply': "📝 ORDER NOW",
        'menu_phone': "📱 LEAVE PHONE",
        'menu_rate': "⭐ RATE US",
        'menu_contact': "📞 CONTACT",
        'menu_help': "❓ HELP",
        'menu_main': "🏠 MAIN MENU",
        'about_text': "🍦✨ *DILBAR OY ICE CREAM* ✨🍦\n\n🌟 *WHO ARE WE?*\nPremium ice cream brand made from natural ingredients.\n\n📞 *CONTACT:*\nPhone: {phone}\nTelegram: {telegram}",
        'services_text': "🍨✨ *OUR ASSORTMENT* ✨🍨\n\n👇 *Select type:*",
        'prices_text': "💰✨ *ICE CREAM PRICES* ✨💰\n\n📞 *ORDER:* {phone}",
        'contact_text': "📞✨ *CONTACT* ✨📞\n\n📱 *PHONE:* {phone}",
        'help_text': "❓✨ *HELP* ✨❓\n\n📱 *ADMIN:* {phone}",
        'app_start_text': "📝✨ *LEAVE APPLICATION* ✨📝\n\n👤 *SEND IN FORMAT:*\nName:    [Your name]\nPhone:   [998 XX YYY YY YY]\nIce Cream: [Type and quantity]\nAddress: [Your address]",
        'app_success': "✅ *Your order has been accepted!*\n\n🆔 *ＩＤ:* {id}\n👤 *Name:* {name}\n📞 *Phone:* {phone}\n🍨 *Ice Cream:* {service}\n\n⏰ *Operator will contact you within 10 minutes.*",
        'phone_start_text': "📱✨ *LEAVE YOUR PHONE NUMBER* ✨📱\n\n👇 *SEND YOUR PHONE NUMBER:*",
        'phone_success': "✅ *Your number has been accepted!*",
        'rating_start_text': "⭐✨ *RATE US* ✨⭐\n\n👇 *RATE FROM 1 TO 5:*",
        'rating_success': "✅ *You gave a {rating}-star rating! Bon appetit! 🍦*",
        'error_no_phone': "❌ Phone number not detected. Please send again.",
        'service_selected': "🎯 *Selected type:* {name}",
        'cancel_btn': "❌ Cancel",
        'back_btn': "🔙 Back",
        'service_website': "🍦 Classic",
        'service_mobile': "🍓 Fruit Ice Cream",
        'service_design': "🎂 Ice Cream Cake",
        'service_seo': "🥤 Milkshakes",
        'service_hosting': "🍨 Ice cream in dishes",
        'service_other': "✨ Other order",
        'lang_changed': "✅ Language successfully changed!",
        'menu_lang': "🌐 Change Language"
    }
}

def t(key, lang, **kwargs):
    """Tarjima yordamchisi"""
    if not lang:
        lang = 'uz_lat'
    
    text = TRANSLATIONS.get(lang, TRANSLATIONS['uz_lat']).get(key, TRANSLATIONS['uz_lat'].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except:
            return text
    return text

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
    
    def set_user_lang(self, user_id: int, lang: str):
        """Foydalanuvchi tilini saqlash"""
        if "users" not in self.data:
            self.data["users"] = {}
        
        user_id_str = str(user_id)
        if user_id_str not in self.data["users"]:
            self.data["users"][user_id_str] = {}
            
        self.data["users"][user_id_str]["lang"] = lang
        self.save_data()

    def get_user_lang(self, user_id: int):
        """Foydalanuvchi tilini olish"""
        if "users" not in self.data:
            return None
        return self.data.get("users", {}).get(str(user_id), {}).get("lang")
    
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
            "status": "new",
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
def get_language_keyboard():
    """Tilni tanlash uchun inline keyboard"""
    keyboard = [
        [InlineKeyboardButton("🇺🇿 O'zbek (Lotin)", callback_data="set_lang_uz_lat")],
        [InlineKeyboardButton("🇺🇿 Ўзбек (Кирилл)", callback_data="set_lang_uz_cyr")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="set_lang_en")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu(is_admin: bool = False, lang: str = 'uz_lat'):
    """Asosiy menyu"""
    if is_admin:
        buttons = [
            ["📊 STATISTIKA", "📋 BUYURTMALAR"],
            ["📅 BUGUNGI", "📞 KONTAKTLAR"],
            ["🏠 ASOSIY MENYU"]
        ]
    else:
        buttons = [
            [t('menu_about', lang), t('menu_services', lang)],
            [t('menu_prices', lang), t('menu_apply', lang)],
            [t('menu_phone', lang), t('menu_rate', lang)],
            [t('menu_contact', lang), t('menu_help', lang)],
            [t('menu_lang', lang)]
        ]
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_admin_applications_menu():
    """Admin arizalar menyusi"""
    keyboard = [
        [InlineKeyboardButton("🆕 Yangi buyurtmalar", callback_data="admin_apps_new")],
        [InlineKeyboardButton("⏳ Jarayonda", callback_data="admin_apps_process")],
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
            InlineKeyboardButton("✅ Bajarildi", callback_data=f"admin_app_complete_{app_id}"),
            InlineKeyboardButton("⏳ Jarayonda", callback_data=f"admin_app_process_{app_id}")
        ],
        [
            InlineKeyboardButton("❌ Bekor qilish", callback_data=f"admin_app_cancel_{app_id}"),
            InlineKeyboardButton("📞 Bog'lanish", callback_data=f"admin_app_contact_{app_id}")
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
    chat_id = update.effective_chat.id
    
    lang = db.get_user_lang(user_id)
    
    if not lang:
        await context.bot.send_message(
            chat_id=chat_id,
            text=t('select_lang', 'uz_lat'),
            reply_markup=get_language_keyboard()
        )
        return

    # Usernameni aniqlash (agar bo'lsa @ bilan, bo'lmasa bo'sh)
    username = f"(@{user.username})" if user.username else ""
    
    welcome_message = t('welcome', lang, name=user.first_name, username=username)
    
    # Admin tekshiruvi
    is_admin = user_id in ADMIN_IDS
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu(is_admin, lang)
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Biz haqimizda"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    about_text = t('about_text', lang, phone=ADMIN_PHONE, telegram=ADMIN_TELEGRAM)
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xizmatlar"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    services_text = t('services_text', lang)
    
    # Custom keyboard for services with translations
    buttons = [
        [InlineKeyboardButton(t('service_website', lang), callback_data="service_website")],
        [InlineKeyboardButton(t('service_mobile', lang), callback_data="service_mobile")],
        [InlineKeyboardButton(t('service_design', lang), callback_data="service_design")],
        [InlineKeyboardButton(t('service_seo', lang), callback_data="service_seo")],
        [InlineKeyboardButton(t('service_hosting', lang), callback_data="service_hosting")],
        [InlineKeyboardButton(t('service_other', lang), callback_data="service_other")]
    ]
    
    await update.message.reply_text(
        services_text, 
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Narxlar"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    prices_text = t('prices_text', lang, phone=ADMIN_PHONE)
    await update.message.reply_text(prices_text, parse_mode='Markdown')

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Aloqa"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    contact_text = t('contact_text', lang, phone=ADMIN_PHONE, telegram=ADMIN_TELEGRAM)
    await update.message.reply_text(contact_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    help_text = t('help_text', lang, phone=ADMIN_PHONE, telegram=ADMIN_TELEGRAM)
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ==================== APPLICATION FUNCTIONS ====================
async def start_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ariza boshlash"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    application_text = t('app_start_text', lang)
    await update.message.reply_text(application_text, parse_mode='Markdown')
    context.user_data['awaiting_application'] = True

async def handle_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ariza ma'lumotlarini qayta ishlash"""
    if not context.user_data.get('awaiting_application'):
        return
    
    user = update.effective_user
    text = update.message.text
    lang = db.get_user_lang(user.id) or 'uz_lat'
    
    # Ma'lumotlarni ajratish
    name = user.first_name or "Noma'lum"
    phone = ""
    service = "Noma'lum"
    address = "Noma'lum"
    
    lines = text.split('\n')
    for line in lines:
        if ':' in line:
            parts = line.split(':', 1)
            key = parts[0].strip().lower()
            value = parts[1].strip()
            
            if any(k in key for k in ['ism', 'name', 'исм']):
                name = value
            elif any(k in key for k in ['tel', 'phone', 'тел']):
                phone = value
            elif any(k in key for k in ['xizmat', 'service', 'хизмат', 'услуга', 'turi', 'muzqaymoq']):
                service = value
            elif any(k in key for k in ['manzil', 'address', 'manzil']):
                address = value
    
    # Raqamni topish (agar parsingda topilmagan bo'lsa)
    if not phone:
        numbers = re.findall(r'[\+\d\s\-\(\)]{10,}', text)
        if numbers:
            phone = numbers[0]
        elif text.replace('+', '').replace(' ', '').isdigit():
            phone = text
    
    # Muzqaymoq turini tekshirish (fallback)
    if service == "Noma'lum":
        # Agar xizmat nomi topilmagan bo'lsa, xabarning birinchi qismini olamiz
        service = text.split('\n')[0][:30] + ("..." if len(text.split('\n')[0]) > 30 else "")
    
    if not phone:
        await update.message.reply_text(t('error_no_phone', lang))
        return
    
    # Ma'lumotlarni birlashtirish (service + address agar bo'lsa)
    full_service_info = service
    if address != "Noma'lum":
        full_service_info += f" | Manzil: {address}"
    
    # Saqlash
    app = db.add_application(user.id, name, phone, full_service_info, text)
    
    # Foydalanuvchiga javob
    await update.message.reply_text(
        t('app_success', lang, id=app['id'], name=name, phone=phone, service=service, admin_phone=ADMIN_PHONE),
        parse_mode='Markdown',
        reply_markup=get_main_menu(lang=lang)
    )
    
    # Adminlarga xabar
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📥 *YANGI BUYURTMA #{app['id']}*\n\n"
                     f"👤 *Ism:* {name}\n"
                     f"📞 *Telefon:* {phone}\n"
                     f"🍨 *Buyurtma:* {service}\n"
                     f"📍 *Manzil:* {address}\n\n"
                     f"📝 *To'liq xabar:*\n{text}\n\n"
                     f"📅 *Vaqt:* {app['date']}\n"
                     f"🆔 *User ID:* {user.id}\n"
                     f"🌐 *Til:* {lang}",
                parse_mode='Markdown'
            )
        except:
            pass
    
    context.user_data.pop('awaiting_application', None)

# ==================== PHONE CONTACT FUNCTIONS ====================
async def start_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon qoldirish"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    phone_text = t('phone_start_text', lang)
    await update.message.reply_text(phone_text, parse_mode='Markdown')
    context.user_data['awaiting_phone'] = True

async def handle_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telefon kontaktini qayta ishlash"""
    if not context.user_data.get('awaiting_phone'):
        return
    
    user = update.effective_user
    text = update.message.text
    lang = db.get_user_lang(user.id) or 'uz_lat'
    
    # Telefon raqamini topish
    phone = ""
    numbers = re.findall(r'[\+\d\s\-\(\)]{10,}', text)
    if numbers:
        phone = numbers[0]
    elif text.replace('+', '').replace(' ', '').isdigit():
        phone = text
    
    if not phone:
        await update.message.reply_text(t('error_no_phone', lang))
        return
    
    name = user.first_name or "Noma'lum"
    
    # Saqlash
    contact = db.add_contact(user.id, name, phone, text)
    
    # Foydalanuvchiga javob
    await update.message.reply_text(
        t('phone_success', lang, name=name, phone=phone, admin_phone=ADMIN_PHONE),
        parse_mode='Markdown',
        reply_markup=get_main_menu(lang=lang)
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
                     f"🆔 *User ID:* {user.id}\n"
                     f"🌐 *Til:* {lang}",
                parse_mode='Markdown'
            )
        except:
            pass
    
    context.user_data.pop('awaiting_phone', None)

# ==================== RATING FUNCTIONS ====================
async def start_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baho berishni boshlash"""
    lang = db.get_user_lang(update.effective_user.id) or 'uz_lat'
    rating_text = t('rating_start_text', lang)
    
    # Custom rating keyboard with translations
    keyboard = []
    for i in range(1, 6):
        stars = "⭐" * i
        keyboard.append([InlineKeyboardButton(f"{stars} ({i}/5)", callback_data=f"rate_{i}")])
    
    keyboard.append([InlineKeyboardButton(t('cancel_btn', lang), callback_data="cancel_rate")])
    
    await update.message.reply_text(
        rating_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baho berish callback"""
    query = update.callback_query
    await query.answer()
    user = query.from_user
    lang = db.get_user_lang(user.id) or 'uz_lat'
    
    if query.data == "cancel_rate":
        await query.edit_message_text(
            f"❌ *{t('cancel_btn', lang)}*."
        )
        return
    
    if query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])
        
        # Bahoni saqlash
        db.add_rating(user.id, rating)
        
        # Bahoga javob
        stars = "⭐" * rating
        empty_stars = "☆" * (5 - rating)
        
        await query.edit_message_text(
            f"{stars}{empty_stars}\n\n"
            f"{t('rating_success', lang, rating=rating, phone=ADMIN_PHONE)}",
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
            "new": "🆕",
            "process": "⏳",
            "completed": "✅",
            "cancelled": "❌"
        }.get(app.get("status", "new"), "🍦")
        
        text += f"""
{status_emoji} *#{app['id']}* - {app['name']}
📞 {app['phone']}
🍨 {app['service']}
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
        "new": "🆕",
        "process": "⏳",
        "completed": "✅",
        "cancelled": "❌"
    }.get(app.get("status", "new"), "🍦")
    
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
                f.write("DILBAR OY ICE CREAM STATISTIKASI\n")
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
                    f.write("DILBAR OY ICE CREAM STATISTIKASI\n")
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
    user = query.from_user
    
    # Tilni sozlash
    if data.startswith("set_lang_"):
        lang_code = data.replace("set_lang_", "")
        db.set_user_lang(user.id, lang_code)
        
        try:
            await query.message.delete()
        except:
            pass
        
        # Start command xabarini yuborish
        await start_command(update, context)
        return

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
        
        elif data.startswith("admin_app_complete_"):
            app_id = int(data.split("_")[3])
            db.update_application_status(app_id, "completed")
            await query.edit_message_text(
                f"✅ Buyurtma #{app_id} bajarildi deb belgilandi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("admin_app_process_"):
            app_id = int(data.split("_")[3])
            db.update_application_status(app_id, "process")
            await query.edit_message_text(
                f"⏳ Buyurtma #{app_id} jarayonda deb belgilandi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("admin_app_cancel_"):
            app_id = int(data.split("_")[3])
            db.update_application_status(app_id, "cancelled")
            await query.edit_message_text(
                f"❌ Buyurtma #{app_id} bekor qilindi!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
            )
        
        elif data.startswith("admin_app_contact_"):
            app_id = int(data.split("_")[3])
            apps = db.get_all_applications()
            app = next((a for a in apps if a["id"] == app_id), None)
            if app:
                await query.edit_message_text(
                    f"📞 *QO'NG'IROQ QILISH:*\n\n"
                    f"👤 Mijoz: {app['name']}\n"
                    f"📞 Telefon: {app['phone']}\n\n"
                    f"💬 Buyurtma: {app['service']}",
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data=f"admin_app_detail_{app_id}")]])
                )
    
    # Export callback lar
    elif data.startswith("export_"):
        export_type = data.split("_")[1]
        await admin_export_data(update, context, export_type)
    
    # User rating callback
    elif data.startswith("rate_"):
        await handle_rating_callback(update, context)
    
    elif data.startswith("service_"):
        user_lang = db.get_user_lang(user.id) or 'uz_lat'
        service_names = {
            "website": t('service_website', user_lang),
            "mobile": t('service_mobile', user_lang),
            "design": t('service_design', user_lang),
            "seo": t('service_seo', user_lang),
            "hosting": t('service_hosting', user_lang),
            "other": t('service_other', user_lang)
        }
        service_type = data.split("_")[1]
        name = service_names.get(service_type, "Noma'lum xizmat")
        
        await query.message.reply_text(
            t('service_selected', user_lang, name=name),
            parse_mode='Markdown',
            reply_markup=get_main_menu(lang=user_lang)
        )
        # Arizani boshlash
        await start_application(update, context)

    elif data == "cancel_rate":
        user_lang = db.get_user_lang(user.id) or 'uz_lat'
        await query.edit_message_text(
            f"❌ *{t('cancel_btn', user_lang)}*"
        )

# ==================== MESSAGE HANDLER ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xabarlarni qayta ishlash"""
    user = update.effective_user
    text = update.message.text
    lang = db.get_user_lang(user.id) or 'uz_lat'
    
    # Admin bo'lsa (admin panel tugmalari o'zgarmaydi)
    if user.id in ADMIN_IDS:
        if text == "📊 STATISTIKA":
            await admin_stats(update, context)
            return
        elif text == "📋 BUYURTMALAR" or text == "📋 ARIZALAR":
            await admin_applications(update, context)
            return
        elif text == "📅 BUGUNGI":
            await admin_today_apps(update, context)
            return
        elif text == "📞 KONTAKTLAR":
            await admin_contacts(update, context)
            return
        elif text == "⭐ BAHOLAR":
            await admin_ratings(update, context)
            return
        elif text == "📤 EXPORT":
            await admin_export(update, context)
            return
        elif text == "⚙️ SOZLAMALAR":
            await admin_settings(update, context)
            return
        elif text == "🏠 ASOSIY MENYU":
            await start_command(update, context)
            return

    # User tugmalarini tekshirish (barcha tillarda)
    def check_btn(key):
        for l in TRANSLATIONS:
            if TRANSLATIONS[l].get(key) == text:
                return True
        return False

    if check_btn('menu_about'):
        await about_command(update, context)
    elif check_btn('menu_services'):
        await services_command(update, context)
    elif check_btn('menu_prices'):
        await prices_command(update, context)
    elif check_btn('menu_apply'):
        await start_application(update, context)
    elif check_btn('menu_phone'):
        await start_phone_contact(update, context)
    elif check_btn('menu_rate'):
        await start_rating(update, context)
    elif check_btn('menu_contact'):
        await contact_command(update, context)
    elif check_btn('menu_help'):
        await help_command(update, context)
    elif check_btn('menu_main'):
        await start_command(update, context)
    elif check_btn('menu_lang'):
        await update.message.reply_text(
            t('select_lang', lang),
            reply_markup=get_language_keyboard()
        )
    else:
        # Agar ariza yoki telefon kutilayotgan bo'lsa
        if context.user_data.get('awaiting_application'):
            await handle_application(update, context)
        elif context.user_data.get('awaiting_phone'):
            await handle_phone_contact(update, context)
        else:
            # Boshqa har qanday xabar uchun
            await update.message.reply_text(
                "🤖 *...*\n\n"
                f"{t('menu_help', lang)}: {ADMIN_PHONE}",
                parse_mode='Markdown',
                reply_markup=get_main_menu(lang=lang)

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
    
    # Event loop-ni sozlash (Render/Python 3.10+ uchun muhim)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Botni ishga tushirish
    # drop_pending_updates=True eski xabarlarni o'chirib yuboradi
    try:
        app.run_polling(drop_pending_updates=True, close_loop=False)
    except Exception as e:
        logger.error(f"BOT TO'XTAB QOLDI! Xatolik: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()