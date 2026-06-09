# TBHPrice

A lightweight Steam Market price checker for **The Harvest Brigade (THB)** — a game whose market has permanently closed. All 737 items are archived locally so prices are always available, even without internet.

## Features

- **Instant search** — type any item name, results appear in real time
- **F10 hotkey** — open the search popup from anywhere without switching windows
- **Rarity colors** — item names are color-coded by rarity (Legendary, Arcana, Immortal, etc.)
- **Multi-variant support** — shows price range when an item has multiple variants
- **TR / EN language toggle** — switch the UI language at any time
- **Offline archive** — falls back to the bundled archive if Steam is unreachable

## Download

Grab the latest **TBHFiyat.zip** from the [Releases](../../releases/latest) page. Extract the folder and run `TBHFiyat.exe`. No installation needed.

## Usage

1. Launch `TBHFiyat.exe`
2. Press **F10** or click **Search Price** to open the search popup
3. Start typing an item name — results filter instantly
4. Click any item to open its Steam Market listing in your browser
5. Click **Refresh Prices** to fetch the latest prices from Steam
6. Click **Update** to open the releases page and download the latest version

## How prices work

Prices are fetched from the Steam Community Market API. On first launch (or after the 2-hour cache expires) the app pulls all listings from Steam. If Steam is unavailable, it falls back to the bundled archive (`market_arsiv.json`) which contains all 737 THB items captured before the market closed.

## Building from source

Requirements: Python 3.10+, pip

```
pip install requests pyinstaller
pyinstaller --onedir --windowed --name "TBHFiyat" --version-file=version_info.txt -y fiyat_bak.py
```
