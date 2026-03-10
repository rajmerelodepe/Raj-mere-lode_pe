#!/usr/bin/env python3
# ===== BugTraceX VIP (No Caching - Direct API) =====
import os, subprocess, hashlib, requests, sys, json, base64, time, random, string

# ========= TOKEN DECRYPT ==========
_enc=[724, 731, 787, 668, 850, 605, 374, 535, 472, 563, 689, 682, 619, 731, 521, 374, 591, 619, 402, 570, 836, 542, 528, 822, 703, 367, 486, 731, 598, 773, 836, 801, 591, 836, 346, 591, 787, 360, 619, 458]
def _token():
    try:
        return "".join([chr((i-3)//7) for i in _enc])
    except:
        return ""

# ===== CONSTANTS =====
REPO = "bughunter11/BugTraceX-Pro"
# GitHub API use karo (no CDN caching)
API_URL = f"https://api.github.com/repos/{REPO}/contents/keys.json"
DEV = "@raj_make NAJAYD BETA OF VISHALr"
TIMEOUT = 10
RETRY = 3
OFFLINE_RUNS = 3

# Local databases
DEVICE_DB_FILE = os.path.join(os.path.expanduser("~"), ".btx_device_bindings.json")
RUNS_DB_FILE = os.path.join(os.path.expanduser("~"), ".btx_offline_runs.json")

# ===== SAFE EXIT =====
def kill(msg):
    print(msg)
    sys.exit(1)

# ===== DEVICE ID =====
def device_id():
    try:
        aid = subprocess.getoutput("settings get secure android_id 2>/dev/null").strip()
        if aid and aid.lower() != "null" and len(aid) >= 6:
            return "AID_" + hashlib.sha256(aid.encode()).hexdigest()[:12].upper()
    except:
        pass
    
    try:
        home = os.path.expanduser("~")
        seed_file = os.path.join(home, ".btx_device_seed")
        if os.path.exists(seed_file):
            with open(seed_file, "r") as f:
                seed = f.read().strip()
        else:
            seed = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
            with open(seed_file, "w") as f:
                f.write(seed)
            os.chmod(seed_file, 0o600)
        return "SEED_" + hashlib.sha256(seed.encode()).hexdigest()[:12].upper()
    except:
        return "RAND_" + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

# ===== NO-CACHE GITHUB CHECK =====
def get_latest_from_github():
    """Direct GitHub API call with NO caching"""
    for attempt in range(RETRY):
        try:
            # Method 1: Try with GitHub token first (most reliable)
            token = _token()
            headers = {
                "User-Agent": "BTX-Verifier/1.0",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
            
            if token:
                headers["Authorization"] = f"token {token}"
            
            # Add random query to prevent caching
            url = f"{API_URL}?t={int(time.time())}&r={random.randint(1000,9999)}"
            
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            
            if response.status_code == 200:
                content = response.json().get("content", "")
                if content:
                    # Decode base64 content
                    decoded = base64.b64decode(content).decode('utf-8')
                    return json.loads(decoded)
            
            # Method 2: Fallback to raw URL with aggressive no-cache
            print("  Trying fallback method...")
            raw_url = f"https://raw.githubusercontent.com/{REPO}/main/keys.json"
            raw_headers = {
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            
            raw_response = requests.get(
                f"{raw_url}?t={int(time.time())}&r={random.randint(10000,99999)}", 
                headers=raw_headers, 
                timeout=TIMEOUT
            )
            
            if raw_response.status_code == 200:
                return raw_response.json()
                
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {str(e)[:50]}")
        
        if attempt < RETRY - 1:
            time.sleep(1)  # Wait before retry
    
    return None

# ===== LOCAL DATABASES =====
def save_device_binding(key, device):
    try:
        data = {}
        if os.path.exists(DEVICE_DB_FILE):
            try:
                with open(DEVICE_DB_FILE, "r") as f:
                    data = json.load(f)
            except:
                pass
        
        data[key] = {
            "device": device,
            "activated_at": int(time.time()),
            "last_used": int(time.time())
        }
        
        with open(DEVICE_DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(DEVICE_DB_FILE, 0o600)
        return True
    except:
        return False

def get_device_binding(key):
    if not os.path.exists(DEVICE_DB_FILE):
        return None
    
    try:
        with open(DEVICE_DB_FILE, "r") as f:
            data = json.load(f)
        return data.get(key)
    except:
        return None

def save_offline_runs(key, device, runs_left):
    try:
        data = {}
        if os.path.exists(RUNS_DB_FILE):
            try:
                with open(RUNS_DB_FILE, "r") as f:
                    data = json.load(f)
            except:
                pass
        
        device_key = f"{key}_{device}"
        data[device_key] = {
            "runs_left": runs_left,
            "last_updated": int(time.time())
        }
        
        with open(RUNS_DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
        os.chmod(RUNS_DB_FILE, 0o600)
        return True
    except:
        return False

def get_offline_runs(key, device):
    if not os.path.exists(RUNS_DB_FILE):
        return None
    
    try:
        with open(RUNS_DB_FILE, "r") as f:
            data = json.load(f)
        
        device_key = f"{key}_{device}"
        entry = data.get(device_key)
        if entry:
            return entry.get("runs_left")
    except:
        pass
    return None

# ===== VERIFY =====
def verify():
    d = device_id()
    
    print("\n" + "="*50)
    print("🔐 BTX VIP LICENSE VERIFICATION")
    print("="*50)
    print(f"📱 Device ID: {d}")
    print("💬 Contact:", DEV)
    
    k = input("\n👉 Press Enter (Raj Maa Chud gi: ").strip().upper()
    
    # STEP 1: Get FRESH data from GitHub (NO CACHE)
    print("\n🔍 Fetching latest key status from GitHub...")
    
    data = get_latest_from_github()
    
    if not data:
        # Check if we have offline runs as fallback
        offline_runs = get_offline_runs(k, d)
        if offline_runs and offline_runs > 0:
            save_offline_runs(k, d, offline_runs - 1)
            print(f"\n⚠ GitHub unavailable, using cached runs")
            print(f"✅ Offline Run Allowed!")
            print(f"   Runs left: {offline_runs - 1}")
            return k
        else:
            kill("\n🌐 ERROR: Cannot connect to GitHub!\n")
    
    print("⚡ DEV MODE: VIP forced enabled RAJ VISHAL KE LAND PE")
    
    # STEP 2: Check offline runs (only if ACTIVE)
    offline_runs = get_offline_runs(k, d)
    
    if offline_runs is not None and offline_runs > 0:
        save_offline_runs(k, d, offline_runs - 1)
        print(f"\n✅ Offline Run Allowed!")
        print(f"   Runs left: {offline_runs - 1}")
        return k
    
    # STEP 3: Device verification
    device_binding = get_device_binding(k)
    
    if not device_binding:
        # First activation
        print("🔐 First Activation → Registering Device...")
        save_device_binding(k, d)
        save_offline_runs(k, d, OFFLINE_RUNS)
        print(f"✅ Device: {d[:8]}...")
        print(f"✅ Offline runs: {OFFLINE_RUNS}")
        
    else:
        # Check device
        bound_device = device_binding.get("device")
        if bound_device != d:
            kill("\n⛔ Key registered to another device!\n")
        
        # Refresh offline runs
        save_offline_runs(k, d, OFFLINE_RUNS)
        print(f"✅ Device verified: {d[:8]}...")
        print(f"✅ Offline runs reset: {OFFLINE_RUNS}")
    
    print("\n" + "="*50)
    print("🚀 VIP ACCESS GRANTED!")
    print("="*50)
    return k

# ===== MAIN =====
if __name__ == "__main__":
    try:
        verify()
        print("\nPress Enter to exit...")
        input()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        print("Please try again or contact support.")
else:
    print("\n🚫 Unauthorized import detected!")
    sys.exit(1)

# ===== BUGTRACEX TOOL START =====

#!/usr/bin/env python3
import os
import sys
import time
import socket
import threading
import requests
import urllib3
import re
import random
import shutil
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from collections import defaultdict
from ipaddress import ip_network
import tldextract
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# === Initialize Colorama ===
init(autoreset=True)
BOLD = Style.BRIGHT
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === Clear screen function ===
def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

# === Universal File Input (Termux / Termius / SSH / Linux / Windows) ===
def get_file_from_user(prompt):
    """Universal file input fix (Termux/Termius/SSH/Ubuntu/Windows)"""
    while True:
        fn = input(Fore.YELLOW + BOLD + prompt).strip().strip('"').strip("'")

        if not fn:
            print(Fore.RED + "  ⚠️ File name required!")
            continue

        # auto add .txt if not included
        if not os.path.splitext(fn)[1]:
            fn_txt = fn + ".txt"
        else:
            fn_txt = fn

        # search everywhere (current dir + home + absolute)
        search_paths = [
            fn, fn_txt,
            os.path.join(os.getcwd(), fn),
            os.path.join(os.getcwd(), fn_txt),
            os.path.join(os.path.expanduser("~"), fn),
            os.path.join(os.path.expanduser("~"), fn_txt),
        ]

        for path in search_paths:
            if os.path.isfile(path):
                return path

        print(Fore.RED + f"  ❌ File not found: {fn}")
        print(Fore.CYAN + "  🔎 Tip: Keep file in script folder or use full path.\n")

# === Banner Function ===
def banner():
    clear_screen()
    print(Fore.RED + BOLD + "  ┏━━┳┳┳━━┳━━┳━┳━━┳━┳━┳┓┏┓")
    print(Fore.YELLOW + BOLD + "  ┃┏┓┃┃┃┏━╋┓┏┫╋┃┏┓┃┏┫┳┻┓┏┛")
    print(Fore.GREEN + BOLD + "  ┃┏┓┃┃┃┗┓┃┃┃┃┓┫┣┫┃┗┫┻┳┛┗┓")
    print(Fore.CYAN + BOLD + "  ┗━━┻━┻━━┛┗┛┗┻┻┛┗┻━┻━┻┛┗┛")
    print()
    print(Fore.MAGENTA + BOLD + "  𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐑 : 𝐑𝐚𝐣_𝐌𝐚𝐤𝐞𝐫")
    print(Fore.MAGENTA + BOLD + "  𝐓𝐄𝐋𝐄𝐆𝐑𝐀𝐌 : @𝐁𝐮𝐠𝐓𝐫𝐚𝐜𝐞𝐗 NAJAYD AULAD VISHAL KII")
    print()

# === Menu Function ===
def menu():
    print(Fore.GREEN + BOLD + "  [01]  HOST SCANNER")
    print(Fore.CYAN + BOLD + "  [02]  SUBFINDER")
    print(Fore.MAGENTA + BOLD + "  [03]  COMPLETE HOST INFO")
    print(Fore.YELLOW + BOLD + "  [04]  SMART TXT SPLITTER")
    print(Fore.LIGHTBLUE_EX + BOLD + "  [05]  INTELLIGENT SUBFINDER")
    print(Fore.GREEN + BOLD + "  [06]  NETWORK CIDR SCANNER")
    print(Fore.CYAN + BOLD + "  [07]  MULTI-SOURCE REVERSE IP")
    print(Fore.MAGENTA + BOLD + "  [08]  CIDR TO DOMAIN FINDER")
    print(Fore.YELLOW + BOLD + "  [09]  SUBDOMAIN MAPPER PRO")
    print(Fore.LIGHTBLUE_EX + BOLD + "  [10]  DOMAIN CLEANER")
    print(Fore.GREEN + BOLD + "  [11]  AUTO-UPDATER")
    print(Fore.RED + BOLD + "  [00]  EXIT\n")
    print(Fore.YELLOW + BOLD + "  [--] Your Choice: ", end='')

# ===== END OF YOUR CODE (NEXT TIME FUNCTIONS ADD HERE) =====

# === Check Dependencies ===
def check_dependencies():
    """Check if required tools are installed"""
    required_tools = ['subfinder']
    missing = []
    
    for tool in required_tools:
        if shutil.which(tool) is None:
            missing.append(tool)
    
    if missing:
        print(Fore.RED + BOLD + f"❌ Missing tools: {', '.join(missing)}")
        print(Fore.YELLOW + BOLD + "Please install them before using:")
        print(Fore.CYAN + BOLD + "For subfinder: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest")
        return False
    return True

# === Common Functions ===
def is_valid_response(r):
    """Check if response is valid (not fake redirects)"""
    try:
        code = r.status_code
        loc = r.headers.get('Location', '').lower()
        
        # Skip Jio fake redirect
        if code in [302, 307] and "jio.com/balanceexhaust" in loc:
            return False
        
        return 100 <= code <= 599
    except:
        return False

def get_file_from_user(prompt="📄 Enter file name: "):
    """Reusable file input with validation"""
    while True:
        print(Fore.YELLOW + BOLD + prompt, end='', flush=True)
        fn = input().strip()
        if not fn.endswith(".txt"):
            fn += ".txt"
        
        # Check common paths
        common_paths = ["", "/data/data/com.termux/files/home/", "/sdcard/", "/sdcard/Download/", "./"]
        for path in common_paths:
            full_path = os.path.join(path, fn)
            if os.path.isfile(full_path):
                print(Fore.GREEN + BOLD + f"✅ {full_path} found!\n")
                return full_path
        
        print(Fore.RED + BOLD + f"❌ File '{fn}' not found.")
        print("\033[F\033[K\033[F\033[K", end="")

def get_output_file(default_name="results"):
    """Get output file with timestamp"""
    output_file_name = input(Fore.YELLOW + BOLD + f"💾 Output file (default: {default_name}.txt): ").strip()
    if not output_file_name:
        output_file_name = default_name
    
    if output_file_name.endswith('.txt'):
        output_file_name = output_file_name[:-4]
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_file_name}_{timestamp}.txt"
    
    # Save in current directory
    if not os.path.exists(output_file):
        return output_file
    
    # If file exists, add counter
    counter = 1
    while os.path.exists(f"{output_file_name}_{timestamp}_{counter}.txt"):
        counter += 1
    return f"{output_file_name}_{timestamp}_{counter}.txt"

def print_header(title):
    """Print formatted header"""
    print("\n" + "═" * 60)
    print(Fore.CYAN + BOLD + f"  {title}")
    print("═" * 60)

def print_result(label, value, color=Fore.GREEN):
    """Print formatted result"""
    print(f"{color}  • {label:<20}: {Fore.WHITE}{value}")

def print_section(title):
    """Print section header"""
    print(f"\n{Fore.YELLOW + BOLD}  {title}")
    print(f"  {'─' * 40}")

# === Option 1: Advanced Host Scanner ===
def host_scanner():
    """Enhanced Host Scanner with better output (fixed: tight table + stable status line)"""
    print_header("🚀 ADVANCED HOST SCANNER")
    
    start_time = time.time()
    
    # Get input file
    fn = get_file_from_user("📄 Enter host file name: ").strip()
    if not fn:   # <-- FIXED INDENT HERE
        return

    # Get ports
    port_input = input(Fore.YELLOW + BOLD + "🔌 Enter port(s) (default 80): ").strip()
    if not port_input:
        port_input = "80"
        print(Fore.CYAN + "  Using default ports: 80")

    # Parse ports
    ports = []
    try:
        for p in port_input.split(','):
            p = p.strip()
            if p.isdigit():
                ports.append(int(p))
            elif '-' in p:
                try:
                    start, end = map(int, p.split('-'))
                    ports.extend(range(start, end + 1))
                except:
                    print(Fore.RED + f"  ⚠️ Invalid range: {p}")
    except:
        print(Fore.RED + "  ❌ Error parsing ports")
        ports = [80, 443]

    ports = sorted(set([p for p in ports if 1 <= p <= 65535]))
    if not ports:
        print(Fore.RED + "  ❌ No valid ports")
        return

    # Threads
    threads_input = input(Fore.YELLOW + BOLD + "⚙️  Threads (default 100): ").strip()
    threads = 100 if not threads_input.isdigit() else min(int(threads_input), 200)

    # Timeout
    timeout_input = input(Fore.YELLOW + BOLD + "⏱️  Timeout (default 3): ").strip()
    try:
        timeout = float(timeout_input) if timeout_input else 3.0
        timeout = max(0.5, min(timeout, 10))
    except:
        timeout = 3.0

    # Method
    method = input(Fore.YELLOW + BOLD + "🌐 Method [HEAD/GET] (default HEAD): ").strip().upper()
    method = method if method in ["GET", "HEAD"] else "HEAD"

    # Output file - FIXED: No timestamp added
    output_name = input(Fore.YELLOW + BOLD + "💾 Output file (default: host_scan_results.txt): ").strip()
    if not output_name:
        output_name = "host_scan_results.txt"
    elif not output_name.endswith('.txt'):
        output_name += '.txt'
    output_file = output_name  # No timestamp

    print_section("📊 SCAN CONFIGURATION")
    print_result("Input File", os.path.basename(fn))
    print_result("Ports to Scan", f"{len(ports)} ports: {', '.join(map(str, ports[:5]))}")
    print_result("Threads", threads)
    print_result("Timeout", f"{timeout}s")
    print_result("Method", method)
    print_result("Output File", output_file)

    # Read hosts
    try:
        with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
            raw_hosts = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    clean_host = re.sub(r'^https?://', '', line)
                    clean_host = re.sub(r':\d+$', '', clean_host)
                    clean_host = clean_host.strip('/')
                    if clean_host and (re.match(r'^[a-zA-Z0-9.-]+$', clean_host) or 
                                     re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', clean_host)):
                        raw_hosts.append(clean_host)

        # Remove duplicates
        unique_hosts = []
        seen = set()
        for host in raw_hosts:
            if host not in seen:
                seen.add(host)
                unique_hosts.append(host)

        if not unique_hosts:
            print(Fore.RED + "  ❌ No valid hosts found")
            return

        print_result("Hosts Loaded", f"{len(unique_hosts)} unique hosts")

    except Exception as e:
        print(Fore.RED + f"  ❌ Error reading file: {e}")
        return

    # Prepare targets
    targets = [(host, port) for host in unique_hosts for port in ports]
    total_targets = len(targets)

    if total_targets == 0:
        print(Fore.RED + "  ❌ No targets to scan")
        return

    print_result("Total Targets", f"{total_targets} ({len(unique_hosts)} hosts × {len(ports)} ports)")

    # Initialize
    live_hosts = []
    lock = threading.Lock()
    scanned_count = 0
    live_count = 0
    host_seen = set()

    # Clear screen for fresh display
    os.system('clear' if os.name == 'posix' else 'cls')

    # Print fresh header
    print_header("🚀 ADVANCED HOST SCANNER - SCANNING")
    print_section("📊 SCAN CONFIGURATION")
    print_result("Input File", os.path.basename(fn))
    print_result("Ports to Scan", f"{len(ports)} ports: {', '.join(map(str, ports[:5]))}")
    print_result("Threads", threads)
    print_result("Timeout", f"{timeout}s")
    print_result("Method", method)
    print_result("Output File", output_file)
    print_result("Hosts Loaded", f"{len(unique_hosts)} unique hosts")
    print_result("Total Targets", f"{total_targets} ({len(unique_hosts)} hosts × {len(ports)} ports)")
    print_section("🔍 SCANNING PROGRESS")
    
    # Table header (aligned exactly, colored)
    print(
        Fore.YELLOW + "\n  METHOD" +
        Fore.GREEN  + "  CODE" +
        Fore.MAGENTA+ "  SERVER            " +
        Fore.MAGENTA+ "PORT" +
        Fore.BLUE   + "  IP               " +
        Fore.WHITE  + "HOST"
    )
    print(Fore.WHITE + "  ------------------------------------------------------------")
    # No extra blank lines after header (keeps output tight)
    
    # ========== CDN/SERVER DETECTION DICTIONARY ADDED HERE ==========
    def detect_cdn_server(server_header, headers):
        """Detect CDN and server types from headers"""
        cdn_indicators = {
            'cloudflare': ['cloudflare', 'CF-', '__cf'],
            'akamai': ['akamai', 'AkamaiGHost', 'Akamai', 'EdgeCast', 'Verizon'],
            'cloudfront': ['cloudfront', 'CloudFront', 'X-Amz-Cf-', 'Amazon CloudFront'],
            'fastly': ['fastly', 'Fastly'],
            'google': ['Google', 'GSE', 'GWS', 'Google Frontend'],
            'azure': ['Microsoft', 'Azure', 'IIS', 'Windows-Azure'],
            'aws': ['AmazonS3', 'awselb', 'ELB-', 'AWS', 'Amazon'],
            'nginx': ['nginx', 'NGINX'],
            'apache': ['Apache', 'httpd', 'Apache/'],
            'litespeed': ['LiteSpeed', 'LiteSpeedTech'],
            'cdn77': ['CDN77'],
            'bunny': ['BunnyCDN', 'Bunny'],
            'keycdn': ['KeyCDN'],
            'stackpath': ['StackPath'],
            'incapsula': ['Incapsula'],
            'imperva': ['Imperva'],
            'sucuri': ['Sucuri'],
            'ovh': ['OVH'],
            'hcdn': ['HCDN'],
            'cachefly': ['CacheFly'],
            'cdnify': ['CDNify'],
            'belugacdn': ['BelugaCDN'],
            'azurecdn': ['Azure CDN'],
            'varnish': ['Varnish'],
            'squid': ['Squid'],
            'caddy': ['Caddy'],
            'openresty': ['OpenResty'],
            'tomcat': ['Tomcat', 'Apache-Coyote'],
            'nodejs': ['Node.js', 'Express'],
            'jetty': ['Jetty'],
            'lighttpd': ['lighttpd'],
            'cherokee': ['Cherokee'],
            'iis': ['IIS', 'Microsoft-IIS'],
            'gunicorn': ['gunicorn'],
            'uwsgi': ['uWSGI'],
            'php': ['PHP'],
            'rails': ['Rails', 'Phusion Passenger'],
            'g-ws': ['gws'],
            'sffe': ['sffe'],
            'netlify': ['Netlify'],
            'vercel': ['Vercel'],
            'github': ['GitHub.com'],
            'gitlab': ['GitLab'],
            'heroku': ['Heroku'],
            'digitalocean': ['DigitalOcean'],
            'linode': ['Linode'],
            'vultr': ['Vultr'],
            'alibaba': ['Aliyun', 'Alibaba'],
            'tencent': ['Tencent'],
            'baidu': ['Baidu'],
            'huawei': ['HuaweiCloud'],
            'oracle': ['Oracle'],
            'ibm': ['IBM'],
            'proxygen': ['proxygen'],
            'bolt': ['bolt'],
        }
        
        server_lower = str(server_header).lower()
        
        # Check server header first
        for cdn, indicators in cdn_indicators.items():
            for indicator in indicators:
                if indicator.lower() in server_lower:
                    return cdn
        
        # Check other headers for CDN clues
        for header_name, header_value in headers.items():
            header_lower = str(header_value).lower()
            for cdn, indicators in cdn_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in header_lower:
                        return cdn
        
        # Check X- headers specifically
        x_headers = {k: v for k, v in headers.items() if k.lower().startswith('x-')}
        for header_name, header_value in x_headers.items():
            header_lower = str(header_value).lower()
            for cdn, indicators in cdn_indicators.items():
                for indicator in indicators:
                    if indicator.lower() in header_lower:
                        return cdn
        
        return None
    # ========== END OF CDN DICTIONARY ==========
    
    # ======= NEW STABLE STATUS (exact format) =======
    def update_status():
        """Write status line like: 39.43% - 151 / 383 - 6 -"""
        if total_targets == 0:
            return
        percent = (scanned_count / total_targets) * 100
        text = f"{percent:.2f}% - {scanned_count} / {total_targets} - {live_count} - "
        # write status on its own line (fixed width to avoid wrapping)
        sys.stdout.write("\r" + text.ljust(60))
        sys.stdout.flush()
    # ======= END STATUS =======
    
    # ========= AUTO COLOR DETECTION (Option 5 mapping) =========
    def color_for_server_label(label):
        """Auto colors:
           - Cloud/CDN -> Magenta (purple-like)
           - Cloud Hosting -> Yellow
           - Web Server -> Green
           - Unknown -> Cyan
        """
        lab = (label or "").lower()
        # cloud/cdn keywords (purple)
        cloud_cdns = ["cloudflare","akamai","cloudfront","fastly","cdn77","bunny","keycdn","stackpath",
                      "incapsula","imperva","sucuri","cachefly","cdnify","belugacdn","azurecdn"]
        # cloud hosting keywords (yellow)
        cloud_hosts = ["amazon","aws","awselb","amazon", "google", "gse", "gws", "azure", "aliyun", "alibaba",
                       "tencent","digitalocean","linode","vultr","oracle","ibm","huawei"]
        # web servers (green)
        web_servers = ["nginx","openresty","apache","httpd","litespeed","tomcat","iis","caddy","varnish",
                       "squid","gunicorn","uwsgi","node.js","node","php","rails","jetty","lighttpd","cherokee"]
        
        for k in cloud_cdns:
            if k in lab:
                return Fore.MAGENTA
        for k in cloud_hosts:
            if k in lab:
                return Fore.YELLOW
        for k in web_servers:
            if k in lab:
                return Fore.GREEN
        return Fore.CYAN
    
    # Modified scan function with real-time results and CDN detection (fixed printing)
    def scan_host(host, port, method, timeout):
        nonlocal scanned_count, live_count
        
        try:
            ip = socket.gethostbyname(host)
        except:
            with lock:
                scanned_count += 1
                if scanned_count % 10 == 0 or scanned_count == total_targets:
                    update_status()
                return
        
        headers = {"User-Agent": "Mozilla/5.0", "Host": host}
        session = requests.Session()
        
        # Try protocols
        for protocol in (["https", "http"] if port in [443, 8443] else ["http", "https"]):
            url = f"{protocol}://{host}:{port}"
            try:
                if method == "HEAD":
                    r = session.head(url, headers=headers, timeout=timeout, verify=False, allow_redirects=False)
                else:
                    r = session.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=False)
                
                if is_valid_response(r):
                    with lock:
                        live_count += 1
                        scanned_count += 1
                        
                        # CDN/SERVER DETECTION USING THE ADDED DICTIONARY
                        server_header = r.headers.get('Server', '')
                        cdn_detected = detect_cdn_server(server_header, r.headers)
                        
                        # Format server display (shortened to fit table)
                        server_display = server_header[:15] if server_header else ''
                        if cdn_detected:
                            server_display = cdn_detected if len(cdn_detected) <= 15 else cdn_detected[:15]
                        
                        # Determine color for server_display using auto mapping
                        server_col = color_for_server_label(server_display)
                        
                        # Create colored result line with exact alignment
                        colored_line = (
                                Fore.YELLOW + f"{method:<6}"
                               + Fore.GREEN + f"{r.status_code:>5}"
                               + server_col + f"{server_display:>15}"
                               + Fore.MAGENTA + f"{port:>6}"
                               + Fore.BLUE + f"{ip:>18}"
                               + Fore.WHITE + f"  {host}"
                      )
                        
                        # Print result in a thread-safe way and then update status
                        # Clear status area first (if status exists), then print the colored result line.
                        sys.stdout.write("\r" + " " * 140 + "\r")
                        print(colored_line)
                        update_status()
                        
                        # Save to file (unique host:port)
                        host_key = f"{host}:{port}"
                        if host_key not in host_seen:
                            host_seen.add(host_key)
                            live_hosts.append(host)
                            with open(output_file, 'a', encoding='utf-8') as f:
                                f.write(f"{host}\n")
                        
                        return
            except Exception:
                # on any request/connection error, try next protocol or mark scanned
                continue
        
        # If we reach here, host/port didn't return valid response
        with lock:
            scanned_count += 1
            if scanned_count % 10 == 0 or scanned_count == total_targets:
                update_status()
    
    # Start scanning
    # ensure output file is cleared
    open(output_file, 'w', encoding='utf-8').close()
    
    # Initial status display
    print("\n⏳ Starting scan...")
    update_status()
    
    try:
        # Create thread pool
        threads_list = []
        
        for host, port in targets:
            # Wait if too many threads
            while threading.active_count() >= threads + 10:
                time.sleep(0.01)
            
            # Start thread
            t = threading.Thread(target=scan_host, args=(host, port, method, timeout))
            t.daemon = True
            t.start()
            threads_list.append(t)
        
        # Wait for all threads
        for t in threads_list:
            t.join(timeout=timeout + 10)
        
        # After all done, ensure status updated final time and move to new line
        update_status()
        sys.stdout.write("\n")
        
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n  ⚠️ Scan interrupted by user")
        # Save partial results
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n⚠️ SCAN INTERRUPTED AT {time.strftime('%H:%M:%S')}\n")
            f.write(f"Scanned: {scanned_count:,}/{total_targets:,} | Live: {live_count:,}\n")
    
    # Final statistics
    elapsed = time.time() - start_time
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    
    print_section("\n📈 SCAN RESULTS")
    print_result("Time Taken", f"{mins}m {secs}s")
    print_result("Targets Scanned", f"{scanned_count:,}")
    print_result("Live Hosts Found", f"{live_count:,}")
    
    if total_targets > 0:
        success_rate = (live_count / scanned_count * 100) if scanned_count > 0 else 0
        avg_speed = (scanned_count / elapsed) if elapsed > 0 else 0
        print_result("Success Rate", f"{success_rate:.1f}%")
        print_result("Avg Speed", f"{avg_speed:.1f} req/sec")
    
    print_result("Results Saved", output_file)
    
    if live_hosts:
        print_section("🏆 TOP LIVE HOSTS")
        unique_live_hosts = sorted(set(live_hosts))
        for i, host in enumerate(unique_live_hosts[:10]):
            print(f"  {i+1:2d}. {Fore.GREEN}{host}")
        if len(unique_live_hosts) > 10:
            print(f"  ... and {len(unique_live_hosts) - 10} more")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 2: Enhanced Subfinder ===
def subfinder():
    """Enhanced Subfinder with better output"""
    print_header("🔍 ENHANCED SUBFINDER")
    
    print(Fore.CYAN + "  [1] Single Domain")
    print(Fore.CYAN + "  [2] Multiple Domains from File")
    
    choice = input(Fore.YELLOW + BOLD + "  Choose option [1/2]: ").strip()
    
    if not check_dependencies():
        input(Fore.RED + "\n  ⏎ Press Enter to continue...")
        return
    
    # Get output file - USER KA INPUT HI USE HOGA
    output_file_name = input(Fore.YELLOW + BOLD + "  💾 Output file (default: subdomains.txt): ").strip()
    if not output_file_name:
        output_file_name = "subdomains.txt"
    
    # Ensure .txt extension
    if not output_file_name.endswith('.txt'):
        output_file_name += '.txt'
    
    output_file = output_file_name  # ✅ NO TIMESTAMP ADDED
    
    if choice == '1':
        domain = input(Fore.YELLOW + BOLD + "  🌐 Enter domain: ").strip()
        if not domain:
            print(Fore.RED + "  ❌ No domain entered")
            return
        
        print_section("🔍 SCANNING")
        print(f"  Scanning: {Fore.CYAN}{domain}")
        
        try:
            # Use subprocess
            result = subprocess.run(['subfinder', '-all', '-d', domain, '-silent'], 
                                   capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(Fore.RED + f"  ❌ Subfinder error: {result.stderr[:100]}")
                return
            
            subdomains = sorted(set([s.strip() for s in result.stdout.split('\n') if s.strip()]))
            count = len(subdomains)
            
            # Save results
            with open(output_file, 'w') as f:
                for sub in subdomains:
                    f.write(sub + '\n')
            
            print_section("📊 RESULTS")
            print_result("Domain", domain)
            print_result("Subdomains Found", count)
            
            # Categorize subdomains
            categories = {
                'API': [s for s in subdomains if s.startswith('api.') or 'api' in s],
                'Admin': [s for s in subdomains if 'admin' in s],
                'Mail': [s for s in subdomains if s.startswith('mail.') or 'smtp' in s or 'mx' in s],
                'Dev/Test': [s for s in subdomains if any(x in s for x in ['dev', 'test', 'staging', 'qa'])]
            }
            
            print_section("🏷️ CATEGORIES")
            for cat, subs in categories.items():
                if subs:
                    print_result(cat, f"{len(subs)} subdomains")
            
            # Show sample
            if subdomains:
                print_section("📋 SAMPLE SUBDOMAINS")
                for i, sub in enumerate(subdomains[:5]):
                    print(f"  {i+1}. {Fore.GREEN}{sub}")
                if count > 5:
                    print(f"  ... and {count - 5} more")
            
            print_result("Saved to", output_file)
            
        except subprocess.TimeoutExpired:
            print(Fore.RED + "  ⏱️ Scan timeout (5 minutes)")
        except Exception as e:
            print(Fore.RED + f"  ❌ Error: {e}")
    
    elif choice == '2':
        file_path = get_file_from_user("  📄 Enter domain list file: ")
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                domains = [line.strip() for line in f if line.strip()]
            
            if not domains:
                print(Fore.RED + "  ❌ No domains in file")
                return
            
            print_section("📊 SCAN CONFIG")
            print_result("Domains to Scan", len(domains))
            print_result("Output File", output_file)
            
            all_subdomains = set()
            scanned = 0
            found_total = 0
            
            with open(output_file, 'w') as out_f:
                for domain in domains:
                    print(f"\n  Scanning: {Fore.CYAN}{domain}")
                    
                    try:
                        result = subprocess.run(['subfinder', '-all', '-d', domain, '-silent'], 
                                               capture_output=True, text=True, timeout=180)
                        
                        if result.returncode == 0:
                            subs = [s.strip() for s in result.stdout.split('\n') if s.strip()]
                            count = len(subs)
                            found_total += count
                            all_subdomains.update(subs)
                            
                            # Save to file
                            for sub in subs:
                                out_f.write(sub + '\n')
                            
                            print(f"  ✅ Found: {Fore.GREEN}{count}{Fore.WHITE} subdomains")
                        else:
                            print(f"  ❌ Failed: {domain}")
                    
                    except subprocess.TimeoutExpired:
                        print(f"  ⏱️ Timeout: {domain}")
                    except Exception as e:
                        print(f"  ❌ Error: {domain} - {e}")
                    
                    scanned += 1
            
            print_section("📈 FINAL RESULTS")
            print_result("Domains Scanned", scanned)
            print_result("Total Subdomains", found_total)
            print_result("Unique Subdomains", len(all_subdomains))
            print_result("Saved to", output_file)
            
        except Exception as e:
            print(Fore.RED + f"  ❌ Error: {e}")
    
    else:
        print(Fore.RED + "  ❌ Invalid choice")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 3: Complete Host Info ===
def complete_host_info():
    """Enhanced Host Information - FAST & CLEAN VERSION (Unified detection, colored output)"""

    import requests, socket, re, time
    from bs4 import BeautifulSoup
    from colorama import Fore, Style

    BOLD = Style.BRIGHT

    # -------------------------------- UI HELPERS --------------------------------
    def print_header(text):
        print("\n" + "═" * 60)
        print(Fore.CYAN + BOLD + f"  {text}")
        print("═" * 60)

    def print_section(title):
        print(Fore.CYAN + "\n  " + title)
        print(Fore.CYAN + "  " + "─" * 40)

    def print_result(label, value):
        print(f"  {Fore.GREEN}{label:<15}{Fore.WHITE}: {value}")

    # ------------------ VALID RESPONSE CHECK ------------------
    def is_valid_response(r):
        """Check if response is valid (not fake redirects)"""
        try:
            code = r.status_code
            loc = r.headers.get('Location', '').lower()
            
            # Skip Jio fake redirect
            if code in [302, 307] and "jio.com/balanceexhaust" in loc:
                return False
            
            return 100 <= code <= 599
        except:
            return False

    # ------------------ Unified Detector (Server + CDN + WAF) ------------------
    def detect_server_cdn(headers, dns_name="", asn_name=""):
        try:
            h_blob = " ".join(f"{k}:{v}" for k, v in (headers or {}).items()).lower()
        except:
            h_blob = str(headers).lower() if headers else ""

        cdn_keywords = [
            ("Cloudflare", ["cloudflare", "cf-ray", "cf-cache"]),
            ("CloudFront", ["cloudfront", "x-amz-cf"]),
            ("Akamai", ["akamai"]),
            ("Fastly", ["fastly"]),
            ("Google CDN", ["gws", "google"]),
            ("Azure CDN", ["azure", "azureedge"]),
            ("StackPath", ["stackpath"]),
            ("BunnyCDN", ["bunnycdn", "b-cdn"]),
            ("KeyCDN", ["keycdn"]),
            ("CDN77", ["cdn77"]),
            ("QUIC.Cloud", ["quic.cloud", "lsws", "litespeed"]),
            ("Netlify", ["netlify"]),
            ("Vercel", ["vercel"]),
            ("Alibaba Cloud", ["alicdn", "aliyun"]),
            ("Tencent CDN", ["tencent"]),
            ("OVH", ["ovh"]),
            ("Sucuri", ["sucuri"]),
            ("Imperva", ["imperva", "incapsula"]),
            ("DDoS-Guard", ["ddos-guard"])
        ]

        cdn_found = "Not detected"
        for name, keys in cdn_keywords:
            if any(k in h_blob for k in keys):
                cdn_found = name
                break

        # Server keywords
        server_keywords = [
            ("LiteSpeed", ["litespeed", "lsws"]),
            ("Nginx", ["nginx"]),
            ("Apache", ["apache"]),
            ("Caddy", ["caddy"]),
            ("IIS", ["microsoft-iis", "iis"]),
            ("Tomcat", ["tomcat"]),
            ("OpenResty", ["openresty"]),
            ("NodeJS", ["express", "node"]),
            ("Gunicorn", ["gunicorn"]),
            ("PHP", ["php"]),
            ("Ruby (Puma)", ["puma"]),
            ("Jetty", ["jetty"]),
            ("Oracle WebLogic", ["weblogic"])
        ]

        server_found = headers.get("Server", "Not disclosed")
        for name, keys in server_keywords:
            if any(k in h_blob for k in keys):
                server_found = name
                break

        # WAF detection
        waf_keywords = [
            ("Cloudflare WAF", ["cf-ray", "cloudflare"]),
            ("Imperva WAF", ["imperva", "incapsula"]),
            ("Sucuri WAF", ["sucuri"]),
            ("Akamai WAF", ["akamai"]),
            ("FortiWeb", ["fortinet", "fortiweb"]),
            ("F5 BIG-IP", ["bigip"]),
            ("ModSecurity", ["mod_security", "modsec"])
        ]

        waf_found = "None"
        for name, keys in waf_keywords:
            if any(k in h_blob for k in keys):
                waf_found = name
                break

        return server_found, cdn_found, waf_found

    # ------------------ ISP / ASN lookup ------------------
    def isp_details(ip):
        try:
            resp = requests.get(f"https://api.iptoasn.com/v1/as/ip/{ip}", timeout=5)
            data = resp.json()
            org = data.get("as_description", "Unknown")
            isp = org.split()[0] if org else "Unknown"
            asn = data.get("as_number", "Unknown")

            # Fix Jio details
            if "JIO" in org.upper() or "RELIANCE" in org.upper():
                return "Reliance Jio", "AS55836", "Jio Infocomm Ltd"

            return isp, asn, org
        except:
            return "Unknown", "Unknown", "Unknown"

    # ======================= START =======================
    print_header("🌐 COMPLETE HOST INFO")

    host = input(Fore.YELLOW + BOLD + "  Enter Domain or IP: ").strip()
    if not host:
        print(Fore.RED + "  ❌ Host is required"); return

    host = re.sub(r'^https?://', '', host).split('/')[0].split(':')[0]

    print_section("🔍 GATHERING INFORMATION")

    # Resolve IPs
    ip_list = []
    try:
        infos = socket.getaddrinfo(host, None)
        for info in infos:
            ip = info[4][0]
            if ip not in ip_list: ip_list.append(ip)
        print_result("Resolved IPs", f"{len(ip_list)} IPs")
    except:
        print(Fore.RED + "  ❌ Could not resolve domain"); return

    for i, ip in enumerate(ip_list[:4]):
        print(f"  {i+1}. {Fore.CYAN}{ip}")
    if len(ip_list) > 4:
        print(f"  ... and {len(ip_list)-4} more")

    # Reverse DNS
    try:
        reverse_dns = socket.gethostbyaddr(ip_list[0])[0]
        print_result("Reverse DNS", reverse_dns)
    except:
        print_result("Reverse DNS", "No PTR record")

    # Browser headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5"
    }

    print("\n  Testing connection...")
    response = None
    for url in [f"https://{host}", f"http://{host}", f"https://www.{host}", f"http://www.{host}"]:
        try:
            print(f"  Trying {url}...")
            r = requests.get(url, headers=headers, timeout=6, verify=False, allow_redirects=False)  # ✅ यहाँ बदलाव: True → False
            if is_valid_response(r):
                response = r
                print(f"  ✅ Valid response: {r.status_code}")
                break
            else:
                print(Fore.YELLOW + "  ⚠️ Skipped bad redirect")
        except:
            pass

    if response is None:
        print(Fore.RED + "  ❌ No valid response received")
        return

    # Extract title
    title = "No title"
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
    except: pass

    # Print HTTP Info
    print_section("🌐 HTTP INFORMATION")
    print_result("Final URL", response.url)
    print_result("Status Code", response.status_code)
    print_result("Protocol", "HTTPS" if response.url.startswith("https") else "HTTP")
    print_result("Title", title)
    print_result("Content Length", f"{len(response.text)} chars")

    # Headers
    print_section("📋 RESPONSE HEADERS")
    for h, v in response.headers.items():
        if len(v) < 80:
            print(f"  • {h:<20}: {v}")

    # Server + CDN + WAF
    print_section("🖥️ SERVER & CDN DETECTION")
    server, cdn, waf = detect_server_cdn(response.headers)
    print_result("Server", server)
    print_result("CDN", f"[CDN] {cdn}" if cdn != "Not detected" else "Not detected")
    print_result("WAF/Proxy", waf)

    # ISP info
    if ip_list:
        isp, asn, org = isp_details(ip_list[0])
        print()
        print_result("ISP", isp)
        print_result("ASN", asn)
        print_result("Organization", org)

    # Security
    print_section("🛡️ SECURITY CHECK")
    sec = response.headers
    print((Fore.GREEN + "  ✅ HTTPS Enabled") if response.url.startswith("https") else (Fore.RED + "  ❌ No HTTPS"))
    print((Fore.GREEN + "  ✅ HSTS Enabled") if 'Strict-Transport-Security' in sec else (Fore.RED + "  ❌ No HSTS"))
    print((Fore.GREEN + "  ✅ Clickjacking Protection") if 'X-Frame-Options' in sec else (Fore.RED + "  ❌ No XFO"))
    print((Fore.GREEN + "  ✅ MIME Sniffing Protection") if 'X-Content-Type-Options' in sec else (Fore.RED + "  ❌ No MIME"))

    # Performance
    print_section("📊 PERFORMANCE")
    print_result("Response Time", f"{int(response.elapsed.total_seconds()*1000)}ms")

    # Tech
    print_section("🏗️ TECH STACK DETECTION")
    body = response.text.lower()
    tech = []
    if 'wp-' in body: tech.append("WordPress")
    if 'drupal' in body: tech.append("Drupal")
    if 'joomla' in body: tech.append("Joomla")
    if response.headers.get("X-Powered-By"): tech.append(response.headers["X-Powered-By"])
    print_result("Technologies", ", ".join(tech) if tech else "Not detected")

    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 4: Smart TXT Splitter ===
def smart_txt_splitter():
    """Enhanced TXT File Splitter"""
    print_header("✂️ SMART TXT SPLITTER")
    
    filename = get_file_from_user("  📄 Enter file to split: ")
    if not filename:
        return
    
    try:
        with open(filename, "r", encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        total_lines = len(lines)
        if total_lines == 0:
            print(Fore.RED + "  ❌ File is empty")
            return
        
        print_section("📊 FILE ANALYSIS")
        print_result("Filename", os.path.basename(filename))
        print_result("Total Lines", f"{total_lines:,}")
        
        # Get split method
        print(Fore.CYAN + "\n  Split Methods:")
        print(Fore.CYAN + "  [1] By Number of Parts")
        print(Fore.CYAN + "  [2] By Lines Per File")
        
        method = input(Fore.YELLOW + BOLD + "  Choose method [1/2]: ").strip()
        
        if method == '1':
            try:
                parts = int(input(Fore.YELLOW + BOLD + "  How many parts: ").strip())
                if parts <= 0 or parts > total_lines:
                    print(Fore.RED + f"  ❌ Must be between 1 and {total_lines}")
                    return
                
                lines_per_part = total_lines // parts
                remainder = total_lines % parts
                
            except ValueError:
                print(Fore.RED + "  ❌ Invalid number")
                return
        
        elif method == '2':
            try:
                lines_per_part = int(input(Fore.YELLOW + BOLD + "  Lines per file: ").strip())
                if lines_per_part <= 0 or lines_per_part > total_lines:
                    print(Fore.RED + f"  ❌ Must be between 1 and {total_lines}")
                    return
                
                parts = total_lines // lines_per_part
                if total_lines % lines_per_part > 0:
                    parts += 1
                remainder = total_lines % lines_per_part
                
            except ValueError:
                print(Fore.RED + "  ❌ Invalid number")
                return
        else:
            print(Fore.RED + "  ❌ Invalid choice")
            return
        
        print_section("⚙️ SPLIT CONFIGURATION")
        print_result("Total Parts", parts)
        print_result("Lines per Part", f"{lines_per_part} (approx)")
        if remainder > 0:
            print_result("Remaining Lines", f"{remainder} in last part")
        
        base_name = os.path.splitext(filename)[0]
        created_files = []
        
        index = 0
        for i in range(parts):
            extra = 1 if i < remainder else 0
            chunk = lines[index:index + lines_per_part + extra]
            
            output_file = f"{base_name}_part{i+1:03d}.txt"
            with open(output_file, "w") as f:
                f.write("\n".join(chunk))
            
            created_files.append((output_file, len(chunk)))
            index += lines_per_part + extra
        
        print_section("📁 CREATED FILES")
        for file_name, line_count in created_files:
            print(f"  ✅ {Fore.GREEN}{file_name}{Fore.WHITE} - {line_count:,} lines")
        
        print_result("Total Files", len(created_files))
        
        # Ask for cleanup
        cleanup = input(Fore.YELLOW + BOLD + "\n  🗑️ Delete original file? (y/n): ").strip().lower()
        if cleanup == 'y':
            try:
                os.remove(filename)
                print(Fore.GREEN + "  ✅ Original file deleted")
            except:
                print(Fore.RED + "  ❌ Could not delete original file")
        
    except FileNotFoundError:
        print(Fore.RED + f"  ❌ File not found: {filename}")
    except PermissionError:
        print(Fore.RED + f"  ❌ Permission denied: {filename}")
    except Exception as e:
        print(Fore.RED + f"  ❌ Error: {e}")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 5: Intelligent Subfinder ===
def intelligent_subfinder():
    """Intelligent Subfinder - FULLY WORKING"""
    print_header("🤖 INTELLIGENT SUBFINDER")
    
    if not check_dependencies():
        input(Fore.RED + "\n  ⏎ Press Enter to continue...")
        return
    
    file_path = get_file_from_user("  📄 Enter domain list file: ")
    if not file_path:
        return
    
    # Get output file
    output_file = input(Fore.YELLOW + BOLD + "  💾 Output file (default: results.txt): " + Fore.WHITE).strip()
    
    if not output_file:
        output_file = "results.txt"
    elif not output_file.endswith('.txt'):
        output_file += ".txt"
    
    try:
        with open(file_path, 'r') as f:
            raw_domains = [line.strip() for line in f if line.strip()]
        
        # Extract root domains
        root_domains = []
        for domain in raw_domains:
            extracted = tldextract.extract(domain)
            if extracted.top_domain_under_public_suffix:
                root_domains.append(extracted.top_domain_under_public_suffix)
        
        root_domains = list(set(root_domains))
        
        print_section("📊 INPUT ANALYSIS")
        print_result("Total Domains", len(raw_domains))
        print_result("Unique Roots", len(root_domains))
        
        if not root_domains:
            print(Fore.RED + "  ❌ No valid domains found")
            return
        
        # Ask user which method to use
        print(Fore.YELLOW + BOLD + "  ⚙️  Select scan method:" + Fore.WHITE)
        print(Fore.CYAN + "  1. Fast Mode (single command, may miss some)")
        print(Fore.CYAN + "  2. Deep Mode (domain-by-domain, slower but thorough)")
        print(Fore.YELLOW + BOLD + "  Choice (1/2): " + Fore.WHITE, end="")
        
        method = input().strip()
        
        print_section("🔍 SCANNING STARTED")
        print(f"  💾 Output file: {output_file}")
        print()
        
        all_subs = []
        successful = 0
        failed = 0
        
        # METHOD 1: FAST MODE (single command)
        if method == "1":
            print(f"  ⚡ Using FAST MODE (single command)")
            
            # Create temp file with all domains
            temp_file = "temp_domains.txt"
            with open(temp_file, 'w') as f:
                f.write("\n".join(root_domains))
            
            start_time = time.time()
            
            # Run subfinder with -all flag for better results
            cmd = [
                'subfinder',
                '-dL', temp_file,
                '-o', output_file,
                '-all',           # Use all sources
                '-silent'         # Quiet mode
            ]
            
            print(f"  🚀 Running: subfinder -all -dL [temp_file] -o {output_file}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            end_time = time.time()
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # Read results
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    all_subs = [line.strip() for line in f if line.strip()]
                
                # Count successful domains by checking output
                domain_sub_counts = {}
                for sub in all_subs:
                    try:
                        extracted = tldextract.extract(sub)
                        if extracted.top_domain_under_public_suffix:
                            domain = extracted.top_domain_under_public_suffix
                            domain_sub_counts[domain] = domain_sub_counts.get(domain, 0) + 1
                    except:
                        pass
                
                successful = len([d for d in root_domains if d in domain_sub_counts])
                failed = len(root_domains) - successful
        
        # METHOD 2: DEEP MODE (domain-by-domain)
        else:
            print(f"  🕵️ Using DEEP MODE (domain-by-domain)")
            
            # Create/clear output file
            with open(output_file, 'w') as f:
                f.write("")
            
            start_time = time.time()
            
            for i, domain in enumerate(root_domains, 1):
                # Display progress
                domain_display = domain[:30] + "..." if len(domain) > 33 else domain
                print(f"  [{i:03d}/{len(root_domains)}] {domain_display:<36}", end="", flush=True)
                
                try:
                    # Run subfinder with timeout
                    result = subprocess.run(
                        ['subfinder', '-d', domain, '-silent'],
                        capture_output=True,
                        text=True,
                        timeout=15  # 15 seconds per domain
                    )
                    
                    # Check if we got results
                    if result.returncode == 0 and result.stdout.strip():
                        subs = [s.strip() for s in result.stdout.split('\n') if s.strip()]
                        
                        if subs:
                            # Append to main file
                            with open(output_file, 'a') as f:
                                for sub in subs:
                                    f.write(sub + '\n')
                            
                            all_subs.extend(subs)
                            successful += 1
                            print(f"{Fore.GREEN}✅ {len(subs):3d} subs{Fore.WHITE}")
                        else:
                            failed += 1
                            print(f"{Fore.YELLOW}⚠️  0 subs{Fore.WHITE}")
                    
                    else:
                        # Try without -silent flag
                        result2 = subprocess.run(
                            ['subfinder', '-d', domain],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        
                        if result2.stdout.strip():
                            subs = [s.strip() for s in result2.stdout.split('\n') if s.strip() and '[' not in s]
                            if subs:
                                with open(output_file, 'a') as f:
                                    for sub in subs:
                                        f.write(sub + '\n')
                                all_subs.extend(subs)
                                successful += 1
                                print(f"{Fore.GREEN}✅ {len(subs):3d} subs{Fore.WHITE}")
                            else:
                                failed += 1
                                print(f"{Fore.YELLOW}⚠️  0 subs{Fore.WHITE}")
                        else:
                            failed += 1
                            print(f"{Fore.RED}❌ failed{Fore.WHITE}")
                            
                except subprocess.TimeoutExpired:
                    failed += 1
                    print(f"{Fore.YELLOW}⏱️ timeout{Fore.WHITE}")
                except Exception as e:
                    failed += 1
                    print(f"{Fore.RED}❌ error{Fore.WHITE}")
            
            end_time = time.time()
        
        # FINAL PROCESSING
        scan_time = end_time - start_time
        
        print()
        print_section("✅ SCAN COMPLETED")
        print_result("Time", f"{scan_time:.1f} seconds")
        print_result("Successful", successful)
        print_result("Failed", failed)
        print_result("Success Rate", f"{(successful/len(root_domains)*100):.1f}%")
        
        # Process final results
        if all_subs:
            # Remove duplicates
            unique_subs = list(set(all_subs))
            
            # Save final file with unique entries
            with open(output_file, 'w') as f:
                f.write("\n".join(sorted(unique_subs)))
            
            print_result("Total Subdomains", len(all_subs))
            print_result("Unique Subdomains", len(unique_subs))
            print_result("Output File", f"{output_file} ({len(unique_subs)} entries)")
            
            # Show TOP DOMAINS if we have results
            if unique_subs:
                # Calculate domain-wise counts
                domain_counts = {}
                for sub in unique_subs:
                    extracted = tldextract.extract(sub)
                    if extracted.top_domain_under_public_suffix:
                        domain = extracted.top_domain_under_public_suffix
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
                
                if domain_counts:
                    # Sort by count
                    sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    print_section("🏆 TOP DOMAINS")
                    top_count = min(10, len(sorted_domains))
                    
                    for i, (domain, count) in enumerate(sorted_domains[:top_count]):
                        print(f"  {i+1:2d}. {domain:<28} [{Fore.GREEN}{count:>4} subs{Fore.WHITE}]")
                    
                    if len(sorted_domains) > top_count:
                        print(f"  ... and {len(sorted_domains) - top_count} more domains")
        
        else:
            print(Fore.RED + "  ❌ No subdomains found!")
            # Delete empty output file
            if os.path.exists(output_file):
                with open(output_file, 'r') as f:
                    if not f.read().strip():
                        os.remove(output_file)
                        print(f"  Deleted empty file: {output_file}")
    
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n  ⚠️  Scan interrupted by user")
        if 'output_file' in locals() and os.path.exists(output_file):
            # Show what was collected
            with open(output_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    print(f"  Partial results saved: {output_file} ({len(lines)} subdomains)")
    
    except Exception as e:
        print(Fore.RED + f"\n  ❌ Error: {e}")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Network CIDR Scanner (Compact) FIXED ===

def network_cidr_scanner():  # DO NOT CHANGE
    """COMPACT NETWORK CIDR SCANNER - ALL FEATURES"""

    import requests, threading, time, sys, random, socket
    from ipaddress import ip_network
    from collections import defaultdict
    from colorama import Fore, Style

    BOLD = Style.BRIGHT
    requests.packages.urllib3.disable_warnings()

    # ------------------ VALID RESPONSE CHECK ------------------
    def is_valid_response(r):
        """Check if response is valid (not fake redirects)"""
        try:
            code = r.status_code
            loc = r.headers.get('Location', '').lower()
            
            # Skip Jio fake redirect
            if code in [302, 307] and "jio.com/balanceexhaust" in loc:  # Fixed pattern
                return False
            
            return 100 <= code <= 599
        except:
            return False

    # ------------------ Extended Detection Helpers ------------------
    def detect_server_type(server_header, headers, body_snippet):
        """Detect server (Apache, Nginx, LiteSpeed, OpenResty, IIS, etc.)"""
        sh = (server_header or "").lower()
        htxt = " ".join(v.lower() for v in headers.values() if v).lower()
        b = (body_snippet or "").lower()

        server_map = [
            ("apache", ["apache", "httpd"]),
            ("nginx", ["nginx"]),
            ("openresty", ["openresty"]),
            ("litespeed", ["litespeed"]),
            ("iis", ["microsoft-iis", "iis"]),
            ("gws", ["gws"]),
            ("gunicorn", ["gunicorn"]),
            ("uwsgi", ["uwsgi"]),
            ("jetty", ["jetty"]),
            ("tomcat", ["tomcat"]),
            ("nodejs", ["node", "nodejs", "express"]),
            ("caddy", ["caddy"]),
            ("varnish", ["varnish"]),
            ("golang", ["gohttp", "gost", "golang"]),
            ("openresty/nginx", ["openresty", "openresty/nginx"]),
            ("lighttpd", ["lighttpd"]),
            ("kestrel", ["kestrel"]),
            ("aws elasticloadbalancer", ["elb/", "amazon"]),
            ("cloudflare", ["cloudflare"])
        ]

        for name, keys in server_map:
            for k in keys:
                if k in sh:
                    return name.capitalize()

        heuristics = [
            ("Nginx", ["server: nginx", "x-nginx"]),
            ("Apache", ["server: apache", "apache"]),
            ("LiteSpeed", ["litespeed"]),
            ("Tomcat", ["tomcat"]),
            ("Jetty", ["jetty"]),
            ("Varnish", ["varnish"]),
            ("Caddy", ["caddy"]),
            ("Gunicorn", ["gunicorn"]),
            ("uWSGI", ["uwsgi"]),
            ("NodeJS", ["node", "express"]),
            ("GoHTTP", ["go-http-server", "golang"])
        ]
        combined = sh + " " + htxt + " " + b
        for label, keys in heuristics:
            for k in keys:
                if k in combined:
                    return label

        return server_header[:30] if server_header else "Unknown"

    def detect_cdn_full(server_header, headers, body_snippet):
        """Return best guess CDN/provider name using many header/body indicators"""
        all_text = (str(server_header) + " " + " ".join(str(v) for v in headers.values()) + " " + (body_snippet or "")).lower()

        cdn_signatures = {
            "Cloudflare": ["cloudflare", "cf-connecting-ip", "cf-ray", "cf-cache-status", "server: cloudflare"],
            "Akamai": ["akamai", "akamaiedge", "akamaitechnologies", "akamaighst", "smax-age"],
            "CloudFront": ["cloudfront", "x-amz-cf-id", "x-amz-cf-pop"],
            "Fastly": ["fastly", "x-served-by", "x-fastly-request-id"],
            "StackPath": ["stackpath", "x-edge-location", "x-akamai-"],
            "Incapsula": ["incapsula", "incap_ses", "visid_incap_"],
            "Imperva": ["imperva", "x-iinfo", "x-cdn"],
            "Sucuri": ["sucuri", "x-sucuri-id", "sucuri/cloudproxy"],
            "DDoS-Guard": ["ddos-guard", "ddosprotection"],
            "AzureCDN": ["azureedge", "cdn-azure", "microsoft-azure"],
            "Google": ["gws", "google"],
            "Edgecast": ["edgecast", "vcdn"],
            "CacheFly": ["cachefly"],
            "Alibaba": ["alicdn", "aliyun", "aegis"],
            "KeyCDN": ["keycdn"],
            "BunnyCDN": ["bunnycdn"],
            "OVH": ["ovh", "cluster", "cdn.ovh.net"],
            "Netlify": ["netlify"],
            "Vercel": ["vercel"],
            "DigitalOcean": ["digitalocean", "sfo1", "nyc3", "droplet"],
            "CDN77": ["cdn77"],
            "G-Core Labs": ["gcdn", "gcore"],
            "Tencent": ["tencent", "qcloud"],
            "Rackspace": ["rackspace"],
            "ArvanCloud": ["arvancloud"],
        }

        for name, keys in cdn_signatures.items():
            for k in keys:
                if k in all_text:
                    return name

        if "amazonaws" in all_text or "ec2" in all_text:
            return "Amazon"
        if "azure" in all_text:
            return "Azure"
        if "google" in all_text:
            return "Google"
        if "digitalocean" in all_text:
            return "DigitalOcean"
        return "Unknown"

    def detect_waf(headers, body_snippet):
        """Detect common WAFs/firewalls"""
        text = " ".join(str(v).lower() for v in headers.values() if v) + " " + (body_snippet or "").lower()

        waf_map = {
            "Cloudflare WAF": ["cloudflare", "cf-chl-bypass", "cf-ray", "sucuri_cloudproxy"],
            "Sucuri WAF": ["sucuri", "x-sucuri-id"],
            "Imperva Incapsula": ["incapsula", "x-cdn", "x-iinfo"],
            "ModSecurity": ["mod_security", "modsec", "mod_security"],
            "F5 BIG-IP ASM": ["bigip", "f5"],
            "AWS WAF": ["awswaf", "x-amzn-requestid"],
            "DenyRules": ["ddos-guard"],
            "FortiWeb": ["fortinet", "fortiweb"],
            "Cloudbric": ["cloudbric"],
            "Barracuda": ["barracuda"],
        }

        for name, keys in waf_map.items():
            for k in keys:
                if k in text:
                    return name
        return ""

    # ------------------ UI HEADER ------------------
    print("\n" + "═" * 60)
    print(Fore.CYAN + BOLD + "  🌐 NETWORK CIDR SCANNER")
    print("═" * 60)

    cidr = input(Fore.YELLOW + BOLD + "  Enter CIDR (e.g., 192.168.1.0/24): " + Fore.WHITE).strip()
    if not cidr:
        print(Fore.RED + "  ❌ CIDR required")
        input(Fore.CYAN + "\n  ⏎ Press Enter...")
        return

    try:
        network = ip_network(cidr, strict=False)
        all_ips = list(network.hosts())

        # -------- Network Info --------
        print(Fore.CYAN + "\n  NETWORK INFO")
        print(Fore.CYAN + "  " + "─" * 40)
        print(f"  {Fore.GREEN}CIDR Range    : {Fore.WHITE}{cidr}")
        print(f"  {Fore.GREEN}Total IPs     : {Fore.WHITE}{len(all_ips):,}")
        print(f"  {Fore.GREEN}First IP      : {Fore.WHITE}{all_ips[0] if all_ips else 'N/A'}")
        print(f"  {Fore.GREEN}Last IP       : {Fore.WHITE}{all_ips[-1] if all_ips else 'N/A'}")

        # -------- Ports --------
        ports_input = input(Fore.YELLOW + BOLD + "\n  Enter Ports (default 80): " + Fore.WHITE).strip()
        ports = []

        if ports_input:
            for p in ports_input.split(','):
                p = p.strip()
                if p.isdigit() and 1 <= int(p) <= 65535:
                    ports.append(int(p))
                elif '-' in p:
                    try:
                        start, end = map(int, p.split('-'))
                        if 1 <= start <= end <= 65535 and (end - start) <= 20:
                            ports.extend(range(start, end + 1))
                    except:
                        pass

        ports = sorted(set(ports or [80]))
        print(Fore.CYAN + f"  Using {len(ports)} port(s): {', '.join(map(str, ports[:5]))}" +
              ("..." if len(ports) > 5 else ""))

        # -------- Threads --------
        threads = 250
        t_input = input(Fore.YELLOW + BOLD + "  Threads (default 250): " + Fore.WHITE).strip()
        if t_input.isdigit():
            threads = max(50, min(int(t_input), 1000))

        # -------- Timeout --------
        timeout = 3.0
        t_input = input(Fore.YELLOW + BOLD + "  Timeout seconds (default 3): " + Fore.WHITE).strip()
        if t_input:
            timeout = max(1.0, min(float(t_input), 15.0))

        # -------- Method --------
        method = input(Fore.YELLOW + BOLD + "  Method [HEAD/GET] (default HEAD): " + Fore.WHITE).strip().upper()
        method = method if method in ["GET", "HEAD"] else "HEAD"

        random.shuffle(all_ips)

        # -------- Output File --------
        output_file = input(Fore.YELLOW + BOLD + "  Output file (default: cidr_scan.txt): " + Fore.WHITE).strip()
        output_file = output_file if output_file else "cidr_scan.txt"
        if not output_file.endswith('.txt'):
            output_file += ".txt"

        total_targets = len(all_ips) * len(ports)

        print(Fore.CYAN + "\n  SCAN CONFIG")
        print(Fore.CYAN + "  " + "─" * 40)
        print(f"  {Fore.GREEN}IPs to Scan   : {Fore.WHITE}{len(all_ips):,}")
        print(f"  {Fore.GREEN}Total Targets : {Fore.WHITE}{total_targets:,}")
        print(f"  {Fore.GREEN}Threads       : {Fore.WHITE}{threads}")
        print(f"  {Fore.GREEN}Method        : {Fore.WHITE}{method}")
        print(f"  {Fore.GREEN}Output        : {Fore.WHITE}{output_file}")

        # -------- Initialize --------
        live_hosts = []
        lock = threading.Lock()
        scanned_count = 0
        live_count = 0
        start_time = time.time()

        # -------- Progress Bar (Simple Style) --------
        def update_progress():
            if total_targets == 0:
                return
            percent = (scanned_count / total_targets) * 100
            sys.stdout.write(
                "\r" + Fore.CYAN +
                f"  {percent:>5.2f}% - {scanned_count:,}/{total_targets:,} - {live_count:,} -" +
                Fore.RESET
            )
            sys.stdout.flush()

        # -------- Scan Function (Fancy Option-1 Output) --------
        def scan_ip_port(ip, port):
            nonlocal scanned_count, live_count
            try:
                url = f"http://{ip}:{port}"
                headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*', 'Connection': 'close'}
                start = time.time()
                # CHANGED: allow_redirects=False करें
                r = requests.head(url, headers=headers, timeout=timeout, verify=False, allow_redirects=False) if method == "HEAD" else \
                    requests.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=False)  # ✅ यहाँ बदलाव
                response_time = (time.time() - start) * 1000

                # read small body snippet safely
                body_snippet = ""
                try:
                    body_snippet = (r.text or "")[:1500]
                except:
                    body_snippet = ""

                if is_valid_response(r):
                    server_name = detect_server_type(r.headers.get('Server', ''), r.headers, body_snippet)
                    cdn_name = detect_cdn_full(r.headers.get('Server', ''), r.headers, body_snippet)
                    waf_name = detect_waf(r.headers, body_snippet)

                    # build fancy parentheses: Apache (CDN: Cloudflare, WAF: Cloudflare WAF)
                    details = []
                    if cdn_name and cdn_name != "Unknown":
                        details.append(f"CDN: {cdn_name}")
                    if waf_name:
                        details.append(f"WAF: {waf_name}")
                    details_str = (", ".join(details)) if details else ""

                    display_info = f"{server_name}" + (f" ({details_str})" if details_str else "")

                    status = r.status_code
                    with lock:
                        live_count += 1
                        live_hosts.append({
                            'ip': ip, 'port': port, 'status': status,
                            'server': server_name, 'cdn': cdn_name, 'waf': waf_name,
                            'response_time': response_time
                        })

                        # ---- Perfect Alignment (Option-1 Fancy) ----
                        status_color = Fore.GREEN if 200 <= status < 300 else Fore.YELLOW if 300 <= status < 400 else Fore.RED
                        sys.stdout.write("\r" + " " * 100 + "\r")
                        print(f"{Fore.WHITE}{str(ip):<15} {port:<5} {status_color}{status:<4} {Fore.MAGENTA}{display_info:<40} {Fore.CYAN}{response_time:>4.0f}ms")

                        update_progress()

            except:
                pass
            finally:
                with lock:
                    scanned_count += 1
                    if scanned_count % 100 == 0 or scanned_count == total_targets:
                        update_progress()

        # -------- Start Scanning --------
        print(Fore.CYAN + "\n  SCANNING... (Ctrl+C to stop)\n")
        update_progress()

        try:
            threads_list = []
            for ip in all_ips:
                for port in ports:
                    while threading.active_count() >= threads + 5:
                        time.sleep(0.01)
                    t = threading.Thread(target=scan_ip_port, args=(str(ip), port))
                    t.daemon = True
                    t.start()
                    threads_list.append(t)

            for t in threads_list:
                t.join(timeout=timeout + 5)

        except KeyboardInterrupt:
            print(Fore.RED + "\n\n  ⚠️ Scan interrupted")

        # -------- Final Result Summary --------
        print(Fore.CYAN + "\n\n  RESULTS")
        print(Fore.CYAN + "  " + "─" * 40)
        print(f"  {Fore.WHITE}Scanned      : {Fore.GREEN}{scanned_count:,}")
        print(f"  {Fore.WHITE}Live Hosts   : {Fore.GREEN}{live_count:,}")
        elapsed = time.time() - start_time
        mins, secs = int(elapsed // 60), int(elapsed % 60)
        print(f"  {Fore.WHITE}Time Taken   : {Fore.GREEN}{mins}m {secs}s")
        print(Fore.CYAN + "\n  " + "═" * 60)

    except Exception as e:
        print(Fore.RED + f"\n  ❌ Error: {str(e)[:200]}")

    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 7: Multi-source Reverse IP (FIXED VERSION) ===
def multi_source_reverse_ip():
    """Enhanced Reverse IP Lookup"""
    print_header("🔄 MULTI-SOURCE REVERSE IP")
    
    target = input(Fore.YELLOW + BOLD + "  Enter IP or Domain: ").strip()
    if not target:
        print(Fore.RED + "  ❌ Target is required")
        return
    
    print_section("🔍 RESOLVING TARGET")
    
    # Resolve domain to IP if needed
    ip_address = target
    try:
        # FIXED: Check if input is IP address using regex
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        
        if not re.match(ip_pattern, target):
            ip_address = socket.gethostbyname(target)
            print_result("Domain", target)
            print_result("Resolved IP", ip_address)
        else:
            print_result("IP Address", ip_address)
            
            # Try reverse DNS
            try:
                hostname = socket.gethostbyaddr(ip_address)[0]
                print_result("Reverse DNS", hostname)
            except:
                print_result("Reverse DNS", "No PTR record")
    except socket.gaierror:
        print(Fore.RED + "  ❌ Could not resolve domain")
        input(Fore.CYAN + "\n  ⏎ Press Enter to continue...")
        return
    except Exception as e:
        print(Fore.RED + f"  ❌ Error during resolution: {e}")
        input(Fore.CYAN + "\n  ⏎ Press Enter to continue...")
        return
    
    # Output options
    print_section("💾 OUTPUT OPTIONS")
    save_to_file = None
    
    while True:
        choice = input(Fore.YELLOW + BOLD + "  Save results to file? (y/n): " + Fore.WHITE).strip().lower()
        if choice in ['y', 'n']:
            break
        print(Fore.RED + "  ❌ Please enter 'y' or 'n'")
    
    if choice == 'y':
        default_filename = f"reverse_ip_{ip_address.replace('.', '_')}.txt"
        filename = input(Fore.YELLOW + BOLD + f"  Enter filename (default: {default_filename}): " + Fore.WHITE).strip()
        if not filename:
            filename = default_filename
        elif not filename.endswith('.txt'):
            filename += '.txt'
        save_to_file = filename
        print(Fore.GREEN + f"  ✓ Will save to: {filename}")
    else:
        print(Fore.CYAN + "  ℹ️ Results will only be displayed on screen")
    
    print_section("🌐 FETCHING DATA")
    print("  Querying multiple sources...")
    
    domains_found = set()
    sources_used = []
    
    # ========== ALTERNATIVE WORKING METHODS ==========
    
    # Method 1: Try RapidDNS with multiple domains and direct IP
    try:
        print("  🔍 Source 1: RapidDNS (Multiple Attempts)...")
        
        rapid_urls = [
            f"https://rapiddns.io/s/{ip_address}?full=1",
            f"https://rapiddns.co/s/{ip_address}?full=1",
            f"http://rapiddns.io/s/{ip_address}?full=1",  # Try HTTP
            f"https://www.rapiddns.io/s/{ip_address}?full=1"
        ]
        
        success = False
        for url in rapid_urls:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Multiple table selectors
                    table_selectors = ['table#table', 'table.table', 'table']
                    for selector in table_selectors:
                        table = soup.select_one(selector)
                        if table:
                            rows = table.find_all('tr')
                            count = 0
                            for row in rows[1:]:  # Skip header
                                cols = row.find_all('td')
                                if cols:
                                    domain = cols[0].text.strip()
                                    if domain and '.' in domain and ' ' not in domain:
                                        domains_found.add(domain)
                                        count += 1
                            
                            if count > 0:
                                print(f"      ✅ Found: {Fore.GREEN}{count}{Fore.WHITE} domains via RapidDNS")
                                sources_used.append("RapidDNS")
                                success = True
                                break
                    
                    if success:
                        break
                        
            except requests.exceptions.RequestException:
                continue
        
        if not success:
            print("      ⚠️ Could not access RapidDNS")
            
    except Exception as e:
        print(f"      ❌ RapidDNS failed: {str(e)[:50]}")
    
    # Method 2: Use Web Scraping alternatives
    try:
        print("  🔍 Source 2: Web Scraping Alternatives...")
        
        # Try HackerTarget web version
        try:
            url = f"https://api.hackertarget.com/reverseiplookup/?q={ip_address}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                lines = response.text.strip().split('\n')
                count = 0
                for line in lines:
                    line = line.strip()
                    if line and 'error' not in line.lower() and ' ' not in line and '.' in line:
                        domains_found.add(line)
                        count += 1
                if count > 0:
                    print(f"      ✅ Found: {Fore.GREEN}{count}{Fore.WHITE} domains via HackerTarget")
                    sources_used.append("HackerTarget")
        except:
            pass
        
        # Try ViewDNS web version
        try:
            url = f"https://viewdns.info/reverseip/?host={ip_address}&t=1"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 1:
                            domain = cols[0].text.strip()
                            if domain and '.' in domain and domain != ip_address:
                                domains_found.add(domain)
                
                if domains_found:
                    print(f"      ✅ Found domains via ViewDNS")
                    sources_used.append("ViewDNS")
        except:
            pass
        
    except Exception as e:
        print(f"      ❌ Web scraping failed")
    
    # Method 3: DNS-Based Reverse Lookup (LOCAL - Always works)
    try:
        print("  🔍 Source 3: DNS Reverse Lookup (Local)...")
        
        # Try DNS PTR records
        try:
            hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(ip_address)
            if hostname and hostname != ip_address:
                domains_found.add(hostname)
                print(f"      ✅ Found PTR record: {hostname}")
                sources_used.append("DNSReverse")
        except socket.herror:
            print("      ⚠️ No PTR record found")
        except Exception as e:
            pass
        
        # Try common reverse DNS patterns
        reverse_patterns = [
            f"{ip_address.replace('.', '-')}.static.isp.com",
            f"{ip_address.replace('.', '-')}.dynamic.isp.com",
            f"host-{ip_address.replace('.', '-')}.isp.com",
            f"static-{ip_address.replace('.', '-')}.network.com",
            f"ip-{ip_address.replace('.', '-')}.elasticbeanstalk.com",
            f"ec2-{ip_address.replace('.', '-')}.compute.amazonaws.com"
        ]
        
        count = 0
        for pattern in reverse_patterns:
            try:
                socket.gethostbyname(pattern)
                domains_found.add(pattern)
                count += 1
            except:
                continue
        
        if count > 0:
            print(f"      ✅ Found: {Fore.GREEN}{count}{Fore.WHITE} reverse DNS patterns")
            if "DNSReverse" not in sources_used:
                sources_used.append("DNSReverse")
            
    except Exception as e:
        print(f"      ❌ DNS lookup failed")
    
    # Method 4: ASN Lookup (Using IPInfo)
    try:
        print("  🔍 Source 4: ASN/Network Information...")
        
        # Try ipinfo.io API (free tier)
        url = f"https://ipinfo.io/{ip_address}/json"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract possible domains from org/hostname
            org = data.get('org', '')
            hostname = data.get('hostname', '')
            
            if hostname:
                domains_found.add(hostname)
            
            # Try to extract domains from org field
            if org:
                # Look for domains in org field
                potential_domains = re.findall(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', org)
                for domain in potential_domains:
                    domains_found.add(domain)
            
            if hostname or org:
                print(f"      ✅ Found network info: {org[:50]}...")
                sources_used.append("IPInfo")
            else:
                print("      ⚠️ No network info found")
                
    except Exception as e:
        print(f"      ❌ ASN lookup failed")
    
    # Method 5: Local Reverse IP using nslookup/dig simulation
    try:
        print("  🔍 Source 5: Local Reverse IP Simulation...")
        
        # Try to find domains sharing IP using common techniques
        possible_domains = set()
        
        # Check if it's a common CDN/service IP
        cdn_patterns = {
            'cloudflare': ['cloudflare.com'],
            'aws': ['amazonaws.com', 'aws.com'],
            'google': ['google.com', 'googleusercontent.com'],
            'azure': ['azure.com', 'microsoft.com'],
            'akamai': ['akamai.net', 'akamaiedge.net']
        }
        
        for service, domains in cdn_patterns.items():
            for domain in domains:
                try:
                    # Check if this domain resolves to our IP
                    resolved_ip = socket.gethostbyname(domain)
                    if resolved_ip == ip_address:
                        possible_domains.add(domain)
                except:
                    continue
        
        if possible_domains:
            for domain in possible_domains:
                domains_found.add(domain)
            print(f"      ✅ Found: {Fore.GREEN}{len(possible_domains)}{Fore.WHITE} CDN/service domains")
            sources_used.append("CDNCheck")
        else:
            print("      ⚠️ No CDN patterns matched")
            
    except Exception as e:
        print(f"      ❌ Local simulation failed")
    
    # Convert to sorted list
    domains_list = sorted(list(domains_found))
    
    print_section("📊 RESULTS")
    print_result("IP Address", ip_address)
    print_result("Sources Used", ", ".join(sources_used) if sources_used else "None")
    print_result("Total Domains Found", len(domains_list))
    
    if domains_list:
        print_section("🌐 DOMAINS FOUND")
        
        # Display domains
        for i, domain in enumerate(domains_list[:15], 1):
            print(f"  {i:2}. {Fore.GREEN}{domain}{Fore.WHITE}")
        
        if len(domains_list) > 15:
            print(Fore.CYAN + f"  ... and {len(domains_list) - 15} more domains")
        
        # Save to file if user requested
        if save_to_file:
            try:
                with open(save_to_file, 'w') as f:
                    f.write(f"Reverse IP Lookup Results\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Target: {target}\n")
                    f.write(f"IP Address: {ip_address}\n")
                    f.write(f"Lookup Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Sources Used: {', '.join(sources_used)}\n")
                    f.write(f"Total Domains Found: {len(domains_list)}\n\n")
                    f.write("DOMAINS:\n")
                    f.write("-" * 60 + "\n")
                    for i, domain in enumerate(domains_list, 1):
                        f.write(f"{i:3}. {domain}\n")
                
                print_result("Saved to", save_to_file)
                
            except Exception as e:
                print(Fore.RED + f"  ❌ Error saving file: {e}")
    else:
        print(Fore.YELLOW + "  ⚠️ No domains found on this IP address")
        
        # Provide troubleshooting tips
        print(Fore.CYAN + "\n  🔧 TROUBLESHOOTING TIPS:")
        print(Fore.CYAN + "  ─────────────────────────")
        print(Fore.CYAN + "  1. Try using a VPN")
        print(Fore.CYAN + "  2. Check your internet connection")
        print(Fore.CYAN + "  3. Some IPs may not have reverse DNS entries")
        print(Fore.CYAN + "  4. Try manual tools: nslookup, dig, whois")
        print(Fore.CYAN + "  5. Some APIs may be blocked in your network")
        
        # Still save empty result if user requested
        if save_to_file:
            try:
                with open(save_to_file, 'w') as f:
                    f.write(f"Reverse IP Lookup Results\n")
                    f.write(f"{'='*60}\n\n")
                    f.write(f"Target: {target}\n")
                    f.write(f"IP Address: {ip_address}\n")
                    f.write(f"Lookup Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Sources Used: {', '.join(sources_used)}\n")
                    f.write(f"Total Domains Found: 0\n\n")
                    f.write("No domains were found on this IP address.\n")
                    f.write("\nPOSSIBLE REASONS:\n")
                    f.write("1. IP has no reverse DNS entries\n")
                    f.write("2. Network blocking API calls\n")
                    f.write("3. APIs are rate-limited\n")
                    f.write("4. Try using VPN\n")
                print(Fore.GREEN + f"  ✓ Empty results saved to: {save_to_file}")
            except Exception as e:
                print(Fore.RED + f"  ❌ Error saving file: {e}")
    
    # Additional info
    print_section("🔍 ADDITIONAL INFORMATION")
    
    # Check common services
    common_ports = [80, 443, 8080, 22, 21, 25, 3306, 3389, 53, 110, 143]
    open_ports = []
    
    print("  Checking common ports...")
    for port in common_ports[:5]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip_address, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except:
            pass
    
    if open_ports:
        print_result("Open Ports", f"{', '.join(map(str, open_ports))}")
    else:
        print_result("Open Ports", "None detected")
    
    # Show IP information
    try:
        octets = ip_address.split('.')
        ip_class = "Unknown"
        if len(octets) == 4:
            try:
                first_octet = int(octets[0])
                if 1 <= first_octet <= 126:
                    ip_class = "Class A"
                elif 128 <= first_octet <= 191:
                    ip_class = "Class B"
                elif 192 <= first_octet <= 223:
                    ip_class = "Class C"
            except:
                pass
        
        print_result("IP Class", ip_class)
        
        # Check if it's private IP
        if (ip_address.startswith('10.') or 
            (ip_address.startswith('172.') and 16 <= int(ip_address.split('.')[1]) <= 31) or 
            ip_address.startswith('192.168.')):
            print(Fore.YELLOW + "  ⚠️ This is a private IP address")
            print(Fore.YELLOW + "     Reverse IP lookup may not work for private IPs")
            
    except:
        pass
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 8: CIDR to Domain Finder ===
def cidr_to_domain_finder():
    """CIDR to Domain Finder - FIXED VERSION"""
    
    # GLOBAL IMPORTS FIX
    import warnings
    from colorama import Fore, Style, init
    init(autoreset=True)
    BOLD = Style.BRIGHT
    
    # DEFINE PRINT FUNCTIONS with EXACT COLORS YOU WANT
    def print_header(text):
        print(f"\n{Fore.MAGENTA}{BOLD}{'═'*80}")
        print(f"{Fore.MAGENTA}{BOLD}  {text}")
        print(f"{Fore.MAGENTA}{BOLD}{'═'*80}")
    
    def print_section(text):
        print(f"\n{Fore.CYAN}{BOLD}  {text}")
        print(f"  {Fore.CYAN}{'─'*40}")
    
    def print_result(key, value):
        # EXACTLY AS YOU WANT: Bullet=GREEN, Key=GREEN, Colon=WHITE, Value=WHITE
        print(f"  {Fore.GREEN}• {Fore.GREEN}{key.ljust(20)} {Fore.WHITE}: {Fore.WHITE}{value}")
    
    # SHOW HEADER
    print_header("📍 CIDR TO DOMAIN FINDER")
    
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    # Get CIDR input
    cidr = input(f"{Fore.YELLOW}{BOLD}  Enter CIDR (e.g., 192.168.0.0/24): {Fore.WHITE}").strip()
    if not cidr:
        print(f"{Fore.RED}  ❌ CIDR is required")
        return
    
    # Output file name
    output_name = input(f"{Fore.CYAN}{BOLD}💾 Output file (default: cidr_domains.txt): {Fore.WHITE}").strip()
    if not output_name:
        output_name = "cidr_domains.txt"
    if not output_name.endswith('.txt'):
        output_name += '.txt'
    
    try:
        # IMPORT OLD CODE STYLE
        import ipaddress, random, threading, time, socket
        from queue import Queue
        
        network = ipaddress.ip_network(cidr, strict=False)
        all_ips = list(network.hosts())
        
        print_section("📊 NETWORK INFO")
        print_result("CIDR Range", str(network))
        print_result("Total IPs", f"{len(all_ips):,}")
        
        # Threads input
        threads_input = input(f"{Fore.YELLOW}{BOLD}  Threads (default 100): {Fore.WHITE}").strip()
        try:
            user_threads = int(threads_input) if threads_input else 100
            if user_threads <= 0:
                user_threads = 100
        except:
            user_threads = 100
        
        print_section("⚙️ SCAN CONFIG")
        print_result("IPs to Scan", f"{len(all_ips):,}")
        print_result("Threads", user_threads)
        print_result("Output File", output_name)
        
        print_section("🔍 SCANNING CIDR RANGE")
        print(f"{Fore.WHITE}  Processing IPs...\n")
        
        # OLD CODE VARIABLES
        scanned = 0
        found = 0
        lock = threading.Lock()
        root_domains = set()
        all_domains = set()
        scan_start_time = time.time()
        
        # OLD CODE FUNCTION - EXACT COPY
        def extract_root_domain(domain):
            parts = domain.strip().split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return domain
        
        # OLD CODE WORKER - EXACT WORKING LOGIC
        def reverse_dns_worker(q):
            nonlocal scanned, found
            colors = [
                Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
                Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTWHITE_EX
            ]
            
            while True:
                ip = q.get()
                if ip is None:
                    break
                try:
                    # OLD CODE'S WORKING LOGIC
                    domain = socket.gethostbyaddr(ip)[0]
                    root = extract_root_domain(domain)
                    
                    with lock:
                        if root not in root_domains:
                            root_domains.add(root)
                            all_domains.add(domain)
                            found += 1
                            
                            # OLD CODE PRINT STYLE - Random colors
                            color = random.choice(colors)
                            print(f"{color}[-] {ip} → {domain}")
                            
                            # Save to file
                            with open(output_name, 'a') as f:
                                f.write(f"{root}\n")
                except socket.herror:
                    # No reverse DNS record
                    pass
                except Exception:
                    # Any other error
                    pass
                finally:
                    with lock:
                        scanned += 1
                    q.task_done()
        
        # START OLD CODE LOGIC
        total_ips = len(all_ips)
        ip_list = list(all_ips)
        random.shuffle(ip_list)
        
        q = Queue()
        for ip in ip_list:
            q.put(str(ip))
        
        # START WORKER THREADS
        threads = []
        for _ in range(user_threads):
            t = threading.Thread(target=reverse_dns_worker, args=(q,), daemon=True)
            t.start()
            threads.append(t)
        
        # WAIT FOR COMPLETION
        q.join()
        
        # STOP WORKERS
        for _ in threads:
            q.put(None)
        for t in threads:
            t.join()
        
        print()  # New line
        
        # FINAL RESULTS
        elapsed = time.time() - scan_start_time
        
        print_section("📈 SCAN RESULTS")
        print_result("IPs Scanned", f"{scanned:,}")
        print_result("Domains Found", f"{found:,}")
        print_result("Time Taken", f"{elapsed:.1f}s")
        
        # FINAL SAVED RESULTS SECTION - EXACTLY AS YOU WANT
        if root_domains:
            print_section("💾 SAVED RESULTS")
            # GREEN emoji + text, WHITE value
            print(f"  {Fore.GREEN}✅ File: {Fore.WHITE}{output_name}")
            print(f"  {Fore.GREEN}📄 Total Domains: {Fore.WHITE}{len(root_domains)}")
        else:
            print(f"{Fore.YELLOW}  ⚠️  No domains found")
        
    except ValueError as e:
        print(f"{Fore.RED}  ❌ Invalid CIDR format: {e}")
    except Exception as e:
        print(f"{Fore.RED}  ❌ Error: {e}")
    
    warnings.filterwarnings('default', category=DeprecationWarning)
    input(f"{Fore.CYAN}{BOLD}\n  ⏎ Press Enter to continue...")

# === Option 9: Subdomain Mapper Pro ===
def subdomain_mapper_pro():
    """Professional Subdomain Mapper"""
    print_header("🗺️ SUBDOMAIN MAPPER PRO")
    
    file_path = get_file_from_user("  📄 Enter subdomain list file: ")
    if not file_path:
        return
    
    # Pehle hi puchhe save ka option
    print("\n" + "─"*60)
    save_choice = input("💾 Save root domains to TXT file? (y/n): ").strip().lower()
    
    output_file = ""
    if save_choice == 'y':
        output_file = input("📄 Output file name (default: root_domains.txt): ").strip()
        if not output_file:
            output_file = "root_domains.txt"
        if not output_file.endswith('.txt'):
            output_file += '.txt'
        print(f"💾 Will save to: {output_file}")
    
    try:
        print_section("📊 READING FILE")
        
        subdomains = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                domain = line.strip().lower()
                if domain and '.' in domain:
                    subdomains.append(domain)
                if line_num % 10000 == 0:
                    print(f"  Read {line_num:,} lines...")
        
        print_result("Total Subdomains", f"{len(subdomains):,}")
        
        if not subdomains:
            print(Fore.RED + "  ❌ No valid subdomains found")
            return
        
        print_section("🗺️ MAPPING SUBDOMAINS")
        print("  Analyzing and categorizing...")
        
        # Create mapping - WARNINGS SUPPRESS KARNE KE LIYE
        root_domain_map = defaultdict(set)
        
        import warnings
        # Suppress tldextract warnings
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        
        for subdomain in subdomains:
            try:
                extracted = tldextract.extract(subdomain)
                
                # Check for root domain using compatible method
                root = None
                if hasattr(extracted, 'top_domain_under_public_suffix'):
                    # New version property
                    root = extracted.top_domain_under_public_suffix
                elif hasattr(extracted, 'registered_domain'):
                    # Old version property (with warning suppressed)
                    root = extracted.registered_domain
                
                if root and root != '':
                    root_domain_map[root].add(subdomain)
                    
            except Exception as e:
                # Fallback: extract manually
                try:
                    parts = subdomain.split('.')
                    if len(parts) >= 2:
                        root = '.'.join(parts[-2:])
                        if root and root != '':
                            root_domain_map[root].add(subdomain)
                except:
                    pass  # Ignore errors in fallback
        
        # Re-enable warnings if needed
        warnings.filterwarnings('default', category=DeprecationWarning)
        
        print_section("📈 MAPPING RESULTS")
        print_result("Unique Root Domains", len(root_domain_map))
        
        total_subs = sum(len(subs) for subs in root_domain_map.values())
        print_result("Total Subdomains Mapped", total_subs)
        
        # Show top domains - SIRF DOMAIN NAMES WITH COUNT
        print_section("🏆 TOP DOMAINS")
        sorted_domains = sorted(root_domain_map.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Show first 15 domains only
        display_limit = 15
        for i, (domain, subs) in enumerate(sorted_domains[:display_limit], 1):
            count = len(subs)
            print(f"  {i:2d}. {Fore.CYAN}{domain:<30}{Fore.GREEN}[{count:3} subdomains]")
        
        # Show remaining count
        if len(sorted_domains) > display_limit:
            remaining = len(sorted_domains) - display_limit
            print(f"  ... and {remaining} more domains")
            
            # Ask if user wants to see all domains
            show_all = input(f"\n  👁️  Show all {len(sorted_domains)} domains? (y/n): ").strip().lower()
            
            if show_all == 'y':
                print_section(f"📋 ALL DOMAINS ({len(sorted_domains)} total)")
                
                # Calculate columns for better display
                terminal_width = 80
                max_domain_len = max(len(domain) for domain, _ in sorted_domains)
                columns = max(1, terminal_width // (max_domain_len + 8))
                
                rows_needed = (len(sorted_domains) + columns - 1) // columns
                
                for row in range(rows_needed):
                    line = "  "
                    for col in range(columns):
                        idx = row + (col * rows_needed)
                        if idx < len(sorted_domains):
                            domain, subs = sorted_domains[idx]
                            count = len(subs)
                            line += f"{Fore.CYAN}{domain:<30}{Fore.GREEN}[{count:3}]  "
                    print(line)
        
        # SAVE LOGIC - MODIFIED
        if save_choice == 'y' and output_file:
            print_section("💾 SAVING ROOT DOMAINS")
            
            try:
                # Get all unique root domains sorted alphabetically
                all_root_domains = sorted(list(set(root_domain_map.keys())))
                
                # Save to file - SIRF DOMAINS, EK LINE PE EK
                with open(output_file, 'w', encoding='utf-8') as f:
                    for domain in all_root_domains:
                        f.write(f"{domain}\n")
                
                # Show simple save confirmation
                file_size = os.path.getsize(output_file)
                print(f"  ✅ Saved: {output_file}")
                print(f"     • Domains: {len(all_root_domains)}")
                print(f"     • Size: {file_size:,} bytes")
                
            except Exception as e:
                print(Fore.RED + f"  ❌ Error saving file: {e}")
        else:
            print(Fore.YELLOW + f"\n  ⚠️  Domains not saved (user selected 'n')")
        
    except Exception as e:
        print(Fore.RED + f"  ❌ Error: {e}")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 10: Domain Cleaner ===
def domain_cleaner():
    """Remove domains and their subdomains from a list"""
    print_header("🧹 DOMAIN CLEANER")
    
    # Get domains to remove
    domains_input = input(Fore.YELLOW + BOLD + "  Enter domains to remove (comma separated): ").strip()
    if not domains_input:
        print(Fore.RED + "  ❌ Domains are required")
        return
    
    domain_list = [d.strip().lower() for d in domains_input.split(',') if d.strip()]
    if not domain_list:
        print(Fore.RED + "  ❌ No valid domains specified")
        return
    
    print_section("🗑️ DOMAINS TO REMOVE")
    for i, domain in enumerate(domain_list, 1):
        print(f"  {i}. {Fore.RED}{domain}")
    
    # Get input file
    file_path = get_file_from_user("  📄 Enter file to clean: ")
    if not file_path:
        return
    
    try:
        print_section("📊 READING FILE")
        
        # Read all domains from file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_domains = [line.strip() for line in f if line.strip()]
        
        original_count = len(original_domains)
        print_result("Total Subdomains", f"{original_count:,}")
        
        if not original_domains:
            print(Fore.RED + "  ❌ File is empty")
            return
        
        print_section("🧹 REMOVING DOMAINS")
        print("  Filtering subdomains...")
        
        removed_count = 0
        kept_domains = []
        
        for domain in original_domains:
            if not domain:
                continue
                
            domain_lower = domain.lower()
            should_remove = False
            
            # Check if this domain or its subdomain should be removed
            for target_domain in domain_list:
                # Exact match
                if domain_lower == target_domain:
                    should_remove = True
                    break
                
                # Subdomain match (e.g., api.jio.com for jio.com)
                if domain_lower.endswith('.' + target_domain):
                    should_remove = True
                    break
            
            if should_remove:
                removed_count += 1
            else:
                kept_domains.append(domain)
        
        # Agar koi subdomain remove nahi hua to simple message dikhao
        if removed_count == 0:
            print(f"\n  {Fore.YELLOW}⚠️  No subdomains removed")
            print(f"     • No subdomains of '{', '.join(domain_list)}' found")
            print(f"     • File unchanged")
        else:
            # Write back to SAME file only if subdomains were removed
            with open(file_path, 'w', encoding='utf-8') as f:
                for domain in kept_domains:
                    f.write(f"{domain}\n")
            
            # Show results
            print_section("📈 CLEANING RESULTS")
            print_result("Original Subdomains", f"{original_count:,}")
            print_result("Removed Subdomains", f"{removed_count:,}")
            print_result("Remaining Subdomains", f"{len(kept_domains):,}")
            
            print(f"\n  ✅ Cleaned: {os.path.basename(file_path)}")
            print(f"     • Removed: {removed_count} subdomains")
            print(f"     • Updated in same file")
        
    except Exception as e:
        print(Fore.RED + f"  ❌ Error: {e}")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Option 11: Auto Updater ===
def auto_updater():
    """Enhanced Auto Updater"""
    print_header("🔄 AUTO UPDATER")
    
    print_section("🔍 CHECKING CURRENT VERSION")
    
    # Check local version
    version_file = "version.txt"
    local_version = "1.0.0"
    
    try:
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                local_version = f.read().strip()
        else:
            # Create version file if not exists
            with open(version_file, 'w') as f:
                f.write("1.0.0")
    except:
        pass
    
    print_result("Current Version", local_version)
    
    print_section("🌐 CHECKING FOR UPDATES")
    
    try:
        # Try to fetch latest version
        version_url = "https://raw.githubusercontent.com/bughunter11/BugTraceX/main/version.txt"
        response = requests.get(version_url, timeout=10)
        
        if response.status_code == 200:
            remote_version = response.text.strip()
            print_result("Latest Version", remote_version)
            
            if remote_version == local_version:
                print(Fore.GREEN + "\n  ✅ You have the latest version!")
                input(Fore.CYAN + "\n  ⏎ Press Enter to continue...")
                return
            
            print_section("📝 UPDATE AVAILABLE")
            print(Fore.YELLOW + f"  Update available: {local_version} → {remote_version}")
            
            # Fetch changelog
            try:
                changelog_url = "https://raw.githubusercontent.com/bughunter11/BugTraceX/main/changelog.txt"
                changelog_response = requests.get(changelog_url, timeout=10)
                if changelog_response.status_code == 200:
                    print_section("📋 WHAT'S NEW")
                    changelog = changelog_response.text.strip()
                    for line in changelog.split('\n')[:10]:  # Show first 10 lines
                        if line.strip():
                            print(f"  • {line}")
            except:
                print(Fore.CYAN + "  No changelog available")
            
            # Ask for update
            update = input(Fore.YELLOW + BOLD + "\n  🔄 Update now? (y/n): ").strip().lower()
            
            if update != 'y':
                print(Fore.RED + "  Update cancelled")
                input(Fore.CYAN + "\n  ⏎ Press Enter to continue...")
                return
            
            print_section("⬇️ DOWNLOADING UPDATE")
            
            # Backup current version
            backup_file = f"BugTraceX_backup_{int(time.time())}.py"
            if os.path.exists("BugTraceX.py"):
                shutil.copy2("BugTraceX.py", backup_file)
                print_result("Backup Created", backup_file)
            
            # Download new version
            script_url = "https://raw.githubusercontent.com/bughunter11/BugTraceX/main/BugTraceX.py"
            response = requests.get(script_url, timeout=30)
            
            if response.status_code == 200:
                # Save new version
                with open("BugTraceX.py", 'wb') as f:
                    f.write(response.content)
                
                # Update version file
                with open(version_file, 'w') as f:
                    f.write(remote_version)
                
                print_section("✅ UPDATE COMPLETE")
                print(Fore.GREEN + "  ✅ Tool updated successfully!")
                print(Fore.CYAN + f"  Updated from v{local_version} to v{remote_version}")
                
                # Make executable
                if os.name == 'posix':
                    os.chmod("BugTraceX.py", 0o755)
                    print(Fore.GREEN + "  ✅ Made script executable")
                
                print(Fore.YELLOW + "\n  🔄 Please restart the tool to apply changes")
                
                # Cleanup old backup
                for file in os.listdir('.'):
                    if file.startswith('BugTraceX_backup_') and file != backup_file:
                        try:
                            os.remove(file)
                        except:
                            pass
                
            else:
                print(Fore.RED + f"  ❌ Download failed: HTTP {response.status_code}")
                # Restore from backup
                if os.path.exists(backup_file):
                    os.replace(backup_file, "BugTraceX.py")
                    print(Fore.GREEN + "  ✅ Restored from backup")
        
        else:
            print(Fore.RED + f"  ❌ Could not check updates: HTTP {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"  ❌ Network error: {e}")
        print(Fore.YELLOW + "  Check your internet connection")
    except Exception as e:
        print(Fore.RED + f"  ❌ Update error: {e}")
    
    # Manual update option
    print_section("🔧 MANUAL UPDATE")
    print(Fore.CYAN + "  If auto-update failed, you can:")
    print(Fore.CYAN + "  1. Visit GitHub: https://github.com/bughunter11/BugTraceX")
    print(Fore.CYAN + "  2. Download latest release")
    print(Fore.CYAN + "  3. Replace your current file")
    
    input(Fore.CYAN + BOLD + "\n  ⏎ Press Enter to continue...")

# === Exit Function ===
def exit_script():
    """Exit the script"""
    print(Fore.YELLOW + "\n┌" + "─" * 60 + "┐")
    print(Fore.MAGENTA + BOLD + "│              THANKS FOR USING BUGTRACEX!              │")
    print(Fore.CYAN    + BOLD + "│        • Keep Hacking Ethically!                    │")
    print(Fore.CYAN    + BOLD + "│        • Knowledge is Power!                        │")
    print(Fore.GREEN   + BOLD + "│        • Made with ♥ by RAJ_MAKER                  │")
    print(Fore.CYAN    + BOLD + "│        • Telegram: @BugTraceX                      │")
    print(Fore.YELLOW + "└" + "─" * 60 + "┘")
    
    # Show quick stats if available
    try:
        if os.path.exists("version.txt"):
            with open("version.txt", 'r') as f:
                version = f.read().strip()
            print(Fore.LIGHTBLACK_EX + f"\n  Version: {version} | Professional Edition")
    except:
        pass
    
    sys.exit()

# === Main Runner ===
def main():
    """Main function to run the tool"""
    while True:
        try:
            banner()
            menu()
            choice = input().strip()

            if choice == '1':
                host_scanner()
            elif choice == '2':
                subfinder()
            elif choice == '3':
                complete_host_info()
            elif choice == '4':
                smart_txt_splitter()
            elif choice == '5':
                intelligent_subfinder()
            elif choice == '6':
                network_cidr_scanner()
            elif choice == '7':
                multi_source_reverse_ip()
            elif choice == '8':
                cidr_to_domain_finder()
            elif choice == '9':
                subdomain_mapper_pro()
            elif choice == '10':
                domain_cleaner()
            elif choice == '11':
                auto_updater()
            elif choice == '0':
                exit_script()
            else:
                print(Fore.RED + BOLD + "  ❌ Invalid option!")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(Fore.YELLOW + BOLD + "\n\n⚠️  Interrupted. Exiting...")
            exit_script()
        except Exception as e:
            print(Fore.RED + BOLD + f"\n❌ Error: {e}")
            time.sleep(2)

# === Execute Only When Run Directly ===
if __name__ == "__main__":
    main()