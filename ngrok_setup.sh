#!/bin/bash
# Ngrok authtoken o'rnatish script'i

echo "🔐 Ngrok Authtoken Setup"
echo "========================"
echo ""
echo "1. https://dashboard.ngrok.com/signup ga boring"
echo "2. Ro'yxatdan o'ting (email tasdiqlash kerak)"
echo "3. https://dashboard.ngrok.com/get-started/your-authtoken dan authtoken oling"
echo ""
echo "Authtoken'ni olganingizdan so'ng, quyidagi buyruqni ishga tushiring:"
echo ""
echo "ngrok config add-authtoken YOUR_TOKEN_HERE"
echo ""
echo "Keyin webhook'ni sozlash uchun:"
echo "ngrok http 8000"
echo ""
echo "Va yangi terminalni ochib webhook setup script'ini ishga tushiring."
