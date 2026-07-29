import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# --- Render Web Service সার্ভার ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- কাস্টম RSI ও SMA ক্যালকুলেটর ---
def calculate_indicators(df, period_rsi=14, period_sma=20):
    close = df['Close']
    sma = close.rolling(window=period_sma).mean().iloc[-1]
    
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period_rsi).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period_rsi).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1]), float(sma)

# --- ক্রিপ্টো এনালাইসিস ---
def get_crypto_analysis(symbol="BTC-USD"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1h")
        if df.empty:
            return f"⚠️ {symbol} এর কোনো ডেটা পাওয়া যায়নি।"

        price = df['Close'].iloc[-1]
        rsi, sma = calculate_indicators(df)

        signal = "⚖️ মার্কেট নিউট্রাল"
        if rsi < 30 and price < sma:
            signal = "🟢 বাই সিগন্যাল (BUY)"
        elif rsi > 70 and price > sma:
            signal = "🔴 সেল সিগন্যাল (SELL)"

        coin_name = symbol.replace("-USD", "").upper()
        msg = f"🚀 *{coin_name} এনালাইসিস রিপোর্ট*\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💰 মূল্য: ${price:,.2f}\n"
        msg += f"📊 RSI (14): {rsi:.2f}\n"
        msg += f"📈 SMA (20): ${sma:,.2f}\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"💡 সিদ্ধান্ত: {signal}\n"
        return msg
    except Exception as e:
        return f"❌ এরর: {str(e)}"

# --- টেক নিউজ ---
def get_ai_news():
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        top_ids = requests.get(url).json()[:5]
        
        news_msg = "🤖 *গ্লোবাল এআই ও টেক নিউজ ট্রেন্ড*\n━━━━━━━━━━━━━━━━━━━━\n"
        for idx, story_id in enumerate(top_ids, 1):
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story = requests.get(item_url).json()
            title = story.get("title", "No Title")
            link = story.get("url", "https://news.ycombinator.com")
            news_msg += f"{idx}. [{title}]({link})\n\n"
            
        return news_msg
    except Exception as e:
        return "⚠️ নিউজ লোড করতে সমস্যা হয়েছে।"

# --- টেলিগ্রাম কমান্ডস ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *স্বাগতম আপনার মাস্টার কমান্ড সেন্টারে!*\n\n"
        "আমি আপনার সুপার এজেন্ট। কমান্ড লিস্ট:\n"
        "🔹 `/trade btc` - ক্রিপ্টো এনালাইসিস\n"
        "🔹 `/ainews` - টপ টেক ও এআই নিউজ"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0] if context.args else "btc"
    formatted_symbol = f"{symbol.upper()}-USD"
    await update.message.reply_text("⏳ মার্কেট ডেটা প্রসেস করা হচ্ছে...")
    report = get_crypto_analysis(formatted_symbol)
    await update.message.reply_text(report, parse_mode="Markdown")

async def ainews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 লেটেস্ট নিউজ আনা হচ্ছে...")
    news = get_ai_news()
    await update.message.reply_text(news, parse_mode="Markdown", disable_web_page_preview=True)

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ডামি সার্ভার চালু রাখা (Render-এর জন্য দরকারি)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # টেলিগ্রাম অ্যাপ্লিকেশন বিল্ড
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trade", trade))
    application.add_handler(CommandHandler("ainews", ainews))
    
    print("🤖 সুপার এজেন্ট সফলভাবে চালু হয়েছে এবং কাজ করছে...")
    application.run_polling() 
