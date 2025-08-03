import logging
import os
import tempfile
import random
import time
import threading
from typing import Tuple, Dict, Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_URL = os.getenv('CHANNEL_URL', "https://t.me/WorkGlows")
GROUP_URL = os.getenv('GROUP_URL', "https://t.me/SoulMeetsHQ")
CATBOX_UPLOAD_URL = "https://catbox.moe/user/api.php"
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB
MAX_GIF_SIZE = 20 * 1024 * 1024    # 20 MB for GIFs
BANNED_EXTENSIONS = {'.exe', '.scr', '.cpl', '.doc', '.docx', '.docm', '.jar'}

# Random photo URLs for visual responses
RANDOM_PHOTOS = [
    "https://ik.imagekit.io/asadofc/Images1.png",
    "https://ik.imagekit.io/asadofc/Images2.png",
    "https://ik.imagekit.io/asadofc/Images3.png",
    "https://ik.imagekit.io/asadofc/Images4.png",
    "https://ik.imagekit.io/asadofc/Images5.png",
    "https://ik.imagekit.io/asadofc/Images6.png",
    "https://ik.imagekit.io/asadofc/Images7.png",
    "https://ik.imagekit.io/asadofc/Images8.png",
    "https://ik.imagekit.io/asadofc/Images9.png",
    "https://ik.imagekit.io/asadofc/Images10.png",
    "https://ik.imagekit.io/asadofc/Images11.png",
    "https://ik.imagekit.io/asadofc/Images12.png",
    "https://ik.imagekit.io/asadofc/Images13.png",
    "https://ik.imagekit.io/asadofc/Images14.png",
    "https://ik.imagekit.io/asadofc/Images15.png",
    "https://ik.imagekit.io/asadofc/Images16.png",
    "https://ik.imagekit.io/asadofc/Images17.png",
    "https://ik.imagekit.io/asadofc/Images18.png",
    "https://ik.imagekit.io/asadofc/Images19.png",
    "https://ik.imagekit.io/asadofc/Images20.png",
    "https://ik.imagekit.io/asadofc/Images21.png",
    "https://ik.imagekit.io/asadofc/Images22.png",
    "https://ik.imagekit.io/asadofc/Images23.png",
    "https://ik.imagekit.io/asadofc/Images24.png",
    "https://ik.imagekit.io/asadofc/Images25.png",
    "https://ik.imagekit.io/asadofc/Images26.png",
    "https://ik.imagekit.io/asadofc/Images27.png",
    "https://ik.imagekit.io/asadofc/Images28.png",
    "https://ik.imagekit.io/asadofc/Images29.png",
    "https://ik.imagekit.io/asadofc/Images30.png",
    "https://ik.imagekit.io/asadofc/Images31.png",
    "https://ik.imagekit.io/asadofc/Images32.png",
    "https://ik.imagekit.io/asadofc/Images33.png",
    "https://ik.imagekit.io/asadofc/Images34.png",
    "https://ik.imagekit.io/asadofc/Images35.png",
    "https://ik.imagekit.io/asadofc/Images36.png",
    "https://ik.imagekit.io/asadofc/Images37.png",
    "https://ik.imagekit.io/asadofc/Images38.png",
    "https://ik.imagekit.io/asadofc/Images39.png",
    "https://ik.imagekit.io/asadofc/Images40.png"
]

# Bot messages
START_MESSAGE = f"""🔗 <b>Catbox File Upload Bot</b>

Send me any file and I'll upload it to Catbox and give you a direct link!

Just send me a file and I'll handle the rest! 📎"""

HELP_SHORT_MESSAGE = f"""
🔗 <b>Quick Start Guide:</b>

1. Send me any file
2. Wait for upload magic
3. Get your Catbox link!

<b>Essential Info:</b>
• Max size: 200 MB
• GIF limit: 20 MB
• Permanent storage
• Zero compression

Want the full scoop? Expand below! 👇"""

HELP_DETAILED_MESSAGE = f"""
🔗 <b>Complete Bot Guide:</b>

<b>All Supported Files:</b>
• Documents, Images, Videos, Audio
• Voice notes, Video messages, Stickers

<b>Rules & Restrictions:</b>
• Forbidden: .exe, .scr, .cpl, .doc, .jar
• No malware, illegal content, full episodes
• Adult content is permitted

☁️ Files live forever on Catbox!"""

# Success messages for uploads
SUCCESS_MESSAGES = [
    "🎉 <b>Boom!</b> Your file is now living its best life on Catbox!",
    "✨ <b>Magic happened!</b> Your file has been successfully uploaded!",
    "🚀 <b>Houston, we have liftoff!</b> File uploaded successfully!",
    "🎯 <b>Bulls-eye!</b> Your file hit Catbox perfectly!",
    "⚡ <b>Lightning fast!</b> Your file is now ready for the world!",
    "🌟 <b>Success!</b> Your file has joined the Catbox family!",
    "🔥 <b>Hot stuff!</b> Your file is now burning up the internet!",
    "💫 <b>Stellar upload!</b> Your file is now among the stars at Catbox!",
    "🎊 <b>Party time!</b> Your file upload was a complete success!",
    "🏆 <b>Victory!</b> Your file has conquered Catbox!",
    "🎪 <b>Ta-da!</b> Your file is now performing on the Catbox stage!",
    "🌈 <b>Rainbow success!</b> Your file has reached the pot of gold!",
    "🎭 <b>Drama-free upload!</b> Your file is now ready for its close-up!",
    "🎨 <b>Masterpiece delivered!</b> Your file is now on display at Catbox!",
    "🎵 <b>Sweet melody!</b> Your file upload hit all the right notes!",
    "🎮 <b>Level completed!</b> Your file has successfully reached Catbox!",
    "🎂 <b>Piece of cake!</b> Your file upload was smooth as butter!",
    "🎪 <b>Center ring success!</b> Your file is now the main attraction!",
    "🌺 <b>Blooming beautiful!</b> Your file has blossomed on Catbox!",
    "🎯 <b>Direct hit!</b> Your file landed exactly where it needed to be!"
]

# Logging setup
class Colors:
    BLUE = '\033[94m'      # INFO/WARNING
    GREEN = '\033[92m'     # DEBUG
    YELLOW = '\033[93m'    # INFO
    RED = '\033[91m'       # ERROR
    RESET = '\033[0m'      # Reset color
    BOLD = '\033[1m'       # Bold text

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to entire log messages"""

    COLORS = {
        'DEBUG': Colors.GREEN,
        'INFO': Colors.YELLOW,
        'WARNING': Colors.BLUE,
        'ERROR': Colors.RED,
    }

    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)

        # Get color based on log level
        color = self.COLORS.get(record.levelname, Colors.RESET)

        # Apply color to the entire message
        colored_format = f"{color}{original_format}{Colors.RESET}"

        return colored_format

def setup_colored_logging():
    """Setup colored logging configuration"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create colored formatter with enhanced format
    formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger

# Initialize colored logger
logger = setup_colored_logging()

def is_private_chat(update: Update) -> bool:
    """Check if the message is from a private chat"""
    return update.message.chat.type == 'private'

def extract_user_info(msg: Message) -> Dict[str, Any]:
    """Extract user and chat information from message"""
    logger.debug("🔍 Extracting user information from message")
    try:
        u = msg.from_user
        c = msg.chat
        info = {
            "user_id": u.id if u else None,
            "username": u.username if u else None,
            "full_name": u.full_name if u else "Unknown User",
            "chat_id": c.id,
            "chat_type": c.type,
            "chat_title": c.title or c.first_name or "",
            "chat_username": f"@{c.username}" if c.username else "No Username",
            "chat_link": f"https://t.me/{c.username}" if c.username else "No Link",
        }
        logger.info(
            f"📑 User info extracted: {info['full_name']} (@{info['username']}) "
            f"[ID: {info['user_id']}] in {info['chat_title']} [{info['chat_id']}] {info['chat_link']}"
        )
        return info
    except Exception as e:
        logger.error(f"❌ Error extracting user info: {e}")
        return {
            "user_id": None,
            "username": None,
            "full_name": "Unknown User",
            "chat_id": msg.chat.id if msg.chat else None,
            "chat_type": "unknown",
            "chat_title": "Unknown Chat",
            "chat_username": "No Username",
            "chat_link": "No Link",
        }

def log_with_user_info(level: str, message: str, user_info: Dict[str, Any]) -> None:
    """Log message with user information"""
    try:
        user_detail = (
            f"👤 {user_info['full_name']} (@{user_info['username']}) "
            f"[ID: {user_info['user_id']}] | "
            f"💬 {user_info['chat_title']} [{user_info['chat_id']}] "
            f"({user_info['chat_type']}) {user_info['chat_link']}"
        )
        full_message = f"{message} | {user_detail}"

        if level.upper() == "INFO":
            logger.info(full_message)
        elif level.upper() == "DEBUG":
            logger.debug(full_message)
        elif level.upper() == "WARNING":
            logger.warning(full_message)
        elif level.upper() == "ERROR":
            logger.error(full_message)
        else:
            logger.info(full_message)
    except Exception as e:
        logger.error(f"❌ Error in log_with_user_info: {e}")
        logger.info(message)  # Fallback to simple logging

class DummyHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for keep-alive server"""

    def do_GET(self):
        try:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Catbox bot is alive!")
            logger.debug("🌐 HTTP GET request handled successfully")
        except Exception as e:
            logger.error(f"❌ Error handling HTTP GET request: {e}")
            self.send_response(500)
            self.end_headers()

    def do_HEAD(self):
        try:
            self.send_response(200)
            self.end_headers()
            logger.debug("🌐 HTTP HEAD request handled successfully")
        except Exception as e:
            logger.error(f"❌ Error handling HTTP HEAD request: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

def start_dummy_server() -> None:
    """Start dummy HTTP server for deployment platforms"""
    try:
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), DummyHandler)
        logger.info(f"🌐 Dummy server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Error starting dummy server: {e}")
        logger.warning("⚠️ Continuing without HTTP server...")

def is_file_allowed(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Check if file meets upload requirements
    
    Args:
        filename: Name of the file
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_allowed, error_message)
    """
    try:
        logger.debug(f"🔍 Checking file: {filename} ({file_size} bytes)")
        
        # Check file size limit
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / (1024 * 1024)
            error_msg = f"File too large! Maximum size is 200 MB, your file is {size_mb:.1f} MB"
            logger.warning(f"⚠️ File rejected - too large: {size_mb:.1f} MB")
            return False, error_msg
        
        # Check banned extensions
        for ext in BANNED_EXTENSIONS:
            if filename.lower().endswith(ext):
                error_msg = f"File type not allowed! Banned extensions: {', '.join(BANNED_EXTENSIONS)}"
                logger.warning(f"⚠️ File rejected - banned extension: {ext}")
                return False, error_msg
        
        # Special GIF size limit
        if filename.lower().endswith('.gif') and file_size > MAX_GIF_SIZE:
            size_mb = file_size / (1024 * 1024)
            error_msg = f"GIF too large! Maximum size for GIF is 20 MB, your file is {size_mb:.1f} MB. Use WebM format for larger animations."
            logger.warning(f"⚠️ GIF rejected - too large: {size_mb:.1f} MB")
            return False, error_msg
        
        logger.info(f"✅ File validation passed: {filename}")
        return True, ""
        
    except Exception as e:
        logger.error(f"❌ Error in file validation: {e}")
        return False, f"Error validating file: {str(e)}"

async def upload_to_catbox(file_path: str, filename: str) -> str:
    """
    Upload file to catbox.moe
    
    Args:
        file_path: Path to local file
        filename: Original filename
        
    Returns:
        URL of uploaded file
        
    Raises:
        Exception: If upload fails
    """
    logger.info(f"🚀 Starting upload to Catbox: {filename}")
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as file:
                data = aiohttp.FormData()
                data.add_field('reqtype', 'fileupload')
                data.add_field('fileToUpload', file, filename=filename)
                
                logger.debug("📤 Sending file to Catbox API...")
                async with session.post(CATBOX_UPLOAD_URL, data=data) as response:
                    if response.status == 200:
                        result = await response.text()
                        result = result.strip()
                        if result.startswith('https://files.catbox.moe/'):
                            logger.info(f"✅ Upload successful: {result}")
                            return result
                        else:
                            error_msg = f"Unexpected response from Catbox: {result}"
                            logger.error(f"❌ {error_msg}")
                            raise Exception(error_msg)
                    else:
                        error_text = await response.text()
                        error_msg = f"HTTP {response.status}: {error_text}"
                        logger.error(f"❌ Upload failed: {error_msg}")
                        raise Exception(error_msg)
                        
    except aiohttp.ClientError as e:
        logger.error(f"❌ Network error during upload: {e}")
        raise Exception(f"Network error: {str(e)}")
    except IOError as e:
        logger.error(f"❌ File I/O error during upload: {e}")
        raise Exception(f"File error: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error during upload: {e}")
        raise

async def process_file(update: Update, context: ContextTypes.DEFAULT_TYPE, file_obj, filename: str):
    """
    Process and upload a file - ONLY works in private chats
    
    Args:
        update: Telegram update object
        context: Bot context
        file_obj: Telegram file object
        filename: Name of the file
    """
    # Check if it's a private chat
    if not is_private_chat(update):
        user_info = extract_user_info(update.message)
        log_with_user_info("WARNING", f"📎 File upload attempt in non-private chat rejected: {filename}", user_info)
        return  # Silently ignore - no response in groups
    
    user_info = extract_user_info(update.message)
    log_with_user_info("INFO", f"📎 Processing file: {filename}", user_info)
    
    processing_msg = None
    temp_path = None
    
    try:
        # Validate file
        file_size = file_obj.file_size
        if file_size is None:
            error_msg = "Cannot determine file size"
            logger.error(f"❌ {error_msg}")
            await update.message.reply_text(
                f"❌ <b>Upload rejected:</b> {error_msg}",
                parse_mode=ParseMode.HTML
            )
            return
            
        is_allowed, error_msg = is_file_allowed(filename, file_size)
        
        if not is_allowed:
            log_with_user_info("WARNING", f"File rejected: {error_msg}", user_info)
            await update.message.reply_text(
                f"❌ <b>Upload rejected:</b> {error_msg}",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Show processing message
        size_mb = file_size / (1024 * 1024)
        processing_msg = await update.message.reply_text(
            f"⏳ <b>Processing file...</b>\n"
            f"📎 <b>File:</b> <code>{filename}</code>\n"
            f"📏 <b>Size:</b> <code>{size_mb:.1f} MB</code>\n\n"
            f"Downloading and uploading to Catbox...",
            parse_mode=ParseMode.HTML
        )
        
        log_with_user_info("INFO", f"📥 Starting download: {filename} ({size_mb:.1f} MB)", user_info)
        
        # Download file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            # For python-telegram-bot 22.3, we need to get the File object first
            file_info = await file_obj.get_file()
            await file_info.download_to_drive(temp_path)
            logger.debug(f"📥 File downloaded to: {temp_path}")
        
        # Upload to catbox
        catbox_url = await upload_to_catbox(temp_path, filename)
        
        # Send success message
        success_message = random.choice(SUCCESS_MESSAGES)
        final_message = (
            f"{success_message}\n\n"
            f"🔗 <b>Direct link:</b> {catbox_url}\n\n"
            f"📎 <b>Original filename:</b> <code>{filename}</code>\n"
            f"📏 <b>Size:</b> <code>{size_mb:.1f} MB</code>\n\n"
            f"☁️ <b>Note:</b> File is stored permanently on Catbox"
        )
        await processing_msg.edit_text(final_message, parse_mode=ParseMode.HTML)
        
        log_with_user_info("INFO", f"✅ Upload completed: {filename} -> {catbox_url}", user_info)
                
    except Exception as e:
        error_message = f"❌ <b>Upload failed:</b> {str(e)}"
        log_with_user_info("ERROR", f"Upload failed for {filename}: {str(e)}", user_info)
        
        try:
            if processing_msg:
                await processing_msg.edit_text(error_message, parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(error_message, parse_mode=ParseMode.HTML)
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message: {reply_error}")
            
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"🗑️ Cleaned up temporary file: {temp_path}")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to clean up temporary file: {cleanup_error}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🚀 /start command attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        log_with_user_info("INFO", "🚀 /start command executed", user_info)
        
        # Create inline keyboard with buttons
        # First row: Updates and Support buttons
        # Second row: Add Me To Your Group button
        bot_username = context.bot.username
        add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
        
        keyboard = [
            [
                InlineKeyboardButton("📢 Updates", url=CHANNEL_URL),
                InlineKeyboardButton("💬 Support", url=GROUP_URL)
            ],
            [
                InlineKeyboardButton("➕ Add Me To Your Group", url=add_to_group_url)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send start message with random photo and inline buttons
        random_photo = random.choice(RANDOM_PHOTOS)
        await update.message.reply_photo(
            photo=random_photo,
            caption=START_MESSAGE,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ Error in start_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred. Please try again later.",
                parse_mode=ParseMode.HTML
            )
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message in start_command: {reply_error}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "❓ /help command attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        log_with_user_info("INFO", "❓ /help command executed", user_info)
        
        random_photo = random.choice(RANDOM_PHOTOS)
        
        keyboard = [[InlineKeyboardButton("📖 Expand Help", callback_data="help_expand")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=random_photo,
            caption=HELP_SHORT_MESSAGE, 
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"❌ Error in help_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred while showing help. Please try again later.",
                parse_mode=ParseMode.HTML
            )
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message in help_command: {reply_error}")

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ping command with latency measurement - Works in ALL chat types"""
    try:
        user_info = extract_user_info(update.message)
        log_with_user_info("INFO", "🏓 /ping command executed", user_info)
        
        start_time = time.time()
        
        # Reply appropriately based on chat type
        ping_msg = await update.message.reply_text("🛰️ Pinging...")
        
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        
        pong_message = f'🏓 <a href="{GROUP_URL}">Pong!</a> {latency:.2f}ms'
        
        await ping_msg.edit_text(
            pong_message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
        log_with_user_info("INFO", f"🏓 Ping response: {latency:.2f}ms", user_info)
        
    except Exception as e:
        logger.error(f"❌ Error in ping_command: {e}")
        try:
            await update.message.reply_text(
                "❌ An error occurred during ping. Please try again.",
                parse_mode=ParseMode.HTML
            )
        except Exception as reply_error:
            logger.error(f"❌ Failed to send error message in ping_command: {reply_error}")

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks - ONLY works in private chats"""
    try:
        query = update.callback_query
        
        # Check if it's a private chat (callback queries inherit from original message)
        if query.message.chat.type != 'private':
            user_info = extract_user_info(query.message)
            log_with_user_info("WARNING", f"🔘 Callback query attempt in non-private chat rejected: {query.data}", user_info)
            await query.answer("❌ This bot only works in private chats!")
            return
        
        user_info = extract_user_info(query.message)
        log_with_user_info("INFO", f"🔘 Callback query: {query.data}", user_info)
        
        if query.data == "help_expand":
            keyboard = [[InlineKeyboardButton("📕 Minimize Help", callback_data="help_minimize")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_caption(
                caption=HELP_DETAILED_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            await query.answer("Detailed help information expanded!")
            
        elif query.data == "help_minimize":
            keyboard = [[InlineKeyboardButton("📖 Expand Help", callback_data="help_expand")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_caption(
                caption=HELP_SHORT_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            await query.answer("Help information minimized!")
            
    except Exception as e:
        logger.error(f"❌ Error in callback_query_handler: {e}")
        try:
            await query.answer("❌ An error occurred. Please try again.")
        except Exception as answer_error:
            logger.error(f"❌ Failed to answer callback query: {answer_error}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document files - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "📄 Document upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        document = update.message.document
        filename = document.file_name or f"document_{document.file_id}"
        
        log_with_user_info("INFO", f"📄 Document received: {filename}", user_info)
        await process_file(update, context, document, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_document: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your document. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_document: {reply_error}")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo files - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "📸 Photo upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        photo = update.message.photo[-1]  # Get highest resolution
        filename = f"photo_{photo.file_id}.jpg"
        
        log_with_user_info("INFO", f"📸 Photo received: {filename}", user_info)
        await process_file(update, context, photo, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_photo: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your photo. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_photo: {reply_error}")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video files - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🎥 Video upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        video = update.message.video
        filename = video.file_name or f"video_{video.file_id}.mp4"
        
        log_with_user_info("INFO", f"🎥 Video received: {filename}", user_info)
        await process_file(update, context, video, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_video: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your video. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_video: {reply_error}")

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio files - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🎵 Audio upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        audio = update.message.audio
        filename = audio.file_name or f"audio_{audio.file_id}.mp3"
        
        log_with_user_info("INFO", f"🎵 Audio received: {filename}", user_info)
        await process_file(update, context, audio, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_audio: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your audio. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_audio: {reply_error}")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🎤 Voice message upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        voice = update.message.voice
        filename = f"voice_{voice.file_id}.ogg"
        
        log_with_user_info("INFO", f"🎤 Voice message received: {filename}", user_info)
        await process_file(update, context, voice, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_voice: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your voice message. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_voice: {reply_error}")

async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle video notes (round video messages) - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "📹 Video note upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        video_note = update.message.video_note
        filename = f"video_note_{video_note.file_id}.mp4"
        
        log_with_user_info("INFO", f"📹 Video note received: {filename}", user_info)
        await process_file(update, context, video_note, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_video_note: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your video note. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_video_note: {reply_error}")

async def handle_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle animations/GIFs - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🎞️ Animation upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        animation = update.message.animation
        filename = animation.file_name or f"animation_{animation.file_id}.gif"
        
        log_with_user_info("INFO", f"🎞️ Animation received: {filename}", user_info)
        await process_file(update, context, animation, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_animation: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your animation. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_animation: {reply_error}")

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle stickers - ONLY works in private chats"""
    try:
        # Check if it's a private chat
        if not is_private_chat(update):
            user_info = extract_user_info(update.message)
            log_with_user_info("WARNING", "🔖 Sticker upload attempt in non-private chat rejected", user_info)
            return  # Silently ignore - no response in groups
        
        user_info = extract_user_info(update.message)
        sticker = update.message.sticker
        
        # Determine file extension based on sticker type
        if sticker.is_animated:
            extension = ".tgs"
        elif sticker.is_video:
            extension = ".webm"
        else:
            extension = ".webp"
        
        filename = f"sticker_{sticker.file_id}{extension}"
        
        log_with_user_info("INFO", f"🔖 Sticker received: {filename}", user_info)
        await process_file(update, context, sticker, filename)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_sticker: {e}")
        # Only send error messages in private chats
        if is_private_chat(update):
            try:
                await update.message.reply_text(
                    "❌ An error occurred while processing your sticker. Please try again.",
                    parse_mode=ParseMode.HTML
                )
            except Exception as reply_error:
                logger.error(f"❌ Failed to send error message in handle_sticker: {reply_error}")

async def setup_bot_commands(application):
    """Set up bot commands menu"""
    try:
        logger.info("🔧 Setting up bot commands menu...")
        
        commands = [
            BotCommand("start", "🗯️ Welcome message"),
            BotCommand("help", "🗒️ Get instructions")
        ]
        
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands menu setup completed")
        
    except Exception as e:
        logger.error(f"❌ Error setting up bot commands: {e}")

def setup_handlers(application):
    """Configure all bot handlers with private chat restrictions"""
    try:
        logger.info("🔧 Setting up bot handlers...")
        
        # Command handlers - /ping works everywhere, others only in private
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("ping", ping_command))  # Works in all chat types
        
        # Callback query handler - only in private chats
        application.add_handler(CallbackQueryHandler(callback_query_handler))
        
        # File handlers - only work in private chats
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.VIDEO, handle_video))
        application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
        application.add_handler(MessageHandler(filters.VOICE, handle_voice))
        application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
        application.add_handler(MessageHandler(filters.ANIMATION, handle_animation))
        application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
        
        logger.info("✅ Bot handlers setup completed")
        logger.info("🔒 Bot restricted to private chats only (except /ping command)")
        
    except Exception as e:
        logger.error(f"❌ Error setting up handlers: {e}")
        raise

async def post_init(application):
    """Post initialization setup"""
    try:
        logger.info("🔧 Running post-initialization setup...")
        await setup_bot_commands(application)
        logger.info("✅ Post-initialization setup completed")
    except Exception as e:
        logger.error(f"❌ Error in post-initialization: {e}")

def main():
    """Main function to run the bot"""
    try:
        logger.info("🚀 Starting Catbox Upload Bot...")
        logger.info("🔒 Bot configured for PRIVATE CHATS ONLY (except /ping)")
        
        if not BOT_TOKEN:
            logger.error("❌ TELEGRAM_BOT_TOKEN environment variable not set")
            print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable")
            print("You can get a token by messaging @BotFather on Telegram")
            return
        
        logger.info("🔑 Bot token found")
        
        # Start dummy HTTP server for deployment platforms
        try:
            threading.Thread(target=start_dummy_server, daemon=True).start()
        except Exception as e:
            logger.warning(f"⚠️ Failed to start HTTP server: {e}")
            logger.info("📡 Continuing without HTTP server...")
        
        # Create and configure application
        logger.info("🔧 Initializing bot application...")
        application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
        setup_handlers(application)
        
        # Start the bot
        logger.info("🤖 Bot is now running and ready to accept files!")
        logger.info("🔒 PRIVATE CHAT MODE: Only responds in private chats (except /ping)")
        logger.info("📡 Press Ctrl+C to stop the bot")
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error in main: {e}")
        logger.error("🔄 Bot will attempt to restart...")
        raise

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error("🛑 Bot shutting down due to fatal error")