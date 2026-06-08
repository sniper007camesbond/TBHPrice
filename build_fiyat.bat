@echo off
echo TBH Fiyat Bakici derleniyor...
pip install pyinstaller >nul 2>&1
pyinstaller --onefile --windowed --name "TBHFiyat" ^
    --hidden-import=win32api ^
    --hidden-import=win32gui ^
    --hidden-import=keyboard ^
    fiyat_bak.py
echo.
echo EXE olusturuldu: dist\TBHFiyat.exe
pause
