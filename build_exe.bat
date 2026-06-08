@echo off
pip install pyinstaller >nul 2>&1
pyinstaller --onefile --windowed --name "TaskBarHeroBot" taskbar_hero_bot.py
echo.
echo EXE olusturuldu: dist\TaskBarHeroBot.exe
pause
