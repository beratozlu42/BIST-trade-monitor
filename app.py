from playwright.sync_api import sync_playwright
from collections import defaultdict, deque
from statistics import median
from datetime import datetime
from dotenv import load_dotenv
import os
import time
import requests
import signal
import sys

RUN_TIME = 60 * 60

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALERT_MULTIPLIER = 1500
MIN_LOT = 1000
BLOCK_WINDOW = 60      # saniye
BLOCK_LOT = 30000      # toplam lot
BLOCK_COUNT = 15       # minimum işlem

flow_history = defaultdict(lambda: deque(maxlen=1000))

last_block_alert = {}

trade_history = defaultdict(
    lambda: deque(maxlen=100)
)

seen_trades = deque(maxlen=5000)

def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    try:

        requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

        print("Bildirim gönderildi")

    except Exception as e:

        print(
            "Telegram hatası:",
            e
        )

def is_stock(symbol):

    if not symbol:
        return False

    if symbol.startswith("X"):
        return False

    if symbol.startswith("F_"):
        return False

    return True

def get_favorite_symbols(frame):

    cards = frame.locator(".fav-card")

    symbols = []

    for i in range(cards.count()):

        symbol = cards.nth(i).get_attribute(
            "data-symbol"
        )

        if is_stock(symbol):
            symbols.append(symbol)

    return symbols

def open_stock(frame, symbol):

    if frame.locator(".fav-card").count() == 0:
        go_home(frame)

    cards = frame.locator(".fav-card")

    for i in range(cards.count()):

        card = cards.nth(i)


        if not card.is_visible():
            continue


        if card.get_attribute("data-symbol") == symbol:

            print(symbol)

            card.click()

            break

    frame.locator(
        ".trades-row"
    ).first.wait_for(
        timeout=10000
    )

def read_trades(frame, symbol):
    rows = frame.locator(
        ".trades-row:visible"
    )

    print(
        symbol,
        "trade:",
        rows.count()
    )

    for i in range(min(rows.count(),20)):
        cols = rows.nth(i).locator("div")

        trade_time = cols.nth(0).inner_text()
        price = cols.nth(1).inner_text()
        quantity_text = cols.nth(2).inner_text()
        buyer = cols.nth(3).inner_text()
        seller = cols.nth(4).inner_text()

        trade_id = (
            symbol,
            trade_time,
            price,
            quantity_text,
            buyer,
            seller
        )

        # daha önce gördüysek geç
        if trade_id in seen_trades:
            continue

        seen_trades.append(trade_id)

        quantity = int(
            quantity_text
            .replace(".", "")
            .replace(",", "")
        )

        history = trade_history[symbol]

        print(
            symbol,
            "|",
            trade_time,
            "|",
            price,
            "|",
            quantity,
            "|",
            buyer,
            "->",
            seller
        )

        if len(history) >= 10:
            normal_lot = median(history)
            ratio = quantity / normal_lot

            if (
                quantity >= MIN_LOT
                and ratio >= ALERT_MULTIPLIER
            ):

                message = f"""
🚨 Anormal Büyük İşlem 🚨

Hisse: {symbol}

Saat:
{trade_time}

Fiyat:
{price}

Lot:
{quantity}

Normal Lot:
{normal_lot:.0f}

Oran:
{ratio:.1f}x

Alan:
{buyer}

Satan:
{seller}
"""
                send_telegram(message) 
        history.append(quantity)

            # -------------------------
        # BLOK İŞLEM TAKİBİ
        # -------------------------

        now = time.time()

        flow_history[symbol].append({
            "time": now,
            "buyer": buyer,
            "seller": seller,
            "quantity": quantity
        })

        # 60 saniyeden eski işlemleri sil
        while (
            flow_history[symbol]
            and now - flow_history[symbol][0]["time"] > BLOCK_WINDOW
        ):
            flow_history[symbol].popleft()

        # Aynı kurum çiftlerini grupla
        pairs = {}

        for trade in flow_history[symbol]:

            key = (
                trade["buyer"],
                trade["seller"]
            )

            if key not in pairs:

                pairs[key] = {
                    "lot": 0,
                    "count": 0
                }

            pairs[key]["lot"] += trade["quantity"]
            pairs[key]["count"] += 1

        # Alarm üret
        for (buyer_name, seller_name), data in pairs.items():

            if (
                data["lot"] >= BLOCK_LOT
                and data["count"] >= BLOCK_COUNT
            ):

                alert_key = (
                    symbol,
                    buyer_name,
                    seller_name
                )

                # Aynı alarmı 5 dakika boyunca tekrar gönderme
                if (
                    alert_key in last_block_alert
                    and now - last_block_alert[alert_key] < 300
                ):
                    continue

                last_block_alert[alert_key] = now

                send_telegram(f"""
🚨 BLOK İŞLEM

Hisse: {symbol}

Kurum:
{buyer_name} -> {seller_name}

Son {BLOCK_WINDOW} saniye

Toplam Lot:
{data['lot']:,}

İşlem Sayısı:
{data['count']}
""")

def go_home(frame):
    home = frame.locator(
        '[data-nav="anasayfa"]'
    )

    for attempt in range(5):
        try:
            home.click(
                force=True
            )

            time.sleep(0.5)

            if frame.locator(
                ".fav-card:visible"
            ).count() > 0:
                
                return True
        except:

            pass

        time.sleep(0.5)

    print(
        "Ana sayfaya dönülemedi"
    )

    return False


with sync_playwright() as p:
    
    context = p.chromium.launch_persistent_context(

        user_data_dir="./telegram_profile",

        headless=False,

        args=[

            "--disable-renderer-backgrounding",

            "--disable-background-timer-throttling",

            "--disable-features=TranslateUI"

        ]
    )

    page = (
        context.pages[0]
        if context.pages
        else context.new_page()
    )

    page.goto(
        "https://web.telegram.org/k/#@ucretsizderinlikbot"
    )

    input(
        "Açılan tarayıcıdan hesabınıza giriş yapın. Ardından mini app'i açın ve terminalden enter'a basın..."
    )

    iframe = page.locator(
        "iframe.payment-verification"
    )

    frame = (
        iframe
        .element_handle()
        .content_frame()
    )

    symbols = get_favorite_symbols(frame)

    print(
        "Takip listesi:"
    )

    print(symbols)

    send_telegram(
        f"""✅ Alarm sistemi başlatıldı!

    Alert multiplier: {ALERT_MULTIPLIER}

    Takip edilen hisseler:
    {", ".join(symbols)}

    Toplam hisse: {len(symbols)}
    """
    )

    start = time.time()

    try: 
        while True:
            if time.time() - start > RUN_TIME:

                print(
                    "Süre doldu."
                )
                break

            for symbol in symbols:
                try:
                    open_stock(
                        frame,
                        symbol
                    )

                    read_trades(
                        frame,
                        symbol
                    )

                    go_home(
                        frame
                    )

                except Exception as e:
                    print(
                        symbol,
                        "hata:",
                        e
                    )

                    try:
                        go_home(frame)

                    except:
                        pass

    except KeyboardInterrupt:

        print("\nDurduruluyor...")

        send_telegram("🛑 Alarm sistemi durduruldu.")

    finally:
        context.close()