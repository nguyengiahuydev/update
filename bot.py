from zlapi import ZaloAPI, Message, ThreadType
from telegram import Bot
import logging
import os
import sys
import warnings
import asyncio
import datetime
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import json
import sqlite3
from typing import Dict, List, Any
import requests  # Thêm để gọi API check update
from packaging import version as pkg_version  # Thêm để so sánh version

# Cấu hình mã hóa UTF-8
if sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr is not None:
    sys.stderr.reconfigure(encoding='utf-8')

# Cấu hình logging
logging.basicConfig(
    filename='stderr.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

warnings.filterwarnings("ignore", message="resource_tracker")
logging.getLogger('websocket').setLevel(logging.ERROR)
logging.getLogger('zlapi').setLevel(logging.ERROR)
os.environ['PYTHONWARNINGS'] = 'ignore::UserWarning'

# Phiên bản hiện tại của bot
VERSION = "1.1.1"  # Thay đổi khi update thủ công

# URL của Google Apps Script Web App (thay bằng URL thực tế của bạn)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycby1Sg-23dmFN5brIPtdVgfYNZCtRtSWMf_MvRPtNJBYGaz5Ijny3VlvJX0ybHrCRw6zfw/exec"  # Thay YOUR_WEB_APP_ID bằng ID thực

# Cấu hình Zalo
COOKIES = {
    "ZConsent": "timestamp=1756612297859&location=https://zalo.me/pc",
    "ozi": "2000.S8lYxye10ezjthIdmGa0YsFTikl63GB1PDkrxyaB2Sit.1",
    "_ga_RYD7END4JE": "GS2.2.s1758610950$o2$g1$t1758610951$j59$l0$h0",
    "_ga_YS1V643LGV": "GS2.1.s1758610950$o3$g0$t1758611068$j60$l0$h0",
    "_gcl_au": "1.1.910863574.1758613163",
    "_fbp": "fb.1.1758613162803.970693199454387",
    "_ga": "GA1.2.1884152419.1756603830",
    "_ga_NVN38N77J3": "GS2.2.s1759243696$o2$g1$t1759243705$j51$l0$h0",
    "_ga_E63JS7SPBL": "GS2.1.s1759243696$o2$g1$t1759243929$j60$l0$h0",
    "_zlang": "vn",
    "_gid": "GA1.2.1586883556.1761383718",
    "__zi": "3000.SSZzejyD0jydXQckra00a3BBfxQL71AQV8UajD1M5vnsXg7yqrOHrd60flZSK1hSDm.1",
    "__zi-legacy": "3000.SSZzejyD0jydXXckra00a3BBfxQL71AQV8UajD1M5vnsXg7yqrOHrd60flZSK1hSDm.1",
    "app.event.zalo.me": "7870179498669832369",
    "_ga_3EM8ZPYYN3": "GS2.2.s1761383718$o2$g1$t1761384151$j60$l0$h0",
    "zpsid": "tNbB.328664273.50.hpuc1XGzINV5ETva63r9Ts5EEqGc1Nz180z-H6yXNTl5MRFi5TNVYtmzINS",
    "zpw_sek": "PwV6.328664273.a0.Q1kk-pC_RcdYE_bw4ZzkQKWT2m8H1KmeNqq274PUB0DGV5aAHqe_4K5G015Y0bDBJaHoVP_k2fEeFeR_prTkQG"
}

IMEI = "c0aa935f-9c25-4a59-8a2d-23b6fe347bbc-3ade46e10ab46df1d7d395ddaa715a24"

# Cấu hình mặc định
ZALO_PHONE = "0355656730"
ZALO_PASSWORD = "Huy@24149345"
TELEGRAM_BOT_TOKEN = "8475520566:AAFRnqn9cfEqAqdrkVyJ9XKG8vrLcNa8_2E"
TELEGRAM_CHAT_ID = "6931026785"
OWNER_ID = "55737151930431655"

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "zalo": {
                "phone": ZALO_PHONE,
                "password": ZALO_PASSWORD,
                "owner_id": OWNER_ID,
                "auto_response": "(ĐÂY LÀ TIN NHẮN TỰ ĐỘNG)\n\nHiện tại mình đang bận, vui lòng chờ mình rep.\n\nMua tool và source code tại:\nhttps://shopphanmemvip.site\n\nCảm ơn bạn!"
            },
            "telegram": {
                "bot_token": TELEGRAM_BOT_TOKEN,
                "chat_id": TELEGRAM_CHAT_ID
            },
            "settings": {
                "auto_start": False,
                "notify_owner": True,
                "response_delay": 2
            }
        }
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Lỗi đọc config: {e}")
                return self.default_config.copy()
        return self.default_config.copy()
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi lưu config: {e}")
            return False
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        return self.save_config()

class Statistics:
    def __init__(self, db_file="bot_stats.db"):
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sender_id TEXT,
                sender_name TEXT,
                message_text TEXT,
                thread_id TEXT,
                response_sent BOOLEAN,
                telegram_notified BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_stats (
                date DATE PRIMARY KEY,
                messages_received INTEGER DEFAULT 0,
                responses_sent INTEGER DEFAULT 0,
                notifications_sent INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_message(self, sender_id: str, sender_name: str, message: str, 
                   thread_id: str, response_sent: bool, telegram_notified: bool):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (sender_id, sender_name, message_text, thread_id, response_sent, telegram_notified)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (sender_id, sender_name, message, thread_id, response_sent, telegram_notified))
        
        # Update daily stats
        today = datetime.date.today().isoformat()
        cursor.execute('''
            INSERT OR REPLACE INTO bot_stats (date, messages_received, responses_sent, notifications_sent)
            VALUES (?, 
                    COALESCE((SELECT messages_received FROM bot_stats WHERE date = ?), 0) + 1,
                    COALESCE((SELECT responses_sent FROM bot_stats WHERE date = ?), 0) + ?,
                    COALESCE((SELECT notifications_sent FROM bot_stats WHERE date = ?), 0) + ?)
        ''', (today, today, today, 1 if response_sent else 0, today, 1 if telegram_notified else 0))
        
        conn.commit()
        conn.close()
    
    def get_daily_stats(self, date: str = None) -> Dict:
        if date is None:
            date = datetime.date.today().isoformat()
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT messages_received, responses_sent, notifications_sent 
            FROM bot_stats WHERE date = ?
        ''', (date,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'messages_received': result[0],
                'responses_sent': result[1],
                'notifications_sent': result[2]
            }
        return {'messages_received': 0, 'responses_sent': 0, 'notifications_sent': 0}

class MyBot(ZaloAPI):
    def __init__(self, output_queue, config_manager, statistics, phone=ZALO_PHONE, password=ZALO_PASSWORD, imei=IMEI, session_cookies=COOKIES, *args, **kwargs):
        super().__init__(phone or "", password or "", imei=imei, session_cookies=session_cookies, *args, **kwargs)
        self.config_manager = config_manager
        self.statistics = statistics
        self.AUTO_RESPONSE = self.config_manager.get("zalo.auto_response", "(ĐÂY LÀ TIN NHẮN TỰ ĐỘNG)\n\nHiện tại mình đang bận, vui lòng chờ mình rep.\n\nMua tool và source code tại:\nhttps://shopphanmemvip.site\n\nCảm ơn bạn!")
        self.telegram_bot = Bot(token=self.config_manager.get("telegram.bot_token", TELEGRAM_BOT_TOKEN))
        self.output_queue = output_queue

    def onListening(self):
        self.output_queue.put("[INFO] Bot is listening")
        logging.info("Bot is listening")

    async def send_telegram_notification(self, message, author_id, thread_id, sender_name=None):
        try:
            sender_display = sender_name if sender_name else f"ID {author_id}"
            telegram_message = (
                f"Zalo Message Received\n"
                f"From: {sender_display}\n"
                f"Thread: {thread_id}\n"
                f"Content: {message}\n"
                f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await self.telegram_bot.send_message(
                chat_id=self.config_manager.get("telegram.chat_id", TELEGRAM_CHAT_ID), 
                text=telegram_message
            )
            self.output_queue.put(f"[OK] Sent Telegram notification: {telegram_message}")
            logging.info(f"Sent Telegram notification: {telegram_message}")
            return True
        except Exception as e:
            self.output_queue.put(f"[ERR] Failed to send Telegram notification: {e}")
            logging.error(f"Failed to send Telegram notification: {e}")
            return False

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        self.output_queue.put(f"[INFO] Received: {message}, Thread: {thread_id}, Type: {thread_type}, Author: {author_id}")
        logging.info(f"Received: {message}, Thread: {thread_id}, Type: {thread_type}, Author: {author_id}")
        
        owner_id = self.config_manager.get("zalo.owner_id", OWNER_ID)
        
        if (thread_type == ThreadType.USER and
            isinstance(message, str) and
            message != self.AUTO_RESPONSE and
            author_id != owner_id):
            
            # Lấy thông tin người gửi
            sender_name = None
            try:
                user_info = self.getUserInfo(author_id)
                sender_name = user_info.get('displayName', None) if user_info else None
                if sender_name:
                    self.output_queue.put(f"[INFO] Sender name: {sender_name}")
                    logging.info(f"Sender name: {sender_name}")
                else:
                    self.output_queue.put(f"[INFO] No sender name found for author_id: {author_id}")
                    logging.info(f"No sender name found for author_id: {author_id}")
            except Exception as e:
                self.output_queue.put(f"[ERR] Failed to fetch sender name: {e}")
                logging.error(f"Failed to fetch sender name: {e}")

            # Gửi tin nhắn trả lời trên Zalo
            self.sendMessage(Message(text=self.AUTO_RESPONSE), thread_id, ThreadType.USER)
            
            # Gửi thông báo đến Telegram
            telegram_success = asyncio.run(self.send_telegram_notification(message, author_id, thread_id, sender_name))
            
            # Log thống kê
            self.statistics.log_message(
                author_id, sender_name or str(author_id), message, 
                thread_id, True, telegram_success
            )
            
        elif thread_type == ThreadType.GROUP:
            self.output_queue.put(f"[INFO] Ignored group message from thread: {thread_id}")
            logging.info(f"Ignored group message from thread: {thread_id}")
        elif author_id == owner_id:
            self.output_queue.put(f"[INFO] Ignored message from owner: {author_id}")
            logging.info(f"Ignored message from owner: {author_id}")

def run_bot(output_queue, config_manager, statistics):
    bot = MyBot(
        output_queue, 
        config_manager, 
        statistics,
        phone=config_manager.get("zalo.phone", ZALO_PHONE),
        password=config_manager.get("zalo.password", ZALO_PASSWORD),
        imei=IMEI, 
        session_cookies=COOKIES
    )
    while True:
        try:
            bot.listen()
        except Exception as e:
            output_queue.put(f"[ERR] Bot encountered an error: {e}. Restarting...")
            logging.error(f"Bot encountered an error: {e}. Restarting...")
        finally:
            output_queue.put("[INFO] Bot stopped, restarting in 5 seconds...")
            logging.info("Bot stopped, restarting in 5 seconds...")
            time.sleep(5)

class BotControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zalo Bot Controller")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Khởi tạo managers
        self.config_manager = ConfigManager()
        self.statistics = Statistics()
        
        # Biến điều khiển
        self.running = False
        self.bot_thread = None
        self.output_queue = queue.Queue()
        
        # Tạo giao diện
        self.setup_gui()
        
        # Check update tự động khi khởi động
        self.check_for_update()
        
        # Bắt đầu kiểm tra queue
        self.check_queue()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 Zalo Auto Response Bot", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Status frame
        self.setup_status_frame(main_frame)
        
        # Configuration frame
        self.setup_config_frame(main_frame)
        
        # Control buttons
        self.setup_control_buttons(main_frame)
        
        # Console output
        self.setup_console(main_frame)
        
    def setup_status_frame(self, parent):
        status_frame = ttk.LabelFrame(parent, text="Trạng thái hệ thống", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        # Status indicators
        indicators_frame = ttk.Frame(status_frame)
        indicators_frame.pack(fill=tk.X)
        
        # Zalo status
        ttk.Label(indicators_frame, text="Zalo:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.zalo_status = tk.Canvas(indicators_frame, width=20, height=20)
        self.zalo_status.grid(row=0, column=1, padx=5)
        self.zalo_light = self.zalo_status.create_oval(2, 2, 18, 18, fill="red")
        
        # Telegram status
        ttk.Label(indicators_frame, text="Telegram:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.telegram_status = tk.Canvas(indicators_frame, width=20, height=20)
        self.telegram_status.grid(row=0, column=3, padx=5)
        self.telegram_light = self.telegram_status.create_oval(2, 2, 18, 18, fill="red")
        
        # Bot status
        ttk.Label(indicators_frame, text="Bot:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.bot_status = tk.Canvas(indicators_frame, width=20, height=20)
        self.bot_status.grid(row=0, column=5, padx=5)
        self.bot_light = self.bot_status.create_oval(2, 2, 18, 18, fill="red")
        
        # Status text
        self.status_text = ttk.Label(status_frame, text="Chưa kết nối", foreground="red")
        self.status_text.pack(pady=5)
        
        # Stats info
        stats = self.statistics.get_daily_stats()
        stats_text = f"Hôm nay: {stats['messages_received']} tin nhắn, {stats['responses_sent']} phản hồi"
        self.stats_label = ttk.Label(status_frame, text=stats_text, foreground="blue")
        self.stats_label.pack(pady=2)
        
    def setup_config_frame(self, parent):
        config_frame = ttk.LabelFrame(parent, text="Cấu hình", padding="10")
        config_frame.pack(fill=tk.X, pady=10)
        
        # Zalo config
        ttk.Label(config_frame, text="Zalo Phone:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.phone_var = tk.StringVar(value=self.config_manager.get("zalo.phone", ZALO_PHONE))
        ttk.Entry(config_frame, textvariable=self.phone_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(config_frame, text="Owner ID:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.owner_var = tk.StringVar(value=self.config_manager.get("zalo.owner_id", OWNER_ID))
        ttk.Entry(config_frame, textvariable=self.owner_var, width=20).grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Telegram config
        ttk.Label(config_frame, text="Telegram Token:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.token_var = tk.StringVar(value=self.config_manager.get("telegram.bot_token", TELEGRAM_BOT_TOKEN))
        ttk.Entry(config_frame, textvariable=self.token_var, width=20, show="*").grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(config_frame, text="Chat ID:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.chat_id_var = tk.StringVar(value=self.config_manager.get("telegram.chat_id", TELEGRAM_CHAT_ID))
        ttk.Entry(config_frame, textvariable=self.chat_id_var, width=20).grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Auto response message - SỬA Ở ĐÂY: Dùng Text widget thay vì Entry
        ttk.Label(config_frame, text="Auto Response:").grid(row=2, column=0, sticky=tk.NW, pady=2)
        
        # Tạo frame cho text area và scrollbar
        response_frame = ttk.Frame(config_frame)
        response_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E, pady=2)
        
        # Text widget cho tin nhắn nhiều dòng
        self.response_text = scrolledtext.ScrolledText(
            response_frame, 
            wrap=tk.WORD, 
            width=50, 
            height=6,
            font=("Arial", 10)
        )
        self.response_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Đặt nội dung mặc định
        default_response = self.config_manager.get("zalo.auto_response", 
            "(ĐÂY LÀ TIN NHẮN TỰ ĐỘNG)\n\nHiện tại mình đang bận, vui lòng chờ mình rep.\n\nMua tool và source code tại:\nhttps://shopphanmemvip.site\n\nCảm ơn bạn!")
        self.response_text.insert(1.0, default_response)
        
        # Configure grid để mở rộng
        config_frame.columnconfigure(1, weight=1)
        
    def setup_control_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="🚀 Khởi động Bot", 
                                   command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Dừng Bot", 
                                  command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(button_frame, text="💾 Lưu cấu hình", 
                                  command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_btn = ttk.Button(button_frame, text="📝 Test Tin nhắn", 
                                  command=self.test_message)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.stats_btn = ttk.Button(button_frame, text="📊 Thống kê", 
                                   command=self.show_stats)
        self.stats_btn.pack(side=tk.LEFT, padx=5)
        
        self.update_btn = ttk.Button(button_frame, text="🔄 Check Update", 
                                    command=self.check_for_update)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(button_frame, text="🗑️ Xóa Console", 
                                   command=self.clear_console)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
    def setup_console(self, parent):
        console_frame = ttk.LabelFrame(parent, text="Console Output", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=20,
            font=("Consolas", 10)
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        # Thêm màu sắc cho các loại log
        self.console_text.tag_config("INFO", foreground="blue")
        self.console_text.tag_config("ERROR", foreground="red")
        self.console_text.tag_config("SUCCESS", foreground="green")
        self.console_text.tag_config("WARNING", foreground="orange")
        
    def update_status(self, status_type, is_connected):
        colors = {"green": "#00ff00", "red": "#ff0000", "yellow": "#ffff00"}
        
        if status_type == "zalo":
            color = colors["green"] if is_connected else colors["red"]
            self.zalo_status.itemconfig(self.zalo_light, fill=color)
        elif status_type == "telegram":
            color = colors["green"] if is_connected else colors["red"]
            self.telegram_status.itemconfig(self.telegram_light, fill=color)
        elif status_type == "bot":
            color = colors["green"] if is_connected else colors["red"]
            self.bot_status.itemconfig(self.bot_light, fill=color)
            
        if self.running:
            self.status_text.config(text="Bot đang chạy", foreground="green")
        else:
            self.status_text.config(text="Bot đã dừng", foreground="red")
    
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.console_text.insert(tk.END, formatted_message + "\n", level)
        self.console_text.see(tk.END)
        
    def check_queue(self):
        try:
            while True:
                message = self.output_queue.get_nowait()
                if message.startswith("[ERR]"):
                    self.log_message(message, "ERROR")
                elif message.startswith("[OK]"):
                    self.log_message(message, "SUCCESS")
                else:
                    self.log_message(message, "INFO")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
    
    def start_bot(self):
        if not self.running:
            # Lưu cấu hình trước khi khởi động
            self.save_config()
            
            self.running = True
            self.bot_thread = threading.Thread(
                target=run_bot, 
                args=(self.output_queue, self.config_manager, self.statistics)
            )
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.update_status("bot", True)
            self.log_message("Bot đã được khởi động", "SUCCESS")
    
    def stop_bot(self):
        if self.running:
            self.running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.update_status("bot", False)
            self.log_message("Bot đã được dừng", "WARNING")
    
    def save_config(self):
        try:
            self.config_manager.set("zalo.phone", self.phone_var.get())
            self.config_manager.set("zalo.owner_id", self.owner_var.get())
            self.config_manager.set("telegram.bot_token", self.token_var.get())
            self.config_manager.set("telegram.chat_id", self.chat_id_var.get())
            
            # Lấy nội dung từ Text widget (có hỗ trợ xuống dòng)
            response_content = self.response_text.get(1.0, tk.END).strip()
            self.config_manager.set("zalo.auto_response", response_content)
            
            self.log_message("Cấu hình đã được lưu", "SUCCESS")
            return True
        except Exception as e:
            self.log_message(f"Lỗi khi lưu cấu hình: {e}", "ERROR")
            return False
    
    def test_message(self):
        """Hiển thị preview tin nhắn auto response"""
        try:
            response_content = self.response_text.get(1.0, tk.END).strip()
            test_window = tk.Toplevel(self.root)
            test_window.title("Preview Tin nhắn")
            test_window.geometry("400x300")
            
            ttk.Label(test_window, text="📝 Preview Tin nhắn Auto Response", 
                     font=("Arial", 12, "bold")).pack(pady=10)
            
            preview_text = scrolledtext.ScrolledText(
                test_window, 
                wrap=tk.WORD, 
                width=45, 
                height=10,
                font=("Arial", 10)
            )
            preview_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            preview_text.insert(1.0, response_content)
            preview_text.config(state=tk.DISABLED)  # Chỉ đọc
            
            ttk.Button(test_window, text="Đóng", 
                      command=test_window.destroy).pack(pady=10)
            
        except Exception as e:
            self.log_message(f"Lỗi khi test tin nhắn: {e}", "ERROR")
    
    def show_stats(self):
        stats = self.statistics.get_daily_stats()
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Thống kê")
        stats_window.geometry("300x200")
        
        ttk.Label(stats_window, text="📊 Thống kê hôm nay", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Label(stats_window, text=f"Tin nhắn nhận được: {stats['messages_received']}").pack(pady=5)
        ttk.Label(stats_window, text=f"Phản hồi tự động: {stats['responses_sent']}").pack(pady=5)
        ttk.Label(stats_window, text=f"Thông báo Telegram: {stats['notifications_sent']}").pack(pady=5)
        
    def clear_console(self):
        self.console_text.delete(1.0, tk.END)
        self.log_message("Console đã được xóa", "INFO")
    
    def check_for_update(self):
        """Kiểm tra update từ Google Apps Script API"""
        try:
            response = requests.get(WEB_APP_URL)
            response.raise_for_status()  # Raise nếu lỗi HTTP
            data = response.json()
            new_version = data.get('version')
            update_url = data.get('updateUrl')
            description = data.get('description', '')  # Lấy description, mặc định rỗng nếu không có
            
            if not new_version or not update_url:
                raise ValueError("Dữ liệu API không hợp lệ")
            
            if pkg_version.parse(new_version) > pkg_version.parse(VERSION):
                # Hiển thị description với xuống dòng (\n được giữ nguyên trong messagebox)
                update_message = f"Phiên bản mới {new_version} có sẵn (hiện tại: {VERSION}).\n\nTính năng mới:\n{description}\n\nBạn có muốn update không?"
                if messagebox.askyesno("Update Có Sẵn", update_message):
                    try:
                        # Tải file update về temp
                        update_response = requests.get(update_url, stream=True)
                        update_response.raise_for_status()
                        with open('bot_updated.py', 'wb') as f:
                            for chunk in update_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Thay thế file hiện tại
                        os.replace('bot_updated.py', 'bot.py')
                        
                        messagebox.showinfo("Update Hoàn Thành", "Update thành công. Vui lòng khởi động lại ứng dụng để áp dụng thay đổi.")
                        self.log_message(f"Update thành công lên version {new_version}. Description: {description}", "SUCCESS")
                    except Exception as e:
                        messagebox.showerror("Lỗi Update", f"Lỗi khi update: {str(e)}")
                        self.log_message(f"Lỗi update: {str(e)}", "ERROR")
            else:
                self.log_message("Không có update mới", "INFO")
        except Exception as e:
            self.log_message(f"Lỗi khi check update: {str(e)}", "ERROR")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotControlGUI(root)
    root.mainloop()