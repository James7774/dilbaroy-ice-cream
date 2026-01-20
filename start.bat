@echo off
chcp 65001 > nul
title Nova.X Telegram Bot
echo ========================================
echo    NOVA.X TELEGRAM BOT - ISHGA TUSHIRISH
echo ========================================
echo.

:: Virtual environmentni tekshirish
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment yaratilmoqda...
    python -m venv venv
)

:: Virtual environmentni yoqish
call venv\Scripts\activate.bat

:: Kutubxonalarni o'rnatish
echo Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt --quiet

:: Botni ishga tushirish
echo.
echo ========================================
echo    BOT ISHGA TUSHMOQDA...
echo ========================================
echo.
python main.py

:: Agar xato bo'lsa
if errorlevel 1 (
    echo.
    echo ========================================
    echo    XATO! QUYIDAGILARNI TEKSHIRING:
    echo ========================================
    echo 1. Python 3.13 o'rnatilganligi
    echo 2. Internet aloqasi
    echo 3. Bot tokeni to'g'riligi
    echo.
    pause
)