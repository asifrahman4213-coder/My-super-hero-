import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import yfinance as yf
import pandas_ta as ta
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")

# --- Render-এর Free Web Service সচল রাখার জন্য ডামি সার্ভার ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# --- মডিউল ১: ক্রিপ্টো ট্রেডিং এনালাইসিস ---
def get_crypto_analysis(symbol="BTC-USD"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1mo", interval="1h")
        if df.empty:
            return f"⚠️ {symbol} এর কোনো ডেটা পাওয়া যায়নি।"

        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['SMA_20'] = ta.sma(df['Close'], length=20)

        price = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        sma = df['SMA_20'].iloc[-1]

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

# --- মডিউল ২: টপ ১০ এআই নিউজ স্ক্যাপার ---
def get_ai_news():
    try:
        url = "https://news.ycombinator.com/show"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        
        stories = soup.select(".titleline > a")[:5]
        news_msg = "🤖 *গ্লোবাল এআই ও টেক নিউজ ট্রেন্ড*\n━━━━━━━━━━━━━━━━━━━━\n"
        
        for idx, story in enumerate(stories, 1):
            title = story.text
            link = story['href']
            news_msg += f"{idx}. [{title}]({link})\n\n"
            
        return news_msg
    except Exception as e:
        return "⚠️ নিউজ লোড করতে সমস্যা হয়েছে।"

# --- টেলিগ্রাম কমান্ড হ্যান্ডলারস ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **স্বাগতম আপনার মাস্টার কমান্ড সেন্টারে!**\n\n"
        "আমি আপনার সুপার এজেন্ট। আমাকে যেসব নির্দেশ দিতে পারেন:\n"
        "🔹 `/trade btc` - ক্রিপ্টো এনালাইসিস (যেমন: btc, eth, sol)\n"
        "🔹 `/ainews` - টপ টেক ও এআই নিউজ ট্রেন্ড\n"
        "🔹 `/help` - কমান্ড লিস্ট"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def trade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = context.args[0] if context.args else "btc"
    formatted_symbol = f"{symbol.upper()}-USD"
    await update.message.reply_text("⏳ মার্কেট ডেটা প্রসেস করা হচ্ছে...")
    report = get_crypto_analysis(formatted_symbol)
    await update.message.reply_text(report, parse_mode="Markdown")

async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 লেটেস্ট এআই নিউজ আনা হচ্ছে...")
    news = get_ai_news()
    await update.message.reply_text(news, parse_mode="Markdown", disable_web_page_preview=True)

# --- মূল রানার ---
if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে এইচটিটিপি সার্ভার চালুকরণ (Render-এর জন্য)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("trade", trade_command))
    app.add_handler(CommandHandler("ainews", news_command))
    
    print("🤖 Render-এ সুপার এজেন্ট চালু হয়েছে...")
    app.run_polling()
