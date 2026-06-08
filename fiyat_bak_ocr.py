# -*- coding: utf-8 -*-
"""
TBH Fiyat Bakici - OCR Surumu
F10 → fare uzerindeki tooltip alanini Windows OCR ile okur
→ item adini otomatik bulur → fiyat popup gosterir.
"""
import requests, os, json, time, webbrowser
import tkinter as tk
from tkinter import ttk
import threading
import keyboard
import mss
import win32api, win32gui
import numpy as np
import cv2
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

APP_ID    = 3678970
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "market_ocr.json")
HEADERS   = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CACHE_TTL = 1800

R = {
    "bg":      "#130b05",
    "panel":   "#1e1008",
    "border":  "#86725e",
    "baslik":  "#f0d888",
    "yesil":   "#6abf40",
    "kirmizi": "#c84020",
    "muted":   "#8e97aa",
    "text":    "#d0bfad",
    "btn":     "#2a1508",
    "sec":     "#3a2010",
}

# ── Market verisi ──────────────────────────────
def fetch_market():
    status("Market verileri aliniyor...")
    set_progress(-1)
    all_items, start, total = [], 0, None
    while total is None or start < total:
        try:
            r = requests.get(
                "https://steamcommunity.com/market/search/render/",
                params={"appid": APP_ID, "norender": 1, "count": 100, "start": start,
                        "sort_column": "popular", "sort_dir": "desc"},
                headers=HEADERS, timeout=20
            )
            data = r.json()
        except Exception as e:
            status(f"Hata: {e}"); break
        results = data.get("results", [])
        if not results: break
        for it in results:
            desc = it.get("asset_description", {})
            all_items.append({
                "name":       it.get("name", ""),
                "hash_name":  it.get("hash_name", ""),
                "price":      it.get("sell_price", 0) / 100,
                "price_text": it.get("sell_price_text", "—"),
                "listings":   it.get("sell_listings", 0),
            })
        total = data.get("total_count", 0)
        start += len(results)
        time.sleep(0.3)

    grouped = {}
    for it in all_items:
        grouped.setdefault(it["name"], []).append(it)
    for n in grouped:
        grouped[n].sort(key=lambda x: x["price"])

    set_progress(0, 1)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": time.time(), "grouped": grouped}, f, ensure_ascii=False)
    status(f"{len(grouped)} item kaydedildi.")
    return grouped

def load_market():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("updated", 0) < CACHE_TTL:
            return c["grouped"]
    return fetch_market()

# ── Windows OCR (PowerShell subprocess) ────────
def ocr_image(bgr_img):
    """Tesseract OCR ile goruntuden metin cek."""
    # Onislem: kontrast artir, buyut
    gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
    pil_img = Image.fromarray(thresh)
    try:
        text = pytesseract.image_to_string(
            pil_img,
            lang="eng",
            config="--psm 6 --oem 3"
        )
        return text
    except Exception as e:
        print(f"OCR hatasi: {e}")
        return ""

# ── Pencere & yakalama ─────────────────────────
def tbh_hwnd():
    found = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == "TaskBarHero":
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            w, h = r - l, b - t
            if w > 200 and h > 200:
                found.append((hwnd, l, t, w, h))
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def grab_stash_tooltip(scale=2):
    """
    Cursor etrafindaki tooltip alanini yakala.
    X: oyun penceresinin sol kenari (tooltip burada baslar).
    Y: cursor pozisyonuna gore (browser sekmeleri yakalanmaz).
    Genislik sabit dar (190px) — sag comparison panel haric.
    """
    info = tbh_hwnd()
    cx, cy = win32api.GetCursorPos()
    sx = win32api.GetSystemMetrics(0)
    sy = win32api.GetSystemMetrics(1)

    if info:
        _, l, t, w, h = info
        cap_l = max(l, 0)
    else:
        cap_l = max(cx - 60, 0)

    cap_w = 190          # sol panel genisligi — comparison panel bu alana girmez
    cap_t = max(cy - 130, 0)   # cursor'in 130px ustusse bas, tooltip burada
    cap_h = 210          # cursor ustunden 130 + altindan 80

    if cap_l + cap_w > sx: cap_l = max(sx - cap_w, 0)
    if cap_t + cap_h > sy: cap_t = max(sy - cap_h, 0)

    with mss.MSS() as sct:
        region = {"top": cap_t, "left": cap_l, "width": cap_w, "height": cap_h}
        img = np.array(sct.grab(region))

    bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    big = cv2.resize(bgr, (bgr.shape[1] * scale, bgr.shape[0] * scale),
                     interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(os.path.join(BASE_DIR, "debug_ocr.png"), big)
    # Tam yakalama referans icin (comparison panel dahil)
    cv2.imwrite(os.path.join(BASE_DIR, "debug_capture.png"), bgr)
    return big, cx, cy

# ── Item adi eslesme ───────────────────────────
_GRADE_WORDS = {
    # Sadece oyun-ici kalite kelimeleri — market tier kelimeleri (Legendary, Beyond vb.) dahil degil
    "grade", "quality", "attack", "damage", "per", "second",
    "stats", "inherent", "slot", "engraving", "decoration",
    "requires", "lv", "ranged", "only", "auto", "inventory",
}

def _clean(text):
    """Grade/tier kelimelerini ve parantezleri temizle, kucuk harfe cevir."""
    import re
    text = re.sub(r"\([^)]*\)", " ", text)   # parantez ici kaldir
    words = [w.lower().strip(".,!?;:") for w in text.split()]
    return " ".join(w for w in words if w and w not in _GRADE_WORDS)

def best_match(ocr_text, grouped):
    """
    OCR metninden market item adini bul.
    Oncelik: tam alt-dizi eslesmesi (uzun eslesme kazanir).
    Yedek: kelime kesisimi.
    """
    if not ocr_text:
        return None, 0

    ocr_clean = _clean(ocr_text)

    best_name  = None
    best_score = 0.0

    for name in grouped:
        name_clean = _clean(name)
        if not name_clean:
            continue

        # Tam alt-dizi var mi? Uzun = daha spesifik = daha iyi
        if name_clean in ocr_clean:
            score = 10.0 + len(name_clean) * 0.1  # uzunluk bonusu
        else:
            # Kelime kesisimi
            name_words = set(name_clean.split())
            ocr_words  = set(ocr_clean.split())
            matched    = len(name_words & ocr_words)
            if matched == 0:
                continue
            # Tum kelimeleri eslesti mi?
            coverage = matched / len(name_words)
            score    = matched + coverage * 2.0

        if score > best_score:
            best_score = score
            best_name  = name

    return best_name, best_score

# ── Fiyat popup ────────────────────────────────
_popup_win  = None
_popup_lock = threading.Lock()

def fmt_price(p): return f"{p:.2f} TL" if p else "—"
def steam_url(h):
    return f"https://steamcommunity.com/market/listings/{APP_ID}/{requests.utils.quote(h)}"
def steam_search_url(n):
    return f"https://steamcommunity.com/market/search?appid={APP_ID}&q={requests.utils.quote(n)}"

def show_price_popup(name, grouped, ocr_text, cx, cy):
    global _popup_win
    with _popup_lock:
        if _popup_win:
            try: _popup_win.destroy()
            except: pass
            _popup_win = None

        w = tk.Toplevel(_root)
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        w.configure(bg=R["border"])

        inner = tk.Frame(w, bg=R["bg"], padx=12, pady=10)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        if name and name in grouped:
            variants  = grouped[name]
            prices    = [v["price"] for v in variants if v["price"] > 0]
            p_min     = min(prices) if prices else 0
            p_max     = max(prices) if prices else 0
            n_var     = len(variants)
            listings  = sum(v["listings"] for v in variants)

            tk.Label(inner, text=name, bg=R["bg"], fg=R["baslik"],
                     font=("Segoe UI", 10, "bold"), anchor="w",
                     wraplength=260).pack(fill="x")

            if n_var == 1:
                pt = variants[0].get("price_text", fmt_price(p_min))
                tk.Label(inner, text=pt, bg=R["bg"], fg=R["yesil"],
                         font=("Segoe UI", 18, "bold"), anchor="w").pack(fill="x", pady=(2,0))
            else:
                tk.Label(inner, text=f"{fmt_price(p_min)}  —  {fmt_price(p_max)}",
                         bg=R["bg"], fg=R["yesil"],
                         font=("Segoe UI", 15, "bold"), anchor="w").pack(fill="x", pady=(2,0))
                tk.Label(inner, text=f"{n_var} varyant  •  {listings:,} satista",
                         bg=R["bg"], fg=R["muted"],
                         font=("Segoe UI", 8), anchor="w").pack(fill="x")

            def open_it(vs=variants, n=name):
                if len(vs) == 1: webbrowser.open(steam_url(vs[0]["hash_name"]))
                else:            webbrowser.open(steam_search_url(n))

            tk.Button(inner, text="Steam'de Goster", bg=R["btn"], fg=R["text"],
                      relief="flat", font=("Segoe UI", 8), padx=6,
                      command=open_it).pack(anchor="w", pady=(6,0))
        else:
            tk.Label(inner, text="Item bulunamadi", bg=R["bg"], fg=R["kirmizi"],
                     font=("Segoe UI", 10, "bold")).pack()
            if ocr_text.strip():
                preview = ocr_text.strip()[:80]
                tk.Label(inner, text=f"OCR: {preview}", bg=R["bg"], fg=R["muted"],
                         font=("Segoe UI", 7), wraplength=250).pack()

        w.update_idletasks()
        pw, ph = w.winfo_reqwidth(), w.winfo_reqheight()
        sx, sy = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
        wx = min(cx + 18, sx - pw - 5)
        wy = cy - ph - 12
        if wy < 0: wy = cy + 25
        w.geometry(f"+{wx}+{wy}")

        _popup_win = w
        w.after(6000, lambda: _close_popup(w))

def _close_popup(w):
    global _popup_win
    with _popup_lock:
        if _popup_win is w: _popup_win = None
        try: w.destroy()
        except: pass

# ── Durum / progress ───────────────────────────
_status_label = None
_progress_bar = None
_progress_max = [1]

def status(msg):
    print(msg)
    if _status_label:
        try: _status_label.config(text=msg); _status_label.update_idletasks()
        except: pass

def set_progress(val, maxv=None):
    if not _progress_bar: return
    try:
        if val < 0:
            _progress_bar.config(mode="indeterminate"); _progress_bar.start(15)
        else:
            _progress_bar.stop(); _progress_bar.config(mode="determinate")
            if maxv: _progress_max[0] = maxv
            _progress_bar["value"] = int(val / max(_progress_max[0], 1) * 100)
            _progress_bar.update_idletasks()
    except: pass

# ── Hotkey ────────────────────────────────────
_root    = None
_grouped = {}

def on_f10():
    # Eski popup'i hemen kapat, "Okunuyor..." goster
    if _root:
        _root.after(0, _close_current_and_show_loading)
    def run():
        status("Ekran okunuyor...")
        img, cx, cy = grab_stash_tooltip(scale=2)
        ocr_text = ocr_image(img)
        print(f"OCR: {repr(ocr_text[:120])}")
        name, score = best_match(ocr_text, _grouped)
        print(f"Eslesen: {name!r}  skor: {score}")
        if _root:
            _root.after(0, lambda: show_price_popup(name, _grouped, ocr_text, cx, cy))
        status("Hazir! F10 ile fiyat sor.")
    threading.Thread(target=run, daemon=True).start()

def _close_current_and_show_loading():
    global _popup_win
    with _popup_lock:
        if _popup_win:
            try: _popup_win.destroy()
            except: pass
            _popup_win = None
    # Kucuk "Okunuyor..." gostergesi
    cx, cy = win32api.GetCursorPos()
    w = tk.Toplevel(_root)
    w.overrideredirect(True)
    w.attributes("-topmost", True)
    w.configure(bg=R["border"])
    tk.Label(w, text="  Okunuyor...  ", bg=R["bg"], fg=R["muted"],
             font=("Segoe UI", 9), padx=10, pady=6).pack(padx=1, pady=1)
    w.update_idletasks()
    sx, sy = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    wx = min(cx + 18, sx - w.winfo_reqwidth() - 5)
    wy = min(cy + 18, sy - w.winfo_reqheight() - 5)
    w.geometry(f"+{wx}+{wy}")
    with _popup_lock:
        _popup_win = w

# ── Ana pencere ────────────────────────────────
_ready_frame   = None
_loading_frame = None

def build_window():
    global _root, _status_label, _progress_bar, _ready_frame, _loading_frame
    root = tk.Tk()
    root.title("TBH Fiyat OCR")
    root.configure(bg=R["bg"])
    root.resizable(False, False)
    root.attributes("-topmost", True)

    tk.Label(root, text="TBH FIYAT (OCR)", bg=R["bg"], fg=R["baslik"],
             font=("Segoe UI", 12, "bold"), padx=20, pady=10).pack(fill="x")

    lf = tk.Frame(root, bg=R["bg"])
    lf.pack(fill="x", padx=20, pady=(0, 12))
    _loading_frame = lf
    lbl = tk.Label(lf, text="Baslatiliyor...", bg=R["bg"], fg=R["text"],
                   font=("Segoe UI", 9), anchor="w", wraplength=300)
    lbl.pack(fill="x", pady=(0, 6))
    _status_label = lbl
    style = ttk.Style(); style.theme_use("clam")
    style.configure("TBH.Horizontal.TProgressbar",
                    troughcolor=R["panel"], background=R["baslik"],
                    bordercolor=R["border"], lightcolor=R["baslik"], darkcolor=R["baslik"])
    pb = ttk.Progressbar(lf, style="TBH.Horizontal.TProgressbar",
                         orient="horizontal", length=300, mode="indeterminate")
    pb.pack(fill="x"); pb.start(15)
    _progress_bar = pb

    rf = tk.Frame(root, bg=R["bg"])
    _ready_frame = rf
    tk.Label(rf, text="Itemin uzerine gel  →  F10", bg=R["bg"], fg=R["yesil"],
             font=("Segoe UI", 11, "bold"), pady=8).pack()
    btn_frame = tk.Frame(rf, bg=R["bg"])
    btn_frame.pack(pady=(0, 10))
    tk.Button(btn_frame, text="Fiyatlari Guncelle", bg=R["btn"], fg=R["text"],
              relief="flat", font=("Segoe UI", 8), padx=8,
              command=lambda: threading.Thread(target=refresh, daemon=True).start()
              ).pack(side="left", padx=4)
    tk.Button(btn_frame, text="Kapat", bg=R["btn"], fg=R["kirmizi"],
              relief="flat", font=("Segoe UI", 8), padx=8,
              command=root.quit).pack(side="left", padx=4)

    root.geometry("340x155")
    _root = root
    return root

def show_ready():
    if _loading_frame: _loading_frame.pack_forget()
    if _ready_frame:   _ready_frame.pack(fill="x")
    if _root:          _root.geometry("340x120")

def refresh():
    global _grouped
    if _ready_frame:   _ready_frame.pack_forget()
    if _loading_frame: _loading_frame.pack(fill="x", padx=20, pady=(0, 12))
    if _root:          _root.geometry("340x155")
    _grouped = fetch_market()
    status("Hazir!")
    if _root: _root.after(0, show_ready)

def init():
    global _grouped
    _grouped = load_market()
    status("Hazir!")
    if _root: _root.after(0, show_ready)

def main():
    root = build_window()
    root.update()
    threading.Thread(target=init, daemon=True).start()
    keyboard.add_hotkey("F10", on_f10, suppress=False)
    root.mainloop()

if __name__ == "__main__":
    main()
