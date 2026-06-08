# TBHPrice

A lightweight Steam Market price checker for **The Harvest Brigade (THB)** — a game whose market has permanently closed. All 737 items are archived locally so prices are always available, even without internet.

## Features

- **Instant search** — type any item name, results appear in real time
- **F10 hotkey** — open the search popup from anywhere without switching windows
- **Rarity colors** — item names are color-coded by rarity (Legendary, Arcana, Immortal, etc.)
- **Multi-variant support** — shows price range when an item has multiple variants
- **Auto-update** — checks GitHub for a newer version and updates itself in one click
- **TR / EN language toggle** — switch the UI language at any time
- **Offline archive** — falls back to the bundled archive if Steam is unreachable

## Download

Grab the latest **TBHFiyat.exe** from the [Releases](../../releases/latest) page. No installation needed — just run it.

## Usage

1. Launch `TBHFiyat.exe`
2. Press **F10** or click **Search Price** to open the search popup
3. Start typing an item name — results filter instantly
4. Click any item to open its Steam Market listing in your browser
5. Click **Refresh Prices** to fetch the latest prices from Steam
6. Click **Update** to check for a new version of the app

## How prices work

Prices are fetched from the Steam Community Market API. On first launch (or after the 2-hour cache expires) the app pulls all listings from Steam. If Steam is unavailable, it falls back to the bundled archive (`market_arsiv.json`) which contains all 737 THB items captured before the market closed.

## Building from source

Requirements: Python 3.10+, pip

```
pip install requests keyboard pywin32 pyinstaller
pyinstaller --onefile --windowed --name "TBHFiyat" ^
    --hidden-import=win32api ^
    --hidden-import=win32gui ^
    --hidden-import=keyboard ^
    --version-file=version_info.txt ^
    fiyat_bak.py
```

## Auto-update flow

When a new release is published on this repo, clicking **Update** will:
1. Download the new `TBHFiyat.exe` from the release assets
2. Replace the current executable after the app closes
3. Restart automatically
