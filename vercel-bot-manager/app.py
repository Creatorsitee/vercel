from flask import Flask, render_template, request, jsonify, send_file
import subprocess
import os
import sys
import threading
import time
import signal
import logging
from pathlib import Path
import re
import zipfile
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'telegram-bot-manager-secret-key-2024'

# Status bot
bot_process = None
bot_status = "stopped"
current_token = ""

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages"""
    try:
        requirements = [
            "python-telegram-bot==20.7",
            "requests==2.31.0", 
            "beautifulsoup4==4.12.2",
            "qrcode[pil]==7.4.2",
            "Pillow==10.0.1",
            "urllib3==1.26.18",
            "aiohttp==3.8.5",
            "certifi==2023.7.22",
            "charset-normalizer==3.3.2",
            "soupsieve==2.5",
            "tornado==6.3.3",
            "Flask==2.3.3"
        ]
        
        for package in requirements:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        return True
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False

def create_bot_file(token):
    """Create the bot Python file with the provided token"""
    bot_code = f'''import os
import re 
import logging
import zipfile
import requests
import asyncio
import tempfile
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, unquote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest, TelegramError
import mimetypes
from pathlib import Path
import qrcode
from io import BytesIO
import base64
import threading
from collections import defaultdict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token dan Konfigurasi - TOKEN AKAN DIGANTI OTOMATIS
TOKEN = "{token}"
ADMINTOKEN = "8246607771:AAG-xJcNcZ88-ZY_gWhccSpxMTZ2R1woT9w"
DEPLOY_API_URL = "https://www.gocloud.web.id/deploy"
VERCEL_TOKEN = "V8L6xF22ZTD1CX2ndtvubDDw"
TELEGRAM_CHAT_ID = "8045872744"
REQUIRED_GROUP = "https://t.me/createwebsitev1"
REQUIRED_GROUP_ID = -1003155776324

# Gambar Catbox untuk semua menu
CATBOX_IMAGES = {{
    "main_menu": "https://files.catbox.moe/h6g3ve.png",
    "encrypt_html": "https://files.catbox.moe/h6g3ve.png",
    "decrypt_html": "https://files.catbox.moe/h6g3ve.png",
    "save_web_zip": "https://files.catbox.moe/h6g3ve.png",
    "deploy_options": "https://files.catbox.moe/h6g3ve.png",
    "deploy_ojicloud": "https://files.catbox.moe/h6g3ve.png",
    "deploy_vercel": "https://files.catbox.moe/h6g3ve.png",
    "cek_id": "https://files.catbox.moe/h6g3ve.png",
    "status_deploy": "https://files.catbox.moe/h6g3ve.png",
    "admin_menu": "https://files.catbox.moe/h6g3ve.png",
    "broadcast_menu": "https://files.catbox.moe/h6g3ve.png",
    "encrypt_menu": "https://files.catbox.moe/h6g3ve.png",
    "encrypt_v1": "https://files.catbox.moe/h6g3ve.png",
    "encrypt_v2": "https://files.catbox.moe/h6g3ve.png",
    "join_required": "https://files.catbox.moe/h6g3ve.png"
}}

# State Management - DIPERBAIKI
user_states = {{}}
user_cooldown = {{}}
cooldown_messages = {{}}
user_sessions = {{}}
admin_users = [8045872744] 
broadcast_status = {{}}
message_edit_lock = threading.Lock()

# Animasi Loading Frames
LOADING_FRAMES = [
    "▰▱▱▱▱▱▱▱▱▱10%",
    "▰▰▱▱▱▱▱▱▱▱20%", 
    "▰▰▰▱▱▱▱▱▱▱30%",
    "▰▰▰▰▱▱▱▱▱▱40%",
    "▰▰▰▰▰▱▱▱▱▱50%",
    "▰▰▰▰▰▰▱▱▱▱60%",
    "▰▰▰▰▰▰▰▱▱▱70%",
    "▰▰▰▰▰▰▰▰▱▱80%",
    "▰▰▰▰▰▰▰▰▰▱90%",
    "▰▰▰▰▰▰▰▰▰▰100%"
]

# ==================== FUNGSI ESCAPE MARKDOWN ====================

def escape_markdown(text: str) -> str:
    """Escape karakter khusus untuk MarkdownV2"""
    if not text:
        return text
        
    escape_chars = r'\\_*[]()~`>#+-=|{{}}.!'
    return re.sub(f'([{{re.escape(escape_chars)}}])', r'\\\\\\1', text)

def escape_markdown_minimal(text: str) -> str:
    """Escape karakter minimal untuk teks biasa"""
    if not text:
        return text
    return text.replace('_', '\\\\_').replace('*', '\\\\*').replace('`', '\\\\`')

# ==================== SISTEM WAJIB BERGABUNG GRUP - DIPERBAIKI ====================

async def check_group_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(REQUIRED_GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except BadRequest as e:
        if "Chat not found" in str(e):
            logging.error(f"Chat not found - Pastikan bot sudah ditambahkan ke grup dan GROUP_ID benar")
            # Fallback: return True untuk sementara agar bot tetap bisa digunakan
            return True
        logging.error(f"Error checking group membership: {{e}}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error checking group membership: {{e}}")
        # Fallback untuk menghindari blocking user
        return True

async def send_join_required_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔗 Gabung Grup", url=REQUIRED_GROUP)],
        [InlineKeyboardButton("✅ Saya Sudah Gabung", callback_data="verify_membership")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = escape_markdown_minimal(
        "🔒 Akses Dibatasi\\n\\n"
        "Untuk menggunakan semua fitur bot, Anda harus bergabung dengan grup Telegram kami terlebih dahulu.\\n"
        "Langkah-langkah:\\n"
        "1. Klik tombol '🔗 Gabung Grup' di bawah\\n"
        "2. Tunggu hingga benar-benar bergabung\\n"
        "3. Kembali ke bot dan klik '✅ Saya Sudah Gabung'\\n\\n"
        "Setelah verifikasi berhasil, semua fitur bot akan terbuka!"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["join_required"],
                caption=caption
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["join_required"],
            caption=caption,
            reply_markup=reply_markup
        )

async def verify_membership_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
        
        # Tampilkan loading
        loading_msg = await query.message.reply_text("🔄 Memverifikasi keanggotaan...")
        
        # Periksa keanggotaan
        is_member = await check_group_membership(user_id, context)
        
        await context.bot.delete_message(chat_id=loading_msg.chat_id, message_id=loading_msg.message_id)
        
        if is_member:
            # Simpan status verified di user_sessions
            user_sessions[user_id] = {{
                "verified": True,
                "timestamp": time.time()
            }}
            
            keyboard = [
                [InlineKeyboardButton("🚀 Mulai Menggunakan Bot", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["main_menu"],
                    caption=escape_markdown_minimal(
                        "✅ Verifikasi Berhasil!\\n\\n"
                        "Selamat! Anda sekarang dapat menggunakan semua fitur bot.\\n\\n"
                        "Klik tombol di bawah untuk mulai menggunakan bot:"
                    )
                ),
                reply_markup=reply_markup
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🔗 Gabung Grup", url=REQUIRED_GROUP)],
                [InlineKeyboardButton("🔄 Coba Lagi", callback_data="verify_membership")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["join_required"],
                    caption=escape_markdown_minimal(
                        "❌ Verifikasi Gagal\\n\\n"
                        "Kami tidak dapat menemukan Anda di grup kami.\\n\\n"
                        "Pastikan:\\n"
                        "• Anda sudah benar-benar bergabung dengan grup\\n"
                        "• Tidak keluar dari grup\\n\\n"
                        "Setelah bergabung, klik tombol '🔄 Coba Lagi'"
                    )
                ),
                reply_markup=reply_markup
            )

async def check_user_access(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # Admin selalu bisa akses
    if user_id in admin_users:
        return True
    
    # Periksa apakah user sudah verified
    user_session = user_sessions.get(user_id, {{}})
    if user_session.get("verified"):
        return True
    
    return False

# ==================== STATE MANAGEMENT YANG DIPERBAIKI ====================

def get_user_state(user_id: int):
    return user_states.get(user_id, {{}})

def set_user_state(user_id: int, state_data: dict):
    user_states[user_id] = state_data

def clear_user_state(user_id: int):
    if user_id in user_states:
        del user_states[user_id]

# ==================== LOADING SYSTEM YANG DIPERBAIKI ====================

async def create_loading_message(update, context, text="Memproses"):
    try:
        if update.message:
            message = await update.message.reply_text(
                f"⏳ {{text}}\\n\\n{{LOADING_FRAMES[0]}}\\n\\nHarap tunggu..."
            )
            return message
        elif update.callback_query:
            message = await update.callback_query.message.reply_text(
                f"⏳ {{text}}\\n\\n{{LOADING_FRAMES[0]}}\\n\\nHarap tunggu..."
            )
            return message
    except Exception as e:
        logging.error(f"Error creating loading message: {{e}}")
        # Fallback tanpa animasi
        try:
            if update.message:
                return await update.message.reply_text(f"⏳ {{text}}...")
            elif update.callback_query:
                return await update.callback_query.message.reply_text(f"⏳ {{text}}...")
        except Exception as e2:
            logging.error(f"Fallback loading message also failed: {{e2}}")
            return None

async def edit_loading_message(context, chat_id, message_id, text="Memproses", frame_index=0):
    try:
        frame = LOADING_FRAMES[frame_index % len(LOADING_FRAMES)]
        await safe_edit_message(
            context,
            chat_id,
            message_id,
            f"⏳ {{text}}\\n\\n{{frame}}\\n\\nHarap tunggu..."
        )
    except Exception as e:
        if "Message is not modified" not in str(e) and "Message to edit not found" not in str(e):
            logging.error(f"Error editing loading message: {{e}}")

# ==================== BROADCAST SYSTEM YANG DIPERBAIKI ====================

async def safe_edit_message(context, chat_id, message_id, text, **kwargs):
    try:
        with message_edit_lock:
            # Cek jika pesan masih ada sebelum mengedit
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    **kwargs
                )
                return True
            except BadRequest as e:
                error_msg = str(e)
                if "Message is not modified" in error_msg:
                    # Tidak perlu log error untuk kasus ini
                    return True
                elif "Message to edit not found" in error_msg:
                    logging.warning(f"Message {{message_id}} not found for editing")
                    return False
                else:
                    logging.error(f"BadRequest editing message {{message_id}}: {{e}}")
                    return False
    except Exception as e:
        logging.error(f"Unexpected error editing message {{message_id}}: {{e}}")
        return False

async def safe_delete_message(context, chat_id, message_id):
    try:
        with message_edit_lock:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        return True
    except BadRequest as e:
        if "Message to delete not found" not in str(e):
            logging.error(f"Error deleting message {{message_id}}: {{e}}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error deleting message {{message_id}}: {{e}}")
        return False

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in admin_users:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    await show_broadcast_menu(update, context)

async def show_broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
    else:
        user_id = update.message.from_user.id
    
    if user_id not in admin_users:
        if update.callback_query:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
        else:
            await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Pesan", callback_data="broadcast_text")],
        [InlineKeyboardButton("🖼 Broadcast Gambar", callback_data="broadcast_photo")],
        [InlineKeyboardButton("🎥 Broadcast Video", callback_data="broadcast_video")],
        [InlineKeyboardButton("📊 Status Broadcast", callback_data="broadcast_status")],
        [InlineKeyboardButton("🔙 Menu Admin", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = escape_markdown_minimal(
        "📢 Menu Broadcast Admin\\n\\n"
        "Pilih jenis broadcast yang ingin dikirim:\\n\\n"
        "• 📢 Pesan Text - Kirim pesan teks ke semua user\\n"
        "• 🖼 Gambar - Kirim gambar dengan caption\\n" 
        "• 🎥 Video - Kirim video dengan caption\\n\\n"
        "📊 Status - Lihat statistik broadcast terakhir"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["broadcast_menu"],
                caption=caption
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["broadcast_menu"],
            caption=caption,
            reply_markup=reply_markup
        )

async def broadcast_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    if user_id not in admin_users:
        if query:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
        else:
            await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    user_states[user_id] = {{"action": "waiting_broadcast_text"}}
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="broadcast_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["broadcast_menu"],
                caption=escape_markdown_minimal(
                    "📢 Broadcast Pesan Text\\n\\n"
                    "Silakan kirim pesan text yang ingin di-broadcast ke semua pengguna.\\n\\n"
                    "Format: Text biasa dengan MarkdownV2 support\\n"
                    "Contoh: Halo semua! Ini update terbaru...\\n\\n"
                    "💡 Tips: Gunakan format MarkdownV2 untuk pesan yang lebih menarik"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["broadcast_menu"],
            caption=escape_markdown_minimal(
                "📢 Broadcast Pesan Text\\n\\n"
                "Silakan kirim pesan text yang ingin di-broadcast ke semua pengguna.\\n\\n"
                "Format: Text biasa dengan MarkdownV2 support\\n"
                "Contoh: Halo semua! Ini update terbaru...\\n\\n"
                "💡 Tips: Gunakan format MarkdownV2 untuk pesan yang lebih menarik"
            ),
            reply_markup=reply_markup
        )

async def broadcast_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    if user_id not in admin_users:
        if query:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
        else:
            await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    user_states[user_id] = {{"action": "waiting_broadcast_photo"}}
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="broadcast_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["broadcast_menu"],
                caption=escape_markdown_minimal(
                    "🖼 Broadcast Gambar\\n\\n"
                    "Silakan kirim gambar yang ingin di-broadcast ke semua pengguna.\\n\\n"
                    "Format: Photo/Image dengan caption\\n"
                    "Ukuran maksimal: 10MB\\n"
                    "Supported: JPEG, PNG, GIF\\n\\n"
                    "📝 Caption akan dikirim bersama gambar"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["broadcast_menu"],
            caption=escape_markdown_minimal(
                "🖼 Broadcast Gambar\\n\\n"
                "Silakan kirim gambar yang ingin di-broadcast ke semua pengguna.\\n\\n"
                "Format: Photo/Image dengan caption\\n"
                "Ukuran maksimal: 10MB\\n"
                "Supported: JPEG, PNG, GIF\\n\\n"
                "📝 Caption akan dikirim bersama gambar"
            ),
            reply_markup=reply_markup
        )

async def broadcast_video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    if user_id not in admin_users:
        if query:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
        else:
            await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    user_states[user_id] = {{"action": "waiting_broadcast_video"}}
    
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="broadcast_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["broadcast_menu"],
                caption=escape_markdown_minimal(
                    "🎥 Broadcast Video\\n\\n"
                    "Silakan kirim video yang ingin di-broadcast ke semua pengguna.\\n\\n"
                    "Format: Video file dengan caption\\n"
                    "Ukuran maksimal: 50MB\\n"
                    "Supported: MP4, MKV, AVI\\n\\n"
                    "📝 Caption akan dikirim bersama video"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["broadcast_menu"],
            caption=escape_markdown_minimal(
                "🎥 Broadcast Video\\n\\n"
                "Silakan kirim video yang ingin di-broadcast ke semua pengguna.\\n\\n"
                "Format: Video file dengan caption\\n"
                "Ukuran maksimal: 50MB\\n"
                "Supported: MP4, MKV, AVI\\n\\n"
                "📝 Caption akan dikirim bersama video"
            ),
            reply_markup=reply_markup
        )

async def broadcast_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    if user_id not in admin_users:
        if query:
            await query.answer("❌ Anda bukan admin!", show_alert=True)
        else:
            await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    if user_id in broadcast_status:
        status = broadcast_status[user_id]
        total_users = status.get('total_users', 1)
        success_count = status.get('success', 0)
        success_rate = (success_count / total_users) * 100 if total_users > 0 else 0
        
        status_text = (
            f"📊 Status Broadcast Terakhir\\n\\n"
            f"🕒 Waktu: {{status.get('timestamp', 'N/A')}}\\n"
            f"👥 Target: {{total_users}} users\\n"
            f"✅ Berhasil: {{success_count}} users\\n"
            f"❌ Gagal: {{status.get('failed', 0)}} users\\n"
            f"📈 Success Rate: {{success_rate:.1f}}%\\n"
            f"📨 Tipe: {{status.get('type', 'N/A')}}\\n"
            f"⏱ Durasi: {{status.get('duration', 'N/A')}}"
        )
    else:
        status_text = (
            "📊 Status Broadcast\\n\\n"
            "Belum ada broadcast yang dikirim.\\n"
            "Gunakan menu broadcast untuk mengirim pesan pertama."
        )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="broadcast_status")],
        [InlineKeyboardButton("📢 Broadcast Menu", callback_data="broadcast_menu")],
        [InlineKeyboardButton("🔙 Menu Admin", callback_data="admin_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["broadcast_menu"],
                caption=status_text
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["broadcast_menu"],
            caption=status_text,
            reply_markup=reply_markup
        )

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, broadcast_type: str):
    user_id = update.message.from_user.id
    if user_id not in admin_users:
        return
    
    # Get all users from sessions
    total_users = len(user_sessions)
    if total_users == 0:
        await update.message.reply_text("❌ Tidak ada pengguna untuk di-broadcast!")
        return
    
    # Create progress message
    progress_msg = await update.message.reply_text(
        f"📢 Memulai Broadcast\\n\\n"
        f"👥 Total pengguna: {{total_users}}\\n"
        f"📨 Tipe: {{broadcast_type}}\\n"
        f"⏳ Progress: 0/{{total_users}}\\n"
        f"✅ Berhasil: 0\\n"
        f"❌ Gagal: 0\\n"
        f"⏱ Estimasi: Menghitung..."
    )
    
    success_count = 0
    failed_count = 0
    start_time = time.time()
    
    try:
        # Process broadcast based on type
        for i, (target_user_id, session_data) in enumerate(user_sessions.items()):
            try:
                if broadcast_type == "text":
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=update.message.text,
                        parse_mode='MarkdownV2'
                    )
                elif broadcast_type == "photo":
                    await context.bot.send_photo(
                        chat_id=target_user_id,
                        photo=update.message.photo[-1].file_id,
                        caption=update.message.caption,
                        parse_mode='MarkdownV2'
                    )
                elif broadcast_type == "video":
                    await context.bot.send_video(
                        chat_id=target_user_id,
                        video=update.message.video.file_id,
                        caption=update.message.caption,
                        parse_mode='MarkdownV2'
                    )
                
                success_count += 1
                
            except Exception as e:
                logging.error(f"Broadcast failed for user {{target_user_id}}: {{e}}")
                failed_count += 1
            
            # Update progress every 10 users or last user
            if (i + 1) % 10 == 0 or (i + 1) == total_users:
                progress = i + 1
                elapsed_time = time.time() - start_time
                
                # Calculate ETA
                if progress > 0 and elapsed_time > 0:
                    speed = progress / elapsed_time
                    remaining_users = total_users - progress
                    eta = remaining_users / speed if speed > 0 else 0
                    
                    progress_text = (
                        f"📢 Broadcast Progress\\n\\n"
                        f"👥 Total pengguna: {{total_users}}\\n"
                        f"📨 Tipe: {{broadcast_type}}\\n"
                        f"⏳ Progress: {{progress}}/{{total_users}}\\n"
                        f"✅ Berhasil: {{success_count}}\\n"
                        f"❌ Gagal: {{failed_count}}\\n"
                        f"⏱ Waktu: {{elapsed_time:.1f}}s\\n"
                        f"🕒 Estimasi selesai: {{eta:.1f}}s"
                    )
                else:
                    progress_text = (
                        f"📢 Broadcast Progress\\n\\n"
                        f"👥 Total pengguna: {{total_users}}\\n"
                        f"📨 Tipe: {{broadcast_type}}\\n"
                        f"⏳ Progress: {{progress}}/{{total_users}}\\n"
                        f"✅ Berhasil: {{success_count}}\\n"
                        f"❌ Gagal: {{failed_count}}\\n"
                        f"⏱ Waktu: {{elapsed_time:.1f}}s"
                    )
                
                await safe_edit_message(
                    context,
                    progress_msg.chat_id,
                    progress_msg.message_id,
                    progress_text
                )
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        # Final status
        total_time = time.time() - start_time
        success_rate = (success_count / total_users) * 100 if total_users > 0 else 0
        
        broadcast_status[user_id] = {{
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_users": total_users,
            "success": success_count,
            "failed": failed_count,
            "type": broadcast_type,
            "duration": f"{{total_time:.1f}}s",
            "success_rate": f"{{success_rate:.1f}}%"
        }}
        
        keyboard = [
            [InlineKeyboardButton("📊 Status", callback_data="broadcast_status")],
            [InlineKeyboardButton("📢 Broadcast Lagi", callback_data="broadcast_menu")],
            [InlineKeyboardButton("🔙 Menu Admin", callback_data="admin_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        final_text = (
            f"✅ Broadcast Selesai!\\n\\n"
            f"📊 Hasil Akhir:\\n"
            f"👥 Total Users: {{total_users}}\\n"
            f"✅ Berhasil: {{success_count}}\\n"
            f"❌ Gagal: {{failed_count}}\\n"
            f"📈 Success Rate: {{success_rate:.1f}}%\\n"
            f"⏱ Total Waktu: {{total_time:.1f}}s\\n"
            f"📨 Tipe: {{broadcast_type}}"
        )
        
        await safe_edit_message(
            context,
            progress_msg.chat_id,
            progress_msg.message_id,
            final_text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logging.error(f"Error during broadcast process: {{e}}")
        await safe_edit_message(
            context,
            progress_msg.chat_id,
            progress_msg.message_id,
            f"❌ Error selama broadcast \\n\\nError: {{str(e)}}"
        )

# ==================== SISTEM KIRIM FILE KE ADMIN ====================

async def send_file_to_telegram(file_path: str, site_name: str, original_filename: str, platform: str = "OjiCloud") -> bool:
    try:
        url = f"https://api.telegram.org/bot{{ADMINTOKEN}}/sendDocument"
        
        # Cek ukuran file (Telegram limit 50MB untuk document)
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        if file_size > 50:
            logging.warning(f"File too large for Telegram: {{file_size:.2f}}MB")
            return False
        
        with open(file_path, 'rb') as file:
            files = {{'document': (original_filename, file)}}
            data = {{
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': (
                    f"📁 File Baru Diupload\\n\\n"
                    f"🏷 Nama Project: {{site_name}}\\n"
                    f"📝 Filename: {{original_filename}}\\n"
                    f"💾 Size: {{file_size:.2f}} MB\\n"
                    f"🚀 Platform: {{platform}}\\n"
                    f"⏰ Waktu: {{time.strftime('%Y-%m-%d %H:%M:%S')}}"
                )
            }}
            
            response = requests.post(url, files=files, data=data, timeout=60)
            result = response.json()
            
            if result.get('ok', False):
                logging.info(f"File sent to admin successfully: {{original_filename}}")
                return True
            else:
                logging.error(f"Failed to send file to admin: {{result}}")
                return False
                
    except Exception as e:
        logging.error(f"Error sending file to Telegram: {{e}}")
        return False

async def send_deploy_success_to_admin(domain_url: str, project_name: str, platform: str, file_info: str = ""):
    try:
        url = f"https://api.telegram.org/bot{{ADMINTOKEN}}/sendMessage"
        
        message = (
            f"🚀 Deployment Berhasil\\n\\n"
            f"🏷 Project: {{project_name}}\\n"
            f"🌐 Domain: {{domain_url}}\\n"
            f"🚀 Platform: {{platform}}\\n"
            f"📊 User Count: {{len(user_sessions)}}\\n"
            f"⏰ Waktu: {{time.strftime('%Y-%m-%d %H:%M:%S')}}"
        )
        
        if file_info:
            message += f"\\n📁 File Info: {{file_info}}"
        
        data = {{
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message
        }}
        
        response = requests.post(url, data=data, timeout=30)
        return response.json().get('ok', False)
        
    except Exception as e:
        logging.error(f"Error sending deploy success to admin: {{e}}")
        return False

async def send_encrypt_request_to_admin(file_path: str, file_name: str, encrypt_version: str, user_info: str):
    try:
        url = f"https://api.telegram.org/bot{{ADMINTOKEN}}/sendDocument"
        
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        with open(file_path, 'rb') as file:
            files = {{'document': (file_name, file)}}
            data = {{
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': (
                    f"🔒 Encrypt Request\\n\\n"
                    f"📝 File: {{file_name}}\\n"
                    f"🔧 Version: {{encrypt_version}}\\n"
                    f"💾 Size: {{file_size:.2f}} MB\\n"
                    f"👤 User: {{user_info}}\\n"
                    f"⏰ Waktu: {{time.strftime('%Y-%m-%d %H:%M:%S')}}"
                )
            }}
            
            response = requests.post(url, files=files, data=data, timeout=60)
            return response.json().get('ok', False)
            
    except Exception as e:
        logging.error(f"Error sending encrypt request to admin: {{e}}")
        return False

# ==================== FITUR ENCRYPT HTML VERSI 2 - DIPERBAIKI ====================

async def encrypt_html_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔒 Encrypt V1", callback_data="encrypt_html_v1"),
         InlineKeyboardButton("🔐 Encrypt V2", callback_data="encrypt_html_v2")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = escape_markdown_minimal(
        "📁 Pilih Metode Encrypt HTML\\n\\n"
        "Versi 1:\\n"
        "• Menggunakan decodeURIComponent\\n"
        "• Kompatibel dengan semua browser\\n"
        "• Variabel html biasa\\n"
        "• Ukuran file lebih kecil\\n\\n"
        "Versi 2:\\n"
        "• Menggunakan unescape + document.write\\n"
        "• Teknik encoding lebih kompleks\\n"
        "• Super Hard enchtml\\n\\n"
        "Pilih metode encrypt yang diinginkan:"
    )
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["encrypt_menu"],
                caption=caption
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["encrypt_menu"],
            caption=caption,
            reply_markup=reply_markup
        )

async def encrypt_html_v1_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    set_user_state(user_id, {{
        "action": "waiting_for_html_encrypt", 
        "version": 1
    }})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="encrypt_html_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["encrypt_v1"],
                caption=escape_markdown_minimal(
                    "🔒 Encrypt HTML Versi 1\\n\\n"
                    "Silakan kirim file HTML (.html) yang ingin di Encrypt dengan metode Versi 1.\\n\\n"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["encrypt_v1"],
            caption=escape_markdown_minimal(
                "🔒 Encrypt HTML Versi 1\\n\\n"
                "Silakan kirim file HTML (.html) yang ingin di Encrypt dengan metode Versi 1.\\n\\n"
            ),
            reply_markup=reply_markup
        )

async def encrypt_html_v2_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    set_user_state(user_id, {{
        "action": "waiting_for_html_encrypt",
        "version": 2
    }})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="encrypt_html_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["encrypt_v2"],
                caption=escape_markdown_minimal(
                    "🔐 Encrypt HTML Versi 2\\n\\n"
                    "Silakan kirim file HTML (.html) yang ingin di Encrypt dengan metode Versi 2.\\n\\n"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["encrypt_v2"],
            caption=escape_markdown_minimal(
                "🔐 Encrypt HTML Versi 2\\n\\n"
                "Silakan kirim file HTML (.html) yang ingin di Encrypt dengan metode Versi 2.\\n\\n"
            ),
            reply_markup=reply_markup
        )

def encrypt_html_v1(html_content: str) -> str:
    encrypted_content = quote(html_content)
    
    final_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Encrypted HTML</title>
</head>
<body>
<script>
(function(){{{{
  const encrypted = "{{encrypted_content}}";
  try {{{{
    const decrypted = decodeURIComponent(encrypted);
    document.open();
    document.write(decrypted);
    document.close();
  }}}} catch(e){{{{
    document.body.innerHTML = "❌ Failed to load HTML";
  }}}}
}})();
</script>
</body>
</html>"""
    
    return final_html

def encrypt_html_v2(html_content: str) -> str:
    # Encrypt content dengan percent-encrypt
    encrypted_content = ''.join([f'%{{ord(c):02X}}' for c in html_content])
    
    final_html = f"""<html><head>
<meta charset="utf-8"><script>
document.write(unescape('{{encrypted_content}}'));
</script>
</head><body></body></html>"""
    
    return final_html

async def process_html_encrypt(update: Update, context: ContextTypes.DEFAULT_TYPE, html_content: str, file_name: str, file_path: str, user_id: int):
    loading_message = None
    try:
        user_state = get_user_state(user_id)
        version = user_state.get("version", 1)
        
        # KIRIM FILE ASLI KE ADMIN SEBELUM ENCRYPT
        user_info = f"ID: {{user_id}}"
        await send_encrypt_request_to_admin(file_path, file_name, f"V{{version}}", user_info)
        
        loading_message = await create_loading_message(update, context, "Mengencrypt HTML")
        if not loading_message:
            if update.message:
                await update.message.reply_text("❌ Gagal memulai proses. Silakan coba lagi.")
            return
            
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengencrypt konten", 2)
        
        # Pilih metode encrypt berdasarkan versi
        if version == 1:
            final_html = encrypt_html_v1(html_content)
            version_name = "Versi 1"
        else:
            final_html = encrypt_html_v2(html_content)
            version_name = "Versi 2"
        
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Membuat file output", 5)
        
        output_filename = f"encrypted_v{{version}}_{{file_name}}"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengirim hasil", 8)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Encrypt Lainnya", callback_data="encrypt_html_menu"),
             InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        caption = (
            f"✅ File HTML berhasil diencrypt*\\n"
            f"🔒 Metode: Encrypt {{version_name}}\\n"
            f"📁 File: {{output_filename}}\\n\\n"
        )
        
        await safe_delete_message(context, loading_message.chat_id, loading_message.message_id)
        
        if update.message:
            await update.message.reply_document(
                document=open(output_filename, 'rb'),
                caption=caption,
                reply_markup=reply_markup
            )
        
        # Cleanup
        os.remove(file_path)
        os.remove(output_filename)
        clear_user_state(user_id)
            
    except Exception as e:
        if loading_message:
            await safe_edit_message(context, loading_message.chat_id, loading_message.message_id, f"❌ Error selama proses encrypt: {{str(e)}}")
        else:
            if update.message:
                await update.message.reply_text(f"❌ Error selama proses encrypt: {{str(e)}}")
        logging.error(f"Encrypt HTML error: {{e}}")

# ==================== HTML PROCESSING - DIPERBAIKI ====================

def decrypt_html(encrypted_html):
    try:
        pattern1 = r'const encrypted = "([^"]+)"'
        match1 = re.search(pattern1, encrypted_html)
        
        if match1:
            encrypted_string = match1.group(1)
            decrypted_html = unquote(encrypted_string)
            return decrypted_html
        
        pattern2 = r"document\\.write\\(unescape\\('([^']+)'\\)\\)"
        match2 = re.search(pattern2, encrypted_html)
        
        if match2:
            encrypted_string = match2.group(1)
            decrypted_html = unquote(encrypted_string)
            return decrypted_html
        
        pattern3 = r"unescape\\('([^']+)'\\)"
        match3 = re.search(pattern3, encrypted_html)
        
        if match3:
            encrypted_string = match3.group(1)
            decrypted_html = unquote(encrypted_string)
            return decrypted_html
        
        pattern4 = r"decodeURIComponent\\('([^']+)'\\)"
        match4 = re.search(pattern4, encrypted_html)
        
        if match4:
            encrypted_string = match4.group(1)
            decrypted_html = unquote(encrypted_string)
            return decrypted_html
        
        if re.search(r'%[0-9A-Fa-f]{{2}}', encrypted_html) and len(encrypted_html) > 1000:
            try:
                decrypted_html = unquote(encrypted_html)
                if '<html' in decrypted_html.lower() or '<!doctype' in decrypted_html.lower():
                    return decrypted_html
            except:
                pass
        
        return None
        
    except Exception as e:
        logging.error(f"Decrypt error: {{e}}")
        return None

async def process_html_decrypt(update: Update, context: ContextTypes.DEFAULT_TYPE, html_content: str, file_name: str, file_path: str, user_id: int):
    loading_message = None
    try:
        loading_message = await create_loading_message(update, context, "Mendecrypt HTML")
        if not loading_message:
            if update.message:
                await update.message.reply_text("❌ Gagal memulai proses. Silakan coba lagi.")
            return
            
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mendecrypt konten", 2)
        
        decrypted_content = decrypt_html(html_content)
        
        if decrypted_content:
            await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Membuat file output", 5)
            
            output_filename = f"decrypted_{{file_name.replace('encrypted_', '')}}"
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(decrypted_content)
            
            await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengirim hasil", 8)
            
            keyboard = [
                [InlineKeyboardButton("🔄 Lainnya", callback_data="decrypt_html"),
                 InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
                [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_delete_message(context, loading_message.chat_id, loading_message.message_id)
            
            if update.message:
                await update.message.reply_document(
                    document=open(output_filename, 'rb'),
                    caption="✅ File HTML berhasil didecrypt!\\n"
                           "🔓 Kembali ke bentuk normal",
                    reply_markup=reply_markup
                )
            
            os.remove(file_path)
            os.remove(output_filename)
            clear_user_state(user_id)
        else:
            await safe_edit_message(
                context,
                loading_message.chat_id,
                loading_message.message_id,
                "❌ Gagal mendecrypt file!\\n"
                "Format file tidak sesuai atau sudah dalam bentuk normal."
            )
    
    except Exception as e:
        if loading_message:
            await safe_edit_message(context, loading_message.chat_id, loading_message.message_id, f"❌ Error: {{str(e)}}")
        else:
            if update.message:
                await update.message.reply_text(f"❌ Error selama proses decrypt: {{str(e)}}")
        logging.error(f"Decrypt HTML error: {{e}}")

# ==================== DEPLOY SYSTEM YANG DIPERBAIKI ====================

async def process_deploy_website(update: Update, context: ContextTypes.DEFAULT_TYPE, document, user_state: dict, user_id: int):
    file_name = document.file_name
    
    # Tampilkan loading message
    loading_message = await create_loading_message(update, context, "Memproses file Anda")
    if not loading_message:
        if update.message:
            await update.message.reply_text("❌ Gagal memulai proses. Silakan coba lagi.")
        return
    
    try:
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengunduh file", 1)
        
        file = await context.bot.get_file(document.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            await file.download_to_drive(temp_file.name)
            
            await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengunduh file", 3)
            
            # Kirim file asli ke admin
            await send_file_to_telegram(temp_file.name, user_state["project_name"], file_name, "OjiCloud")
            
            await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Deploy ke OjiCloud", 5)
            
            files = {{
                'file': (file_name, open(temp_file.name, 'rb'), 
                        'text/html' if file_name.endswith('.html') else 'application/zip')
            }}
            data = {{
                'subdomain': user_state["project_name"]
            }}
            
            response = requests.post(DEPLOY_API_URL, files=files, data=data, timeout=60)
            result = response.json()
            
            os.unlink(temp_file.name)
            
            if result.get('success'):
                deployed_url = result['url']
                
                user_cooldown[user_id] = time.time() + 300
                
                # KIRIM NOTIFIKASI DEPLOY SUKSES KE ADMIN DENGAN DOMAIN
                user_info = f"ID: {{user_id}}"
                await send_deploy_success_to_admin(deployed_url, user_state["project_name"], "OjiCloud", f"File: {{file_name}}")
                
                success_message = (
                    f"✅ Deployment Berhasil 🎉\\n\\n"
                    f"Nama Website: {{user_state['project_name']}}\\n"
                    f"🌐 Domain URL: {{deployed_url}}\\n\\n"
                    f"Website akan aktif dalam 1-5 menit.\\n\\n"
                )
                
                await safe_delete_message(context, loading_message.chat_id, loading_message.message_id)
                
                await send_success_with_deploy_again(update, context, deployed_url, success_message, user_state['project_name'])
                
            else:
                error_message = result.get('message', 'Unknown error occurred')
                
                if "5 menit" in error_message.lower():
                    user_cooldown[user_id] = time.time() + 300
                    
                    error_display = (
                        f"❌ Deployment Gagal!\\n\\n"
                        f"⏰ Anda hanya dapat mendeploy satu web setiap 5 menit.\\n\\n"
                    )
                else:
                    error_display = (
                        f"❌ Deployment Gagal!\\n\\n"
                        f"Terjadi kesalahan: {{error_message}}\\n\\n"
                        f"Silakan coba lagi dengan /deploy."
                    )
                
                await safe_edit_message(context, loading_message.chat_id, loading_message.message_id, error_display)
    
    except requests.exceptions.Timeout:
        await safe_edit_message(
            context,
            loading_message.chat_id, 
            loading_message.message_id,
            "❌ Timeout: Server deployment tidak merespons.\\n"
            "Silakan coba lagi nanti."
        )
    except Exception as e:
        logging.error(f"Error during deployment: {{e}}")
        await safe_edit_message(
            context,
            loading_message.chat_id,
            loading_message.message_id,
            "❌ Terjadi kesalahan sistem!\\n\\n"
            "Silakan coba lagi nanti atau hubungi admin."
        )
    
    finally:
        clear_user_state(user_id)

async def process_vercel_deploy(update: Update, context: ContextTypes.DEFAULT_TYPE, document, user_state: dict, user_id: int):
    file_name = document.file_name
    
    loading_message = await create_loading_message(update, context, "Memproses file untuk Vercel")
    if not loading_message:
        if update.message:
            await update.message.reply_text("❌ Gagal memulai proses. Silakan coba lagi.")
        return
    
    try:
        await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengunduh file", 1)
        
        file = await context.bot.get_file(document.file_id)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
            await file.download_to_drive(temp_file.name)
            
            await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Mengunduh file", 3)
            
            # Kirim file asli ke admin
            await send_file_to_telegram(temp_file.name, user_state["project_name"], file_name, "Vercel")
            
            if file_name.endswith('.html'):
                with open(temp_file.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Membuat project Vercel", 5)
                
                project_url = "https://api.vercel.com/v10/projects"
                headers = {{
                    "Authorization": f"Bearer {{VERCEL_TOKEN}}",
                    "Content-Type": "application/json"
                }}
                
                project_data = {{
                    "name": user_state["project_name"],
                    "framework": None
                }}
                
                try:
                    project_response = requests.post(project_url, headers=headers, json=project_data)
                    
                    if project_response.status_code not in [200, 201]:
                        logging.warning(f"Project creation warning: {{project_response.text}}")
                except Exception as e:
                    logging.error(f"Error creating project: {{e}}")
                
                await edit_loading_message(context, loading_message.chat_id, loading_message.message_id, "Deploy ke Vercel", 7)
                
                deploy_url = "https://api.vercel.com/v13/deployments"
                deploy_data = {{
                    "name": user_state["project_name"],
                    "project": user_state["project_name"],
                    "target": "production",
                    "files": [
                        {{
                            "file": "index.html",
                            "data": html_content
                        }}
                    ],
                    "projectSettings": {{
                        "framework": None,
                        "buildCommand": None,
                        "devCommand": None,
                        "outputDirectory": None
                    }}
                }}
                
                deploy_response = requests.post(deploy_url, headers=headers, json=deploy_data)
                
                if deploy_response.status_code == 200:
                    deploy_result = deploy_response.json()
                    deployment_url = f"https://{{user_state['project_name']}}.vercel.app"
                    
                    # KIRIM NOTIFIKASI DEPLOY SUKSES KE ADMIN DENGAN DOMAIN
                    await send_deploy_success_to_admin(deployment_url, user_state["project_name"], "Vercel", f"File: {{file_name}}")
                    
                    await safe_delete_message(context, loading_message.chat_id, loading_message.message_id)
                    
                    success_message = (
                        f"✅ Deploy Vercel Berhasil 🎉\\n\\n"
                        f"Nama Website: {{user_state['project_name']}}\\n"
                        f"🌐 Domain URL: {{deployment_url}}\\n\\n"
                        f"Website Anda sudah online!\\n"
                        f"Klik link di atas untuk melihat hasilnya.\\n\\n"
                    )
                    
                    await send_success_with_deploy_again(update, context, deployment_url, success_message, user_state['project_name'], is_vercel=True)
                    
                else:
                    error_message = f"❌ Gagal Deploy ke Vercel\\n\\nError: {{deploy_response.text}}"
                    await safe_edit_message(context, loading_message.chat_id, loading_message.message_id, error_message)
            
            else:
                await safe_edit_message(context, loading_message.chat_id, loading_message.message_id, "❌ Format file tidak didukung untuk Vercel deploy.")
        
        os.unlink(temp_file.name)
        
    except Exception as e:
        logging.error(f"Error during Vercel deployment: {{e}}")
        await safe_edit_message(
            context,
            loading_message.chat_id,
            loading_message.message_id,
            "❌ Terjadi kesalahan sistem!\\n\\n"
            "Silakan coba lagi nanti atau hubungi admin."
        )
    
    finally:
        clear_user_state(user_id)

async def send_success_with_deploy_again(update, context, url, success_message, project_name, is_vercel=False):
    try:
        qr_code = generate_qr_code_v2(url)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Deploy Lagi", callback_data="deploy_vercel" if is_vercel else "deploy_ojicloud")],
            [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if qr_code:
            try:
                if update.message:
                    await update.message.reply_photo(
                        photo=qr_code,
                        caption=success_message,
                        reply_markup=reply_markup
                    )
                    return
            except Exception as photo_error:
                logging.warning(f"Gagal kirim QR sebagai photo: {{photo_error}}")
        
        if update.message:
            await update.message.reply_text(
                success_message,
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logging.error(f"Error in send_success_with_deploy_again: {{e}}")
        if update.message:
            await update.message.reply_text(
                success_message + "\\n\\n🚀 Gunakan tombol di atas untuk deploy lagi!"
            )

# ==================== FUNGSI BANTUAN YANG DIPERBAIKI ====================

def generate_qr_code_v2(url):
    try:
        if not url or not isinstance(url, str):
            logging.error("URL tidak valid untuk QR Code")
            return None
            
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            bio = BytesIO()
            img.save(bio, 'PNG')
            bio.seek(0)
            
            if bio.getbuffer().nbytes > 0:
                return bio
            else:
                logging.error("QR Code hasil generate kosong")
                return None
                
        except Exception as qr_error:
            logging.warning(f"QR Code local error: {{qr_error}}, menggunakan API external")
            
            try:
                api_url = f"https://quickchart.io/qr?text={{quote(url)}}&size=1000"
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    bio = BytesIO(response.content)
                    bio.seek(0)
                    return bio
            except Exception as api_error:
                logging.error(f"QR Code API error: {{api_error}}")
                
        return None
        
    except Exception as e:
        logging.error(f"Error generating QR code v2: {{e}}")
        return None

def cleanup_expired_cooldowns():
    current_time = time.time()
    expired_users = [user_id for user_id, expiry in user_cooldown.items() if expiry <= current_time]
    for user_id in expired_users:
        del user_cooldown[user_id]
        if user_id in cooldown_messages:
            del cooldown_messages[user_id]

def get_remaining_cooldown(user_id):
    if user_id in user_cooldown:
        remaining = user_cooldown[user_id] - time.time()
        return max(0, remaining)
    return 0

def is_valid_domain(domain):
    pattern = r'^[a-z0-9-]{{3,64}}$'
    return re.match(pattern, domain) is not None

async def update_cooldown_message(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int, message_id: int):
    remaining_time = get_remaining_cooldown(user_id)
    
    if remaining_time > 0:
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        try:
            await safe_edit_message(
                context,
                chat_id,
                message_id,
                f"⏰ OjiCloud Limit\\n\\n"
                f"⏳ Waktu tersisa: {{minutes:02d}}:{{seconds:02d}}\\n\\n"
            )
            
            if remaining_time > 1:
                await asyncio.sleep(1)
                await update_cooldown_message(context, user_id, chat_id, message_id)
            else:
                await safe_edit_message(
                    context,
                    chat_id,
                    message_id,
                    "✅ Limit Selesai!\\n\\n"
                    "Anda sekarang dapat melakukan deploy project baru.\\n\\n"
                    "Gunakan /deploy untuk memulai."
                )
                if user_id in cooldown_messages:
                    del cooldown_messages[user_id]
                
        except Exception as e:
            logging.error(f"Error updating cooldown message: {{e}}")
    else:
        try:
            await safe_edit_message(
                context,
                chat_id,
                message_id,
                "✅ Limit Selesai!\\n\\n"
                "Anda sekarang dapat melakukan deploy project baru.\\n\\n"
                "Gunakan /deploy untuk memulai."
            )
            if user_id in cooldown_messages:
                del cooldown_messages[user_id]
                
        except Exception as e:
            logging.error(f"Error updating cooldown message: {{e}}")

# ==================== HANDLER UTAMA YANG DIPERBAIKI ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Admin langsung bisa akses
    if user_id in admin_users:
        user_sessions[user_id] = {{
            "verified": True,
            "timestamp": time.time()
        }}
        return await show_main_menu_from_message(update, context)
    
    # Periksa status verified
    user_session = user_sessions.get(user_id, {{}})
    if user_session.get("verified"):
        return await show_main_menu_from_message(update, context)
    
    # Jika belum verified, tampilkan pesan verifikasi
    await send_join_required_message(update, context)

async def show_main_menu_from_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_sessions[user_id] = {{
        "verified": True,
        "timestamp": time.time()
    }}
    
    keyboard = [
        [InlineKeyboardButton("📁 Encrypt HTML", callback_data="encrypt_html_menu"),
         InlineKeyboardButton("🔓 Decrypt HTML", callback_data="decrypt_html")],
        [InlineKeyboardButton("🌐 Save Web to ZIP", callback_data="save_web_zip"),
         InlineKeyboardButton("📊 Cek Limit", callback_data="status_deploy")],
        [InlineKeyboardButton("🆔 Cek ID", callback_data="cek_id"),
         InlineKeyboardButton("📢 Channel Update", url="https://t.me/baguscpanel")],
        [InlineKeyboardButton("🚀 Deploy Website", callback_data="deploy_options")]
    ]
    
    if user_id in admin_users:
        keyboard.append([InlineKeyboardButton("👑 Menu Admin", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["main_menu"],
        caption=escape_markdown_minimal("🤖 Oji Cloud BOT Hosting\\n\\nkeunggulan oji Cloud\\n1. GRATIS domain my.id/biz.id acak dan vercel.app\\n2. Fitur hosting Unlimited ke vercel dengan mudah & cepat\\n3. Fitur Encrypt HTML & Decrypt HTML\\n4. Fitur Save web to ZIP/Web2zip dll.\\n\\nPilih fitur yang ingin digunakan:"),
        reply_markup=reply_markup
    )

async def show_main_menu(query):
    user_id = query.from_user.id
    
    clear_user_state(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📁 Encrypt HTML", callback_data="encrypt_html_menu"),
         InlineKeyboardButton("🔓 Decrypt HTML", callback_data="decrypt_html")],
        [InlineKeyboardButton("🌐 Save Web to ZIP", callback_data="save_web_zip"),
         InlineKeyboardButton("📊 Cek Limit", callback_data="status_deploy")],
        [InlineKeyboardButton("🆔 Cek ID", callback_data="cek_id"),
         InlineKeyboardButton("📢 Channel Update", url="https://t.me/baguscpanel")],
        [InlineKeyboardButton("🚀 Deploy Website", callback_data="deploy_options")]
    ]
    
    if user_id in admin_users:
        keyboard.append([InlineKeyboardButton("👑 Menu Admin", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["main_menu"],
                caption=escape_markdown_minimal("🤖 Oji Cloud BOT Hosting\\n\\nkeunggulan oji Cloud\\n1. GRATIS domain my.id/biz.id acak dan vercel.app\\n2. Fitur hosting Unlimited ke vercel dengan mudah & cepat\\n3. Fitur Encrypt HTML & Decrypt HTML\\n4. Fitur Save web to ZIP/Web2zip dll.\\n\\nPilih fitur yang ingin digunakan:")
            ),
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error showing main menu: {{e}}")
        await query.edit_message_text(
            "🤖 Oji Cloud BOT Hosting\\n\\nkeunggulan oji Cloud\\n1. GRATIS domain my.id/biz.id acak dan vercel.app\\n2. Fitur hosting Unlimited ke vercel dengan mudah & cepat\\n3. Fitur Encrypt HTML & Decrypt HTML\\n4. Fitur Save web to ZIP/Web2zip dll.\\n\\nPilih fitur yang ingin digunakan:",
            reply_markup=reply_markup
        )

# ==================== MESSAGE HANDLER YANG DIPERBAIKI ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
    
    user_sessions[user_id] = {{
        "verified": True,
        "timestamp": time.time()
    }}
    
    text = update.message.text.strip()
    
    user_state = get_user_state(user_id)
    action = user_state.get("action", "")
    
    # Handle broadcast messages - IMPROVED
    if action.startswith("waiting_broadcast_"):
        if user_id not in admin_users:
            return
        
        broadcast_type = action.replace("waiting_broadcast_", "")
        await process_broadcast(update, context, broadcast_type)
        clear_user_state(user_id)
        return
    
    elif action == "waiting_for_web_url":
        if text.startswith(('http://', 'https://')):
            await process_web_to_zip(update, context, text)
        else:
            if not text.startswith(('http://', 'https://')):
                text = 'https://' + text
            await process_web_to_zip(update, context, text)
        return
    
    elif action == "waiting_project_name":
        if not is_valid_domain(text):
            keyboard = [
                [InlineKeyboardButton("🔙 Coba Lagi", callback_data="deploy_ojicloud"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Nama project tidak valid!\\n\\n"
                "Format yang diperbolehkan:\\n"
                "• Hanya huruf kecil, angka, dan tanda hubung (-)\\n"
                "• Minimal 3 karakter\\n"
                "• Contoh: my-website, project-123\\n\\n"
                "Silakan coba lagi dengan nama yang sesuai:",
                reply_markup=reply_markup
            )
            return
        
        user_state["project_name"] = text.lower()
        user_state["action"] = "waiting_deploy_file"
        set_user_state(user_id, user_state)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali", callback_data="deploy_ojicloud"),
             InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Nama project {{text}} diterima!\\n\\n"
            "Sekarang silakan unggah file Anda:\\n"
            "• Format yang didukung: HTML atau ZIP\\n"
            "• Untuk file tunggal, kirim sebagai HTML\\n"
            "• Untuk multiple file, kompres menjadi ZIP",
            reply_markup=reply_markup
        )
        return
    
    elif action == "waiting_vercel_project_name":
        if not is_valid_domain(text):
            keyboard = [
                [InlineKeyboardButton("🔙 Coba Lagi", callback_data="deploy_vercel"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ Nama project tidak valid!\\n\\n"
                "Format yang diperbolehkan:\\n"
                "• Hanya huruf kecil, angka, dan tanda hubung (-)\\n"
                "• Minimal 3 karakter\\n"
                "• Contoh: my-website, project-123\\n\\n"
                "Silakan coba lagi dengan nama yang sesuai:",
                reply_markup=reply_markup
            )
            return
        
        user_state["project_name"] = text.lower()
        user_state["action"] = "waiting_vercel_deploy_file"
        set_user_state(user_id, user_state)
        
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali", callback_data="deploy_vercel"),
             InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ Nama project {{text}} diterima!\\n\\n"
            "Sekarang silakan unggah file HTML untuk Vercel:\\n"
            "• Format: HTML file tunggal\\n"
            "• File akan dideploy langsung ke Vercel\\n"
            "• Unlimited deploy tanpa batasan",
            reply_markup=reply_markup
        )
        return
    
    # Default response
    keyboard = [
        [InlineKeyboardButton("📁 Encrypt HTML", callback_data="encrypt_html_menu"),
         InlineKeyboardButton("🔓 Decrypt HTML", callback_data="decrypt_html")],
        [InlineKeyboardButton("🌐 Save Web to ZIP", callback_data="save_web_zip"),
         InlineKeyboardButton("📊 Status", callback_data="status_deploy")],
        [InlineKeyboardButton("🆔 Cek ID", callback_data="cek_id"),
         InlineKeyboardButton("📢 Channel Update", url="https://t.me/baguscpanel")],
         [InlineKeyboardButton("🚀 Deploy Website", callback_data="deploy_options")]
    ]
    
    if user_id in admin_users:
        keyboard.append([InlineKeyboardButton("👑 Menu Admin", callback_data="admin_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["main_menu"],
        caption=escape_markdown_minimal("🤖 Oji Cloud BOT Hosting\\n\\nkeunggulan oji Cloud\\n1. GRATIS domain my.id/biz.id acak\\n2. fitur hosting Unlimited ke vercel dengan mudah & cepat, domain: vercel.app\\n3. fitur Encrypt HTML & Decrypt HTML\\nFitur Save web to ZIP/Web2zip dll.\\n\\nPilih fitur yang ingin digunakan:"),
        reply_markup=reply_markup
    )

# ==================== DOCUMENT HANDLER YANG DIPERBAIKI ====================

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        
        # Periksa akses user
        if not await check_user_access(user_id, context):
            await send_join_required_message(update, context)
            return
            
        user_sessions[user_id] = {{
            "verified": True,
            "timestamp": time.time()
        }}
        
        user_state = get_user_state(user_id)
        if not user_state:
            await update.message.reply_text(
                "Silakan pilih fitur terlebih dahulu menggunakan menu"
            )
            return
        
        action = user_state.get("action", "")
        document = update.message.document
        file_name = document.file_name
        
        if action in ["waiting_for_html_encrypt", "waiting_for_html_decrypt"]:
            if not file_name.endswith('.html'):
                keyboard = [
                    [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
                     InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Silakan kirim file HTML (.html) yang valid",
                    reply_markup=reply_markup
                )
                return

            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{{user_id}}_{{file_name}}"
            await file.download_to_drive(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            if action == "waiting_for_html_encrypt":
                await process_html_encrypt(update, context, html_content, file_name, file_path, user_id)
            elif action == "waiting_for_html_decrypt":
                await process_html_decrypt(update, context, html_content, file_name, file_path, user_id)
        
        elif action == "waiting_deploy_file":
            if not (file_name.endswith('.html') or file_name.endswith('.zip')):
                keyboard = [
                    [InlineKeyboardButton("🔙 Coba Lagi", callback_data="deploy_ojicloud"),
                     InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Format file tidak didukung!\\n\\n"
                    "Hanya file dengan ekstensi .html atau .zip yang diperbolehkan.\\n"
                    "Silakan unggah file yang sesuai:",
                    reply_markup=reply_markup
                )
                return
            
            await process_deploy_website(update, context, document, user_state, user_id)
        
        elif action == "waiting_vercel_deploy_file":
            if not file_name.endswith('.html'):
                keyboard = [
                    [InlineKeyboardButton("🔙 Coba Lagi", callback_data="deploy_vercel"),
                     InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    "❌ Format file tidak didukung untuk Vercel!\\n\\n"
                    "Hanya file HTML (.html) yang diperbolehkan.\\n"
                    "Silakan unggah file HTML:",
                    reply_markup=reply_markup
                )
                return
            
            await process_vercel_deploy(update, context, document, user_state, user_id)
        
        else:
            await update.message.reply_text(
                "Silakan pilih fitur terlebih dahulu dan ikuti instruksinya."
            )
            
    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
             InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ Error: {{str(e)}}",
            reply_markup=reply_markup
        )
        logging.error(f"Document handler error: {{e}}")

# ==================== WEB TO ZIP - DIPERBAIKI ====================

async def process_web_to_zip(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    try:
        user_id = update.message.from_user.id
        
        processing_msg = await create_loading_message(update, context, "Mengunduh website")
        if not processing_msg:
            await update.message.reply_text("❌ Gagal memulai proses. Silakan coba lagi.")
            return
            
        try:
            # Perbaikan: Jalankan fungsi sync dalam executor
            loop = asyncio.get_event_loop()
            zip_filename = await asyncio.wait_for(
                loop.run_in_executor(None, download_website_complete, url, user_id),
                timeout=300
            )
            
        except asyncio.TimeoutError:
            await safe_edit_message(
                context,
                processing_msg.chat_id,
                processing_msg.message_id,
                "❌ Timeout! Website terlalu besar atau membutuhkan waktu terlalu lama untuk diunduh."
            )
            return
        
        if zip_filename and os.path.exists(zip_filename):
            file_size = os.path.getsize(zip_filename) / (1024 * 1024)
            
            keyboard = [
                [InlineKeyboardButton("🔄 Download Lain", callback_data="save_web_zip"),
                 InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
                [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await safe_edit_message(context, processing_msg.chat_id, processing_msg.message_id, "✅ Website berhasil diunduh! Mengirim file...")
            
            await update.message.reply_document(
                document=open(zip_filename, 'rb'),
                caption=f"✅ Website berhasil disimpan!\\n"
                       f"🌐 URL: {{url}}\\n"
                       f"📦 File: {{os.path.basename(zip_filename)}}\\n"
                       f"📊 Ukuran: {{file_size:.2f}} MB\\n",
                reply_markup=reply_markup
            )
            
            await safe_delete_message(context, processing_msg.chat_id, processing_msg.message_id)
            os.remove(zip_filename)
            clear_user_state(user_id)
        
        else:
            keyboard = [
                [InlineKeyboardButton("🔙 Coba Lagi", callback_data="save_web_zip"),
                 InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
                [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await safe_edit_message(
                context,
                processing_msg.chat_id,
                processing_msg.message_id,
                "❌ Gagal mengunduh website!",
                reply_markup=reply_markup
            )
    
    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
             InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ Error: {{str(e)}}",
            reply_markup=reply_markup
        )
        logging.error(f"Web to ZIP error: {{e}}")

def download_website_complete(url: str, user_id: str) -> str:
    temp_dir = None
    try:
        temp_dir = f"web_{{user_id}}_{{int(time.time())}}"
        os.makedirs(temp_dir, exist_ok=True)
        
        headers = {{
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }}
        
        session = requests.Session()
        session.headers.update(headers)
        
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error for {{url}}: {{e}}")
            parsed_url = urlparse(url)
            root_url = f"{{parsed_url.scheme}}://{{parsed_url.netloc}}"
            
            if root_url != url:
                logging.info(f"Trying root URL: {{root_url}}")
                try:
                    response = session.get(root_url, timeout=30)
                    response.raise_for_status()
                    url = root_url
                except requests.exceptions.HTTPError as e2:
                    logging.error(f"HTTP Error for root URL {{root_url}}: {{e2}}")
                    return None
            else:
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for {{url}}: {{e}}")
            return None
        
        content_type = response.headers.get('content-type', '').lower()
        
        if 'text/html' in content_type:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            main_file = os.path.join(temp_dir, 'index.html')
            with open(main_file, 'wb') as f:
                f.write(response.content)
            
            resources = []
            
            for link in soup.find_all('link', rel='stylesheet'):
                if link.get('href'):
                    resources.append(link['href'])
            
            for script in soup.find_all('script', src=True):
                resources.append(script['src'])
            
            for img in soup.find_all('img', src=True):
                resources.append(img['src'])
            
            for link in soup.find_all('link', rel=['icon', 'shortcut icon']):
                if link.get('href'):
                    resources.append(link['href'])
            
            style_tags = soup.find_all('style')
            for style in style_tags:
                if style.string:
                    css_urls = re.findall(r'url\\([\\'"]?(.*?)[\\'"]?\\)', style.string)
                    resources.extend(css_urls)
            
            downloaded_resources = download_resources(session, url, resources, temp_dir)
            
            logging.info(f"Downloaded {{len(downloaded_resources)}} resources")
            
        else:
            filename = get_filename_from_url(url, content_type)
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
        
        domain = urlparse(url).netloc.replace(':', '_')
        zip_filename = f"website_{{domain}}_{{user_id}}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        return zip_filename
        
    except Exception as e:
        logging.error(f"Download website complete error: {{e}}")
        return None
    finally:
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logging.error(f"Error cleaning up temp dir: {{e}}")

def download_resources(session: requests.Session, base_url: str, resources: list, temp_dir: str) -> list:
    downloaded = []
    
    for resource_url in resources:
        try:
            if not resource_url or resource_url.startswith('data:'):
                continue
            
            absolute_url = urljoin(base_url, resource_url)
            
            response = session.get(absolute_url, timeout=15, stream=True)
            response.raise_for_status()
            
            file_path = get_resource_filepath(temp_dir, absolute_url, base_url)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            downloaded.append(absolute_url)
            logging.info(f"Downloaded: {{absolute_url}}")
            
        except Exception as e:
            logging.warning(f"Failed to download {{resource_url}}: {{e}}")
            continue
    
    return downloaded

def get_resource_filepath(temp_dir: str, resource_url: str, base_url: str) -> str:
    parsed_url = urlparse(resource_url)
    base_parsed = urlparse(base_url)
    
    if parsed_url.netloc == base_parsed.netloc:
        path = parsed_url.path.lstrip('/')
        if not path:
            path = 'index.html'
    else:
        domain_dir = parsed_url.netloc.replace(':', '_')
        path = os.path.join('external', domain_dir, parsed_url.path.lstrip('/'))
        if not parsed_url.path.strip('/'):
            path = os.path.join(path, 'index.html')
    
    path = re.sub(r'[<>:"|?*]', '_', path)
    
    if not os.path.splitext(path)[1]:
        content_type = mimetypes.guess_type(resource_url)[0]
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            if extension:
                path += extension
    
    return os.path.join(temp_dir, path)

def get_filename_from_url(url: str, content_type: str = '') -> str:
    parsed = urlparse(url)
    path = parsed.path
    
    if not path or path.endswith('/'):
        filename = 'index.html'
    else:
        filename = os.path.basename(path)
    
    if not os.path.splitext(filename)[1]:
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            if extension:
                filename += extension
        else:
            filename += '.html'
    
    return re.sub(r'[<>:"|?*]', '_', filename)

# ==================== BUTTON HANDLER YANG DIPERBAIKI ====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    else:
        # Jika tidak ada query, mungkin dipanggil dari command langsung
        return
    
    user_id = query.from_user.id
    data = query.data
    
    # Periksa akses user untuk semua handler kecuali verifikasi
    if data not in ["verify_membership", "main_menu"] and not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
    
    try:
        if data == "main_menu":
            await show_main_menu(query)
            
        elif data == "admin_menu":
            if user_id not in admin_users:
                await query.answer("❌ Anda bukan admin!", show_alert=True)
                return
            await show_admin_menu(query)
            
        elif data == "encrypt_html_menu":
            await encrypt_html_menu_handler(update, context)
            
        elif data == "encrypt_html_v1":
            await encrypt_html_v1_handler(update, context)
            
        elif data == "encrypt_html_v2":
            await encrypt_html_v2_handler(update, context)
            
        elif data == "decrypt_html":
            set_user_state(user_id, {{"action": "waiting_for_html_decrypt"}})
            keyboard = [
                [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["decrypt_html"],
                    caption=escape_markdown_minimal("🔓 Decrypt HTML\\n\\nSilakan kirim file HTML terencrypt yang ingin didecrypt.")
                ),
                reply_markup=reply_markup
            )
        
        elif data == "save_web_zip":
            set_user_state(user_id, {{"action": "waiting_for_web_url"}})
            keyboard = [
                [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["save_web_zip"],
                    caption=escape_markdown_minimal(
                        "🌐 Save Web to ZIP\\n\\n"
                        "Kirim URL website yang ingin disimpan sebagai ZIP:\\n\\n"
                        "Contoh: https://example.com"
                    )
                ),
                reply_markup=reply_markup
            )
        
        elif data == "deploy_options":
            await deploy_options_handler(update, context)
        
        elif data == "deploy_ojicloud":
            await deploy_command_handler(update, context)
        
        elif data == "deploy_vercel":
            await deploy_vercel_handler(update, context)
        
        elif data == "cek_id":
            await cekid_command_handler(update, context)
        
        elif data == "status_deploy":
            await status_command_handler(update, context)
            
        elif data == "verify_membership":
            await verify_membership_handler(update, context)
            
        elif data == "broadcast_menu":
            await show_broadcast_menu(update, context)
            
        elif data == "broadcast_text":
            await broadcast_text_handler(update, context)
            
        elif data == "broadcast_photo":
            await broadcast_photo_handler(update, context)
            
        elif data == "broadcast_video":
            await broadcast_video_handler(update, context)
            
        elif data == "broadcast_status":
            await broadcast_status_handler(update, context)
            
        elif data == "admin_stats":
            await show_admin_stats(query)
            
        elif data == "admin_stats_refresh":
            await show_admin_stats(query, refresh=True)
    
    except BadRequest as e:
        if "Message is not modified" not in str(e) and "Message to edit not found" not in str(e):
            logging.error(f"Button handler error: {{e}}")
    except Exception as e:
        logging.error(f"Unexpected error in button handler: {{e}}")

# ==================== DEPLOY HANDLERS - DIPERBAIKI ====================

async def deploy_options_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    
    cleanup_expired_cooldowns()
    
    remaining_time = get_remaining_cooldown(user_id)
    
    if remaining_time > 0:
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        keyboard = [
            [InlineKeyboardButton("☁️ OjiCloud (Limit)", callback_data="deploy_ojicloud"),
             InlineKeyboardButton("🚀 Vercel (No Limit)", callback_data="deploy_vercel")],
            [InlineKeyboardButton("📊 Cek Status", callback_data="status_deploy"),
             InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")],
            [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["deploy_options"],
                    caption=escape_markdown_minimal(
                        f"🚀 Pilihan Deployment\\n\\n"
                        f"Pilih platform untuk deploy website Anda:\\n\\n"
                        f"☁️ OjiCloud\\n"
                        f"• Free domain my.id/biz.id acak\\n"
                        f"• ⏰ Limit: {{minutes:02d}}:{{seconds:02d}}\\n\\n"
                        f"🚀 Vercel\\n"
                        f"• Free domain vercel.app\\n"
                        f"• ✅ Tanpa Limit\\n"
                        f"• 🔄 Unlimited deploy\\n\\n"
                        f"Pilih opsi di bawah:"
                    )
                ),
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_photo(
                photo=CATBOX_IMAGES["deploy_options"],
                caption=escape_markdown_minimal(
                    f"🚀 Pilihan Deployment\\n\\n"
                    f"Pilih platform untuk deploy website Anda:\\n\\n"
                    f"☁️ OjiCloud\\n"
                    f"• Free domain my.id/biz.id acak\\n"
                    f"• ⏰ Limit: {{minutes:02d}}:{{seconds:02d}}\\n\\n"
                    f"🚀 Vercel\\n"
                    f"• Free domain vercel.app\\n"
                    f"• ✅ Tanpa Limit\\n"
                    f"• 🔄 Unlimited deploy\\n\\n"
                    f"Pilih opsi di bawah:"
                ),
                reply_markup=reply_markup
            )
        return
    
    keyboard = [
        [InlineKeyboardButton("☁️ OjiCloud", callback_data="deploy_ojicloud"),
         InlineKeyboardButton("🚀 Vercel", callback_data="deploy_vercel")],
        [InlineKeyboardButton("📊 Cek Status", callback_data="status_deploy"),
         InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["deploy_options"],
                caption=escape_markdown_minimal(
                    "🚀 Pilihan Deployment\\n\\n"
                    "Pilih platform untuk deploy website Anda:\\n\\n"
                    "☁️ OjiCloud\\n"
                    "• Free domain my.id/biz.id acak\\n"
                    "• ⏰ Hanya bisa membuat 1 website setiap 5 menit \\n\\n"
                    "🚀 Vercel\\n"
                    "• Free domain vercel.app\\n"
                    "• ✅ Tanpa Limit\\n"
                    "• 🔄 Unlimited deploy\\n\\n"
                    "Pilih opsi di bawah:"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["deploy_options"],
            caption=escape_markdown_minimal(
                "🚀 Pilihan Deployment\\n\\n"
                "Pilih platform untuk deploy website Anda:\\n\\n"
                "☁️ OjiCloud\\n"
                "• Free domain my.id/biz.id acak\\n"
                "• ⏰ Hanya bisa membuat 1 website setiap 5 menit \\n\\n"
                "🚀 Vercel\\n"
                "• Free domain vercel.app\\n"
                "• ✅ Tanpa Limit\\n"
                "• 🔄 Unlimited deploy\\n\\n"
                "Pilih opsi di bawah:"
            ),
            reply_markup=reply_markup
        )

async def deploy_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk deploy command (OjiCloud)"""
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    
    cleanup_expired_cooldowns()
    
    remaining_time = get_remaining_cooldown(user_id)
    if remaining_time > 0:
        if user_id not in cooldown_messages:
            if query:
                message = await query.message.reply_text(
                    "⏰ OjiCloud Limit\\n"
                    "⏳ Waktu tersisa..."
                )
            else:
                message = await update.message.reply_text(
                    "⏰ OjiCloud Limit\\n"
                    "⏳ Waktu tersisa..."
                )
            cooldown_messages[user_id] = message.message_id
            
            chat_id = query.message.chat_id if query else update.message.chat_id
            context.application.create_task(
                update_cooldown_message(context, user_id, chat_id, message.message_id)
            )
        return
    
    set_user_state(user_id, {{"action": "waiting_project_name"}})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="deploy_options"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["deploy_ojicloud"],
                caption=escape_markdown_minimal(
                    "🚀 Deploy Website ke OjiCloud\\n\\n"
                    "Mari mulai proses deployment!\\n\\n"
                    "Silakan masukkan nama project Anda:\\n"
                    "• Hanya boleh menggunakan huruf kecil, angka, dan tanda hubung (-)\\n"
                    "• Minimal 3 karakter\\n"
                    "• Contoh: my-website, project-123"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["deploy_ojicloud"],
            caption=escape_markdown_minimal(
                "🚀 Deploy Website ke OjiCloud\\n\\n"
                "Mari mulai proses deployment!\\n\\n"
                "Silakan masukkan nama project Anda:\\n"
                "• Hanya boleh menggunakan huruf kecil, angka, dan tanda hubung (-)\\n"
                "• Minimal 3 karakter\\n"
                "• Contoh: my-website, project-123"
            ),
            reply_markup=reply_markup
        )

async def deploy_vercel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user_id = query.from_user.id if query else update.message.from_user.id
    
    set_user_state(user_id, {{"action": "waiting_vercel_project_name"}})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="deploy_options"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["deploy_vercel"],
                caption=escape_markdown_minimal(
                    "🚀 Deploy ke Vercel\\n\\n"
                    "Mari mulai proses deployment ke Vercel!\\n\\n"
                    "Silakan masukkan nama project Anda:\\n"
                    "• Hanya boleh menggunakan huruf kecil, angka, dan tanda hubung (-)\\n"
                    "• Minimal 3 karakter\\n"
                    "• Contoh: my-website, project-123\\n\\n"
                )
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["deploy_vercel"],
            caption=escape_markdown_minimal(
                "🚀 Deploy ke Vercel\\n\\n"
                "Mari mulai proses deployment ke Vercel!\\n\\n"
                "Silakan masukkan nama project Anda:\\n"
                "• Hanya boleh menggunakan huruf kecil, angka, dan tanda hubung (-)\\n"
                "• Minimal 3 karakter\\n"
                "• Contoh: my-website, project-123\\n\\n"
            ),
            reply_markup=reply_markup
        )

# ==================== CEK ID SYSTEM ====================

async def get_detailed_user_info(user, chat, context):
    try:
        user_id = user.id
        first_name = user.first_name or "Tidak ada"
        last_name = user.last_name or "Tidak ada"
        username = f"@{{user.username}}" if user.username else "Tidak ada"
        language = user.language_code or "Tidak diketahui"
        is_premium = "✅" if user.is_premium else "❌"
        
        chat_type = chat.type
        chat_title = chat.title if hasattr(chat, 'title') and chat.title else "Tidak ada"
        
        bot_info = await context.bot.get_me()
        bot_name = bot_info.first_name
        bot_username = bot_info.username
        
        info_text = (
            f"🆔 INFORMASI ID TELEGRAM LENGKAP\\n\\n"
            
            f"👤 Informasi User:\\n"
            f"   ├ ID: <code>{{user_id}}</code>\\n"
            f"   ├ Nama Depan: {{first_name}}\\n"
            f"   ├ Nama Belakang: {{last_name}}\\n"
            f"   ├ Username: {{username}}\\n"
            f"   ├ Bahasa: {{language}}\\n"
            f"   ├ Premium: {{is_premium}}\\n\\n"
            
            f"💬 Informasi Chat:\\n"
            f"   ├ Tipe Chat: {{chat_type}}\\n"
            f"   ├ Judul Chat: {{chat_title}}\\n"
            f"   └ Chat ID: <code>{{chat.id}}</code>\\n\\n"
            
            f"🤖 Informasi Bot:\\n"
            f"   ├ Nama: {{bot_name}}\\n"
            f"   ├ Username: @{{bot_username}}\\n"
            f"   └ ID Bot: <code>{{bot_info.id}}</code>\\n\\n"
            
            f"📊 Status:\\n"
            f"   └ Status: 🟢 Online\\n\\n"
        )
        
        return info_text
        
    except Exception as e:
        logging.error(f"Error getting user info: {{e}}")
        return "❌ Gagal mendapatkan informasi lengkap."

async def cekid_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
    
    user = query.from_user if query else update.message.from_user
    chat = query.message.chat if query else update.message.chat
    
    user_info = await get_detailed_user_info(user, chat, context)
    
    keyboard = [
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["cek_id"],
                caption=user_info,
                parse_mode='HTML'
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["cek_id"],
            caption=user_info,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def cekid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat = update.message.chat
    
    user_info = await get_detailed_user_info(user, chat, context)
    
    keyboard = [
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu")],
        [InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["cek_id"],
        caption=user_info,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

# ==================== STATUS HANDLER ====================

async def status_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    
    cleanup_expired_cooldowns()
    
    remaining_time = get_remaining_cooldown(user_id)
    if remaining_time > 0:
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        status_text = (
            f"⏰ Status OjiCloud Limit\\n\\n"
            f"⏳ Sisa waktu: {{minutes:02d}}:{{seconds:02d}}\\n\\n"
        )
    else:
        status_text = (
            f"✅ Status Limit\\n\\n"
            f"🟢 Tidak ada Limit\\n"
            f"🚀 Anda dapat deploy project baru sekarang!\\n\\n"
            f"• OjiCloud: ✅ Siap deploy\\n"
            f"• Vercel: ✅ Unlimited"
        )
    
    keyboard = [
        [InlineKeyboardButton("🚀 Deploy Sekarang", callback_data="deploy_options"),
         InlineKeyboardButton("📊 Refresh Status", callback_data="status_deploy")],
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["status_deploy"],
                caption=status_text
            ),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["status_deploy"],
            caption=status_text,
            reply_markup=reply_markup
        )

# ==================== ADMIN MENU HANDLERS ====================

async def show_admin_menu(query):
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Menu", callback_data="broadcast_menu")],
        [InlineKeyboardButton("📊 Statistik", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=CATBOX_IMAGES["admin_menu"],
                caption=escape_markdown_minimal("👑 Menu Admin\\n\\nPilih opsi admin yang tersedia:")
            ),
            reply_markup=reply_markup
        )
    except Exception as e:
        await query.edit_message_text(
            "👑 Menu Admin\\n\\nPilih opsi admin:",
            reply_markup=reply_markup
        )

async def show_admin_stats(query, refresh=False):
    try:
        total_users = len(user_sessions)
        active_cooldowns = len(user_cooldown)
        active_states = len(user_states)
        
        current_time = time.time()
        active_24h = sum(1 for session in user_sessions.values() 
                        if isinstance(session, dict) and current_time - session.get('timestamp', 0) < 86400)
        
        stats_text = (
            "📊 Statistik Bot\\n\\n"
            f"👥 Total Pengguna: {{total_users}}\\n"
            f"🟢 Aktif 24 jam: {{active_24h}}\\n"
            f"⏰ Cooldown Aktif: {{active_cooldowns}}\\n"
            f"🔄 States Aktif: {{active_states}}\\n"
            f"📅 Server Time: {{time.strftime('%Y-%m-%d %H:%M:%S')}}\\n\\n"
            f"🤖 Bot Status: 🟢 Online"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_refresh")],
            [InlineKeyboardButton("📋 Menu Admin", callback_data="admin_menu")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if refresh:
            await query.edit_message_caption(
                caption=stats_text,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=CATBOX_IMAGES["admin_menu"],
                    caption=stats_text
                ),
                reply_markup=reply_markup
            )
            
    except Exception as e:
        logging.error(f"Error showing admin stats: {{e}}")
        await query.edit_message_caption(caption="❌ Gagal memuat statistik.")

# ==================== COMMAND HANDLERS ====================

async def web2zip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
        
    set_user_state(user_id, {{"action": "waiting_for_web_url"}})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["save_web_zip"],
        caption=escape_markdown_minimal(
            "🌐 Save Web to ZIP\\n\\n"
            "Kirim URL website yang ingin disimpan sebagai ZIP:\\n\\n"
            "Contoh: https://example.com"
        ),
        reply_markup=reply_markup
    )

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
        
    user = update.message.from_user
    user_info = (
        f"🆔 Informasi ID Telegram Anda\\n\\n"
        f"ID Pengguna: <code>{{user.id}}</code>\\n"
        f"Nama: {{user.first_name or ''}} {{user.last_name or ''}}\\n"
        f"Username: @{{user.username or 'Tidak ada'}}\\n"
        f"Bahasa: {{user.language_code or 'Tidak diketahui'}}\\n\\n"
    )
    
    keyboard = [
        [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["cek_id"],
        caption=user_info,
        reply_markup=reply_markup
    )

async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in admin_users:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    try:
        total_users = len(user_sessions)
        active_cooldowns = len(user_cooldown)
        active_states = len(user_states)
        
        current_time = time.time()
        active_24h = sum(1 for session in user_sessions.values() 
                        if isinstance(session, dict) and current_time - session.get('timestamp', 0) < 86400)
        
        stats_text = (
            "📊 Statistik Bot\\n\\n"
            f"👥 Total Pengguna: {{total_users}}\\n"
            f"🟢 Aktif 24 jam: {{active_24h}}\\n"
            f"⏰ Cooldown Aktif: {{active_cooldowns}}\\n"
            f"🔄 States Aktif: {{active_states}}\\n"
            f"📅 Server Time: {{time.strftime('%Y-%m-%d %H:%M:%S')}}\\n\\n"
            f"🤖 Bot Status: 🟢 Online"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats_refresh")],
            [InlineKeyboardButton("📋 Menu Admin", callback_data="admin_menu")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_photo(
            photo=CATBOX_IMAGES["admin_menu"],
            caption=stats_text,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logging.error(f"Error in admin stats: {{e}}")
        await update.message.reply_text("❌ Gagal mengambil statistik.")

# ==================== MEDIA BROADCAST HANDLER ====================

async def handle_media_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    if user_id not in admin_users:
        return
        
    user_state = get_user_state(user_id)
    action = user_state.get("action", "")
    
    if action in ["waiting_broadcast_photo", "waiting_broadcast_video"]:
        broadcast_type = action.replace("waiting_broadcast_", "")
        await process_broadcast(update, context, broadcast_type)
        clear_user_state(user_id)

# ==================== ERROR HANDLER YANG DIPERBAIKI ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling an update: {{context.error}}")
    
    try:
        if update and update.effective_message:
            keyboard = [
                [InlineKeyboardButton("📋 Menu Utama", callback_data="main_menu"),
                 InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.effective_message.reply_text(
                "❌ Terjadi error!\\nSilakan coba lagi atau gunakan menu utama.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logging.error(f"Error in error handler: {{e}}")

# ==================== COMMAND /encrypt DAN /decrypt ====================

async def encrypt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /encrypt"""
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
        
    user_sessions[user_id] = {{
        "verified": True,
        "timestamp": time.time()
    }}
    
    keyboard = [
        [InlineKeyboardButton("🔒 Encrypt V1", callback_data="encrypt_html_v1"),
         InlineKeyboardButton("🔐 Encrypt V2", callback_data="encrypt_html_v2")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = escape_markdown_minimal(
        "📁 Pilih Metode Encrypt HTML\\n\\n"
        "Versi 1:\\n"
        "• Menggunakan decodeURIComponent\\n"
        "• Kompatibel dengan semua browser\\n"
        "• Variabel html biasa\\n"
        "• Ukuran file lebih kecil\\n\\n"
        "Versi 2:\\n"
        "• Menggunakan unescape + document.write\\n"
        "• Teknik encoding lebih kompleks\\n"
        "• Super Hard enchtml\\n\\n"
        "Pilih metode encrypt yang diinginkan:"
    )
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["encrypt_menu"],
        caption=caption,
        reply_markup=reply_markup
    )

async def decrypt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /decrypt"""
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
        
    user_sessions[user_id] = {{
        "verified": True,
        "timestamp": time.time()
    }}
    
    set_user_state(user_id, {{"action": "waiting_for_html_decrypt"}})
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu"),
         InlineKeyboardButton("📢 Channel", url="https://t.me/baguscpanel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_photo(
        photo=CATBOX_IMAGES["decrypt_html"],
        caption=escape_markdown_minimal(
            "🔓 Decrypt HTML\\n\\n"
            "Silakan kirim file HTML terencrypt yang ingin didecrypt.\\n\\n"
            "Format yang didukung:\\n"
            "• File HTML yang telah diencrypt dengan metode V1/V2\\n"
            "• File dengan kode JavaScript encrypted\\n"
            "• File dengan format percent-encoding"
        ),
        reply_markup=reply_markup
    )

# ==================== COMMAND /deploy UNTUK MENAMPILKAN DEPLOY MENU ====================

async def deploy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /deploy - menampilkan menu deploy options"""
    user_id = update.message.from_user.id
    
    # Periksa akses user
    if not await check_user_access(user_id, context):
        await send_join_required_message(update, context)
        return
        
    user_sessions[user_id] = {{
        "verified": True,
        "timestamp": time.time()
    }}
    
    await deploy_options_handler(update, context)

# ==================== MAIN FUNCTION ====================

def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status_command_handler))
    application.add_handler(CommandHandler("deploy", deploy_command))  # Diperbaiki
    application.add_handler(CommandHandler("web2zip", web2zip_command))
    application.add_handler(CommandHandler("cekid", cekid_command))
    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(CommandHandler("adminstats", admin_stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    
    # TAMBAHAN: Command /encrypt dan /decrypt
    application.add_handler(CommandHandler("encrypt", encrypt_command))
    application.add_handler(CommandHandler("decrypt", decrypt_command))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Document handler untuk fitur lain
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handler untuk broadcast media - TAMBAHAN
    application.add_handler(MessageHandler(filters.PHOTO, handle_media_broadcast))
    application.add_handler(MessageHandler(filters.VIDEO, handle_media_broadcast))

    # Error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    print("Bot Active - Application running...")
    application.run_polling()

if __name__ == '__main__':
    main()
'''
    
    with open("telegram_bot.py", "w", encoding="utf-8") as f:
        f.write(bot_code)
    
    return "telegram_bot.py"

def run_bot(token):
    """Jalankan bot dengan token yang diberikan"""
    global bot_process, bot_status, current_token
    
    try:
        # Buat file bot dengan token yang baru
        bot_file = create_bot_file(token)
        current_token = token
        
        # Jalankan bot sebagai subprocess
        bot_process = subprocess.Popen(
            [sys.executable, bot_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        bot_status = "running"
        logger.info(f"Bot started with token: {token}")
        return True
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        bot_status = "error"
        return False

def stop_bot():
    """Hentikan bot"""
    global bot_process, bot_status
    
    try:
        if bot_process:
            bot_process.terminate()
            bot_process.wait(timeout=10)
            bot_process = None
            bot_status = "stopped"
            logger.info("Bot stopped successfully")
            return True
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        try:
            if bot_process:
                bot_process.kill()
                bot_process = None
                bot_status = "stopped"
        except:
            pass
        return False

def get_bot_status():
    """Dapatkan status bot"""
    global bot_process, bot_status
    
    if bot_process and bot_process.poll() is None:
        return "running"
    else:
        return "stopped"

@app.route('/')
def index():
    """Halaman utama"""
    status = get_bot_status()
    return render_template('index.html', 
                         status=status, 
                         current_token=current_token,
                         bot_status=bot_status)

@app.route('/install_packages', methods=['POST'])
def install_packages_route():
    """Install required packages"""
    try:
        result = install_requirements()
        if result:
            return jsonify({'success': True, 'message': 'Package berhasil diinstall!'})
        else:
            return jsonify({'success': False, 'message': 'Gagal menginstall package'})
    except Exception as e:
        logger.error(f"Error installing packages: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/start_bot', methods=['POST'])
def start_bot_route():
    """Start bot dengan token baru"""
    try:
        token = request.form.get('token', '').strip()
        
        if not token:
            return jsonify({'success': False, 'message': 'Token tidak boleh kosong'})
        
        # Validasi format token (contoh: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ)
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            return jsonify({'success': False, 'message': 'Format token tidak valid'})
        
        # Hentikan bot jika sedang berjalan
        if get_bot_status() == "running":
            stop_bot()
            time.sleep(2)
        
        # Jalankan bot dengan token baru
        success = run_bot(token)
        
        if success:
            return jsonify({'success': True, 'message': 'Bot berhasil dijalankan!'})
        else:
            return jsonify({'success': False, 'message': 'Gagal menjalankan bot'})
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/stop_bot', methods=['POST'])
def stop_bot_route():
    """Stop bot"""
    try:
        success = stop_bot()
        if success:
            return jsonify({'success': True, 'message': 'Bot berhasil dihentikan!'})
        else:
            return jsonify({'success': False, 'message': 'Gagal menghentikan bot'})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/status')
def status_route():
    """Dapatkan status bot"""
    status = get_bot_status()
    return jsonify({
        'status': status,
        'current_token': current_token if current_token else 'Belum diatur'
    })

@app.route('/download_bot')
def download_bot():
    """Download file bot yang sudah dibuat"""
    try:
        if not current_token:
            return jsonify({'success': False, 'message': 'Belum ada token yang diatur'})
        
        # Buat file bot
        bot_file = create_bot_file(current_token)
        
        # Kirim file sebagai download
        return send_file(
            bot_file,
            as_attachment=True,
            download_name='telegram_bot.py',
            mimetype='text/x-python'
        )
        
    except Exception as e:
        logger.error(f"Error downloading bot: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

if __name__ == '__main__':
    # Buat direktori templates jika belum ada
    os.makedirs('templates', exist_ok=True)
    
    # Jalankan aplikasi Flask
    print("Website Telegram Bot Manager berjalan di http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)