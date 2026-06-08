@echo off
echo TBH Fiyat Bakici derleniyor...
pip install pyinstaller >nul 2>&1
pyinstaller --onedir --windowed --name "TBHFiyat" ^
    --hidden-import=win32api ^
    --hidden-import=win32gui ^
    --version-file=version_info.txt ^
    fiyat_bak.py
echo.
echo EXE olusturuldu: dist\TBHFiyat.exe
pause
