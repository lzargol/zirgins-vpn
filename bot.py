import os
import sys
import asyncio
import logging
import psutil
import subprocess
import re
import sqlite3
import json
import base64
import zlib
import time
import hashlib
import urllib.request
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramBadRequest

load_dotenv('/opt/vps-bot/.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 694466008))
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID', ADMIN_ID))

if not BOT_TOKEN:
    sys.exit("Error: BOT_TOKEN is missing in .env")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class RenameDeviceState(StatesGroup):
    waiting_for_main_name = State()
    waiting_for_extra_name = State()
    waiting_for_new_name = State()

class AddDeviceState(StatesGroup):
    waiting_for_name = State()


DB_PATH = '/opt/vps-bot/users.db'
HYSTERIA_LINK = "hysteria2://cbe005fdda405a301d5d972d4442dbb3@jzargo.com:50329/?sni=jzargo.com&insecure=0#ZirginsVPN"
PSK2 = "8MC1TGqUTKEEG2ZgG7fgRhDh/N/REedGiWAc604JGEo="
PSK1 = "GP8NhsjeJCoL2kZje/c5f1dRurdUmILkLRmzbpoC9sA="
ADMIN_HYSTERIA_PASS = "cbe005fdda405a301d5d972d4442dbb3"

# Download Links
URL_IOS_KARING = "https://apps.apple.com/app/karing/id6472431552"
URL_IOS_V2BOX = "https://apps.apple.com/app/v2box-v2ray-client/id1644129233"
URL_IOS_STREISAND = "https://apps.apple.com/app/streisand/id6450534064"
URL_IOS_HAPP = "https://apps.apple.com/app/happ-proxy-utility/id6504287913"
URL_IOS_AMNEZIA = "https://apps.apple.com/app/amneziavpn/id1600299950"
URL_ANDROID_ZIRGINS_VPN = "https://github.com/lzargol/zirgins-vpn/releases/download/v1.0.0/ZirginsVPN.apk"
URL_ANDROID_AMNEZIA_GP = "https://play.google.com/store/apps/details?id=org.amnezia.vpn"
URL_ANDROID_NEKOBOX_GH = "https://github.com/MatsuriDayo/NekoBoxForAndroid/releases/latest"
URL_ANDROID_V2RAYNG_GH = "https://github.com/2dust/v2rayNG/releases/latest"
URL_PC_CLASH_PARTY_GH = "https://github.com/mihomo-party-org/clash-party/releases/latest"
URL_PC_AMNEZIA_GH = "https://amnezia.org"
URL_PC_AMNEZIA_OFFICIAL = "https://amnezia.org"
MTPROTO_LINK = "tg://proxy?server=178.17.52.67&port=443&secret=7sX6yNvZ9Z0zX6yNvZ9Z0w=="



_apk_cache = {}
def get_latest_apk_url(repo: str, default_url: str) -> str:
    now = time.time()
    cached = _apk_cache.get(repo)
    if cached and (now - cached['ts']) < 43200:  # 12-hour cache
        return cached['url']

    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest", headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=4).read().decode('utf-8'))
        for a in data.get('assets', []):
            url = a.get('browser_download_url', '')
            if url.endswith('.apk') and ('arm64' in url or 'v8a' in url):
                _apk_cache[repo] = {'url': url, 'ts': now}
                return url
    except Exception as _e:
        logging.error(f"Failed to fetch latest APK for {repo}: {_e}")
    return default_url



URL_PC_CLASH_PARTY_GH = "https://github.com/mihomo-party-org/clash-party/releases/latest"

# In-memory support state tracking
user_support_state = {}
admin_reply_state = {}

def encode_amnezia_vpn_file(priv_key: str, pub_key: str, client_ip: str) -> str:
    raw_config = (
        f'[Interface]\n'
        f'Address = {client_ip}/32\n'
        f'DNS = 1.1.1.1, 1.0.0.1\n'
        f'MTU = 1280\n'
        f'PrivateKey = {priv_key}\n'
        f'Jc = 4\n'
        f'Jmin = 10\n'
        f'Jmax = 50\n'
        f'S1 = 102\n'
        f'S2 = 69\n'
        f'S3 = 38\n'
        f'S4 = 0\n'
        f'H1 = 119470833-310942355\n'
        f'H2 = 1613015718-1817974309\n'
        f'H3 = 1838481383-1854835765\n'
        f'H4 = 1897799796-1956106855\n'
        f'I1 = <b 0x084481800001000300000000077469636b65747306776964676574096b696e6f706f69736b0272750000010001c00c0005000100000039001806776964676574077469636b6574730679616e646578c025c0390005000100000039002b1765787465726e616c2d7469636b6574732d776964676574066166697368610679616e646578036e657400c05d000100010000001c000457fafe25>\n'
        f'I2 = \nI3 = \nI4 = \nI5 = \n\n'
        f'[Peer]\n'
        f'PublicKey = L42Mxgr3+Ss7a65QPCsaW5x620KKV4qD8O19HMRgRTI=\n'
        f'PresharedKey = {PSK2}\n'
        f'AllowedIPs = 0.0.0.0/0, ::/0\n'
        f'Endpoint = 178.17.52.67:48220\n'
        f'PersistentKeepalive = 25\n'
    )
    
    last_config_dict = {
        'H1': '119470833-310942355',
        'H2': '1613015718-1817974309',
        'H3': '1838481383-1854835765',
        'H4': '1897799796-1956106855',
        'I1': '<b 0x084481800001000300000000077469636b65747306776964676574096b696e6f706f69736b0272750000010001c00c0005000100000039001806776964676574077469636b6574730679616e646578c025c0390005000100000039002b1765787465726e616c2d7469636b6574732d776964676574066166697368610679616e646578036e657400c05d000100010000001c000457fafe25>',
        'Jc': '4',
        'Jmax': '50',
        'Jmin': '10',
        'S1': '102',
        'S2': '69',
        'S3': '38',
        'S4': '0',
        'allowed_ips': ['0.0.0.0/0', '::/0'],
        'clientId': pub_key,
        'client_ip': client_ip,
        'client_priv_key': priv_key,
        'client_pub_key': pub_key,
        'config': raw_config,
        'hostName': '178.17.52.67',
        'mtu': '1280',
        'persistent_keep_alive': '25',
        'port': 48220,
        'psk_key': PSK2,
        'server_pub_key': 'L42Mxgr3+Ss7a65QPCsaW5x620KKV4qD8O19HMRgRTI='
    }
    
    payload_dict = {
        'containers': [
            {
                'awg': {
                    'H1': '119470833-310942355',
                    'H2': '1613015718-1817974309',
                    'H3': '1838481383-1854835765',
                    'H4': '1897799796-1956106855',
                    'I1': '<b 0x084481800001000300000000077469636b65747306776964676574096b696e6f706f69736b0272750000010001c00c0005000100000039001806776964676574077469636b6574730679616e646578c025c0390005000100000039002b1765787465726e616c2d7469636b6574732d776964676574066166697368610679616e646578036e657400c05d000100010000001c000457fafe25>',
                    'I2': '',
                    'I3': '',
                    'I4': '',
                    'I5': '',
                    'Jc': '4',
                    'Jmax': '50',
                    'Jmin': '10',
                    'S1': '102',
                    'S2': '69',
                    'S3': '38',
                    'S4': '0',
                    'last_config': json.dumps(last_config_dict),
                    'port': '48220',
                    'protocol_version': '2',
                    'subnet_address': '10.8.1.0',
                    'transport_proto': 'udp'
                },
                'container': 'amnezia-awg2'
            }
        ],
        'defaultContainer': 'amnezia-awg2',
        'description': 'ZirginsVPN',
        'dns1': '1.1.1.1',
        'dns2': '1.0.0.1',
        'hostName': '178.17.52.67'
    }

    json_bytes = json.dumps(payload_dict, separators=(',', ':')).encode('utf-8')
    compressed = zlib.compress(json_bytes)
    header = len(json_bytes).to_bytes(4, 'big')
    full = header + compressed
    b64 = base64.b64encode(full).decode('utf-8').replace('+', '-').replace('/', '_').rstrip('=')
    return f'vpn://{b64}'


def format_relative_time(ts: int) -> str:
    if not ts or ts <= 0:
        return "Не подключался"
    now = int(time.time())
    diff = max(0, now - ts)
    if diff < 60:
        return "Только что"
    elif diff < 3600:
        mins = diff // 60
        return f"{mins} мин назад"
    elif diff < 86400:
        hours = diff // 3600
        mins = (diff % 3600) // 60
        return f"{hours} ч {mins} мин назад"
    else:
        days = diff // 86400
        hours = (diff % 86400) // 3600
        return f"{days} дн {hours} ч назад"

def format_bytes(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b / 1024:.1f} KB"
    elif b < 1024**3:
        return f"{b / (1024**2):.1f} MB"
    else:
        return f"{b / (1024**3):.2f} GB"

def get_wireguard_user_metrics() -> dict:
    """Combines WireGuard metrics AND sing-box clash_api metrics cleanly per internal IP.
       Guarantees strictly monotonic traffic values and persistent last_seen_ts.
    """
    global _max_user_traffic
    metrics = {}
    endpoint_to_internal = {}
    db_last_seen = {}
    amip_to_uid = {}
    
    try:
        conn_db = sqlite3.connect(DB_PATH, timeout=20.0)
        cur_db = conn_db.cursor()
        cur_db.execute("SELECT user_id, amnezia_ip, last_seen_ts FROM users WHERE amnezia_ip IS NOT NULL")
        for r in cur_db.fetchall():
            clean_ip = r[1].replace("/32", "").strip()
            amip_to_uid[clean_ip] = r[0]
            db_last_seen[clean_ip] = r[2] or 0
        conn_db.close()
    except Exception as _db_e:
        logging.error(f"Failed to load db_last_seen: {_db_e}")

    # 1. WireGuard Metrics across BOTH containers (48220 & 47400)
    out_wg2 = subprocess.getoutput("docker exec amnezia-awg2 awg show awg0 dump")
    out_wg1 = subprocess.getoutput("docker exec amnezia-awg wg show wg0 dump")

    for out_wg in [out_wg2, out_wg1]:
        for line in out_wg.splitlines():
            parts = line.split('\t')
            if len(parts) >= 8:
                pub_key = parts[0]
                endpoint = parts[2]
                allowed_ip = parts[3]
                latest_hs = int(parts[4]) if parts[4].isdigit() else 0
                rx = int(parts[5]) if parts[5].isdigit() else 0
                tx = int(parts[6]) if parts[6].isdigit() else 0
                
                ip_clean = allowed_ip.replace("/32", "").strip()
                endpoint_ip = endpoint.rsplit(":", 1)[0] if ":" in endpoint else endpoint
                if endpoint_ip and endpoint_ip != "(none)":
                    endpoint_to_internal[endpoint_ip] = ip_clean

                is_act = (time.time() - latest_hs) < 90 if latest_hs > 0 else False
                tot = rx + tx

                if ip_clean not in metrics:
                    metrics[ip_clean] = {
                        "pub_key": pub_key,
                        "endpoint": endpoint_ip,
                        "latest_handshake": max(latest_hs, db_last_seen.get(ip_clean, 0)),
                        "rx_bytes": rx,
                        "tx_bytes": tx,
                        "total_bytes": tot,
                        "is_active": is_act
                    }
                else:
                    metrics[ip_clean]["rx_bytes"] += rx
                    metrics[ip_clean]["tx_bytes"] += tx
                    metrics[ip_clean]["total_bytes"] += tot
                    if is_act:
                        metrics[ip_clean]["is_active"] = True
                    if latest_hs > metrics[ip_clean].get("latest_handshake", 0):
                        metrics[ip_clean]["latest_handshake"] = latest_hs
                    if endpoint_ip and endpoint_ip != "(none)":
                        metrics[ip_clean]["endpoint"] = endpoint_ip

    # 2. Map public IPs to user amnezia_ip & check Hysteria recent activity
    ip_to_amip = {}
    uid_last_active = {}
    try:
        log_ip_to_uid, uid_last_active = parse_singbox_log_user_mappings()
        for pub_ip, u_id in log_ip_to_uid.items():
            for am_ip, u_id_db in amip_to_uid.items():
                if u_id_db == u_id:
                    ip_to_amip[pub_ip] = am_ip

        # Apply Hysteria recent activity (3 min window) to metrics & update DB last_seen_ts
        now_ts = int(time.time())
        conn_up = sqlite3.connect(DB_PATH, timeout=20.0)
        cur_up = conn_up.cursor()

        for u_id, last_ts in uid_last_active.items():
            if last_ts > 0:
                cur_up.execute("UPDATE users SET last_seen_ts = ? WHERE user_id = ? AND ? > last_seen_ts", (last_ts, u_id, last_ts))
            for am_ip, u_id_db in amip_to_uid.items():
                if u_id_db == u_id:
                    is_active_h2 = (now_ts - last_ts) < 90 if last_ts > 0 else False
                    effective_hs = max(last_ts, db_last_seen.get(am_ip, 0))
                    if am_ip not in metrics:
                        metrics[am_ip] = {
                            "pub_key": "(Hysteria2)",
                            "endpoint": "(none)",
                            "latest_handshake": effective_hs,
                            "rx_bytes": 0,
                            "tx_bytes": 0,
                            "total_bytes": 0,
                            "is_active": is_active_h2
                        }
                    else:
                        if is_active_h2:
                            metrics[am_ip]["is_active"] = True
                        if effective_hs > metrics[am_ip].get("latest_handshake", 0):
                            metrics[am_ip]["latest_handshake"] = effective_hs
        conn_up.commit()
        conn_up.close()
    except Exception as _e:
        logging.error(f"ip_to_amip error: {_e}")

    # 3. Sing-box Hysteria 2 / Clash API Metrics (Port 9090)
    try:
        sb_res = subprocess.getoutput("curl -s http://127.0.0.1:9090/connections")
        if sb_res and sb_res.startswith("{"):
            sb_data = json.loads(sb_res)
            now_ts = int(time.time())

            for conn in sb_data.get("connections", []):
                meta = conn.get("metadata", {})
                src_ip = meta.get("sourceIP", "").strip()
                dl = conn.get("download", 0)
                ul = conn.get("upload", 0)
                total = dl + ul
                if src_ip:
                    target_key = ip_to_amip.get(src_ip) or endpoint_to_internal.get(src_ip) or (src_ip if src_ip in metrics else None)
                    if target_key:
                        if target_key not in metrics:
                            metrics[target_key] = {
                                "pub_key": "(Hysteria2)",
                                "endpoint": src_ip,
                                "latest_handshake": now_ts,
                                "rx_bytes": dl,
                                "tx_bytes": ul,
                                "total_bytes": total,
                                "is_active": True
                            }
                        else:
                            metrics[target_key]["total_bytes"] += total
                            metrics[target_key]["rx_bytes"] += dl
                            metrics[target_key]["tx_bytes"] += ul
                            metrics[target_key]["is_active"] = True
                            metrics[target_key]["latest_handshake"] = now_ts
                            if not metrics[target_key].get("endpoint") or metrics[target_key]["endpoint"] == "(none)":
                                metrics[target_key]["endpoint"] = src_ip

                        u_id_target = amip_to_uid.get(target_key)
                        if u_id_target:
                            conn_up = sqlite3.connect(DB_PATH, timeout=20.0)
                            conn_up.execute("UPDATE users SET last_seen_ts = ? WHERE user_id = ? AND ? > last_seen_ts", (now_ts, u_id_target, now_ts))
                            conn_up.commit()
                            conn_up.close()
    except Exception as e:
        logging.error(f"Failed to fetch sing-box clash_api metrics: {e}")

    # 4. Add accumulated clash traffic from DB
    try:
        conn_db = sqlite3.connect(DB_PATH, timeout=20.0)
        cur_db = conn_db.cursor()
        cur_db.execute("SELECT user_id, amnezia_ip, clash_traffic_bytes, last_seen_ts FROM users WHERE clash_traffic_bytes > 0 OR last_seen_ts > 0")
        for uid, am_ip, clash_bytes, db_ts in cur_db.fetchall():
            ip_key = (am_ip or "").replace("/32", "").strip()
            if ip_key:
                if ip_key not in metrics:
                    metrics[ip_key] = {
                        "pub_key": "(Hysteria2 DB)",
                        "endpoint": "(none)",
                        "latest_handshake": db_ts or 0,
                        "rx_bytes": clash_bytes,
                        "tx_bytes": 0,
                        "total_bytes": clash_bytes,
                        "is_active": False
                    }
                else:
                    metrics[ip_key]["total_bytes"] += clash_bytes
                    if (db_ts or 0) > metrics[ip_key].get("latest_handshake", 0):
                        metrics[ip_key]["latest_handshake"] = db_ts
        conn_db.close()
    except Exception as _db_e:
        logging.error(f"Failed to load clash DB traffic: {_db_e}")

    # 5. Enforce STRICT MONOTONIC GUARANTEE per IP / User (Traffic NEVER jumps down)
    for ip_key, m_data in metrics.items():
        curr_total = m_data.get("total_bytes", 0)
        highest_prev = _max_user_traffic.get(ip_key, 0)
        if curr_total < highest_prev:
            m_data["total_bytes"] = highest_prev
        else:
            _max_user_traffic[ip_key] = curr_total

    return metrics


def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            status TEXT DEFAULT 'pending',
            amnezia_privkey TEXT,
            amnezia_pubkey TEXT,
            amnezia_ip TEXT,
            hysteria_pass TEXT,
            is_legacy INTEGER DEFAULT 0,
            family_head_id INTEGER DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        cur.execute("ALTER TABLE users ADD COLUMN hysteria_pass TEXT")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_legacy INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN family_head_id INTEGER DEFAULT NULL")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN clash_traffic_bytes INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN main_device_name TEXT DEFAULT 'Основное устройство #1'")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE users ADD COLUMN primary_platform TEXT DEFAULT ''")
    except Exception:
        pass
    cur.execute("UPDATE users SET is_legacy = 1 WHERE is_legacy IS NULL OR is_legacy = 0")
    conn.commit()
    conn.close()

init_db()

@dp.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: Message, state: FSMContext, command: CommandObject = None):
    try:
        await state.clear()
    except Exception:
        pass
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Пользователь"
    username = message.from_user.username or ""

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    if not row:
        h_pass = ADMIN_HYSTERIA_PASS if user_id == ADMIN_ID else hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()
        cur.execute("INSERT INTO users (user_id, first_name, username, status, hysteria_pass) VALUES (?, ?, ?, 'approved', ?)",
                    (user_id, first_name, username, h_pass))
        conn.commit()
    conn.close()

    text = (
        f"👋 <b>Добро пожаловать в ZirginsVPN, {first_name}!</b>\n\n"
        "⚡ <b>Высокоскоростной и защищенный доступ в интернет</b>\n\n"
        "Выберите раздел из меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_keyboard(user_id), parse_mode="HTML")


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_user_status(user_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT status, amnezia_privkey, amnezia_pubkey, amnezia_ip, hysteria_pass, is_legacy, family_head_id FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_family_members(head_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, username, status FROM users WHERE family_head_id = ?", (head_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_main_keyboard(user_id: int):
    admin_mode = is_admin(user_id)
    kb = [
        [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
        [
            InlineKeyboardButton(text="🤖 Android", callback_data="menu_android"),
            InlineKeyboardButton(text="🍏 iPhone / iOS", callback_data="menu_ios"),
            InlineKeyboardButton(text="💻 ПК (Clash Party)", callback_data="info_pc")
        ],
        [
            InlineKeyboardButton(text="👨‍👩‍👧‍👦 Семейная подписка", callback_data="menu_family"),
            InlineKeyboardButton(text="⚡ Telegram Прокси", callback_data="info_mtproto")
        ],
        [
            InlineKeyboardButton(text="🤝 Поделиться ботом с друзьями", switch_inline_query="🔥 Попробуй быстрый и защищенный ZirginsVPN с обходом блокировок РКН!"),
            InlineKeyboardButton(text="⚙️ Поддержка / FAQ", callback_data="ask_support")
        ]
    ]
    if admin_mode:
        kb.append([InlineKeyboardButton(text="👑 Админ Панель", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_user_devices(user_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT device_id, device_name, amnezia_ip, amnezia_pubkey, amnezia_privkey, device_type FROM user_devices WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_main_device_name(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT main_device_name FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else "Основное устройство #1"

def set_user_main_device_name(user_id: int, name: str):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE users SET main_device_name = ? WHERE user_id = ?", (name, user_id))
    conn.commit()
    conn.close()

def get_user_primary_platform(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT primary_platform FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row and row[0] else ""

def set_user_primary_platform(user_id: int, platform: str):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE users SET primary_platform = ? WHERE user_id = ?", (platform, user_id))
    conn.commit()
    conn.close()

def get_family_members(head_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, username, status FROM users WHERE family_head_id = ?", (head_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def name_defined(name: str) -> bool:
    return name in globals()




def get_user_hysteria_pass(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT hysteria_pass FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]
    return ADMIN_HYSTERIA_PASS if user_id == ADMIN_ID else hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()

def delete_user_device(device_id: int, user_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("DELETE FROM user_devices WHERE device_id = ? AND user_id = ?", (device_id, user_id))
    conn.commit()
    conn.close()

def update_device_type(device_id: int, user_id: int, dev_type: str):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE user_devices SET device_type = ? WHERE device_id = ? AND user_id = ?", (dev_type, device_id, user_id))
    conn.commit()
    conn.close()

def rename_user_device(device_id: int, user_id: int, new_name: str):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE user_devices SET device_name = ? WHERE device_id = ? AND user_id = ?", (new_name, device_id, user_id))
    conn.commit()
    conn.close()

def get_user_hysteria_link(user_id: int) -> str:
    h_pass = get_user_hysteria_pass(user_id)
    return f"hysteria2://{h_pass}@jzargo.com:50329/?sni=jzargo.com&insecure=0#ZirginsVPN"




async def safe_reply(call, text, reply_markup=None, parse_mode="HTML", disable_web_page_preview=False):
    """Edit existing message or delete+send new. Prevents cloning and freezing."""
    kw = {"parse_mode": parse_mode}
    if reply_markup:
        kw["reply_markup"] = reply_markup
    if disable_web_page_preview:
        kw["disable_web_page_preview"] = True
    try:
        await call.message.edit_text(text, **kw)
    except Exception:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(text, **kw)

@dp.callback_query(F.data == "send_sub_link_pc")
async def cb_send_sub_link_pc(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    h_pass = get_user_hysteria_pass(user_id)
    sub_url = f"http://178.17.52.67/sub/{h_pass}"

    text = (
        "<b>💻 Персональная ссылка авто-подписки для ПК (Clash Party):</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        "<b>📥 1. Скачайте программу для ПК:</b>\n"
        f"• <a href='{URL_PC_CLASH_PARTY_GH}'>Скачать Clash Party для ПК (GitHub)</a>\n\n"
        "<b>📱 2. Инструкция по установке:</b>\n"
        "• Нажмите на ссылку выше для копирования.\n"
        "• В <b>Clash Party</b> перейдите в раздел <b>Profiles</b> ➔ нажмите <b>Import from Clipboard</b>.\n\n"
        "<b>⚙️ Режимы работы (System Proxy vs TUN):</b>\n"
        "• <b>System Proxy (Системный прокси):</b> Работает для браузеров и основных программ.\n"
        "• <b>TUN Mode (Туннельный режим — Рекомендуется 🛡):</b> Направляет весь трафик ПК (игры, Discord, приложения, консоль) на сетевом уровне.\n\n"
        "<b>🌐 Режимы маршрутизации (Rule / Global / Direct):</b>\n"
        "• 🔀 <b>Rule (Правило — Рекомендуется ⚡):</b> Умный обход РКН! Заблокированные сайты идут через VPN, а Сбербанк, Госуслуги и росс. сервисы напрямую.\n"
        "• 🌍 <b>Global (Глобальный):</b> Пускает 100% трафика компьютера через VPN.\n"
        "• 🚫 <b>Direct (Прямой):</b> Отключает VPN, весь трафик идет напрямую."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к ПК", callback_data="info_pc")],
        [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)


@dp.callback_query(F.data == "send_sub_link_android")
async def cb_send_sub_link_android(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    h_pass = get_user_hysteria_pass(user_id)
    sub_url = f"http://178.17.52.67/sub/{h_pass}?flag=singbox"

    text = (
        "<b>🤖 Персональная ссылка авто-подписки для Android (NekoBox / v2rayNG):</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        "<b>📥 1. Скачайте приложение для Android:</b>\n"
        f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>Скачать NekoBox / v2rayNG для Android (GitHub)</a>\n"
        f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>Скачать v2rayNG для Android (GitHub)</a>\n\n"
        "<b>📱 2. Инструкция по установке (занимает 1 минуту):</b>\n"
        "• Нажмите на ссылку в рамке выше, чтобы скопировать её.\n"
        "• В <b>NekoBox / v2rayNG</b>: на главном экране нажмите <b>«+»</b> (вверху) ➔ <b>Subscription</b> ➔ вставьте ссылку ➔ <b>Обновить</b>.\n"
        ""
        "✨ <i>В шапке экрана появится виджет потраченного трафика и статус подписки!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к Android", callback_data="menu_android")],
        [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)


@dp.callback_query(F.data == "send_sub_link_ios")
async def cb_send_sub_link_ios(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    h_pass = get_user_hysteria_pass(user_id)
    sub_url = f"http://178.17.52.67/sub/{h_pass}"

    text = (
        "<b>🍏 Персональная ссылка авто-подписки для iPhone / iPad (iOS):</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        "<b>📥 1. Скачайте приложение из App Store:</b>\n"
        f"• <a href='{URL_IOS_KARING}'>1. Karing (Российский App Store)</a>\n"
        f"• <a href='{URL_IOS_STREISAND}'>2. Streisand (Иностранный App Store)</a>\n"
        f"• <a href='{URL_IOS_HAPP}'>3. Happ Proxy (Иностранный App Store)</a>\n"
        
        "<b>📱 2. Инструкция по установке (занимает 1 минуту):</b>\n"
        "• Нажмите на ссылку в рамке выше, чтобы скопировать её.\n"
        "• В <b>Karing</b>: откройте приложение ➔ вкладка <b>Profile</b> ➔ нажмите <b>«+»</b> ➔ <b>From URL</b> ➔ вставьте ссылку.\n"
        "• В <b>Streisand / Happ</b>: нажмите <b>«+» ➔ Import from Clipboard</b> (Импорт из буфера обмена).\n\n"
        "✨ <i>Сбербанк и Госуслуги работают напрямую, а заблокированные сайты летают через VPN!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к iOS", callback_data="menu_ios")],
        [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "send_sub_link")
async def cb_send_sub_link(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    h_pass = get_user_hysteria_pass(user_id)
    sub_url = f"http://178.17.52.67/sub/{h_pass}"

    text = (
        "<b>🔗 Ваша персональная ссылка авто-подписки:</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        "<b>🚀 Что это такое и как работает?</b>\n"
        "1. <b>Авто-обновление 24/7:</b> Вставьте эту ссылку 1 раз в <b>Karing, Streisand, NekoBox / v2rayNG, v2rayNG или Clash Party</b> — настройки и блокировки РКН будут обновляться автоматически.\n"
        "2. <b>Виджет трафика:</b> В шапке экрана приложения отобразится потраченный объём трафика и статус активности.\n"
        "3. <b>Умные белые списки:</b> Все сайты РФ (Сбербанк, Госуслуги, Яндекс, ВТБ) работают напрямую без потери скорости.\n\n"
        "<b>📱 Инструкция по добавлению:</b>\n"
        "• Нажмите на ссылку выше для копирования.\n"
        "• В приложении (Karing/NekoBox / v2rayNG/Clash) выберите <b>«Добавить подписку»</b> или <b>«Import from Clipboard»</b>.\n"
        "• Готово! Подключение настроено."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb)

def get_admin_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="adm_users"), InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")],
        [InlineKeyboardButton(text="📬 Обращения", callback_data="adm_tickets"), InlineKeyboardButton(text="🔄 Синхронизация", callback_data="adm_restart_singbox")],
        [InlineKeyboardButton(text="⚙️ Статус служб", callback_data="adm_services"), InlineKeyboardButton(text="🔗 Подключения", callback_data="adm_conn")],
        [InlineKeyboardButton(text="⬅️ Главное Меню", callback_data="main_menu")]
    ])
    return kb

def get_all_users():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, username, status, hysteria_pass, main_device_name FROM users ORDER BY CASE WHEN user_id = ? THEN 0 ELSE 1 END, created_at DESC", (ADMIN_ID,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_user_total_traffic_and_status(user_id: int) -> tuple[int, bool, int]:
    user_info = get_user_status(user_id)
    am_ip = user_info[3] if user_info else ""
    devices = get_user_devices(user_id)
    
    main_ip = (am_ip or "").replace("/32", "").strip()
    all_ips = [main_ip] + [(d[2] or "").replace("/32", "").strip() for d in devices if len(d) >= 3 and d[2]]
    
    wg_metrics = get_wireguard_user_metrics()
    
    total_bytes = 0
    is_active = False
    latest_hs = 0
    
    for ip in all_ips:
        if ip and ip in wg_metrics:
            m = wg_metrics[ip]
            total_bytes += m.get("total_bytes", 0)
            if m.get("is_active"):
                is_active = True
            if m.get("latest_handshake", 0) > latest_hs:
                latest_hs = m.get("latest_handshake", 0)
                
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT clash_traffic_bytes, last_seen_ts FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        db_bytes = row[0] or 0
        db_ts = row[1] or 0
        if db_bytes > total_bytes:
            total_bytes = db_bytes
        if db_ts > latest_hs:
            latest_hs = db_ts
            
    now_ts = int(time.time())
    if (now_ts - latest_hs) < 90 if latest_hs > 0 else False:
        is_active = True
        
    return total_bytes, is_active, latest_hs

def get_server_stats() -> str:
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    users = get_all_users()
    total_users = len(users)
    wg_metrics = get_wireguard_user_metrics()
    active_conn = sum(1 for m in wg_metrics.values() if m.get("is_active"))
    
    text = (
        "<b>📊 Статистика сервера VPS & ZirginsVPN:</b>\n\n"
        f"💻 <b>Загрузка ЦП (CPU):</b> {cpu}%\n"
        f"🧠 <b>Оперативная память (RAM):</b> {mem.percent}% ({format_bytes(mem.used)} / {format_bytes(mem.total)})\n"
        f"💾 <b>Дисковое пространство:</b> {disk.percent}% ({format_bytes(disk.used)} / {format_bytes(disk.total)})\n\n"
        f"👥 <b>Зарегистрировано пользователей:</b> {total_users}\n"
        f"🟢 <b>Активных подключений VPN:</b> {active_conn}\n"
    )
    return text

def get_service_statuses() -> str:
    sb = "🟢 Работает (Active)" if subprocess.getoutput("systemctl is-active sing-box").strip() == "active" else "🔴 Остановлен"
    bot_st = "🟢 Работает (Active)" if subprocess.getoutput("systemctl is-active vps-bot").strip() == "active" else "🔴 Остановлен"
    awg = "🟢 Работает (Active)" if subprocess.getoutput("docker inspect -f '{{.State.Running}}' amnezia-awg").strip() == "true" else "🔴 Остановлен"
    return f"⚡ <b>sing-box (Hysteria 2):</b> {sb}\n🤖 <b>vps-bot (Telegram Bot):</b> {bot_st}\n🛡 <b>amnezia-awg (WireGuard):</b> {awg}"

def get_active_connections():
    metrics = get_wireguard_user_metrics()
    active_count = sum(1 for m in metrics.values() if m.get("is_active"))
    return active_count

def get_unique_users_info():
    users = get_all_users()
    return len(users)


def ensure_user_amnezia_peer(user_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT amnezia_privkey, amnezia_pubkey, amnezia_ip, hysteria_pass FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    h_pass = ADMIN_HYSTERIA_PASS if user_id == ADMIN_ID else hashlib.md5(f"{user_id}_{time.time()}".encode()).hexdigest()

    if row and row[0] and row[1] and row[2]:
        priv_key, pub_key, client_ip = row[0], row[1], row[2]
        if not row[3]:
            cur.execute("UPDATE users SET hysteria_pass = ? WHERE user_id = ?", (h_pass, user_id))
            conn.commit()
        conn.close()
        cmd2 = f"echo '{PSK2}' > /tmp/psk2.key && docker cp /tmp/psk2.key amnezia-awg2:/tmp/psk2.key && docker exec amnezia-awg2 awg set awg0 peer {pub_key} preshared-key /tmp/psk2.key allowed-ips {client_ip}/32"
        cmd1 = f"echo '{PSK1}' > /tmp/psk1.key && docker cp /tmp/psk1.key amnezia-awg:/tmp/psk1.key && docker exec amnezia-awg wg set wg0 peer {pub_key} preshared-key /tmp/psk1.key allowed-ips {client_ip}/32"
        subprocess.getoutput(cmd2)
        subprocess.getoutput(cmd1)
        return priv_key, pub_key, client_ip
    else:
        priv_key = subprocess.getoutput("docker exec amnezia-awg wg genkey").strip()
        pub_key = subprocess.getoutput(f"echo '{priv_key}' | docker exec -i amnezia-awg wg pubkey").strip()
        
        cur.execute("SELECT amnezia_ip FROM users WHERE amnezia_ip IS NOT NULL")
        used_ips = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT amnezia_ip FROM user_devices WHERE amnezia_ip IS NOT NULL")
        used_ips.update({r[0] for r in cur.fetchall()})

        for last_octet in range(2, 250):
            candidate_ip = f"10.8.0.{last_octet}"
            if candidate_ip not in used_ips:
                client_ip = candidate_ip
                break
        else:
            client_ip = "10.8.0.250"

        cur.execute(
            "UPDATE users SET amnezia_privkey = ?, amnezia_pubkey = ?, amnezia_ip = ?, hysteria_pass = ? WHERE user_id = ?",
            (priv_key, pub_key, client_ip, h_pass, user_id)
        )
        conn.commit()
        conn.close()

        cmd2 = f"echo '{PSK2}' > /tmp/psk2.key && docker cp /tmp/psk2.key amnezia-awg2:/tmp/psk2.key && docker exec amnezia-awg2 awg set awg0 peer {pub_key} preshared-key /tmp/psk2.key allowed-ips {client_ip}/32"
        cmd1 = f"echo '{PSK1}' > /tmp/psk1.key && docker cp /tmp/psk1.key amnezia-awg:/tmp/psk1.key && docker exec amnezia-awg wg set wg0 peer {pub_key} preshared-key /tmp/psk1.key allowed-ips {client_ip}/32"
        subprocess.getoutput(cmd2)
        subprocess.getoutput(cmd1)
        return priv_key, pub_key, client_ip


def create_extra_device_peer(user_id: int, device_name: str, device_type: str = 'android_amnezia'):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()

    priv_key = subprocess.getoutput("docker exec amnezia-awg wg genkey").strip()
    pub_key = subprocess.getoutput(f"echo '{priv_key}' | docker exec -i amnezia-awg wg pubkey").strip()

    cur.execute("SELECT amnezia_ip FROM users WHERE amnezia_ip IS NOT NULL")
    used_ips = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT amnezia_ip FROM user_devices WHERE amnezia_ip IS NOT NULL")
    used_ips.update({r[0] for r in cur.fetchall()})

    client_ip = "10.8.0.250"
    for last_octet in range(2, 250):
        candidate_ip = f"10.8.0.{last_octet}"
        if candidate_ip not in used_ips:
            client_ip = candidate_ip
            break

    cur.execute(
        "INSERT INTO user_devices (user_id, device_name, amnezia_ip, amnezia_pubkey, amnezia_privkey, device_type) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, device_name, client_ip, pub_key, priv_key, device_type)
    )
    conn.commit()
    conn.close()

    cmd2 = f"echo '{PSK2}' > /tmp/psk2.key && docker cp /tmp/psk2.key amnezia-awg2:/tmp/psk2.key && docker exec amnezia-awg2 awg set awg0 peer {pub_key} preshared-key /tmp/psk2.key allowed-ips {client_ip}/32"
    cmd1 = f"echo '{PSK1}' > /tmp/psk1.key && docker cp /tmp/psk1.key amnezia-awg:/tmp/psk1.key && docker exec amnezia-awg wg set wg0 peer {pub_key} preshared-key /tmp/psk1.key allowed-ips {client_ip}/32"
    subprocess.getoutput(cmd2)
    subprocess.getoutput(cmd1)

    return priv_key, pub_key, client_ip

def get_my_devices_text_and_kb(user_id: int):
    devices = get_user_devices(user_id)
    admin_mode = is_admin(user_id)
    main_name = get_user_main_device_name(user_id)

    limit_str = "∞ (Безлимит Администратора)" if admin_mode else f"{len(devices) + 1} из 5 разрешенных мест"

    text = (
        "<b>📱 Ваши созданные устройства:</b>\n\n"
        f"1️⃣ 📱 <b>{main_name}</b> (Основное устройство #1)\n"
    )

    kb_buttons = [
        [
            InlineKeyboardButton(text=f"🛡 Скачать {main_name}.vpn", callback_data="gen_amnezia_file"),
            InlineKeyboardButton(text=f"✏️ Имя №1", callback_data="rename_main_dev")
        ]
    ]

    for idx, row in enumerate(devices, start=2):
        d_id = row[0]
        d_name = row[1]
        d_type = row[5] if len(row) >= 6 and row[5] else 'android_amnezia'

        if d_type in ['ios', 'android_nekobox']:
            icon = "🍏" if d_type == 'ios' else "🔀"
            type_label = "Hysteria 2" if d_type == 'ios' else "NekoBox / v2rayNG"
        elif d_type == 'android_combo':
            icon = "⚡"
            type_label = "Связка + Прокси"
        elif d_type in ['pc', 'pc_amnezia', 'pc_clash']:
            icon = "💻"
            type_label = "ПК Clash" if d_type in ['pc', 'pc_clash'] else "ПК Amnezia"
        else:
            icon = "🤖"
            type_label = "AmneziaVPN"

        text += f"{idx}️⃣ {icon} <b>{d_name}</b> ({type_label})\n"
        kb_buttons.append([
            InlineKeyboardButton(text=f"{icon} {d_name} ({type_label})", callback_data=f"dl_dev_{d_id}")
        ])

    text += f"\n<i>Использовано профилей: {limit_str}.</i>"

    if len(devices) < 4 or admin_mode:
        kb_buttons.append([InlineKeyboardButton(text="➕ Создать ещё устройство (+1)", callback_data="add_extra_device")])

    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")])

    return text, InlineKeyboardMarkup(inline_keyboard=kb_buttons)


@dp.callback_query(F.data == "ask_support")
async def cb_ask_support(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_support_state[call.from_user.id] = True
    text = (
        "<b>💬 Служба техподдержки ZirginsVPN</b>\n\n"
        "Опишите ваш вопрос или возникшую проблему в сообщении ниже.\n"
        "Администратор получит вашу заявку вместе с автоматической технической диагностикой вашего подключения и ответит вам прямо в этот чат!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]])
    await safe_reply(call, text, reply_markup=kb)

@dp.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def handle_user_text_messages(message: Message):
    user_id = message.from_user.id
    
    # Check if admin is currently replying to a user via prompt
    if is_admin(user_id) and user_id in admin_reply_state:
        target_u_id = admin_reply_state.pop(user_id)
        try:
            await bot.send_message(
                target_u_id,
                f"<b>💬 Ответ от техподдержки ZirginsVPN:</b>\n\n{message.text}",
                parse_mode="HTML"
            )
            await message.answer(f"✅ Ваш ответ успешно доставлен пользователю <code>{target_u_id}</code>!", parse_mode="HTML")
        except Exception as e:
            await message.answer(f"❌ Ошибка отправки ответа: {e}", parse_mode="HTML")
        return

    # Check if user is sending a support inquiry
    if user_support_state.get(user_id):
        user_support_state[user_id] = False
        first_name = message.from_user.first_name or "User"
        username = message.from_user.username or "no_tag"
        
        user_info = get_user_status(user_id)
        am_ip = user_info[3] if user_info else "None"
        
        wg_metrics = get_wireguard_user_metrics()
        ip_clean = (am_ip or "").replace("/32", "").strip()
        m = wg_metrics.get(ip_clean, {})
        
        ext_ip = m.get("endpoint", "Не определен")
        is_active = "🟢 В сети" if m.get("is_active") else "⚪ Офлайн"
        traffic_str = format_bytes(m.get("total_bytes", 0))

        # Save ticket in DB
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        cur = conn.cursor()
        cur.execute("INSERT INTO support_tickets (user_id, message_text) VALUES (?, ?)", (user_id, message.text))
        conn.commit()
        conn.close()

        ticket_text = (
            f"<b>📩 Новое обращение в техподдержку!</b>\n\n"
            f"👤 <b>Пользователь:</b> {first_name} (@{username})\n"
            f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
            f"🟢 <b>Статус VPN:</b> {is_active}\n"
            f"🌐 <b>Внешний IP устройства:</b> <code>{ext_ip}</code>\n"
            f"🛡 <b>Выделенный IP туннеля:</b> <code>{am_ip}</code>\n"
            f"💾 <b>Потрачено трафика:</b> {traffic_str}\n\n"
            f"💬 <b>Текст обращения:</b>\n<i>«{message.text}»</i>"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить пользователю", callback_data=f"reply_u_{user_id}")],
            [InlineKeyboardButton(text="ℹ️ Диагностика IP", callback_data=f"diag_u_{user_id}")]
        ])
        
        await message.answer(
                "✅ <b>Ваше обращение принято!</b>\n\n"
                "Администратор рассмотрит его в разделе «📬 Обращения» админ-панели и ответит вам в ближайшее время!",
                reply_markup=get_main_keyboard(user_id),
                parse_mode="HTML"
            )

@dp.callback_query(F.data.startswith("reply_u_"))
async def cb_reply_user(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    admin_reply_state[call.from_user.id] = target_id
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    u_row = cur.fetchone()
    conn.close()

    u_name = u_row[0] if u_row and u_row[0] else "Пользователю"
    u_tag = f"(@{u_row[1]})" if u_row and u_row[1] else ""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"adm_u_{target_id}")]
    ])
    text = (
        f"✍️ <b>Введите ваш ответ пользователю {u_name} {u_tag} (<code>{target_id}</code>):</b>\n\n"
        f"<i>Напишите ваш текст в следующем сообщении, и бот сразу передаст его клиенту!</i>"
    )
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("diag_u_"))
async def cb_diag_user(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    user_info = get_user_status(target_id)
    devices = get_user_devices(target_id)
    
    am_ip = user_info[3] if user_info else "None"
    wg_metrics = get_wireguard_user_metrics()
    ip_clean = (am_ip or "").replace("/32", "").strip()
    m = wg_metrics.get(ip_clean, {})
    
    text = (
        f"<b>🔍 Диагностика подключения пользователя <code>{target_id}</code>:</b>\n\n"
        f"• Status: <code>{user_info[0] if user_info else 'Unknown'}</code>\n"
        f"• Основной IP: <code>{am_ip}</code>\n"
        f"• Внешний IP: <code>{m.get('endpoint', '(none)')}</code>\n"
        f"• Активность: {'🟢 В сети' if m.get('is_active') else '⚪ Офлайн'}\n"
        f"• Всего устройств: {len(devices) + 1}\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад к пользователю", callback_data=f"adm_u_{target_id}")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "rename_main_dev")
async def cb_rename_main_device_prompt(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()
    except Exception:
        pass
    await state.set_state(RenameDeviceState.waiting_for_main_name)
    await state.update_data(prompt_msg_id=call.message.message_id)
    text = (
        "<b>✏️ Введите новое название для вашего Основного устройства №1:</b>\n\n"
        "Отправьте текстом (например: <code>Мой iPhone 15</code>, <code>Главный смартфон</code>, <code>Рабочий телефон</code>)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="my_devices_list")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.message(RenameDeviceState.waiting_for_main_name)
async def handle_rename_main_device(message: Message, state: FSMContext):
    data = await state.get_data()
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prompt_msg_id)
        except Exception:
            pass

    new_name = message.text.strip() if message.text else "Основное устройство #1"
    clean_name = re.sub(r'[^\w\s\-А-Яа-яЁё]', '', new_name).strip()[:20]
    if not clean_name:
        clean_name = "Основное устройство #1"
    set_user_main_device_name(message.from_user.id, clean_name)
    await state.clear()
    text, kb = get_my_devices_text_and_kb(message.from_user.id)
    await message.answer(f"✅ Название основного устройства изменено на «<b>{clean_name}</b>»!\n\n" + text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("dev_rename_") | F.data.startswith("rename_dev_"))
async def cb_rename_extra_device_prompt(call: CallbackQuery, state: FSMContext):
    try:
        await call.answer()
    except Exception:
        pass
    device_id = int(call.data.split("_")[2])
    await state.set_state(RenameDeviceState.waiting_for_extra_name)
    await state.update_data(rename_dev_id=device_id, prompt_msg_id=call.message.message_id)
    
    text = (
        "<b>✏️ Введите новое название для этого устройства:</b>\n\n"
        "Отправьте текстом понятное имя (например: <code>Планшет мамы</code>, <code>Ноутбук 2</code>)."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="my_devices_list")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.message(RenameDeviceState.waiting_for_extra_name)
async def handle_rename_extra_device(message: Message, state: FSMContext):
    data = await state.get_data()
    device_id = data.get("rename_dev_id")
    prompt_msg_id = data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await message.bot.delete_message(message.chat.id, prompt_msg_id)
        except Exception:
            pass

    new_name = message.text.strip() if message.text else "Устройство"
    clean_name = re.sub(r'[^\w\s\-А-Яа-яЁё]', '', new_name).strip()[:20]
    if not clean_name:
        clean_name = "Устройство"

    if device_id:
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        cur = conn.cursor()
        cur.execute("UPDATE user_devices SET device_name = ? WHERE device_id = ? AND user_id = ?", (clean_name, device_id, message.from_user.id))
        conn.commit()
        conn.close()

    await state.clear()
    text, kb = get_my_devices_text_and_kb(message.from_user.id)
    await message.answer(f"✅ Устройство успешно переименовано в «<b>{clean_name}</b>»!\n\n" + text, reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.in_({"my_devices", "my_devices_list"}))
async def cb_my_devices_list_cancel(call: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    text, reply_markup = get_my_devices_text_and_kb(user_id)
    await safe_reply(call, text, reply_markup=reply_markup)
async def cb_my_devices_list(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    text, reply_markup = get_my_devices_text_and_kb(user_id)
    await safe_reply(call, text, reply_markup=reply_markup)

def get_device_by_id_full(device_id: int):
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT device_id, user_id, device_name, amnezia_ip, amnezia_pubkey, amnezia_privkey, device_type FROM user_devices WHERE device_id = ?", (device_id,))
    row = cur.fetchone()
    conn.close()
    return row



async def render_device_details(call: CallbackQuery, device_id: int):
    dev = get_device_by_id_full(device_id)
    if not dev or dev[1] != call.from_user.id:
        await call.answer("Устройство не найдено", show_alert=True)
        return

    d_id, u_id, d_name, d_ip, d_pubkey, d_privkey, d_type = dev

    if d_type in ['pc', 'pc_clash']:
        type_str = "🔀 Умный профиль (Clash Party для ПК)"
    elif d_type in ['pc_amnezia', 'amnezia_pc']:
        type_str = "🛡 Чистый VPN (AmneziaVPN .vpn для ПК)"
    elif d_type in ['android', 'android_nekobox']:
        type_str = "🔀 Умный VPN (NekoBox / v2rayNG Hysteria 2)"
    elif d_type in ['android_amnezia', 'amnezia_android']:
        type_str = "🛡 Чистый VPN (AmneziaVPN .vpn)"
    elif d_type == 'android_combo':
        type_str = "⚡ Связка NekoBox / v2rayNG + Amnezia + Прокси ТГ"
    else:
        type_str = "🍏 Умный VPN (iOS Hysteria 2)"

    text = (
        f"📱 <b>Устройство: «{d_name}»</b>\n"
        f"⚙️ <b>Текущий способ:</b> {type_str}\n\n"
        f"<i>Выберите нужное действие:</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Скачать ключ / файл", callback_data=f"send_dev_file_{d_id}")],
        [InlineKeyboardButton(text="⚙️ Настройки устройства", callback_data=f"dev_actions_{d_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку устройств", callback_data="my_devices_list")]
    ])

    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)


@dp.callback_query(F.data.startswith("dl_dev_"))
async def cb_download_device_file(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    device_id = int(call.data.split("_")[2])
    await render_device_details(call, device_id)



@dp.callback_query(F.data.startswith("dev_actions_"))
async def cb_device_actions_menu(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    device_id = int(call.data.split("_")[2])
    dev = get_device_by_id_full(device_id)
    if not dev or dev[1] != call.from_user.id:
        await call.answer("Устройство не найдено", show_alert=True)
        return

    d_id, u_id, d_name, d_ip, d_pubkey, d_privkey, d_type = dev

    text = (
        f"⚙️ <b>Настройки устройства «{d_name}»:</b>\n\n"
        f"Выберите действие из списка ниже:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сменить способ подключения", callback_data=f"dev_change_type_menu_{d_id}")],
        [InlineKeyboardButton(text="✏️ Переименовать устройство", callback_data=f"dev_rename_{d_id}")],
        [InlineKeyboardButton(text="🗑 Удалить устройство", callback_data=f"del_dev_{d_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к устройству", callback_data=f"dl_dev_{d_id}")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("dev_change_type_menu_"))
async def cb_device_change_type_menu(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    device_id = int(call.data.split("_")[4])
    dev = get_device_by_id_full(device_id)
    if not dev or dev[1] != call.from_user.id:
        await call.answer("Устройство не найдено", show_alert=True)
        return

    d_id, u_id, d_name, d_ip, d_pubkey, d_privkey, d_type = dev

    if d_type in ['pc', 'pc_clash', 'pc_amnezia', 'amnezia_pc']:
        text = (
            f"🔄 <b>Выберите новый способ подключения для ПК «{d_name}»:</b>\n\n"
            "🔗 <b>1. Авто-ссылка подписки (Clash Party):</b> Авто-обновление правил РКН 24/7 и белых списков.\n\n"
            "📄 <b>2. Умный профиль Clash (.txt):</b> Традиционный файл конфигурации Clash_ZirginsVPN.txt.\n\n"
            "🛡 <b>3. Чистый VPN (AmneziaVPN .vpn):</b> Файл AmneziaAWG для полного туннелирования всего ПК."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 1. Ссылка авто-подписки (Clash Party)", callback_data=f"switch_dev_type_{d_id}_pc_sub")],
            [InlineKeyboardButton(text="📄 2. Умный профиль Clash (.txt)", callback_data=f"switch_dev_type_{d_id}_pc_clash")],
            [InlineKeyboardButton(text="🛡 3. Чистый VPN (AmneziaVPN .vpn)", callback_data=f"switch_dev_type_{d_id}_pc_amnezia")],
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data=f"dev_actions_{d_id}")]
        ])
    elif d_type == 'ios':
        text = (
            f"🔄 <b>Выберите новый способ подключения для iPhone / iOS «{d_name}»:</b>\n\n"
            "🔗 <b>1. Авто-ссылка подписки (Karing / Streisand):</b> Авто-обновление правил РКН 24/7 и виджет трафика.\n\n"
            "🔑 <b>2. Текстовый ключ Hysteria 2:</b> Одиночный ключ Hysteria 2."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 1. Авто-ссылка подписки (iOS)", callback_data="send_sub_link_ios")],
            [InlineKeyboardButton(text="🔑 2. Текстовый ключ Hysteria 2", callback_data="send_key")],
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data=f"dev_actions_{d_id}")]
        ])
    else:  # Android
        text = (
            f"🔄 <b>Выберите новый способ подключения для Android «{d_name}»:</b>\n\n"
            "🔗 <b>1. Авто-ссылка подписки (NekoBox / v2rayNG):</b> Авто-обновление правил РКН 24/7 и виджет трафика.\n\n"
            "🔀 <b>2. Умный VPN (NekoBox / v2rayNG Hysteria 2):</b> Одиночный ключ Hysteria 2. РКН через VPN, Сбербанк и Госуслуги напрямую.\n\n"
            "🛡 <b>3. Чистый VPN (AmneziaVPN .vpn):</b> Файл AmneziaAWG для 100% шифрования смартфона.\n\n"
            "⚡ <b>4. Связка NekoBox / v2rayNG + Amnezia + Прокси ТГ:</b> VPN для заблокированных сайтов + прямой прокси для Telegram."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 1. Авто-ссылка подписки (Android)", callback_data="send_sub_link_android")],
            [InlineKeyboardButton(text="🔀 2. Умный VPN (NekoBox / v2rayNG Hysteria 2)", callback_data=f"switch_dev_type_{d_id}_android_nekobox")],
            [InlineKeyboardButton(text="🛡 3. Чистый VPN (AmneziaVPN .vpn)", callback_data=f"switch_dev_type_{d_id}_android_amnezia")],
            [InlineKeyboardButton(text="⚡ 4. Связка NekoBox / v2rayNG + Amnezia + Прокси ТГ", callback_data=f"switch_dev_type_{d_id}_android_combo")],
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data=f"dev_actions_{d_id}")]
        ])

    await safe_reply(call, text, reply_markup=kb)

# [REMOVED] Duplicate rename handler (consolidated into cb_rename_extra_device_prompt)


@dp.callback_query(F.data.startswith("send_dev_file_"))
async def cb_send_device_file(call: CallbackQuery):
    try:
        await call.answer("Отправка...")
    except Exception:
        pass
    device_id = int(call.data.split("_")[3])
    dev = get_device_by_id_full(device_id)
    if not dev or dev[1] != call.from_user.id:
        await call.answer("Устройство не найдено", show_alert=True)
        return

    d_id, u_id, d_name, d_ip, d_pubkey, d_privkey, d_type = dev
    safe_filename_part = d_name.replace(" ", "_")
    user_h_link = get_user_hysteria_link(u_id)
    dev_h_link = user_h_link.replace("#ZirginsVPN", f"#ZirginsVPN_{safe_filename_part}")

    if d_type in ['pc', 'pc_clash']:
        file_name = f"Clash_ZirginsVPN_{safe_filename_part}.txt"
        local_path = f"/tmp/{file_name}"
        if not os.path.exists("/opt/vps-bot/Clash_jzargo.txt"):
            await call.message.answer("❌ Файл шаблон Clash не найден на сервере.")
            return

        with open("/opt/vps-bot/Clash_jzargo.txt", "r", encoding="utf-8") as f:
            clash_content = f.read()

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(clash_content)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"<b>📄 Профиль Clash Party для «{d_name}»:</b>\n\n"
            f"1. Перетащите файл <code>{file_name}</code> в Clash Party в раздел <b>Profiles</b>.\n\n"
            "<b>⚙️ Режимы работы (System Proxy vs TUN):</b>\n"
            "• <b>System Proxy:</b> Для браузеров.\n"
            "• <b>TUN Mode (Рекомендуется 🛡):</b> Весь трафик ПК на сетевом уровне.\n\n"
            "<b>🌐 Маршрутизация (Rule / Global / Direct):</b>\n"
            "• 🔀 <b>Rule (Рекомендуется ⚡):</b> Заблокированные сайты через VPN, Сбербанк напрямую.\n"
            "• 🌍 <b>Global:</b> 100% трафика через VPN.\n"
            "• 🚫 <b>Direct:</b> Напрямую без VPN."
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(doc, caption=text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)
    elif d_type in ['android', 'android_nekobox']:
        text = (
            f"🔀 <b>Персональный ключ Hysteria 2 для «{d_name}»:</b>\n\n"
            f"<code>{dev_h_link}</code>\n\n"
            f"<b>📥 Приложения для Android:</b>\n"
            f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>1. Скачать NekoBox / v2rayNG для Android (GitHub)</a>\n"
            f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>2. Скачать v2rayNG для Android (GitHub)</a>"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Прислать NekoBox / v2rayNG.apk файлом в чат", callback_data="send_apk_nekobox")],
            [InlineKeyboardButton(text="📦 Прислать v2rayNG.apk файлом в чат", callback_data="send_apk_v2rayng")],
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
    elif d_type == 'android_combo':
        file_name = f"ZirginsVPN_{safe_filename_part}.vpn"
        local_path = f"/tmp/{file_name}"
        vpn_payload = encode_amnezia_vpn_file(d_privkey, d_pubkey, d_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"⚡ <b>Конфигурация Связки для «{d_name}»:</b>\n\n"
            f"<b>1️⃣ MTProto Прокси в Telegram:</b>\n"
            f"• <a href='{MTPROTO_LINK}'>Подключить MTProto Прокси</a>\n\n"
            f"<b>2️⃣ Ключ Hysteria 2 (для NekoBox / v2rayNG):</b>\n"
            f"<code>{dev_h_link}</code>\n\n"
            f"<b>3️⃣ Файл AmneziaVPN ({file_name}):</b> прикреплён выше!"
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(doc, caption=text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)
    elif d_type == 'ios':
        text = (
            f"🍏 <b>Персональный ключ Hysteria 2 для «{d_name}» (iOS):</b>\n\n"
            f"<code>{dev_h_link}</code>\n\n"
            f"<b>📥 Приложения в App Store:</b>\n"
            f"• <a href='{URL_IOS_KARING}'>Скачать Karing (Российский App Store)</a>\n"
            f"• <a href='{URL_IOS_STREISAND}'>Скачать Streisand (Иностранный App Store)</a>\n"
            f"• <a href='{URL_IOS_HAPP}'>Скачать Happ Proxy (Иностранный App Store)</a>\n"
            
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)
    else:  # AmneziaVPN (.vpn)
        file_name = f"ZirginsVPN_{safe_filename_part}.vpn"
        local_path = f"/tmp/{file_name}"
        vpn_payload = encode_amnezia_vpn_file(d_privkey, d_pubkey, d_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"<b>🛡 Файл AmneziaVPN (.vpn) для «{d_name}»:</b>\n\n"
            f"Загрузите полученный файл <code>{file_name}</code> в приложение AmneziaVPN.\n\n"
            f"• <a href='{URL_PC_AMNEZIA_OFFICIAL}'>Скачать AmneziaVPN (Официальный сайт)</a>"
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(doc, caption=text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)

@dp.callback_query(F.data.startswith("switch_dev_type_"))
async def cb_switch_device_type(call: CallbackQuery):
    parts = call.data.split("_")
    device_id = int(parts[3])
    new_type = "_".join(parts[4:])
    update_device_type(device_id, call.from_user.id, new_type)
    try:
        await call.answer("Способ подключения устройства успешно изменён! ✨", show_alert=True)
    except Exception:
        pass
    await render_device_details(call, device_id)


@dp.callback_query(F.data.startswith("del_dev_"))
async def cb_delete_device_ask(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    device_id = int(call.data.split("_")[2])
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT device_name FROM user_devices WHERE device_id = ? AND user_id = ?", (device_id, call.from_user.id))
    row = cur.fetchone()
    conn.close()
    
    d_name = row[0] if row else "Устройство"
    
    text = (
        "⚠️ <b>Предупреждение перед удалением устройства!</b>\n\n"
        f"Вы действительно хотите удалить устройство <b>«{d_name}»</b>?\n\n"
        "❗️ <b>Внимание:</b> После удаления выданный ключ и файл конфигурации для этого устройства <u>станут полностью недействительными</u> и перестанут работать на сервере.\n\n"
        "Вы уверены?"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_dev_{device_id}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="my_devices")
        ]
    ])
    
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("confirm_del_dev_"))
async def cb_confirm_delete_device(call: CallbackQuery):
    try:
        await call.answer("Устройство удалено, ключ аннулирован!", show_alert=True)
    except Exception:
        pass
    device_id = int(call.data.split("_")[3])
    delete_user_device(device_id, call.from_user.id)
    await cb_my_devices_list(call)

@dp.callback_query(F.data == "menu_family")
async def cb_menu_family(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    user_info = get_user_status(user_id)
    head_id = user_info[6] if user_info and len(user_info) >= 7 and user_info[6] else user_id
    admin_mode = is_admin(user_id)

    members = get_family_members(head_id)
    devices = get_user_devices(user_id)

    bot_info = await bot.get_me()
    invite_link = f"https://t.me/{bot_info.username}?start=fam_{head_id}"

    members_limit_str = "∞ (Безлимит)" if admin_mode else f"{len(members)} / 6 человек"
    devices_limit_str = "∞ (Безлимит)" if admin_mode else f"{len(devices) + 1} / 5"

    members_list_text = ""
    if members:
        members_list_text = "\n<b>👥 Состав вашей семьи:</b>\n" + "\n".join([f"• {m[1]} (@{m[2] if m[2] else m[0]})" for m in members])

    text = (
        "<b>👨‍👩‍👧‍👦 Раздел «Семья» ZirginsVPN:</b>\n\n"
        f"👑 <b>Глава семьи ID:</b> <code>{head_id}</code>\n"
        f"👥 <b>Участников в семье:</b> {members_limit_str}\n"
        f"📱 <b>Всего устройств:</b> {devices_limit_str}{members_list_text}\n\n"
        "<b>🔗 Ваша семейная пригласительная ссылка:</b>\n"
        f"<code>{invite_link}</code>\n\n"
        "💡 <i>Отправьте эту ссылку членам семьи. При переходе по ней они автоматически подключатся к вашей семейной подписке!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Поделиться ссылкой с семьей в 1 клик", switch_inline_query=f"Присоединяйся к моей Семейной подписке ZirginsVPN: {invite_link}")],
        [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "add_extra_device")
async def cb_add_extra_device_start(call: CallbackQuery):
    user_id = call.from_user.id
    devices = get_user_devices(user_id)
    if len(devices) >= 4 and not is_admin(user_id):
        await call.answer("Вы достигли лимита в 5 устройств!", show_alert=True)
        return

    try:
        await call.answer()
    except Exception:
        pass

    text = (
        "<b>📱 Выберите тип устройства и способ подключения:</b>\n\n"
        "Укажите нужную платформу и тип приложения:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android — Выбрать способ", callback_data="menu_devtype_android")],
        [InlineKeyboardButton(text="🍏 iPhone / iPad — Выбрать способ", callback_data="menu_devtype_ios")],
        [InlineKeyboardButton(text="💻 ПК / Ноутбук — Выбрать способ", callback_data="menu_devtype_pc")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="my_devices_list")]
    ])
    
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "menu_devtype_android")
async def cb_menu_devtype_android(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    text = (
        "<b>🤖 Выберите способ подключения для Android:</b>\n\n"
        f"🔗 <b>1. Авто-ссылка подписки (NekoBox / Karing):</b> Авто-обновление списков РКН 24/7 и виджет остатка трафика.\n\n"
        f"1️⃣ <b>🔀 2. Умный VPN (Hysteria 2):</b> Ключ Hysteria 2 для NekoBox.\n"
        f"   • <a href='{URL_ANDROID_NEKOBOX_GH}'>1. Скачать NekoBox для Android (GitHub)</a>\n"
        f"   • <a href='{URL_ANDROID_V2RAYNG_GH}'>2. Скачать v2rayNG для Android (GitHub)</a>\n\n"
        f"2️⃣ <b>🛡 3. Чистый VPN (AmneziaVPN):</b> 100% шифрование всего трафика телефона через `.vpn` файл.\n"
        f"   • <a href='{URL_ANDROID_AMNEZIA_GP}'>Скачать AmneziaVPN из Google Play</a>\n\n"
        f"3️⃣ <b>⚡ 4. Связка NekoBox + Amnezia + Прокси ТГ:</b> Комплексное решение.\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 1. Авто-ссылка подписки (Android)", callback_data="devtype_android_sub")],
        [InlineKeyboardButton(text="🔀 2. Умный VPN (NekoBox Hysteria 2)", callback_data="devtype_android_nekobox")],
        [InlineKeyboardButton(text="🛡 3. Чистый VPN (AmneziaVPN .vpn)", callback_data="devtype_android_amnezia")],
        [InlineKeyboardButton(text="⚡ 4. Связка NekoBox + Amnezia + Прокси ТГ", callback_data="devtype_android_combo")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору устройства", callback_data="add_extra_device")],
        [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "menu_devtype_pc", StateFilter("*"))
async def cb_menu_devtype_pc(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    text = (
        "<b>💻 Выберите способ подключения для ПК / Компьютера:</b>\n\n"
        f"🔗 <b>1. Авто-ссылка подписки (Clash Party):</b> Авто-обновление списков РКН 24/7 и встроенные белые списки РФ.\n"
        f"   • <a href='{URL_PC_CLASH_PARTY_GH}'>Скачать Clash Party для ПК (GitHub)</a>\n\n"
        f"📄 <b>2. Умный профиль Clash (.txt):</b> Традиционный файл Clash_ZirginsVPN.txt.\n"
        f"   • <a href='{URL_PC_CLASH_PARTY_GH}'>Скачать Clash Party для ПК (GitHub)</a>\n\n"
        f"🛡 <b>3. Чистый VPN (AmneziaVPN .vpn):</b> Файл AmneziaAWG для полного VPN-туннеля всего ПК.\n"
        f"   • <a href='{URL_PC_AMNEZIA_OFFICIAL}'>Скачать AmneziaVPN (Официальный сайт)</a>\n\n"
        "<b>⚙️ Режимы Clash Party (System Proxy vs TUN):</b>\n"
        "• <b>System Proxy:</b> Для браузеров и базовых программ.\n"
        "• <b>TUN Mode (Рекомендуется 🛡):</b> Весь трафик ПК (игры, Discord, Telegram, приложения) на сетевом уровне.\n\n"
        "<b>🌐 Маршрутизация (Rule / Global / Direct):</b>\n"
        "• 🔀 <b>Rule (Рекомендуется ⚡):</b> Заблокированные сайты через VPN, Сбербанк и Госуслуги напрямую.\n"
        "• 🌍 <b>Global:</b> 100% трафика через VPN.\n"
        "• 🚫 <b>Direct:</b> Весь трафик напрямую без VPN."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 1. Авто-ссылка подписки (Clash Party)", callback_data="devtype_pc_sub")],
        [InlineKeyboardButton(text="📄 2. Умный профиль (Clash Party .txt)", callback_data="devtype_pc_clash")],
        [InlineKeyboardButton(text="🛡 3. Чистый VPN (AmneziaVPN .vpn)", callback_data="devtype_pc_amnezia")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору устройства", callback_data="add_extra_device")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "menu_devtype_ios", StateFilter("*"))
async def cb_menu_devtype_ios(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    text = (
        "<b>🍏 Выберите способ подключения для iPhone / iPad (iOS):</b>\n\n"
        "🔗 <b>1. Авто-ссылка подписки (Karing / Streisand):</b> Авто-обновление списков РКН 24/7 и виджет остатка трафика.\n\n"
        "🔑 <b>2. Текстовый ключ Hysteria 2:</b> Одиночный ключ Hysteria 2 для быстрого импорта.\n\n"
        f"• <a href='{URL_IOS_KARING}'>1. Karing (Российский App Store)</a>\n"
        f"• <a href='{URL_IOS_STREISAND}'>2. Streisand (Иностранный App Store)</a>\n"
        f"• <a href='{URL_IOS_HAPP}'>3. Happ Proxy (Иностранный App Store)</a>\n"
        f"• <a href='{URL_IOS_V2BOX}'>4. V2Box (Иностранный App Store)</a>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 1. Авто-ссылка подписки (iOS)", callback_data="devtype_ios_sub")],
        [InlineKeyboardButton(text="🔑 2. Текстовый ключ Hysteria 2", callback_data="devtype_ios")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору устройства", callback_data="add_extra_device")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)


@dp.callback_query(F.data.in_({"devtype_android_sub", "devtype_android_nekobox", "devtype_android_amnezia", "devtype_android_combo", "devtype_ios_sub", "devtype_ios", "devtype_pc_sub", "devtype_pc_clash", "devtype_pc_amnezia"}))
async def cb_select_device_type(call: CallbackQuery, state: FSMContext):
    dev_type = call.data.replace("devtype_", "")
    await state.set_state(AddDeviceState.waiting_for_name)
    await state.update_data(dev_type=dev_type, prompt_msg_id=call.message.message_id)
    
    try:
        await call.answer()
    except Exception:
        pass

    titles = {
        "android_sub": "Android — Авто-подписка",
        "android_amnezia": "Android — AmneziaVPN",
        "android_nekobox": "Android — NekoBox / v2rayNG",
        "android_combo": "Android — Связка + Прокси",
        "ios_sub": "iPhone / iPad — Авто-подписка",
        "ios": "iPhone / iPad",
        "pc_sub": "ПК — Авто-подписка",
        "pc_amnezia": "ПК — AmneziaVPN",
        "pc_clash": "ПК — Clash Party"
    }
    type_title = titles.get(dev_type, "Устройство")

    text = (
        f"<b>✏️ Назовите новое устройство ({type_title}):</b>\n\n"
        "Отправьте текстом понятное название (например: <code>Телефон мамы</code>, <code>Рабочий ноут</code>, <code>Планшет</code>, <code>ТВ в гостиной</code>).\n\n"
        "<i>Или выберите один из быстрых вариантов ниже:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Телефон №2", callback_data="preset_dev_Телефон_2"),
            InlineKeyboardButton(text="💻 Ноутбук", callback_data="preset_dev_Ноутбук")
        ],
        [
            InlineKeyboardButton(text="🖥 ПК", callback_data="preset_dev_ПК"),
            InlineKeyboardButton(text="📟 Планшет", callback_data="preset_dev_Планшет")
        ],
        [
            InlineKeyboardButton(text="📺 Smart TV", callback_data="preset_dev_Smart_TV")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="my_devices_list")
        ]
    ])

    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("preset_dev_"), AddDeviceState.waiting_for_name)
async def cb_preset_device_name(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    dev_type = data.get("dev_type", "android_amnezia")
    raw_name = call.data.replace("preset_dev_", "").replace("_", " ")
    await state.clear()
    await process_create_device(call.message, call.from_user.id, raw_name, dev_type, is_callback=True, call=call)

@dp.message(AddDeviceState.waiting_for_name)
async def handle_custom_device_name(message: Message, state: FSMContext):
    data = await state.get_data()
    dev_type = data.get("dev_type", "android_amnezia")
    device_name = message.text.strip() if message.text else "Устройство"
    await state.clear()
    await process_create_device(message, message.from_user.id, device_name, dev_type, is_callback=False)

async def process_create_device(msg: Message, user_id: int, device_name: str, dev_type: str = "android_amnezia", is_callback: bool = False, call: CallbackQuery = None):
    devices = get_user_devices(user_id)
    if len(devices) >= 4 and not is_admin(user_id):
        err_txt = "❌ Вы достигли лимита в 5 устройств!"
        if is_callback and call:
            await call.answer(err_txt, show_alert=True)
        else:
            await msg.answer(err_txt)
        return

    clean_name = re.sub(r'[^\w\s\-А-Яа-яЁё]', '', device_name).strip()[:20]
    if not clean_name:
        clean_name = f"Устройство_{len(devices) + 2}"

    if is_callback and call:
        try:
            await call.answer("Генерация конфигурации...", show_alert=False)
        except Exception:
            pass

    priv_key, pub_key, client_ip = create_extra_device_peer(user_id, clean_name, device_type=dev_type)

    # Message #1: Devices List Menu
    menu_text, menu_kb = get_my_devices_text_and_kb(user_id)
    if is_callback and call and call.message:
        try:
            await call.message.edit_text(menu_text, reply_markup=menu_kb, parse_mode="HTML")
        except Exception:
            await msg.answer(menu_text, reply_markup=menu_kb, parse_mode="HTML")
    else:
        await msg.answer(menu_text, reply_markup=menu_kb, parse_mode="HTML")

    if dev_type in ['ios_sub', 'android_sub', 'pc_sub']:
        h_pass = get_user_hysteria_pass(user_id)
        sub_url = f"http://178.17.52.67/sub/{h_pass}"
        if dev_type == 'ios_sub':
            sub_txt = (
                f"✅ <b>Устройство «{clean_name}» создано и добавлено!</b>\n\n"
                f"<b>🍏 Ваша ссылка авто-подписки:</b>\n<code>{sub_url}</code>\n\n"
                "<b>📥 Скачайте приложение:</b>\n"
                f"• <a href='{URL_IOS_KARING}'>1. Karing (App Store)</a>\n"
                f"• <a href='{URL_IOS_STREISAND}'>2. Streisand (App Store)</a>\n"
                f"• <a href='{URL_IOS_HAPP}'>3. Happ Proxy (App Store)</a>\n"
                
                "<b>📱 Инструкция:</b> Вставьте скопированную ссылку в Karing / Streisand в раздел подписок."
            )
        elif dev_type == 'android_sub':
            sub_txt = (
                f"✅ <b>Устройство «{clean_name}» создано и добавлено!</b>\n\n"
                f"<b>🤖 Ваша ссылка авто-подписки:</b>\n<code>{sub_url}?flag=singbox</code>\n\n"
                "<b>📥 Скачайте приложение:</b>\n"
                f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>1. NekoBox / v2rayNG (GitHub)</a>\n"
                f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>2. v2rayNG (GitHub)</a>\n\n"
                "<b>📱 Инструкция:</b> Вставьте скопированную ссылку в NekoBox / v2rayNG."
            )
        else:
            sub_txt = (
                f"✅ <b>Устройство «{clean_name}» создано и добавлено!</b>\n\n"
                f"<b>💻 Ваша ссылка авто-подписки:</b>\n<code>{sub_url}</code>\n\n"
                "<b>📥 Скачайте приложение:</b>\n"
                f"• <a href='{URL_PC_CLASH_PARTY_GH}'>Clash Party для ПК (GitHub)</a>\n\n"
                "<b>📱 Инструкция:</b> Скопируйте ссылку и нажмите Import в Clash Party."
            )
        sub_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Мои устройства", callback_data="my_devices_list")],
            [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
        ])
        await msg.answer(sub_txt, reply_markup=sub_kb, parse_mode="HTML", disable_web_page_preview=True)
        return

    # Message #2: Deliver specific key or file based on dev_type
    safe_filename_part = clean_name.replace(" ", "_")

    if dev_type in ['ios', 'android_nekobox']:
        user_h_link = get_user_hysteria_link(user_id)
        dev_h_link = user_h_link.replace("#ZirginsVPN", f"#ZirginsVPN_{safe_filename_part}")
        
        if dev_type == 'ios':
            text = (
                f"✅ <b>Устройство «{clean_name}» (iOS) успешно создано!</b>\n\n"
                f"<b>🔑 Персональный ключ Hysteria 2 для «{clean_name}»:</b>\n\n"
                f"<code>{dev_h_link}</code>\n\n"
                f"<b>📥 Приложения в App Store (iOS):</b>\n"
                f"• <a href='{URL_IOS_KARING}'>Скачать Karing (Российский App Store)</a>\n"
                f"• <a href='{URL_IOS_STREISAND}'>Скачать Streisand (Иностранный App Store)</a>\n"
                f"• <a href='{URL_IOS_HAPP}'>Скачать Happ Proxy (Иностранный App Store)</a>\n"
                
            )
            await msg.answer(text, parse_mode="HTML", disable_web_page_preview=True)
        else:
            h_pass_for_sub = get_user_hysteria_pass(user_id)
            sub_url = f"http://178.17.52.67/sub/{h_pass_for_sub}?flag=singbox"
            text = (
                f"✅ <b>Устройство «{clean_name}» (Android / NekoBox / v2rayNG) успешно создано!</b>\n\n"
                f"<b>🤖 Ваша ссылка авто-подписки:</b>\n<code>{sub_url}</code>\n\n"
                f"<b>🔑 Либо персональный ключ Hysteria 2:</b>\n"
                f"<code>{dev_h_link}</code>\n\n"
                f"<b>📥 Приложения для Android:</b>\n"
                f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>1. Скачать NekoBox / v2rayNG для Android (GitHub)</a>\n"
                f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>2. Скачать v2rayNG для Android (GitHub)</a>\n\n"
                f"💡 <i>Подсказка: Вы можете скачать установочные файлы `.apk` прямо в чат кнопками ниже!</i>"
            )
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📦 Прислать NekoBox / v2rayNG.apk файлом в чат", callback_data="send_apk_nekobox")],
                [InlineKeyboardButton(text="📦 Прислать v2rayNG.apk файлом в чат", callback_data="send_apk_v2rayng")],
                [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
                [InlineKeyboardButton(text="🏠 Главное Меню", callback_data="main_menu")]
            ])
            await msg.answer(text, reply_markup=kb, parse_mode="HTML", disable_web_page_preview=True)
        return
    elif dev_type == 'android_combo':
        user_h_link = get_user_hysteria_link(user_id)
        dev_h_link = user_h_link.replace("#ZirginsVPN", f"#ZirginsVPN_{safe_filename_part}")
        file_name = f"ZirginsVPN_{safe_filename_part}.vpn"
        local_path = f"/tmp/{file_name}"
        vpn_payload = encode_amnezia_vpn_file(priv_key, pub_key, client_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"✅ <b>Устройство «{clean_name}» (Связка + Прокси) успешно создано!</b>\n\n"
            f"<b>1️⃣ Инструкция для Telegram (MTProto Прокси в 1 клик):</b>\n"
            f"• Нажмите ссылку для прямого подключения прокси: <a href='{MTPROTO_LINK}'>Подключить MTProto Прокси в Telegram</a>\n\n"
            f"<b>2️⃣ Ключ Hysteria 2 (для NekoBox / v2rayNG):</b>\n"
            f"<code>{dev_h_link}</code>\n"
            f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>Скачать NekoBox / v2rayNG из GitHub</a>\n\n"
            f"<b>3️⃣ Файл AmneziaVPN ({file_name}):</b>\n"
            f"• <a href='{URL_ANDROID_AMNEZIA_GP}'>Скачать AmneziaVPN из Google Play</a>"
        )
        await msg.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)
    elif dev_type in ['pc', 'pc_clash']:
        file_name = f"Clash_ZirginsVPN_{safe_filename_part}.txt"
        local_path = f"/tmp/{file_name}"

        if not os.path.exists("/opt/vps-bot/Clash_jzargo.txt"):
            if is_callback and call and call.message:
                await call.message.answer("❌ Файл шаблон Clash не найден на сервере.")
            else:
                await msg.answer("❌ Файл шаблон Clash не найден на сервере.")
            return

        with open("/opt/vps-bot/Clash_jzargo.txt", "r", encoding="utf-8") as f:
            clash_content = f.read()

        with open(local_path, "w", encoding="utf-8") as f:
            f.write(clash_content)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"✅ <b>Устройство «{clean_name}» (ПК Clash Party) успешно создано!</b>\n\n"
            f"<b>📄 Персональный профиль Clash Party для ПК:</b>\n"
            f"1. Перетащите полученный файл <code>{file_name}</code> в программу Clash Party в раздел <b>Profiles</b>.\n"
            f"2. Переключите тумблер <b>TUN</b> в положение <b>Включено (ON)</b>.\n\n"
            f"• <a href='{URL_PC_CLASH_PARTY_GH}'>Скачать Clash Party для ПК (GitHub)</a>"
        )
        if is_callback and call and call.message:
            await call.message.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await msg.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)
    elif dev_type in ['pc_amnezia', 'amnezia_pc']:
        file_name = f"ZirginsVPN_{safe_filename_part}.vpn"
        local_path = f"/tmp/{file_name}"
        vpn_payload = encode_amnezia_vpn_file(priv_key, pub_key, client_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"✅ <b>Устройство «{clean_name}» (ПК AmneziaVPN) успешно создано!</b>\n\n"
            f"<b>📄 Файл AmneziaVPN (.vpn) для ПК:</b>\n"
            f"1. Скачайте приложение AmneziaVPN для Windows.\n"
            f"2. Загрузите файл <code>{file_name}</code> в программу AmneziaVPN.\n\n"
            f"• <a href='{URL_PC_AMNEZIA_GH}'>Скачать AmneziaVPN для ПК (Официальный сайт)</a>"
        )
        if is_callback and call and call.message:
            await call.message.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)
        else:
            await msg.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)
    else:
        file_name = f"ZirginsVPN_{safe_filename_part}.vpn"
        local_path = f"/tmp/{file_name}"
        vpn_payload = encode_amnezia_vpn_file(priv_key, pub_key, client_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"✅ <b>Устройство «{clean_name}» успешно создано!</b>\n\n"
            f"<b>📱 Файл AmneziaVPN ({file_name}):</b>\n\n"
            f"• <a href='{URL_ANDROID_AMNEZIA_GP}'>Скачать AmneziaVPN из Google Play</a>\n"
            f"• Откройте приложение AmneziaVPN на устройстве <b>«{clean_name}»</b> и импортируйте этот файл."
        )
        await msg.answer_document(doc, caption=text, parse_mode="HTML", disable_web_page_preview=True)

@dp.callback_query(F.data.startswith("approve_"))
async def cb_approve_user(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[1])
    set_user_status(target_id, 'approved')
    ensure_user_amnezia_peer(target_id)

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    u_row = cur.fetchone()
    conn.close()

    u_name = u_row[0] if u_row and u_row[0] else "Пользователь"
    u_tag = f"(@{u_row[1]})" if u_row and u_row[1] else "(без тега)"

    try:
        await call.message.edit_text(f"✅ Пользователь <b>{u_name}</b> {u_tag} (<code>{target_id}</code>) успешно <b>ОДОБРЕН</b>!", parse_mode="HTML")
    except Exception:
        pass
    try:
        await bot.send_message(target_id, "🎉 <b>Ваш доступ к ZirginsVPN успешно одобрен!</b>\n\nНажмите /start чтобы открыть меню.", parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("reject_"))
async def cb_reject_user(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[1])
    set_user_status(target_id, 'rejected')

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    u_row = cur.fetchone()
    conn.close()

    u_name = u_row[0] if u_row and u_row[0] else "Пользователь"
    u_tag = f"(@{u_row[1]})" if u_row and u_row[1] else "(без тега)"

    try:
        await call.message.edit_text(f"❌ Пользователь <b>{u_name}</b> {u_tag} (<code>{target_id}</code>) <b>ОТКЛОНЕН</b>.", parse_mode="HTML")
    except Exception:
        pass
    try:
        await bot.send_message(target_id, "❌ К сожалению, ваша заявка на доступ в ZirginsVPN была отклонена.", parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data == "adm_manage_users")
async def cb_adm_manage_users(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
        
    users = get_all_users()
    wg_metrics = get_wireguard_user_metrics()
    
    text = "<b>👥 Управление и Трафик Пользователей ZirginsVPN:</b>\n\n"
    kb_buttons = []
    
    # Fetch all user extra devices
    conn_dev = sqlite3.connect(DB_PATH, timeout=20.0)
    cur_dev = conn_dev.cursor()
    cur_dev.execute("SELECT user_id, amnezia_ip FROM user_devices")
    u_extra_devs = cur_dev.fetchall()
    conn_dev.close()

    user_ips_map = {}
    for u_id, u_name, u_user, u_status, u_ip, u_pubkey, u_hpass, is_leg, fam_head in users:
        p_ip = (u_ip or "").replace("/32", "").strip()
        ips = [p_ip] if p_ip else []
        for dev_uid, dev_ip in u_extra_devs:
            if dev_uid == u_id:
                clean_d_ip = (dev_ip or "").replace("/32", "").strip()
                if clean_d_ip and clean_d_ip not in ips:
                    ips.append(clean_d_ip)
        user_ips_map[u_id] = ips

    for u_id, u_name, u_user, u_status, u_ip, u_pubkey, u_hpass, is_leg, fam_head in users:
        icon = "🟢" if u_status == 'approved' else ("🟡" if u_status == 'paused' else "🔴")
        user_ips = user_ips_map.get(u_id, [])
        
        is_active = False
        traffic_bytes = 0
        endpoint = "(none)"
        last_hs = 0

        for user_ip in user_ips:
            m = wg_metrics.get(user_ip, {})
            if m.get("is_active"):
                is_active = True
            traffic_bytes += m.get("total_bytes", 0)
            if m.get("endpoint") and m.get("endpoint") != "(none)":
                endpoint = m["endpoint"]
            if m.get("latest_handshake", 0) > last_hs:
                last_hs = m["latest_handshake"]

        if not is_active and (is_leg == 1 or u_id == ADMIN_ID):
            admin_m = wg_metrics.get("10.8.1.30", {})
            if admin_m.get("is_active"):
                is_active = True
                if admin_m.get("endpoint"):
                    endpoint = admin_m["endpoint"]
                traffic_bytes += admin_m.get("total_bytes", 0)
                if admin_m.get("latest_handshake", 0) > last_hs:
                    last_hs = admin_m["latest_handshake"]

        traffic_str = format_bytes(traffic_bytes)
        active_status = "🟢 В сети" if is_active else "⚪ Офлайн"
        time_str = "🟢 Прямо сейчас" if is_active else format_relative_time(last_hs)
        
        if u_id == ADMIN_ID:
            tag_str = " 👑 (Администратор — Безлимит)"
        elif is_leg == 1:
            tag_str = " ⭐ (Основной доступ)"
        elif fam_head:
            tag_str = f" 👨‍👩‍👧‍👦 (Семья: {fam_head})"
        else:
            tag_str = ""
        
        text += (
            f"{icon} <b>{u_name}</b> (@{u_user or 'no_username'}){tag_str}\n"
            f"   • Status: <code>{u_status}</code> | IP: <code>{u_ip or 'None'}</code>\n"
            f"   • 💾 <b>Трафик VPN:</b> {traffic_str} | Статус: {active_status}\n"
            f"   • ⏱ <b>Активность:</b> {time_str}\n"
        )
        if endpoint and endpoint != "(none)":
            text += f"   • 🌐 <b>Устройство IP:</b> <code>{endpoint}</code>\n"
        text += "\n"
        
        if u_id != ADMIN_ID:
            row = []
            if u_status == 'approved':
                row.append(InlineKeyboardButton(text=f"🟡 Пауза {u_name[:10]}", callback_data=f"pause_u_{u_id}"))
            elif u_status == 'paused':
                row.append(InlineKeyboardButton(text=f"🟢 Старт {u_name[:10]}", callback_data=f"resume_u_{u_id}"))
            row.append(InlineKeyboardButton(text=f"🔴 Удалить {u_name[:10]}", callback_data=f"delete_u_{u_id}"))
            kb_buttons.append(row)

    kb_buttons.append([InlineKeyboardButton(text="🔄 Обновить Метрики Трафика", callback_data="adm_manage_users")])
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")])
    
    try:
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons), parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("pause_u_"))
async def cb_pause_user(call: CallbackQuery):
    try:
        await call.answer("Доступ пользователя приостановлен!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    set_user_status(target_id, 'paused')
    
    # Disable main key + all additional device keys in WireGuard
    row = get_user_status(target_id)
    if row and row[2]:
        disable_amnezia_peer(row[2])
    devs = get_user_devices(target_id)
    for d in devs:
        if d[3]:
            disable_amnezia_peer(d[3])
        
    await cb_adm_manage_users(call)
    try:
        await bot.send_message(target_id, "⏸ <b>Ваш доступ к VPN был временно приостановлен администратором.</b>", parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("resume_u_"))
async def cb_resume_user(call: CallbackQuery):
    try:
        await call.answer("Доступ пользователя возобновлен!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    set_user_status(target_id, 'approved')
    ensure_user_amnezia_peer(target_id)
    devs = get_user_devices(target_id)
    for d in devs:
        if d[3] and d[4]:
            cmd2 = f"echo '{PSK2}' > /tmp/psk2.key && docker cp /tmp/psk2.key amnezia-awg2:/tmp/psk2.key && docker exec amnezia-awg2 awg set awg0 peer {d[3]} preshared-key /tmp/psk2.key allowed-ips {d[4]}/32"
            cmd1 = f"echo '{PSK1}' > /tmp/psk1.key && docker cp /tmp/psk1.key amnezia-awg:/tmp/psk1.key && docker exec amnezia-awg wg set wg0 peer {d[3]} preshared-key /tmp/psk1.key allowed-ips {d[4]}/32"
            subprocess.getoutput(cmd2)
            subprocess.getoutput(cmd1)

    await cb_adm_manage_users(call)
    try:
        await bot.send_message(target_id, "🟢 <b>Ваш доступ к VPN возобновлен!</b>", parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("delete_u_"))
async def cb_delete_user(call: CallbackQuery):
    try:
        await call.answer("Пользователь полностью удален из базы и сервера!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    delete_user_from_db(target_id)
    await cb_adm_manage_users(call)
    try:
        await bot.send_message(target_id, "❌ <b>Ваш аккаунт был удален из базы данных ZirginsVPN.</b>", parse_mode="HTML")
    except Exception:
        pass


@dp.callback_query(F.data == "del_file_msg_and_menu")
async def cb_del_file_msg_and_menu(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    try:
        await call.message.delete()
    except Exception:
        pass
    text = "👋 <b>Главное меню ZirginsVPN</b>\n\nВыберите ваше устройство или нужный раздел ниже:"
    await call.message.answer(text, reply_markup=get_main_keyboard(call.from_user.id), parse_mode="HTML")


@dp.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_status_info = get_user_status(call.from_user.id)
    status = user_status_info[0] if user_status_info else 'approved'
    if status != 'approved' and not is_admin(call.from_user.id):
        return
    text = "👋 <b>Главное меню ZirginsVPN</b>\n\nВыберите ваше устройство или нужный раздел ниже:"
    try:
        if call.message.text:
            await call.message.edit_text(text, reply_markup=get_main_keyboard(call.from_user.id), parse_mode="HTML")
        else:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer(text, reply_markup=get_main_keyboard(call.from_user.id), parse_mode="HTML")
    except Exception as e:
        logging.error(f"Error in main_menu: {e}")
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(text, reply_markup=get_main_keyboard(call.from_user.id), parse_mode="HTML")


async def render_android_menu(call: CallbackQuery):
    text = (
        "<b>🤖 Способы подключения для Android:</b>\n\n"
        "⭐ <b>1. Фирменное приложение Zirgins VPN (Рекомендуется):</b>\n"
        "• Вшит умный обход 70+ приложений РФ (Сбер, Т-Банк, Госуслуги работают напрямую).\n"
        "• Высокая скорость Hysteria 2 + авто-подписка в 1 клик.\n"
        f"👉 <a href='{URL_ANDROID_ZIRGINS_VPN}'><b>Скачать Zirgins VPN (.apk)</b></a>\n\n"
        f"🔗 <b>2. Ссылка авто-подписки:</b> Для сторонних клиентов (NekoBox, v2rayNG, Happ).\n"
        f"🛡 <b>3. Чистый VPN (AmneziaVPN):</b> 100% шифрование через `.vpn` файл.\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 1. Скачать Zirgins VPN (Android .apk)", url=URL_ANDROID_ZIRGINS_VPN)],
        [InlineKeyboardButton(text="🔗 2. Скопировать ссылку авто-подписки", callback_data="send_sub_link_android")],
        [InlineKeyboardButton(text="🔀 3. Одиночный ключ Hysteria 2", callback_data="send_key")],
        [InlineKeyboardButton(text="🛡 4. Чистый VPN (AmneziaVPN .vpn)", callback_data="info_pure_vpn")],
        [InlineKeyboardButton(text="⚡ 5. Связка NekoBox + Amnezia + Прокси ТГ", callback_data="info_combo_vpn")],
        [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

async def render_ios_menu(call: CallbackQuery):
    text = (
        "<b>🍏 Инструкция и выбор подключения для iPhone / iPad (iOS):</b>\n\n"
        f"🔗 <b>1. Авто-ссылка подписки (Karing / Streisand):</b> Авто-обновление РКН + виджет трафика.\n"
        f"🔑 <b>2. Текстовый ключ Hysteria 2:</b> Одиночный ключ Hysteria 2.\n\n"
        "1️⃣ <b>Скачайте приложение из App Store:</b>\n"
        f"   • <a href='{URL_IOS_KARING}'>Скачать Karing (App Store)</a>\n"
        f"   • <a href='{URL_IOS_STREISAND}'>Скачать Streisand (App Store)</a>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 1. Скопировать ссылку авто-подписки (iOS)", callback_data="send_sub_link_ios")],
        [InlineKeyboardButton(text="🔑 2. Скопировать ключ Hysteria 2", callback_data="send_key")],
        [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

async def render_pc_menu(call: CallbackQuery):
    text = (
        "<b>💻 Выберите способ подключения для ПК / Ноутбука:</b>\n\n"
        f"🔗 <b>1. Авто-ссылка подписки (Clash Party):</b> Авто-обновление списков РКН и белых списков РФ.\n"
        f"📄 <b>2. Файл профиля Clash (.txt):</b> Традиционный скачиваемый файл.\n"
        f"🛡 <b>3. Чистый VPN (AmneziaVPN .vpn):</b> Полный VPN-туннель для всего компьютера."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 1. Скопировать ссылку авто-подписки (ПК)", callback_data="send_sub_link_pc")],
        [InlineKeyboardButton(text="📄 2. Скачать профиль Clash (.txt)", callback_data="send_clash_file")],
        [InlineKeyboardButton(text="🛡 3. Скачать файл AmneziaVPN (.vpn)", callback_data="gen_amnezia_file")],
        [InlineKeyboardButton(text="📥 Скачать Clash Party для ПК (GitHub)", url=URL_PC_CLASH_PARTY_GH)],
        [InlineKeyboardButton(text="📱 Мои устройства (Список & Удаление)", callback_data="my_devices_list")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)


@dp.callback_query(F.data.startswith("menu_android"), StateFilter("*"))
async def cb_menu_android(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    curr_plat = get_user_primary_platform(user_id)
    if curr_plat and curr_plat != 'android' and not call.data.endswith("_force"):
        await send_platform_change_warning(call, 'android')
        return

    set_user_primary_platform(user_id, 'android')
    await render_android_menu(call)

@dp.callback_query(F.data == "menu_ios", StateFilter("*"))
async def cb_menu_ios(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    curr_plat = get_user_primary_platform(user_id)
    if curr_plat and curr_plat != 'ios' and not call.data.endswith("_force"):
        await send_platform_change_warning(call, 'ios')
        return

    set_user_primary_platform(user_id, 'ios')

    user_h_link = get_user_hysteria_link(call.from_user.id)
    text = (
        "<b>🍏 Инструкция подключения для iPhone / iPad (iOS):</b>\n\n"
        "1️⃣ <b>Скачайте приложение из App Store:</b>\n"
        f"   • <a href='{URL_IOS_KARING}'>Скачать Karing (Российский App Store)</a>\n"
        f"   • <a href='{URL_IOS_STREISAND}'>Скачать Streisand (Иностранный App Store)</a>\n"
        f"   • <a href='{URL_IOS_HAPP}'>Скачать Happ Proxy (Иностранный App Store)</a>\n"
        f"   • <a href='{URL_IOS_V2BOX}'>Скачать V2Box (Иностранный App Store)</a>\n\n"
        "2️⃣ <b>Добавьте ваш ключ подключения:</b>\n"
        "   • Нажмите синюю кнопку <b>«🔑 Скопировать ключ Hysteria 2»</b> ниже.\n"
        "   • В приложении Karing / Streisand / Happ нажмите иконку <b>«+» -> Import from Clipboard</b> (Импорт из буфера обмена) и включите тумблер.\n\n"
        "✨ <i>Сбербанк, Госуслуги и росс. сервисы автоматически работают напрямую, а Telegram, YouTube, Instagram и заблокированные сайты летают на максимальной скорости!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Скопировать ключ Hysteria 2", callback_data="send_key")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "info_pure_vpn")
async def cb_info_pure_vpn(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    text = (
        "<b>🛡 Инструкция: Чистый VPN (AmneziaVPN)</b>\n\n"
        "Этот вариант идеален, если вам нужен обычный классический VPN, пропускающий **абсолютно весь трафик устройства** через наш сервер.\n\n"
        f"1️⃣ Установите официальное приложение <a href='{URL_ANDROID_AMNEZIA_GP}'>AmneziaVPN из GitHub</a>.\n"
        "2️⃣ Нажмите синюю кнопку <b>«🛡 Сгенерировать мой AmneziaVPN файл (.vpn)»</b> ниже — бот вышлет ваш личный файл.\n"
        "3️⃣ Откройте приложение -> нажмите <b>«Импортировать файл конфигурации»</b> и выберите этот файл `.vpn`.\n"
        "4️⃣ Нажмите кнопку **«Подключиться»**."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛡 Сгенерировать мой AmneziaVPN файл (.vpn)", callback_data="gen_amnezia_file")],
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "info_combo_vpn")
async def cb_info_combo_vpn(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_h_link = get_user_hysteria_link(call.from_user.id)
    text = (
        "<b>⚙️ НАСТРОЙКИ NekoBox / v2rayNG + AmneziaVPN:</b>\n\n"
        f"<b>Шаг 1: Добавление вашего ключа Hysteria 2 в NekoBox / v2rayNG</b> (<a href='{URL_ANDROID_NEKOBOX_GH}'>Скачать NekoBox / v2rayNG GitHub</a>)\n"
        "• Скопируйте ваш ключ ниже и нажмите **«+» -> Импорт из буфера**:\n"
        f"<code>{user_h_link}</code>\n\n"
        "<b>Шаг 2: Настройки приложения NekoBox / v2rayNG:</b>\n"
        "⚙️ <b>Параметры приложения:</b>\n"
        "• Сервисный режим: <b>Только прокси</b>\n"
        "• Реализация TUN: <code>gVisor</code> | MTU: <code>1280</code>\n\n"
        "🌐 <b>Настройки маршрута:</b>\n"
        "• Обход LAN & Обход LAN в ядре: <b>Включено (ON)</b>\n"
        "• Маршрут IPv6: <b>Отключить</b>\n\n"
        "🔒 <b>Настройки DNS:</b>\n"
        "• Удаленный DNS: <code>https://jzargo.com/dns-query</code>\n"
        "• Правила доменов (Удаленный, Прямой, Сервер): <code>ipv4_only</code>\n"
        "• Прямой DNS: <code>1.1.1.1</code> | DNS маршрутизация & FakeDNS: <b>ON</b>\n\n"
        "<b>Шаг 3: Добавление прокси SOCKS5 в Telegram</b>\n"
        "• Включите NekoBox / v2rayNG.\n"
        "• В Telegram откройте <i>Настройки -> Данные и память -> Настройки прокси -> Добавить прокси -> SOCKS5</i>:\n"
        "  • Сервер: <code>127.0.0.1</code> | Порт: <code>2080</code>\n"
        "• <i>ИЛИ нажмите кнопку ниже «🔗 Добавить SOCKS5 в Telegram»!</i>\n\n"
        f"<b>Шаг 4: Настройка AmneziaVPN (Раздельное туннелирование)</b> (<a href='{URL_ANDROID_AMNEZIA_GP}'>Скачать GitHub</a>)\n"
        "• Нажмите синюю кнопку ниже для генерации <code>.vpn</code> файла.\n\n"
        "📱 <b>1. Разделение по ПРИЛОЖЕНИЯМ (Рекомендуется):</b>\n"
        "• В AmneziaVPN откройте <i>Раздельное туннелирование -> Приложения</i> -> выберите <b>«Исключить выбранные приложения»</b>.\n"
        "• Отметьте галочками приложения, которые <b>НЕ ДОЛЖНЫ работать через VPN</b> (Сбербанк, Тинькофф, ВТБ, Госуслуги, Яндекс + приложения Telegram и NekoBox / v2rayNG).\n\n"
        "🌐 <b>2. Разделение по САЙТАМ (Для браузеров):</b>\n"
        "• По умолчанию в браузере <b>абсолютно ВСЕ сайты идут через VPN</b>.\n"
        "• Если вы хотите, чтобы отдельные сайты <b>НЕ РАБОТАЛИ через VPN</b> (открывались напрямую без VPN): откройте <i>Раздельное туннелирование -> Сайты</i> и вручную добавьте домены сайтов, которые <b>НЕ ДОЛЖНЫ работать через VPN</b>."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Подключить MTProto Прокси в ТГ в 1 клик", url="https://t.me/proxy?server=178.17.52.67&port=1443&secret=eed0d6e111bada5511fcce9584deadbeef73332e616d617a6f6e6177732e636f6d")],
        [InlineKeyboardButton(text="🔗 Добавить SOCKS5 прокси в Telegram (127.0.0.1:2080)", url="https://t.me/socks?server=127.0.0.1&port=2080")],
        [InlineKeyboardButton(text="🛡 Сгенерировать мой AmneziaVPN файл (.vpn)", callback_data="gen_amnezia_file")],
        [InlineKeyboardButton(text="🔑 Скопировать мой ключ Hysteria 2 (NekoBox / v2rayNG)", callback_data="send_key")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору Android", callback_data="menu_android")]
    ])
    await safe_reply(call, text, reply_markup=kb, disable_web_page_preview=True)

@dp.callback_query(F.data == "gen_amnezia_file")
async def cb_gen_amnezia_file(call: CallbackQuery):
    user_id = call.from_user.id
    user_status_info = get_user_status(user_id)
    status = user_status_info[0] if user_status_info else 'approved'
    
    if status != 'approved' and not is_admin(user_id):
        await call.answer("Ваш доступ временно приостановлен или не одобрен", show_alert=True)
        return

    try:
        await call.answer("Генерация персонального файла AmneziaVPN (.vpn)...", show_alert=False)
    except Exception:
        pass
    
    try:
        priv_key, pub_key, client_ip = ensure_user_amnezia_peer(user_id)
        file_name = "ZirginsVPN.vpn"
        local_path = f"/tmp/{file_name}"

        vpn_payload = encode_amnezia_vpn_file(priv_key, pub_key, client_ip)
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(vpn_payload)

        doc = FSInputFile(local_path, filename=file_name)
        text = (
            f"<b>🛡 Ваш персональный файл конфигурации AmneziaVPN ({file_name}):</b>\n\n"
            f"1. Скачайте <a href='{URL_ANDROID_AMNEZIA_GP}'>AmneziaVPN из GitHub</a>.\n"
            "2. Выберите <b>«Импортировать файл конфигурации»</b> и укажите файл `ZirginsVPN.vpn`.\n"
            "3. Внутри зашит ваш персональный ключ, защитный MTU 1280 и быстрейший DNS (`1.1.1.1`)!"
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(doc, caption=text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await call.message.answer(f"⚠️ Ошибка при генерации файла: {e}")

async def send_platform_change_warning(call: CallbackQuery, target_platform: str):
    platform_names = {
        "ios": "iPhone / iPad (iOS)",
        "android": "Android",
        "pc": "ПК / Компьютер"
    }
    user_id = call.from_user.id
    curr_plat = get_user_primary_platform(user_id)
    curr_name = platform_names.get(curr_plat, "другую платформу")
    target_name = platform_names.get(target_platform, "выбранную платформу")
    main_name = get_user_main_device_name(user_id)

    text = (
        "⚠️ <b>Предупреждение перед перевыдачей конфигурации!</b>\n\n"
        f"Ваше <b>«{main_name}»</b> (Основное устройство №1) изначально настраивалось под <b>{curr_name}</b>.\n\n"
        f"Вы сейчас запрашиваете конфигурацию под <b>{target_name}</b>.\n\n"
        "❗️ <b>Внимание:</b>\n"
        f"• Нажатие «Да, перезаписать» изменит настройки вашего устройства <b>«{main_name}»</b>.\n"
        "• Если вам нужно подключить <u>второе независимое устройство</u> (чтобы одновременно работали и первое устройство, и второе) — нажмите кнопку <b>«➕ Создать ещё устройство»</b> ниже!\n\n"
        "Вы уверены?"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, перезаписать №1", callback_data=f"confirm_plat_{target_platform}")],
        [InlineKeyboardButton(text="➕ Создать ещё устройство (+1)", callback_data="add_extra_device")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ])

    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("confirm_plat_"), StateFilter("*"))
async def cb_confirm_platform_change(call: CallbackQuery):
    try:
        await call.answer("Тип устройства успешно изменен!")
    except Exception:
        pass
    target_platform = call.data.replace("confirm_plat_", "")
    user_id = call.from_user.id
    set_user_primary_platform(user_id, target_platform)
    if target_platform == "android":
        await render_android_menu(call)
    elif target_platform == "ios":
        await render_ios_menu(call)
    elif target_platform == "pc":
        await render_pc_menu(call)

@dp.callback_query(F.data == "info_pc", StateFilter("*"))
async def cb_info_pc(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    user_id = call.from_user.id
    curr_plat = get_user_primary_platform(user_id)
    if curr_plat and curr_plat != 'pc' and not call.data.endswith("_force"):
        await send_platform_change_warning(call, 'pc')
        return

    set_user_primary_platform(user_id, 'pc')
    await render_pc_menu(call)


@dp.callback_query(F.data == "send_apk_nekobox", StateFilter("*"))
async def cb_send_apk_nekobox(call: CallbackQuery):
    try:
        await call.answer("Отправка NekoBox / v2rayNG.apk файлом в чат...")
    except Exception:
        pass
    apk_path = "/opt/vps-bot/apks/NekoBox / v2rayNG.apk"
    if os.path.exists(apk_path):
        doc = FSInputFile(apk_path, filename="NekoBox / v2rayNG_v1.4.2_arm64.apk")
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(
            doc,
            caption="<b>📱 Установочный файл NekoBox / v2rayNG для Android:</b>\n\n1. Нажмите на файл выше прямо в чате Telegram.\n2. Нажмите <b>«Установить»</b>.",
            reply_markup=kb_file,
            parse_mode="HTML"
        )
    else:
        await call.answer("Файл временно недоступен", show_alert=True)

@dp.callback_query(F.data == "send_apk_v2rayng", StateFilter("*"))
async def cb_send_apk_v2rayng(call: CallbackQuery):
    try:
        await call.answer("Отправка v2rayNG.apk файлом в чат...")
    except Exception:
        pass
    apk_path = "/opt/vps-bot/apks/v2rayNG.apk"
    if os.path.exists(apk_path):
        doc = FSInputFile(apk_path, filename="v2rayNG_v2.2.6_arm64.apk")
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(
            doc,
            caption="<b>📱 Установочный файл v2rayNG для Android:</b>\n\n1. Нажмите на файл выше прямо в чате Telegram.\n2. Нажмите <b>«Установить»</b>.",
            reply_markup=kb_file,
            parse_mode="HTML"
        )
    else:
        await call.answer("Файл временно недоступен", show_alert=True)




@dp.callback_query(F.data == "send_exe_clash", StateFilter("*"))
async def cb_send_exe_clash(call: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    try:
        await call.answer("Запрос ссылки на Clash Party...")
    except Exception:
        pass
    text = (
        "<b>💻 Скачивание Clash Party для ПК (Windows):</b>\n\n"
        "<i>Инсталлятор Clash Party (173 МБ) превышает системный лимит Telegram для ботов (50 МБ).</i>\n\n"
        f"👉 <b>Скачайте файл <code>clash-party-windows-x64-setup.exe</code> на официальной странице релизов:</b>\n"
        f"• <a href='{URL_PC_CLASH_PARTY_GH}'>Перейти на страницу релизов Clash Party (GitHub)</a>"
    )
    kb_file = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
    ])
    try:
        await call.message.delete()
    except Exception:
        pass
    try:
        await call.message.answer(text, reply_markup=kb_file, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        logging.error(f"Error in send_exe_clash: {e}")

@dp.callback_query(F.data == "send_clash_file")
async def cb_send_clash_file(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    custom_filename = "Clash_ZirginsVPN.txt"
    file_path = "/opt/vps-bot/Clash_jzargo.txt"
    
    if os.path.exists(file_path):
        doc = FSInputFile(file_path, filename=custom_filename)
        text = (
            f"<b>📄 Ваш персональный файл конфигурации ({custom_filename}):</b>\n\n"
            f"1. <a href='{URL_PC_CLASH_PARTY_GH}'>Скачать последнюю версию Clash Party с GitHub</a>.\n"
            "2. Перетащите этот файл в раздел Profiles вашего Clash-клиента.\n\n"
            "<b>⚙️ Режимы работы (System Proxy vs TUN):</b>\n"
            "• <b>System Proxy:</b> Для браузеров.\n"
            "• <b>TUN Mode (Рекомендуется 🛡):</b> Весь трафик ПК на сетевом уровне.\n\n"
            "<b>🌐 Маршрутизация (Rule / Global / Direct):</b>\n"
            "• 🔀 <b>Rule (Рекомендуется ⚡):</b> Заблокированные сайты через VPN, Сбербанк напрямую.\n"
            "• 🌍 <b>Global:</b> 100% трафика через VPN.\n"
            "• 🚫 <b>Direct:</b> Напрямую без VPN."
        )
        kb_file = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="del_file_msg_and_menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer_document(
            doc, caption=text, reply_markup=kb_file,
            parse_mode="HTML", disable_web_page_preview=True
        )
    else:
        await call.answer("Файл временно недоступен", show_alert=True)

@dp.callback_query(F.data == "info_mtproto")
async def cb_info_mtproto(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    text = (
        "<b>⚡ Telegram MTProto Прокси (Без приложений):</b>\n\n"
        "⚠️ <b>ВНИМАНИЕ:</b>\n"
        "Из-за системных блокировок ТСПУ/РКН в РФ прямое подключение MTProto может блокироваться у некоторых операторов связи (МТС, Билайн, Мегафон) без активного VPN.\n\n"
        "Если MTProto не подключается - используйте полноценный VPN в связке с прокси."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Попробовать подключить MTProto", url="https://t.me/proxy?server=178.17.52.67&port=1443&secret=eed0d6e111bada5511fcce9584deadbeef73332e616d617a6f6e6177732e636f6d")],
        [InlineKeyboardButton(text="⬅️ Назад в Меню", callback_data="main_menu")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    text = "<b>👑 Панель Администратора VPS</b>\n\nВыберите категорию для просмотра метрик или управления:"
    await safe_reply(call, text, reply_markup=get_admin_keyboard())

@dp.callback_query(F.data == "adm_stats")
async def cb_adm_stats(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    text = get_server_stats()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_stats"), InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")]])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "adm_users")
async def cb_adm_users(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    users = get_all_users()

    text = f"<b>👥 Управление пользователями ({len(users)} всего):</b>\n\n"
    kb_buttons = []

    for u in users:
        u_id, f_name, username, status, h_pass, main_name = u[0], u[1], u[2], u[3], u[4], u[5]
        devices = get_user_devices(u_id)
        dev_count = len(devices) + 1

        total_bytes, is_act, last_hs = get_user_total_traffic_and_status(u_id)

        traffic_str = format_bytes(total_bytes)
        u_tag = f"👑 [АДМИН] (@{username})" if u_id == ADMIN_ID else (f"(@{username})" if username else f"ID:{u_id}")
        st_icon = "🟢" if is_act else ("⚪" if status in ['approved', 'active'] else "🔴")

        kb_buttons.append([InlineKeyboardButton(
            text=f"{st_icon} {f_name} {u_tag} — {dev_count} устр. | 💾 {traffic_str}",
            callback_data=f"adm_u_{u_id}"
        )])

    kb_buttons.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_users")])
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")])

    await safe_reply(call, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons))

@dp.callback_query(F.data.startswith("adm_u_"))
async def cb_adm_user_detail(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, username, status, amnezia_ip, hysteria_pass, created_at FROM users WHERE user_id = ?", (target_id,))
    u_row = cur.fetchone()
    conn.close()

    if not u_row:
        await call.answer("Пользователь не найден", show_alert=True)
        return

    u_id, f_name, username, status, am_ip, h_pass, created_at = u_row
    devices = get_user_devices(target_id)
    dev_count = len(devices) + 1

    total_bytes, is_act, last_hs = get_user_total_traffic_and_status(target_id)

    traffic_str = format_bytes(total_bytes)
    u_tag = f"@{username}" if username else "без_тега"
    text = (
        f"👤 <b>Пользователь:</b> {f_name} ({u_tag})\n"
        f"🆔 <b>Telegram ID:</b> <code>{u_id}</code>\n"
        f"🟢 <b>Статус:</b> <code>{status}</code>\n"
        f"🌐 <b>IP туннеля:</b> <code>{am_ip}</code>\n"
        f"⚡ <b>Состояние:</b> {'🟢 В сети' if is_act else '⚪ Офлайн'}\n"
        f"💾 <b>Потрачено трафика:</b> <b>{traffic_str}</b>\n"
        f"📱 <b>Всего устройств:</b> {dev_count}\n"
        f"📅 <b>Дата регистрации:</b> <code>{created_at}</code>"
    )

    toggle_btn = (
        InlineKeyboardButton(text="▶️ Возобновить доступ", callback_data=f"resume_u_{target_id}")
        if status == 'paused' else
        InlineKeyboardButton(text="⏸ Приостановить доступ", callback_data=f"pause_u_{target_id}")
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать сообщение", callback_data=f"reply_u_{target_id}")],
        [InlineKeyboardButton(text="ℹ️ Диагностика IP", callback_data=f"diag_u_{target_id}")],
        [toggle_btn],
        [InlineKeyboardButton(text="🗑 Удалить пользователя", callback_data=f"del_u_{target_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="adm_users")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data.startswith("pause_u_"))
async def cb_pause_user(call: CallbackQuery):
    try:
        await call.answer("Доступ пользователя и членов семьи приостановлен!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = 'paused' WHERE user_id = ? OR family_head_id = ?", (target_id, target_id))
    conn.commit()
    conn.close()
    
    safe_sync_singbox_users()
    await cb_adm_user_detail(call)

@dp.callback_query(F.data.startswith("resume_u_"))
async def cb_resume_user(call: CallbackQuery):
    try:
        await call.answer("Доступ пользователя и членов семьи возобновлён!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE users SET status = 'approved' WHERE user_id = ? OR family_head_id = ?", (target_id, target_id))
    conn.commit()
    conn.close()
    
    safe_sync_singbox_users()
    await cb_adm_user_detail(call)

@dp.callback_query(F.data.startswith("del_u_"))
async def cb_delete_user_ask(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[2])
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    row = cur.fetchone()
    conn.close()
    
    u_name = row[0] if row and row[0] else "Пользователь"
    u_tag = f"(@{row[1]})" if row and row[1] else ""
    
    text = (
        "⚠️ <b>Предупреждение об удалении пользователя!</b>\n\n"
        f"Вы действительно хотите навсегда удалить пользователя <b>{u_name} {u_tag}</b> (<code>{target_id}</code>)?\n\n"
        "❗️ <b>Внимание:</b> Все устройства и ключи данного пользователя будут аннулированы и удалены из базы."
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить навсегда", callback_data=f"confirm_del_u_{target_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"adm_u_{target_id}")
        ]
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass

@dp.callback_query(F.data.startswith("confirm_del_u_"))
async def cb_confirm_delete_user(call: CallbackQuery):
    try:
        await call.answer("Пользователь удалён!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[3])
    
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE users SET family_head_id = NULL WHERE family_head_id = ?", (target_id,))
    cur.execute("DELETE FROM user_devices WHERE user_id = ?", (target_id,))
    cur.execute("DELETE FROM support_tickets WHERE user_id = ?", (target_id,))
    cur.execute("DELETE FROM users WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    
    safe_sync_singbox_users()
    await cb_adm_users(call)

@dp.callback_query(F.data == "adm_conn")
async def cb_adm_conn(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return

    wg_metrics = get_wireguard_user_metrics()
    active_items = []
    for ip, data in wg_metrics.items():
        if data.get("is_active"):
            rx = format_bytes(data.get("rx_bytes", 0))
            tx = format_bytes(data.get("tx_bytes", 0))
            endpoint = data.get("endpoint", "unknown")
            active_items.append(f"• <code>{ip}</code> ({endpoint}) — ⬇️{rx} / ⬆️{tx}")

    if active_items:
        text = f"<b>🔗 Активные VPN подключения ({len(active_items)}):</b>\n\n" + "\n".join(active_items)
    else:
        text = "<b>🔗 Активные VPN подключения:</b>\n\n<i>В данный момент нет активных подключений.</i>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_conn")],
        [InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "adm_services")
async def cb_adm_services(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return

    text = (
        "<b>⚙️ Статус системных служб VPS:</b>\n\n" +
        get_service_statuses()
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_services")],
        [InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")]
    ])
    await safe_reply(call, text, reply_markup=kb)

@dp.callback_query(F.data == "adm_restart_singbox")
async def cb_adm_restart_singbox(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    out = subprocess.getoutput("systemctl restart sing-box").strip()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")]
    ])
    await safe_reply(call, "✅ Служба <b>sing-box</b> успешно перезапущена!", reply_markup=kb)


@dp.callback_query(F.data == "adm_tickets")
async def cb_adm_tickets(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("""
        SELECT t.user_id, u.first_name, u.username, COUNT(t.ticket_id) as cnt,
               MAX(t.created_at) as last_time
        FROM support_tickets t
        LEFT JOIN users u ON u.user_id = t.user_id
        WHERE t.status = 'open'
        GROUP BY t.user_id
        ORDER BY last_time DESC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")]])
        try:
            await call.message.edit_text("<b>📬 Обращения пользователей</b>\n\n<i>Нет новых обращений. Всё чисто!</i>", reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
        return

    text = "<b>📬 Обращения в Техподдержку ZirginsVPN:</b>\n\n<i>Нажмите на пользователя, чтобы прочитать его обращение и ответить:</i>"
    kb_buttons = []
    for u_id, u_name, u_user, cnt, last_time in rows:
        label = u_name or f"ID:{u_id}"
        tag = f" (@{u_user})" if u_user else ""
        kb_buttons.append([InlineKeyboardButton(
            text=f"📩 {label}{tag} — {cnt} обр.",
            callback_data=f"adm_ticket_u_{u_id}"
        )])
    kb_buttons.append([InlineKeyboardButton(text="🗑 Очистить все закрытые", callback_data="adm_tickets_close_all")])
    kb_buttons.append([InlineKeyboardButton(text="⬅️ Назад в Админку", callback_data="admin_panel")])
    try:
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_buttons), parse_mode="HTML")
    except Exception:
        pass


@dp.callback_query(F.data.startswith("adm_ticket_u_"))
async def cb_adm_ticket_user(call: CallbackQuery):
    try:
        await call.answer()
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[3])

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT first_name, username, amnezia_ip FROM users u WHERE u.user_id = ?", (target_id,))
    u_row = cur.fetchone()
    cur.execute("SELECT ticket_id, message_text, created_at, status FROM support_tickets WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (target_id,))
    tickets = cur.fetchall()
    conn.close()

    u_name = u_row[0] if u_row else f"ID:{target_id}"
    u_tag = f"(@{u_row[1]})" if u_row and u_row[1] else ""
    am_ip = u_row[2] if u_row else "None"

    wg_metrics = get_wireguard_user_metrics()
    ip_clean = (am_ip or "").replace("/32", "").strip()
    m = wg_metrics.get(ip_clean, {})
    ext_ip = m.get("endpoint", "Не определен")
    is_active = "🟢 В сети" if m.get("is_active") else "⚪ Офлайн"
    traffic_str = format_bytes(m.get("total_bytes", 0))

    text = (
        f"<b>📩 Обращения: {u_name} {u_tag}</b>\n"
        f"<code>{target_id}</code>\n\n"
        f"🌐 <b>Внешний IP:</b> <code>{ext_ip}</code>\n"
        f"🛡 <b>Туннель IP:</b> <code>{am_ip}</code>\n"
        f"💾 <b>Трафик:</b> {traffic_str} | {is_active}\n\n"
        f"<b>💬 Последние обращения:</b>\n"
    )
    for t_id, t_msg, t_time, t_status in tickets:
        icon = "🟢" if t_status == "open" else "✅"
        text += f"{icon} <i>«{t_msg[:200]}»</i>\n<code>{t_time}</code>\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить пользователю", callback_data=f"reply_u_{target_id}")],
        [InlineKeyboardButton(text="✅ Закрыть обращения", callback_data=f"adm_ticket_close_{target_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="adm_tickets")]
    ])
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass


@dp.callback_query(F.data.startswith("adm_ticket_close_"))
async def cb_adm_ticket_close(call: CallbackQuery):
    try:
        await call.answer("Обращения закрыты!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.split("_")[3])
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE support_tickets SET status = 'closed' WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await cb_adm_tickets(call)


@dp.callback_query(F.data == "adm_tickets_close_all")
async def cb_adm_tickets_close_all(call: CallbackQuery):
    try:
        await call.answer("Все закрыты!", show_alert=True)
    except Exception:
        pass
    if not is_admin(call.from_user.id):
        return
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("UPDATE support_tickets SET status = 'closed'")
    conn.commit()
    conn.close()
    await cb_adm_tickets(call)



# In-memory snapshot of last seen clash_api connection bytes (conn_id -> bytes)
# Used to avoid double-counting on same connection
_clash_last_seen: dict = {}
_max_user_traffic: dict = {}  # user_id -> highest_seen_bytes
_user_public_ips: dict = {}   # public_ip -> user_id persistent map

def parse_singbox_log_user_mappings() -> tuple[dict, dict]:
    global _user_public_ips
    ip_to_uid = dict(_user_public_ips)
    uid_last_active = {}
    try:
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        cur = conn.cursor()
        cur.execute("SELECT user_id, username, first_name FROM users")
        user_rows = cur.fetchall()
        conn.close()

        tag_to_uid = {}
        for u_id, u_name, f_name in user_rows:
            if u_name:
                tag_to_uid[f"@{u_name.lower()}"] = u_id
            if f_name:
                tag_to_uid[f"{f_name.lower()}"] = u_id
            tag_to_uid[f"id:{u_id}"] = u_id

        logs = subprocess.getoutput("journalctl -u sing-box -n 500 --no-pager --output=short-iso")
        tx_to_ip = {}
        tx_to_user = {}
        tx_to_time = {}

        for line in logs.splitlines():
            m_tx = re.search(r'\[(\d+)\s+\d+ms\]', line)
            if not m_tx:
                continue
            tx_id = m_tx.group(1)

            m_time = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
            if m_time:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(m_time.group(1))
                    tx_to_time[tx_id] = int(dt.timestamp())
                except Exception:
                    pass

            m_ip = re.search(r'inbound connection from (\d+\.\d+\.\d+\.\d+)', line)
            if m_ip:
                tx_to_ip[tx_id] = m_ip.group(1)

            m_tag = re.search(r'\[(.*?)\s*\(@?([a-zA-Z0-9_]+)\)\]', line)
            if m_tag:
                u_tag = f"@{m_tag.group(2).lower()}"
                if u_tag in tag_to_uid:
                    tx_to_user[tx_id] = tag_to_uid[u_tag]
            else:
                m_id = re.search(r'\[(?:ID:)?(\d{6,12})\]', line)
                if m_id:
                    matched_id = int(m_id.group(1))
                    if f"id:{matched_id}" in tag_to_uid:
                        tx_to_user[tx_id] = matched_id

        for tx_id, ip in tx_to_ip.items():
            if tx_id in tx_to_user:
                u_id = tx_to_user[tx_id]
                ip_to_uid[ip] = u_id
                _user_public_ips[ip] = u_id
                t_stamp = tx_to_time.get(tx_id, int(time.time()))
                if u_id not in uid_last_active or t_stamp > uid_last_active[u_id]:
                    uid_last_active[u_id] = t_stamp
    except Exception as _e:
        logging.error(f"parse_singbox_log_user_mappings error: {_e}")
    return ip_to_uid, uid_last_active

async def clash_traffic_accumulator():
    """Background task: every 30s poll clash_api and accumulate traffic per user into DB."""
    global _clash_last_seen
    import asyncio
    while True:
        try:
            sb_raw = subprocess.getoutput("curl -s http://127.0.0.1:9090/connections")
            if sb_raw and sb_raw.startswith("{"):
                sb_data = json.loads(sb_raw)

                conn_db = sqlite3.connect(DB_PATH, timeout=20.0)
                cur_db = conn_db.cursor()

                # Map WireGuard endpoints -> tunnel_ip -> user_id
                cur_db.execute("SELECT user_id, amnezia_ip FROM users WHERE amnezia_ip IS NOT NULL")
                tunnel_to_uid = {}
                for uid, am_ip in cur_db.fetchall():
                    ip_clean = (am_ip or "").replace("/32", "").strip()
                    if ip_clean:
                        tunnel_to_uid[ip_clean] = uid

                cur_db.execute("SELECT user_id, amnezia_ip FROM user_devices WHERE amnezia_ip IS NOT NULL")
                for uid, am_ip in cur_db.fetchall():
                    ip_clean = (am_ip or "").replace("/32", "").strip()
                    if ip_clean:
                        tunnel_to_uid[ip_clean] = uid

                wg_raw = subprocess.getoutput("docker exec amnezia-awg2 awg show awg0 dump")
                src_to_tunnel = {}
                for line in wg_raw.splitlines():
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        endpoint = parts[2]
                        allowed_ip = parts[3].replace("/32", "").strip()
                        ep_ip = endpoint.rsplit(":", 1)[0] if ":" in endpoint else endpoint
                        if ep_ip and ep_ip != "(none)":
                            src_to_tunnel[ep_ip] = allowed_ip

                # Parse transaction-based log mappings for iPhone Hysteria users
                ip_to_uid, _ = parse_singbox_log_user_mappings()

                # Process connections
                current_ids = set()
                uid_delta: dict = {}

                for conn2 in sb_data.get("connections", []):
                    conn_id = conn2.get("id", "")
                    meta = conn2.get("metadata", {})
                    src_ip = meta.get("sourceIP", "").strip()
                    dl = conn2.get("download", 0)
                    ul = conn2.get("upload", 0)
                    total = dl + ul

                    if not src_ip or not conn_id:
                        continue

                    current_ids.add(conn_id)

                    # Method A: Log-matched public IP (exact Hysteria user)
                    uid = ip_to_uid.get(src_ip)

                    # Method B: WireGuard endpoint -> tunnel -> user_id
                    if uid is None:
                        tunnel_ip = src_to_tunnel.get(src_ip)
                        uid = tunnel_to_uid.get(tunnel_ip) if tunnel_ip else None

                    # Method C: Direct tunnel IP match
                    if uid is None:
                        uid = tunnel_to_uid.get(src_ip)

                    if uid is None:
                        continue

                    prev = _clash_last_seen.get(conn_id, 0)
                    delta = max(0, total - prev)
                    _clash_last_seen[conn_id] = total

                    if delta > 0:
                        uid_delta[uid] = uid_delta.get(uid, 0) + delta

                # Flush to DB
                if uid_delta:
                    for uid, delta in uid_delta.items():
                        cur_db.execute(
                            "UPDATE users SET clash_traffic_bytes = COALESCE(clash_traffic_bytes, 0) + ? WHERE user_id = ?",
                            (delta, uid)
                        )
                    conn_db.commit()

                # Cleanup stale conn ids
                stale = set(_clash_last_seen.keys()) - current_ids
                for k in stale:
                    del _clash_last_seen[k]

                conn_db.close()
        except Exception as _e:
            logging.error(f"clash_traffic_accumulator error: {_e}")

        await asyncio.sleep(30)

@dp.callback_query(F.data == "send_key", StateFilter("*"))
async def cb_send_key(call: CallbackQuery, state: FSMContext):
    try:
        await state.clear()
    except Exception:
        pass
    try:
        await call.answer("Персональный ключ отправлен в чат!")
    except Exception:
        pass
    user_id = call.from_user.id
    user_h_link = get_user_hysteria_link(user_id)
    curr_plat = get_user_primary_platform(user_id)

    if curr_plat == 'android':
        apps_text = (
            "<b>📥 Приложения для Android:</b>\n"
            f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>1. Скачать NekoBox / v2rayNG для Android (GitHub)</a>\n"
            f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>2. Скачать v2rayNG для Android (GitHub)</a>\n\n"
            "💡 <i>Подсказка: Если загрузка по ссылке зависла — нажмите <b>⋮ (три точки)</b> вверху справа ➔ <b>«Открыть в браузере»</b> (Chrome/Яндекс) ИЛИ нажмите синюю кнопку ниже, чтобы получить .apk файл прямо в чат Telegram!</i>"
        )
        kb_buttons = [
            [InlineKeyboardButton(text="📦 Прислать NekoBox / v2rayNG.apk файлом в чат", callback_data="send_apk_nekobox")],
            [InlineKeyboardButton(text="📦 Прислать v2rayNG.apk файлом в чат", callback_data="send_apk_v2rayng")],
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
        ]
    elif curr_plat == 'ios':
        apps_text = (
            "<b>📥 Приложения в App Store (iOS):</b>\n"
            f"• <a href='{URL_IOS_KARING}'>Скачать Karing (Российский App Store)</a>\n"
            f"• <a href='{URL_IOS_STREISAND}'>Скачать Streisand (Иностранный App Store)</a>\n"
            f"• <a href='{URL_IOS_HAPP}'>Скачать Happ Proxy (Иностранный App Store)</a>\n"
            
        )
        kb_buttons = [[InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]]
    else:
        apps_text = (
            "<b>📥 Приложения для Android:</b>\n"
            f"• <a href='{URL_ANDROID_NEKOBOX_GH}'>1. Скачать NekoBox / v2rayNG для Android (GitHub)</a>\n"
            f"• <a href='{URL_ANDROID_V2RAYNG_GH}'>2. Скачать v2rayNG для Android (GitHub)</a>\n\n"
            "💡 <i>Подсказка для Android: Нажмите синюю кнопку ниже, чтобы получить .apk файл прямо в чат Telegram без браузера!</i>\n\n"
            "<b>📥 Приложения в App Store (iOS):</b>\n"
            f"• <a href='{URL_IOS_KARING}'>Скачать Karing (Российский App Store)</a>\n"
            f"• <a href='{URL_IOS_STREISAND}'>Скачать Streisand (Иностранный App Store)</a>\n"
            f"• <a href='{URL_IOS_HAPP}'>Скачать Happ Proxy (Иностранный App Store)</a>\n"
            
        )
        kb_buttons = [
            [InlineKeyboardButton(text="📦 Прислать NekoBox / v2rayNG.apk файлом в чат", callback_data="send_apk_nekobox")],
            [InlineKeyboardButton(text="📦 Прислать v2rayNG.apk файлом в чат", callback_data="send_apk_v2rayng")],
            [InlineKeyboardButton(text="⬅️ Назад в Главное Меню", callback_data="main_menu")]
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        f"<b>🔑 Ваш персональный ключ Hysteria 2:</b>\n\n⚠️ <i>Обратите внимание: одиночный ключ пускает 100% трафика через VPN. Для автоматического обхода Сбербанка и Госуслуг используйте <b>Способ №1 (Авто-ссылка подписки)</b>!</i>\n\n"
        f"<code>{user_h_link}</code>\n\n"
        f"{apps_text}",
        reply_markup=kb,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

def safe_sync_singbox_users():
    """Ensures all approved user passwords AND 500 pre-allocated pool slots are present in /etc/sing-box/config.json with correct name tags."""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, hysteria_pass, first_name, username FROM users WHERE status = 'approved' OR status = 'active'")
    users = cur.fetchall()
    conn.close()

    try:
        with open("/etc/sing-box/config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)

        users_list = []

        # 1. Approved / Active Users
        passwords_seen = set()

        # Always include ADMIN_HYSTERIA_PASS
        users_list.append({
            "name": "Admin_Default",
            "password": ADMIN_HYSTERIA_PASS
        })
        passwords_seen.add(ADMIN_HYSTERIA_PASS)

        for u_id, h_pass, f_name, u_name in users:
            if h_pass:
                clean_fn = (f_name or "").replace('"', '').replace('\\', '')
                clean_un = (u_name or "").replace('"', '').replace('\\', '')
                tag_name = f"{clean_fn} (@{clean_un})" if clean_un else f"{clean_fn} (ID:{u_id})"
                users_list.append({
                    "name": tag_name,
                    "password": h_pass
                })
                passwords_seen.add(h_pass)

        # 2. Pool Slots
        for i in range(1, 501):
            users_list.append({
                "name": f"slot_{i}",
                "password": f"pool_pass_slot_{i:04d}"
            })

        for inb in cfg.get("inbounds", []):
            if inb.get("type") == "hysteria2" or inb.get("tag") == "hy2-in":
                inb["users"] = users_list

        with open("/etc/sing-box/config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

        subprocess.getoutput("systemctl reload sing-box")
        logging.info("sing-box reloaded with 500+ slot pool and name tags")
    except Exception as e:
        logging.error(f"Failed to safe_sync_singbox_users: {e}")


from aiohttp import web

async def sub_http_handler(request: web.Request) -> web.Response:
    h_pass = request.match_info.get('h_pass', '').strip()
    if not h_pass:
        return web.Response(text="Invalid subscription link", status=400)

    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cur = conn.cursor()
    cur.execute("SELECT user_id, first_name, username, status, clash_traffic_bytes FROM users WHERE hysteria_pass = ?", (h_pass,))
    row = cur.fetchone()
    conn.close()

    if not row or row[3] not in ['approved', 'active']:
        return web.Response(text="Subscription inactive or not found", status=403)

    user_id = row[0]
    total_bytes = row[4] or 0
    user_info_hdr = f"upload=0; download={total_bytes}; total=1073741824000; expire=1788220800"
    user_agent = request.headers.get('User-Agent', '').lower()

    # 1. PC Clash Clients (Clash Party, Mihomo, ClashX) -> Deliver Mihomo YAML Profile
    if request.query.get('flag') == 'clash' or ('clash' in user_agent or 'mihomo' in user_agent or 'clashparty' in user_agent) and not ('nekobox' in user_agent):
        if os.path.exists('/opt/vps-bot/Clash_jzargo.txt'):
            with open('/opt/vps-bot/Clash_jzargo.txt', 'r', encoding='utf-8') as f:
                clash_content = f.read()
            clash_content = clash_content.replace('password: "cbe005fdda405a301d5d972d4442dbb3"', f'password: "{h_pass}"')
            return web.Response(
                text=clash_content,
                content_type='text/plain',
                headers={
                    'Subscription-Userinfo': user_info_hdr,
                    'profile-update-interval': '24'
                }
            )

    # 2. Universal Mobile Sing-box Profile (Karing, Streisand, NekoBox, Happ, iOS, Android)
    singbox_profile = {
        "dns": {
            "servers": [
                {"tag": "dns-remote", "type": "https", "server": "8.8.8.8", "detour": "Proxy"},
                {"tag": "dns-direct", "type": "udp", "server": "77.88.8.8"}
            ],
            "rules": [
                {"domain": ["jzargo.com"], "server": "dns-direct"},
                {
                    "domain_keyword": [
                        "yandex", "yastatic", "yamarkets", "sberbank", "sber", "gosuslugi",
                        "tbank", "tinkoff", "vtb", "alfabank", "gazprombank", "vk", "ozon", "wildberries", "avito"
                    ],
                    "server": "dns-direct"
                },
                {
                    "domain_suffix": [
                        "ru", "xn--p1ai", "su", "sberbank.com", "tinkoff-group.com", "vtb.org"
                    ],
                    "server": "dns-direct"
                },
                {"rule_set": ["geosite-ru", "geosite-bank-ru", "geosite-gov-ru"], "server": "dns-direct"},
                {"clash_mode": "Direct", "server": "dns-direct"},
                {"clash_mode": "Global", "server": "dns-remote"}
            ],
            "final": "dns-remote"
        },
        "inbounds": [
            {"type": "mixed", "tag": "mixed-in", "listen": "127.0.0.1", "listen_port": 2080},
            {"type": "tun", "tag": "tun-in", "auto_route": True, "strict_route": False, "stack": "mixed"}
        ],
        "outbounds": [
            {
                "type": "hysteria2",
                "tag": "Proxy",
                "server": "jzargo.com",
                "server_port": 50329,
                "password": h_pass,
                "tls": {"enabled": True, "server_name": "jzargo.com", "insecure": False}
            },
            {"type": "direct", "tag": "direct"}
        ],
        "route": {
            "default_domain_resolver": "dns-direct",
            "rules": [
                {
                    "domain_keyword": [
                        "yandex", "yastatic", "yamarkets", "sberbank", "sber", "gosuslugi",
                        "tbank", "tinkoff", "vtb", "alfabank", "gazprombank", "vk", "ozon", "wildberries", "avito"
                    ],
                    "outbound": "direct"
                },
                {
                    "domain_suffix": [
                        "ru", "xn--p1ai", "su", "sberbank.com", "tinkoff-group.com", "vtb.org"
                    ],
                    "outbound": "direct"
                },
                {"rule_set": ["geosite-ru", "geosite-bank-ru", "geosite-gov-ru", "geoip-ru"], "outbound": "direct"}
            ],
            "rule_set": [
                {
                    "tag": "geosite-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/lyc8503/sing-box-rules/rule-set-geosite/geosite-category-ru.srs",
                    "download_detour": "Proxy"
                },
                {
                    "tag": "geosite-bank-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/lyc8503/sing-box-rules/rule-set-geosite/geosite-category-bank-ru.srs",
                    "download_detour": "Proxy"
                },
                {
                    "tag": "geosite-gov-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/lyc8503/sing-box-rules/rule-set-geosite/geosite-category-gov-ru.srs",
                    "download_detour": "Proxy"
                },
                {
                    "tag": "geoip-ru",
                    "type": "remote",
                    "format": "binary",
                    "url": "https://raw.githubusercontent.com/lyc8503/sing-box-rules/rule-set-geoip/geoip-ru.srs",
                    "download_detour": "Proxy"
                }
            ],
            "final": "Proxy",
            "auto_detect_interface": True
        }
    }
    return web.Response(
        text=json.dumps(singbox_profile, indent=2, ensure_ascii=False),
        content_type='application/json',
        headers={
            'Subscription-Userinfo': user_info_hdr,
            'profile-update-interval': '24'
        }
    )

    # 3. Base64 Stream for NekoBox / v2rayNG / General Subscriptions
    hy2_link = get_user_hysteria_link(user_id)
    socks_link = "socks5://127.0.0.1:2080#ZirginsVPN_SOCKS5"
    sub_raw = f"{hy2_link}\n{socks_link}\n"
    sub_b64 = base64.b64encode(sub_raw.encode('utf-8')).decode('utf-8')

    return web.Response(
        text=sub_b64,
        content_type='text/plain',
        headers={
            'Subscription-Userinfo': user_info_hdr,
            'profile-update-interval': '24'
        }
    )

async def start_web_subscription_server():
    app = web.Application()
    app.router.add_get('/sub/{h_pass}', sub_http_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logging.info("Subscription HTTP server listening on http://0.0.0.0:80/sub/<pass>")

async def main():
    import asyncio
    safe_sync_singbox_users()
    asyncio.create_task(clash_traffic_accumulator())
    asyncio.create_task(start_web_subscription_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


