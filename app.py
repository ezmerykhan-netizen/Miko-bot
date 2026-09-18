import os
import threading
from flask import Flask
from main import main  # از فایل main.py ایمپورت می‌کنه

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    # ربات رو تو یه ترد جدا اجرا کن
    bot_thread = threading.Thread(target=main, daemon=True)
    bot_thread.start()
    
    # وب‌سرور رو اجرا کن (Render پورت رو از env می‌خونه)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
