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
            volumes = [float(x[5]) for x in data]
            return highs, lows, closes, volumes
        return None, None, None, None
    except:
        return None, None, None, None

def get_klines_fallback(symbol, interval):
    try:
        url = f"https://api1.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=60"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            highs = [float(x[2]) for x in data]
            lows = [float(x[3]) for x in data]
            closes = [float(x[4]) for x in data]
            volumes = [float(x[5]) for x in data]
            return highs, lows, closes, volumes
        return None, None, None, None
    except:
        return None, None, None, None

def find_fvg(highs, lows, closes):
    fvg_levels = []
    if len(highs) < 5:
        return fvg_levels
    for i in range(2, len(highs) - 2):
        if lows[i] > highs[i-2]:
            gap_bottom = highs[i-2]
            gap_top = lows[i]
            gap_size = (gap_top - gap_bottom) / gap_bottom
            if gap_size > 0.005:
                fvg_levels.append({
                    'type': 'BULLISH_FVG',
                    'bottom': gap_bottom,
                    'top': gap_top,
                    'mid': (gap_bottom + gap_top) / 2
                })
        elif highs[i] < lows[i-2]:
            gap_bottom = highs[i]
            gap_top = lows[i-2]
            gap_size = (gap_top - gap_bottom) / gap_bottom
            if gap_size > 0.005:
                fvg_levels.append({
                    'type': 'BEARISH_FVG',
                    'bottom': gap_bottom,
                    'top': gap_top,
                    'mid': (gap_bottom + gap_top) / 2
                })
    return fvg_levels

def find_trading_nodes(highs, lows, volumes):
    nodes = []
    if len(volumes) < 10:
        return nodes
    avg_vol = sum(volumes) / len(volumes)
    for i in range(len(volumes)):
        if volumes[i] > avg_vol * 1.5:
            node_price = (highs[i] + lows[i]) / 2
            nodes.append({
                'price': node_price,
                'volume': volumes[i],
                'index': i
            })
    return nodes

def check_signal(symbol):
    h1, l1, c1, v1 = get_klines(symbol, '1h')
    if h1 is None:
        h1, l1, c1, v1 = get_klines_fallback(symbol, '1h')
    if h1 is None:
        return None
    
    h4, l4, c4, v4 = get_klines(symbol, '4h')
    if h4 is None:
        h4, l4, c4, v4 = get_klines_fallback(symbol, '4h')
    if h4 is None:
        return None
    
    price = c1[-1]
    signals = []
    
    resistance_1h = max(h1)
    support_1h = min(l1)
    fvg_1h = find_fvg(h1, l1, c1)
    nodes_1h = find_trading_nodes(h1, l1, v1)
    
    resistance_4h = max(h4)
    support_4h = min(l4)
    fvg_4h = find_fvg(h4, l4, c4)
    nodes_4h = find_trading_nodes(h4, l4, v4)
    
    sell_reason = []
    sell_timeframe = []
    
    if abs(price - resistance_1h) / resistance_1h < 0.015:
        sell_reason.append("مقاومت 1h")
        sell_timeframe.append("1 ساعت")
    if abs(price - resistance_4h) / resistance_4h < 0.015:
        sell_reason.append("مقاومت 4h")
        sell_timeframe.append("4 ساعت")
    
    for fvg in fvg_1h:
        if fvg['type'] == 'BEARISH_FVG' and abs(price - fvg['mid']) / fvg['mid'] < 0.01:
            sell_reason.append("FVG نزولی 1h")
            sell_timeframe.append("1 ساعت")
            break
    for fvg in fvg_4h:
        if fvg['type'] == 'BEARISH_FVG' and abs(price - fvg['mid']) / fvg['mid'] < 0.01:
            sell_reason.append("FVG نزولی 4h")
            sell_timeframe.append("4 ساعت")
            break
    
    for node in nodes_1h:
        if abs(price - node['price']) / node['price'] < 0.01:
            sell_reason.append("گره معاملاتی 1h")
            sell_timeframe.append("1 ساعت")
            break
    for node in nodes_4h:
        if abs(price - node['price']) / node['price'] < 0.01:
            sell_reason.append("گره معاملاتی 4h")
            sell_timeframe.append("4 ساعت")
            break
    
    if sell_reason:
        signals.append({
            'type': 'SELL',
            'timeframe': ', '.join(set(sell_timeframe)),
            'reason': ' + '.join(sell_reason),
            'price': price
        })
    
    buy_reason = []
    buy_timeframe = []
    
    if abs(price - support_1h) / support_1h < 0.015:
        buy_reason.append("حمایت 1h")
        buy_timeframe.append("1 ساعت")
    if abs(price - support_4h) / support_4h < 0.015:
        buy_reason.append("حمایت 4h")
        buy_timeframe.append("4 ساعت")
    
    for fvg in fvg_1h:
        if fvg['type'] == 'BULLISH_FVG' and abs(price - fvg['mid']) / fvg['mid'] < 0.01:
            buy_reason.append("FVG صعودی 1h")
            buy_timeframe.append("1 ساعت")
            break
    for fvg in fvg_4h:
        if fvg['type'] == 'BULLISH_FVG' and abs(price - fvg['mid']) / fvg['mid'] < 0.01:
            buy_reason.append("FVG صعودی 4h")
            buy_timeframe.append("4 ساعت")
            break
    
    for node in nodes_1h:
        if abs(price - node['price']) / node['price'] < 0.01:
            buy_reason.append("گره معاملاتی 1h")
            buy_timeframe.append("1 ساعت")
            break
    for node in nodes_4h:
        if abs(price - node['price']) / node['price'] < 0.01:
            buy_reason.append("گره معاملاتی 4h")
            buy_timeframe.append("4 ساعت")
            break
    
    if buy_reason:
        signals.append({
            'type': 'BUY',
            'timeframe': ', '.join(set(buy_timeframe)),
            'reason': ' + '.join(buy_reason),
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
                    'change_24h': float(item['priceChangePercent']),
                    'volume': float(item['quoteVolume'])
                })
            
            print(f"✅ {len(coins)} رمز ارز دریافت شد")
            return coins
        else:
            return get_top_40_fallback()
    except:
        return get_top_40_fallback()

def get_top_40_fallback():
    try:
        url = "https://api1.binance.com/api/v3/ticker/24hr"
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
                    'change_24h': float(item['priceChangePercent']),
                    'volume': float(item['quoteVolume'])
                })
            
            print(f"✅ {len(coins)} رمز ارز از آدرس جایگزین دریافت شد")
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
        "LTCUSDT", "BCHUSDT", "NEARUSDT", "ALGOUSDT", "VETUSDT",
        "ICPUSDT", "FILUSDT", "APTUSDT", "ARBUSDT", "STXUSDT",
        "AAVEUSDT", "MKRUSDT", "RNDRUSDT", "HNTUSDT", "KASUSDT",
        "THETAUSDT", "FETUSDT", "GRTUSDT", "RUNEUSDT", "INJUSDT",
        "SUIUSDT", "OPUSDT", "LDOUSDT", "EOSUSDT", "XTZUSDT"
    ]
    
    coins = []
    for symbol in symbols:
        name = symbol.replace('USDT', '')
        coins.append({
            'name': name,
            'symbol': symbol,
            'change_24h': 0,
            'volume': 0
        })
    
    print(f"📋 {len(coins)} رمز ارز از لیست دستی بارگذاری شد")
    return coins

print("🚀 ربات سیگنال‌گیری شروع شد!")
print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*50)

send("🤖 <b>ربات سیگنال‌گیری روشن شد!</b>\n"
     "📊 استراتژی: حمایت/مقاومت + FVG + گره معاملاتی\n"
     "⏱️ تایم فریم: ۱ ساعت و ۴ ساعت\n"
     "🪙 تعداد رمز ارزها: ۴۰")

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
            time.sleep(0.5)
        
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
