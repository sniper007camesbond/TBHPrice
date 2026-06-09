# -*- coding: utf-8 -*-
"""
TBH Fiyat Bakici
F10 → arama popup'i acilir → item adi yaz → fiyat + Steam linki.
"""
import requests, os, json, time, webbrowser
import tkinter as tk
from tkinter import ttk
import threading
from concurrent.futures import ThreadPoolExecutor
import ctypes, ctypes.wintypes
import io
from PIL import Image, ImageTk

_user32 = ctypes.windll.user32

def _get_cursor_pos():
    pt = ctypes.wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

def _get_screen_size():
    return _user32.GetSystemMetrics(0), _user32.GetSystemMetrics(1)

APP_ID       = 3678970
VERSION      = "1.4.1"
GITHUB_REPO  = "sniper007camesbond/TBHFiyat"
import sys

_lang = ["tr"]

LANG = {
    "tr": {
        "win_title":    "TBH FIYAT BAKICI",
        "starting":     "Baslatiliyor...",
        "ready":        "Hazir!",
        "search_btn":   "FIYAT ARA",
        "or_f10":       "veya F10",
        "refresh_btn":  "Fiyatlari Guncelle",
        "update_btn":   "Guncelle",
        "close_btn":    "Kapat",
        "lang_btn":     "EN",
        "popup_title":  "TBH FIYAT ARA",
        "no_match":     "Eslesme bulunamadi",
        "listings":     "satista",
        "variant":      "varyant",
        "tab_guncel":   "Guncel Fiyatlar",
        "tab_arsiv":    "Arsiv Fiyatlari",
        "chk_update":   "Guncelleme kontrol ediliyor...",
        "up_to_date":   "Zaten guncel! (v{v})",
        "new_ver":      "Yeni surum bulundu: v{v} — indirme sayfasi aciliyor...",
        "dl_error":     "Indirme hatasi: {e}",
        "fetching":     "Steam'den veriler cekiliyor {n}/{total}",
        "saved":        "{n} item kaydedildi.",
        "cache_ok":     "Cache'den {n} item yuklendi.",
        "arsiv_ok":     "Arsivden {n} item yuklendi.",
        "rate_limit":   "Steam rate limit, {w}s bekleniyor...",
        "steam_err":    "Steam hatasi: {e} — arsiv kullaniliyor.",
        "steam_fail":   "Steam'e erisilemedi — arsiv kullaniliyor.",
        "fetching1":    "Steam'den fiyatlar cekiliyor (1. sayfa)...",
    },
    "en": {
        "win_title":    "TBH PRICE CHECKER",
        "starting":     "Starting...",
        "ready":        "Ready!",
        "search_btn":   "SEARCH PRICE",
        "or_f10":       "or F10",
        "refresh_btn":  "Refresh Prices",
        "update_btn":   "Update",
        "close_btn":    "Close",
        "lang_btn":     "TR",
        "popup_title":  "TBH PRICE SEARCH",
        "no_match":     "No results found",
        "listings":     "listed",
        "variant":      "variant",
        "tab_guncel":   "Current Prices",
        "tab_arsiv":    "Archive Prices",
        "chk_update":   "Checking for updates...",
        "up_to_date":   "Up to date! (v{v})",
        "new_ver":      "New version found: v{v} — opening download page...",
        "dl_error":     "Download error: {e}",
        "fetching":     "Fetching from Steam {n}/{total}",
        "saved":        "{n} items saved.",
        "cache_ok":     "Loaded {n} items from cache.",
        "arsiv_ok":     "Loaded {n} items from archive.",
        "rate_limit":   "Steam rate limit, waiting {w}s...",
        "steam_err":    "Steam error: {e} — using archive.",
        "steam_fail":   "Steam unavailable — using archive.",
        "fetching1":    "Fetching prices from Steam (page 1)...",
    },
}

def t(key, **kw):
    s = LANG[_lang[0]].get(key, key)
    return s.format(**kw) if kw else s
BASE_DIR  = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "market_fiyat.json")
HEADERS   = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
CACHE_TTL = 7200  # 2 saat

RARITY_COLOR = {
    "D7D7D7": "#9ba3ad",   # Yaygin
    "7CE937": "#7ce937",   # Malzeme (yesil)
    "E8695A": "#e8695a",   # Az Nadir
    "519FFF": "#54a8ff",   # Nadir
    "EBBB00": "#f1a23c",   # Efsanevi
    "00F6FF": "#a2f4ff",   # Olümsüz / Goksel
    "FB86FF": "#bd7cff",   # Arkan
    "FF0080": "#ff8ec7",   # Otesi
    "F6E7A2": "#f6e7a2",   # Divine
    "FC00FF": "#fc00ff",   # Cosmic
}

_RARITY_WORD = {
    "legendary": "#f1a23c", "immortal": "#a2f4ff", "arcana":  "#bd7cff",
    "beyond":    "#ff8ec7", "celestial":"#a2f4ff", "divine":  "#f6e7a2",
    "cosmic":    "#fc00ff",
}

def _rarity_fg(variants):
    import re
    if not variants: return "#d0bfad"
    nc = (variants[0].get("name_color") or "").upper()[:6]
    if nc in RARITY_COLOR:
        return RARITY_COLOR[nc]
    m = re.search(r'\((\w+)\)', variants[0].get("name", ""))
    if m:
        return _RARITY_WORD.get(m.group(1).lower(), "#d0bfad")
    return "#d0bfad"

def _rarity_bg(variants):
    fg = _rarity_fg(variants).lstrip("#")
    try:
        r, g, b = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
        return f"#{int(r*0.28):02x}{int(g*0.28):02x}{int(b*0.28):02x}"
    except Exception:
        return R["panel"]

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

ARSIV_FILE = os.path.join(BASE_DIR, "market_arsiv.json")

# ── Market verisi ──────────────────────────────
def _fetch_page(start, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(
                "https://steamcommunity.com/market/search/render/",
                params={"appid": APP_ID, "norender": 1, "count": 100, "start": start,
                        "sort_column": "popular", "sort_dir": "desc"},
                headers=HEADERS, timeout=20
            )
            if r.status_code == 429:
                wait = 8 * (attempt + 1)
                status(t("rate_limit", w=wait))
                time.sleep(wait)
                continue
            data = r.json()
            items = []
            for it in data.get("results", []):
                desc = it.get("asset_description", {})
                items.append({
                    "name":       it.get("name", ""),
                    "hash_name":  it.get("hash_name", ""),
                    "price":      it.get("sell_price", 0) / 100,
                    "price_text": it.get("sell_price_text", "—"),
                    "listings":   it.get("sell_listings", 0),
                    "icon_url":   desc.get("icon_url", ""),
                    "name_color": desc.get("name_color", ""),
                })
            return items, data.get("total_count", 0)
        except Exception:
            time.sleep(3)
    return [], 0

def _load_arsiv():
    """market_arsiv.json'dan grouped yap (Steam çalışmıyorsa fallback)."""
    if not os.path.exists(ARSIV_FILE):
        return None
    with open(ARSIV_FILE, "r", encoding="utf-8") as f:
        d = json.load(f)
    grouped = {}
    for it in d.get("items", []):
        grouped.setdefault(it["name"], []).append(it)
    for n in grouped:
        grouped[n].sort(key=lambda x: x.get("price", 0))
    return grouped

def fetch_market():
    """Steam'den güncel fiyat çek — sıralı, 1.2s bekleme, ban riski yok."""
    status(t("fetching1"))
    set_progress(-1)

    try:
        first, total = _fetch_page(0)
    except Exception as e:
        status(t("steam_err", e=e))
        return _load_arsiv() or {}

    if not first:
        status(t("steam_fail"))
        return _load_arsiv() or {}

    page_size = len(first)
    all_items = list(first)
    offsets   = list(range(page_size, total, page_size))
    total_pg  = len(offsets) + 1

    for i, off in enumerate(offsets):
        time.sleep(0.3)
        items, _ = _fetch_page(off)
        all_items.extend(items)
        status(t("fetching", n=i+2, total=total_pg))

    grouped = {}
    for it in all_items:
        grouped.setdefault(it["name"], []).append(it)
    for n in grouped:
        grouped[n].sort(key=lambda x: x["price"])

    set_progress(0, 1)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": time.time(), "grouped": grouped}, f, ensure_ascii=False)
    status(t("saved", n=len(grouped)))
    return grouped

def load_market():
    """Steam cache tazeyse cache'den, değilse Steam'den çek. Arşivle karışmaz."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
        if time.time() - c.get("updated", 0) < CACHE_TTL:
            status(t("cache_ok", n=len(c["grouped"])))
            return c["grouped"]
    return fetch_market()

# ── Yardimci ───────────────────────────────────
def fmt_price(p):
    return f"{p:.2f} TL" if p else "—"

def steam_url(hash_name):
    return (f"https://steamcommunity.com/market/listings/{APP_ID}/"
            f"{requests.utils.quote(hash_name)}")

def steam_search_url(name):
    return (f"https://steamcommunity.com/market/search?appid={APP_ID}"
            f"&q={requests.utils.quote(name)}")

# ── Durum / progress ───────────────────────────
_status_label = None
_progress_bar = None
_progress_max = [1]

def status(msg):
    print(msg)
    if _status_label:
        try:
            _status_label.config(text=msg)
            _status_label.update_idletasks()
        except: pass

def set_progress(val, maxv=None):
    if _progress_bar is None: return
    try:
        if val < 0:
            _progress_bar.config(mode="indeterminate")
            _progress_bar.start(15)
        else:
            _progress_bar.stop()
            _progress_bar.config(mode="determinate")
            if maxv: _progress_max[0] = maxv
            _progress_bar["value"] = int(val / max(_progress_max[0], 1) * 100)
            _progress_bar.update_idletasks()
    except: pass

# ── Item ikonları ──────────────────────────────
_img_photo   = {}   # (icon_url, size) → ImageTk.PhotoImage  (RAM cache)
_build_gen   = [0]
_img_pending = set()              # indirilmekte olan url'ler
_icon_pool   = ThreadPoolExecutor(max_workers=4)

def _icon_cache_dir():
    d = os.path.join(BASE_DIR, "icon_cache")
    os.makedirs(d, exist_ok=True)
    return d

def _icon_disk_path(icon_url):
    safe = icon_url.replace("/", "_").replace("\\", "_")[:120]
    return os.path.join(_icon_cache_dir(), safe + ".png")

def _load_pil_from_disk(icon_url):
    """Disk cache'den oku; yoksa None."""
    p = _icon_disk_path(icon_url)
    if os.path.exists(p):
        try:
            return Image.open(p).convert("RGBA")
        except Exception:
            pass
    return None

def _save_pil_to_disk(icon_url, img):
    try:
        img.save(_icon_disk_path(icon_url), "PNG")
    except Exception:
        pass

def _get_photo(icon_url, size):
    """RAM cache'den PhotoImage döner; yoksa None."""
    return _img_photo.get((icon_url, size))

def _fetch_and_cache(icon_url, callback, gen, size):
    """
    Worker (thread pool): disk → Steam CDN sırasıyla dene.
    Resize + PhotoImage oluşturma da burada (main thread yük almaz).
    Hazır olunca main thread'de canvas güncelle.
    """
    if icon_url in _img_pending:
        return
    _img_pending.add(icon_url)
    def _worker():
        pil = None
        try:
            pil = _load_pil_from_disk(icon_url)
            if pil is None:
                url = f"https://community.akamai.steamstatic.com/economy/image/{icon_url}"
                r = requests.get(url, timeout=6, headers=HEADERS)
                pil = Image.open(io.BytesIO(r.content)).convert("RGBA")
                _save_pil_to_disk(icon_url, pil)
            # Resize burada (worker thread) — main thread'e yük yok
            key = (icon_url, size)
            if key not in _img_photo:
                resized = pil.resize((size, size), Image.LANCZOS)
                # ImageTk.PhotoImage main thread'de oluşturulmalı
                if _root and gen == _build_gen[0]:
                    _root.after(0, lambda p=resized: _make_photo_and_cb(icon_url, size, p, callback, gen))
        except Exception:
            pass
        finally:
            _img_pending.discard(icon_url)
    _icon_pool.submit(_worker)

def _make_photo_and_cb(icon_url, size, resized_pil, callback, gen):
    """Main thread'de PhotoImage oluştur, callback çağır."""
    if gen != _build_gen[0]: return
    key = (icon_url, size)
    if key not in _img_photo:
        try:
            _img_photo[key] = ImageTk.PhotoImage(resized_pil)
        except Exception:
            return
    callback(icon_url, gen, size)

def _load_icon_canvas(icon_url, canvas, item_id, gen, size):
    """Canvas image item'ını async yükle."""
    if not icon_url: return
    photo = _get_photo(icon_url, size)
    if photo:
        try: canvas.itemconfig(item_id, image=photo)
        except: pass
        return
    def _cb(url, g, sz):
        if g != _build_gen[0]: return
        try:
            p = _get_photo(url, sz)
            if p: canvas.itemconfig(item_id, image=p)
        except: pass
    _fetch_and_cache(icon_url, _cb, gen, size)

# ── Arama popup'i ──────────────────────────────
_search_win = None

def open_search():
    global _search_win
    if _search_win:
        try:
            _search_win.lift()
            _search_win.focus_force()
            return
        except: pass

    cx, cy = _get_cursor_pos()
    sw = tk.Toplevel(_root)
    sw.title("")
    sw.overrideredirect(True)
    sw.attributes("-topmost", True)
    sw.configure(bg=R["border"])
    _search_win = sw

    inner = tk.Frame(sw, bg=R["bg"], padx=0, pady=0)
    inner.pack(padx=1, pady=1, fill="both", expand=True)

    # Baslik + kapat + sürükleme
    top = tk.Frame(inner, bg=R["panel"], padx=8, pady=6, cursor="fleur")
    top.pack(fill="x")
    title_lbl = tk.Label(top, text=t("popup_title"), bg=R["panel"], fg=R["baslik"],
                         font=("Segoe UI", 9, "bold"), cursor="fleur")
    title_lbl.pack(side="left")
    _ui_popup["popup_title"] = title_lbl
    tk.Button(top, text="✕", bg=R["panel"], fg=R["kirmizi"],
              font=("Segoe UI", 9, "bold"), relief="flat", bd=0, padx=4,
              cursor="arrow",
              command=lambda: close_search(sw)).pack(side="right")

    _drag = {"x": 0, "y": 0}
    def drag_start(e): _drag["x"] = e.x_root; _drag["y"] = e.y_root
    def drag_move(e):
        dx = e.x_root - _drag["x"]; dy = e.y_root - _drag["y"]
        sw.geometry(f"+{sw.winfo_x()+dx}+{sw.winfo_y()+dy}")
        _drag["x"] = e.x_root; _drag["y"] = e.y_root
    for w in (top, title_lbl):
        w.bind("<ButtonPress-1>", drag_start)
        w.bind("<B1-Motion>",     drag_move)

    # Arama kutusu
    srch_frame = tk.Frame(inner, bg=R["bg"], padx=8, pady=6)
    srch_frame.pack(fill="x")
    entry = tk.Entry(srch_frame, bg=R["panel"], fg=R["text"],
                     insertbackground=R["text"], relief="flat",
                     font=("Segoe UI", 11), bd=0)
    entry.pack(fill="x", ipady=5, padx=2)
    entry.focus_set()

    # Kaynak seçici tab butonları
    _src = ["guncel"]   # "guncel" veya "arsiv"
    tab_frame = tk.Frame(inner, bg=R["bg"], padx=8)
    tab_frame.pack(fill="x", pady=(0, 4))

    def _make_tab(key, src_val):
        def _cmd():
            _src[0] = src_val
            _refresh_tabs()
            build_results(entry.get())
        btn = tk.Button(tab_frame, text=t(key), relief="flat", bd=0,
                        font=("Segoe UI", 8, "bold"), padx=10, pady=3,
                        cursor="hand2", command=_cmd)
        return btn

    btn_guncel = _make_tab("tab_guncel", "guncel")
    btn_arsiv  = _make_tab("tab_arsiv",  "arsiv")
    btn_guncel.pack(side="left", padx=(0, 2))
    btn_arsiv.pack(side="left")
    _ui_popup["tab_guncel"] = btn_guncel
    _ui_popup["tab_arsiv"]  = btn_arsiv

    def _refresh_tabs():
        if _src[0] == "guncel":
            btn_guncel.config(bg=R["yesil"],  fg=R["bg"])
            btn_arsiv.config( bg=R["panel"],  fg=R["muted"])
        else:
            btn_guncel.config(bg=R["panel"],  fg=R["muted"])
            btn_arsiv.config( bg=R["yesil"],  fg=R["bg"])
    _refresh_tabs()

    # Sonuc listesi — Canvas tabanlı (hızlı), yeniden boyutlandırılabilir
    BASE_W  = 380
    ROW_H_B = 54

    list_frame = tk.Frame(inner, bg=R["bg"])
    list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 0))

    sb = tk.Scrollbar(list_frame, orient="vertical")
    sb.pack(side="right", fill="y")

    cv = tk.Canvas(list_frame, bg=R["bg"], highlightthickness=0,
                   yscrollcommand=sb.set, yscrollincrement=4)
    cv.pack(side="left", fill="both", expand=True)
    sb.config(command=cv.yview)
    sw.bind_all("<MouseWheel>", lambda e: cv.yview_scroll(int(-1*(e.delta/120)), "units"))

    # Yeniden boyutlandırma tutamacı
    grip = tk.Frame(inner, bg=R["border"], height=8, cursor="size_nw_se")
    grip.pack(fill="x", side="bottom")
    _rsz = {"x": 0, "y": 0, "w": 0, "h": 0}
    _rsz_after = [None]
    def rsz_start(e):
        _rsz.update(x=e.x_root, y=e.y_root, w=sw.winfo_width(), h=sw.winfo_height())
    def rsz_move(e):
        dw = e.x_root - _rsz["x"]; dh = e.y_root - _rsz["y"]
        sw.geometry(f"{max(320, _rsz['w']+dw)}x{max(260, _rsz['h']+dh)}")
    def rsz_end(e):
        if _rsz_after[0]: sw.after_cancel(_rsz_after[0])
        _rsz_after[0] = sw.after(80, lambda: build_results(entry.get()))
    grip.bind("<ButtonPress-1>", rsz_start)
    grip.bind("<B1-Motion>",     rsz_move)
    grip.bind("<ButtonRelease-1>", rsz_end)

    _row_rects   = {}
    _row_actions = {}
    _hovered     = [-1]
    _cur_row_h   = [ROW_H_B]

    def _on_motion(e):
        y   = cv.canvasy(e.y)
        idx = int(y // _cur_row_h[0])
        if idx == _hovered[0]: return
        if _hovered[0] in _row_rects:
            cv.itemconfig(_row_rects[_hovered[0]], fill=R["bg"])
        _hovered[0] = idx
        if idx in _row_rects:
            cv.itemconfig(_row_rects[idx], fill=R["sec"])

    def _on_click(e):
        idx = int(cv.canvasy(e.y) // _cur_row_h[0])
        fn  = _row_actions.get(idx)
        if fn: fn()

    cv.bind("<Motion>",   _on_motion)
    cv.bind("<Button-1>", _on_click)

    def build_results(q=""):
        cv.delete("all")
        _row_rects.clear(); _row_actions.clear(); _hovered[0] = -1
        _build_gen[0] += 1
        gen = _build_gen[0]

        cw  = cv.winfo_width() or BASE_W
        sc  = max(1.0, cw / BASE_W) if cw > 50 else 1.0
        rh  = max(48, int(ROW_H_B * sc))
        isz = max(32, int(38 * sc))
        _cur_row_h[0] = rh
        fn_name  = ("Segoe UI", max(9,  int(9  * sc)), "bold")
        fn_info  = ("Segoe UI", max(7,  int(7  * sc)))
        fn_price = ("Segoe UI", max(10, int(10 * sc)), "bold")

        q_low    = q.lower()
        src_list = _sorted_items if _src[0] == "guncel" else _sorted_items_arsiv
        filtered = []
        for name, variants in src_list:
            if q_low and q_low not in name.lower(): continue
            filtered.append((name, variants))
            if len(filtered) >= 60: break

        total_h = len(filtered) * rh
        cv.configure(scrollregion=(0, 0, cw, max(total_h, 1)))

        for i, (name, variants) in enumerate(filtered):
            y    = i * rh
            ibg  = _rarity_bg(variants)
            ifg  = _rarity_fg(variants)
            prices   = [v["price"] for v in variants if v["price"] > 0]
            p_min    = min(prices) if prices else 0
            p_max    = max(prices) if prices else 0
            n_var    = len(variants)
            listings = sum(v["listings"] for v in variants)

            rect_id = cv.create_rectangle(0, y, cw, y+rh-1,
                                           fill=R["bg"], outline="")
            _row_rects[i] = rect_id

            ix = 4
            cv.create_rectangle(ix, y+3, ix+isz, y+3+isz,
                                 fill=ibg, outline="")

            icon_url = variants[0].get("icon_url", "")
            if icon_url:
                img_id = cv.create_image(ix + isz//2, y + rh//2, anchor="center")
                _load_icon_canvas(icon_url, cv, img_id, gen, isz)

            tx = ix + isz + 8
            cv.create_text(tx, y + 6, text=name, fill=ifg,
                           font=fn_name, anchor="nw")

            info = f"{listings:,} {t('listings')}"
            if n_var > 1: info += f"  •  {n_var} {t('variant')}"
            cv.create_text(tx, y + 6 + fn_name[1] + 6, text=info,
                           fill=R["muted"], font=fn_info, anchor="nw")

            sv = sorted(variants, key=lambda x: x.get("price", 0))
            pt_min = sv[0].get("price_text") or fmt_price(p_min)
            pt_max = sv[-1].get("price_text") or fmt_price(p_max)
            price_str = pt_min if pt_min == pt_max else f"{pt_min} ~ {pt_max}"
            cv.create_text(cw - 6, y + rh//2, text=price_str,
                           fill=R["yesil"], font=fn_price, anchor="e")

            cv.create_line(0, y+rh-1, cw, y+rh-1, fill=R["border"])

            def _make_action(n=name, vs=variants):
                def _fn():
                    if len(vs) == 1:
                        webbrowser.open(steam_url(vs[0]["hash_name"]))
                    else:
                        webbrowser.open(steam_search_url(n))
                    close_search(sw)
                return _fn
            _row_actions[i] = _make_action()

        if not filtered and q_low:
            cv.create_text(cw//2, 30, text=t("no_match"),
                           fill=R["muted"], font=fn_info, anchor="center")

    sw.after(30, build_results)   # pencere render olduktan sonra listele

    _after = [None]
    def on_type(*_):
        if _after[0]:
            sw.after_cancel(_after[0])
        _after[0] = sw.after(160, lambda: build_results(entry.get()))
    entry.bind("<KeyRelease>", on_type)

    # Escape ile kapat
    sw.bind("<Escape>", lambda e: close_search(sw))
    entry.bind("<Escape>", lambda e: close_search(sw))

    # Konumlama
    sw.update_idletasks()
    pw, ph = sw.winfo_reqwidth(), sw.winfo_reqheight()
    sx, sy = _get_screen_size()
    wx = min(cx + 10, sx - pw - 10)
    wy = min(cy + 10, sy - ph - 10)
    sw.geometry(f"{pw}x{ph}+{wx}+{wy}")

def close_search(w):
    global _search_win
    _search_win = None
    _ui_popup.clear()
    try: w.destroy()
    except: pass

# ── Ana pencere ────────────────────────────────
# ── Otomatik güncelleme ────────────────────────
def _ver_tuple(v):
    return tuple(int(x) for x in v.lstrip("v").split("."))

def check_update():
    """(latest_ver, download_url) döner, yoksa None."""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "TBHFiyat"},
            timeout=10
        )
        if r.status_code != 200:
            return None
        data   = r.json()
        tag    = data.get("tag_name", "")
        assets = data.get("assets", [])
        asset  = next((a for a in assets if a["name"].endswith(".exe")), None)
        if not asset:
            return None
        latest = tag.lstrip("v")
        if _ver_tuple(latest) > _ver_tuple(VERSION):
            return latest, asset["browser_download_url"]
        return None
    except Exception:
        return None

def run_update_check():
    webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")

_root               = None
_ready_frame        = None
_loading_frame      = None
_grouped            = {}
_sorted_items       = []
_grouped_arsiv      = {}
_sorted_items_arsiv = []
_ui                 = {}

def _presort():
    global _sorted_items
    _sorted_items = sorted(_grouped.items())

def _presort_arsiv():
    global _sorted_items_arsiv
    _grouped_arsiv.clear()
    g = _load_arsiv() or {}
    _grouped_arsiv.update(g)
    _sorted_items_arsiv[:] = sorted(_grouped_arsiv.items())

_ui_popup = {}   # popup'a ait lang widget'ları (popup açıkken dolu)

def toggle_lang():
    _lang[0] = "en" if _lang[0] == "tr" else "tr"
    for key, widget in _ui.items():
        try: widget.config(text=t(key))
        except: pass
    for key, widget in _ui_popup.items():
        try: widget.config(text=t(key))
        except: pass

def build_window():
    global _root, _status_label, _progress_bar, _ready_frame, _loading_frame
    root = tk.Tk()
    root.title("TBH Fiyat")
    root.configure(bg=R["bg"])
    root.resizable(False, False)
    root.attributes("-topmost", True)

    # Başlık satırı + dil butonu
    hdr = tk.Frame(root, bg=R["bg"])
    hdr.pack(fill="x")
    win_lbl = tk.Label(hdr, text=t("win_title"), bg=R["bg"], fg=R["baslik"],
                       font=("Segoe UI", 12, "bold"), padx=20, pady=10)
    win_lbl.pack(side="left")
    _ui["win_title"] = win_lbl
    lang_btn = tk.Button(hdr, text=t("lang_btn"), bg=R["btn"], fg=R["muted"],
                         font=("Segoe UI", 8), relief="flat", padx=6, pady=2,
                         cursor="hand2", command=toggle_lang)
    lang_btn.pack(side="right", padx=10, pady=10)
    _ui["lang_btn"] = lang_btn

    # Loading frame
    lf = tk.Frame(root, bg=R["bg"])
    lf.pack(fill="x", padx=20, pady=(0, 12))
    _loading_frame = lf

    lbl = tk.Label(lf, text=t("starting"), bg=R["bg"], fg=R["text"],
                   font=("Segoe UI", 9), anchor="w", wraplength=300)
    lbl.pack(fill="x", pady=(0, 6))
    _status_label = lbl

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TBH.Horizontal.TProgressbar",
                    troughcolor=R["panel"], background=R["baslik"],
                    bordercolor=R["border"], lightcolor=R["baslik"], darkcolor=R["baslik"])
    pb = ttk.Progressbar(lf, style="TBH.Horizontal.TProgressbar",
                         orient="horizontal", length=300, mode="indeterminate")
    pb.pack(fill="x")
    pb.start(15)
    _progress_bar = pb

    # Ready frame (gizli)
    rf = tk.Frame(root, bg=R["bg"])
    _ready_frame = rf

    search_btn = tk.Button(rf, text=t("search_btn"), bg=R["yesil"], fg=R["bg"],
                           font=("Segoe UI", 12, "bold"), relief="flat", padx=16, pady=6,
                           cursor="hand2",
                           command=lambda: _root.after(0, open_search))
    search_btn.pack(pady=(8, 4))
    _ui["search_btn"] = search_btn

    or_lbl = tk.Label(rf, text=t("or_f10"), bg=R["bg"], fg=R["muted"],
                      font=("Segoe UI", 8))
    or_lbl.pack()
    _ui["or_f10"] = or_lbl

    btn_frame = tk.Frame(rf, bg=R["bg"])
    btn_frame.pack(pady=(6, 10))

    refresh_btn = tk.Button(btn_frame, text=t("refresh_btn"), bg=R["btn"], fg=R["text"],
                            relief="flat", font=("Segoe UI", 10), padx=14, pady=5,
                            cursor="hand2",
                            command=lambda: threading.Thread(target=refresh, daemon=True).start())
    refresh_btn.pack(side="left", padx=4)
    _ui["refresh_btn"] = refresh_btn

    upd_btn = tk.Button(btn_frame, text=t("update_btn"), bg=R["btn"], fg=R["baslik"],
                        relief="flat", font=("Segoe UI", 10), padx=14, pady=5,
                        cursor="hand2",
                        command=lambda: threading.Thread(target=run_update_check, daemon=True).start())
    upd_btn.pack(side="left", padx=4)
    _ui["update_btn"] = upd_btn

    close_btn = tk.Button(btn_frame, text=t("close_btn"), bg=R["btn"], fg=R["kirmizi"],
                          relief="flat", font=("Segoe UI", 10), padx=14, pady=5,
                          cursor="hand2", command=root.quit)
    close_btn.pack(side="left", padx=4)
    _ui["close_btn"] = close_btn

    root.geometry("340x170")
    _root = root
    return root

def show_ready():
    if _loading_frame: _loading_frame.pack_forget()
    if _ready_frame:   _ready_frame.pack(fill="x")
    if _root:          _root.geometry("340x160")

def refresh():
    global _grouped
    if _ready_frame:   _ready_frame.pack_forget()
    if _loading_frame: _loading_frame.pack(fill="x", padx=20, pady=(0, 12))
    if _root:          _root.geometry("340x155")
    _grouped = fetch_market()
    _presort()
    _presort_arsiv()
    status(t("ready"))
    if _root: _root.after(0, show_ready)

def init():
    global _grouped
    _grouped = load_market()
    _presort()
    _presort_arsiv()
    status(t("ready"))
    if _root: _root.after(0, show_ready)

# ── Hotkey (ctypes RegisterHotKey — keyboard lib yok) ──────────
HOTKEY_ID = 1
VK_F10    = 0x79
WM_HOTKEY = 0x0312

def _hotkey_thread():
    user32 = ctypes.windll.user32
    user32.RegisterHotKey(None, HOTKEY_ID, 0, VK_F10)
    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            if _root:
                _root.after(0, open_search)
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

# ── Baslat ─────────────────────────────────────
def main():
    root = build_window()
    root.update()
    threading.Thread(target=init, daemon=True).start()
    threading.Thread(target=_hotkey_thread, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    main()
