@echo off
title Push MedHelper to GitHub
cd /d "%~dp0"
echo ===================================================
echo     جاري رفع مشروع MedHelper إلى GitHub
echo ===================================================
echo سيتم الآن إرسال الملفات إلى مستودعك...
echo (إذا ظهرت لك نافذة تسجيل الدخول إلى GitHub اضغط Sign in with your browser)
echo.
git push -u origin main
echo.
echo ===================================================
echo اضغط أي زر للإغلاق...
pause
