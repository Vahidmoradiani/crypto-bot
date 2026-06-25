import requests
import time
from datetime import datetime

TOKEN = "8807180650:AAHBp-5_rCTKlUH_mk0KFyqXtDZnfOpCKTs"
CHAT_ID = "6206752190"

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        r = requests.post(url, data=data, timeout=30)
        if r.status_code == 200:
            print("✅")
            return True
        else:
            print(f"❌ {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ {e}")
        return False

def get_klines(symbol, interval):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=60"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            highs = [float(x[2]) for x in data]
            lows = [float(x[3]) for x in data]
            closes = [float(x[4]) for x in data]
            return highs, lows, closes
        return None, None, None
    except:
        return None, None, None

def check_signal(symbol):
    # دریافت داده ۱ ساعته
    h1, l1, c1 = get_klines(symbol, '1h')
    if h1 is None:
        return None
    
    # دریافت داده ۴ ساعته
    h4, l4, c4 = get_klines(symbol, '4h')
    if h4 is None:
        return None
    
    price = c1[-1]
    signals = []
    
    # سطوح ۱ ساعت
    resistance_1h = max(h1)
    support_1h = min(l1)
    
    # سطوح ۴ ساعت
    resistance_4h = max(h4)
    support_4h = min(l4)
    
    # ===== سیگنال فروش (SELL) =====
    # اگه قیمت به مقاومت نزدیک باشه (۳٪)
    if abs(price - resistance_1h) / resistance_1h < 0.03:
        signals.append({
            'type': 'SELL',
            'timeframe': '1 ساعت',
            'reason': f'قیمت به مقاومت {resistance_1h:.4f} رسید',
            'price': price
        })
    elif abs(price - resistance_4h) / resistance_4h < 0.03:
        signals.append({
            'type': 'SELL',
            'timeframe': '4 ساعت',
            'reason': f'قیمت به مقاومت {resistance_4h:.4f} رسید',
            'price': price
        })
    
    # ===== سیگنال خرید (BUY) =====
    # اگه قیمت به حمایت نزدیک باشه (۳٪)
    if abs(price - support_1h) / support_1h < 0.03:
        signals.append({
            'type': 'BUY',
            'timeframe': '1 ساعت',
            'reason': f'قیمت به حمایت {support_1h:.4f} رسید',
            'price': price
        })
    elif abs(price - support_4h) / support_4h < 0.03:
        signals.append({
            'type': 'BUY',
            'timeframe': '4 ساعت',
            'reason': f'قیمت به حمایت {support_4h:.4f} رسید',
            'price': price
        })
    
    return signals if signals else None

def get_top_40():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        r = requests.get(url, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            usdt_pairs = [x for x in data if x['symbol'].endswith('USDT')]
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            top_40 = usdt_pairs[:40]
            
            coins = []
            for item in top_40:
                symbol = item['symbol']
                name = symbol.replace('USDT', '')
                coins.append({
                    'name': name,
                    'symbol': symbol,
                    'change_24h': float(item['priceChangePercent'])
                })
            
            print(f"✅ {len(coins)} رمز ارز دریافت شد")
            return coins
        else:
            return get_top_40_manual()
    except:
        return get_top_40_manual()

def get_top_40_manual():
    symbols = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
        "MATICUSDT", "SHIBUSDT", "TRXUSDT", "ATOMUSDT", "UNIUSDT",
        "LTCUSDT", "BCHUSDT", "NEARUSDT", "ALGOUSDT", "VETUSDT"
    ]
    
    coins = []
    for symbol in symbols:
        name = symbol.replace('USDT', '')
        coins.append({
            'name': name,
            'symbol': symbol,
            'change_24h': 0
        })
    
    print(f"📋 {len(coins)} رمز ارز از لیست دستی بارگذاری شد")
    return coin

while True:
    try:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        
        coins = get_top_40()
        
        if not coins:
            print("❌ لیست رمز ارزها دریافت نشد")
            time.sleep(60)
            continue
        
        all_signals = []
        
        for coin in coins:
            signals = check_signal(coin['symbol'])
            if signals:
                for s in signals:
                    all_signals.append({
                        'name': coin['name'],
                        'type': s['type'],
                        'timeframe': s['timeframe'],
                        'reason': s['reason'],
                        'price': s['price']
                    })
            time.sleep(0.3)
        
        if all_signals:
            msg = "📊 <b>سیگنال‌های جدید</b>\n━━━━━━━━━━━━━━━━\n"
            for s in all_signals:
                emoji = "🟢" if s['type'] == 'BUY' else "🔴"
                msg += f"{emoji} <b>{s['type']}</b> {s['name']}\n"
                msg += f"⏱️ تایم: {s['timeframe']}\n"
                msg += f"💰 قیمت: {s['price']:.4f}\n"
                msg += f"📝 دلیل: {s['reason']}\n"
                msg += "━━━━━━━━━━━━━━━━\n"
            
            send(msg)
            print(f"✅ {len(all_signals)} سیگنال ارسال شد")
        else:
            print("📭 بدون سیگنال")
        
        time.sleep(300)
        
    except KeyboardInterrupt:
        print("🛑 توقف")
        send("🛑 ربات متوقف شد")
        break
    except Exception as e:
        print(f"❌ خطا: {e}")
        time.sleep(60)
