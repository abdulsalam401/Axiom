#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║              Axiom — Advanced Android Security Framework         ║
║          Author : Abdul Salam                                    ║
║          Contact: Salamcs.app                                    ║
║          For authorized penetration testing use only             ║
╚══════════════════════════════════════════════════════════════════╝
"""

import argparse
import sys
import os
import time
import json
import random
import subprocess
import tempfile
import re
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

# ── Rich UI ────────────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich import box
    from rich.align import Align
except ImportError:
    print("[!] 'rich' not installed. Run: pip install rich")
    sys.exit(1)

# ── Optional Dependencies ────────────────────────────────────────────────────
try:
    from PIL import Image
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── Modules ────────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from modules import adb_manager, apk_analyzer, network_scanner
from modules import vulnerability_scanner, exploit_engine, payload_generator, report_generator

console = Console()

VERSION     = "2.1.0"
AUTHOR      = "Abdul Salam"
WEBSITE     = "Salamcs.app"
LINKEDIN    = "https://www.linkedin.com/in/abdul-salam-39467a274"
GITHUB      = "https://github.com/abdulsalam401"
TOOL_NAME   = "Axiom"
YEAR        = "2026"

# ── Remote Controller Class ──────────────────────────────────────────────────────

class RemoteController:
    """Handle remote control of Android device via ADB."""
    
    def __init__(self, device_id: str = None):
        self.device_id = device_id
        self.wifi_port = 5555
        self.device_ip = None
        self.connected_wireless = False
        
    def _run_adb(self, args: list, capture=True):
        cmd = ["adb"]
        if self.device_id:
            cmd += ["-s", self.device_id]
        cmd += args
        try:
            r = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
            return r.stdout.strip() if capture else r.returncode
        except Exception as e:
            return str(e)
    
    def get_device_ip(self) -> Optional[str]:
        out = self._run_adb(["shell", "ip addr show wlan0"])
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
        if match:
            return match.group(1)
        out = self._run_adb(["shell", "ifconfig wlan0"])
        match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", out)
        return match.group(1) if match else None
    
    def get_local_subnets(self) -> List[str]:
        """Get all local network subnets, prioritizing physical networks and excluding virtual ones."""
        subnets = set()
        
        # 1. Parse already connected adb devices (most reliable way to find the active subnet)
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip() and "device" in line and ":" in line:
                    ip = line.split()[0].split(':')[0]
                    if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                        subnet = '.'.join(ip.split('.')[:-1])
                        subnets.add(subnet)
        except:
            pass

        # 2. If a USB device is connected, check its WiFi IP
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
            lines = [l.split()[0] for l in result.stdout.strip().split('\n')[1:] if l.strip() and "device" in l and ":" not in l]
            for serial in lines:
                out = subprocess.run(["adb", "-s", serial, "shell", "ip addr show wlan0"], capture_output=True, text=True, timeout=5).stdout
                match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
                if match:
                    subnet = '.'.join(match.group(1).split('.')[:-1])
                    subnets.add(subnet)
                else:
                    out = subprocess.run(["adb", "-s", serial, "shell", "ifconfig wlan0"], capture_output=True, text=True, timeout=5).stdout
                    match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", out)
                    if match:
                        subnet = '.'.join(match.group(1).split('.')[:-1])
                        subnets.add(subnet)
        except:
            pass

        # 3. Try running ipconfig.exe (WSL/Linux host environment check)
        try:
            result = subprocess.run(["ipconfig.exe"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            current_adapter = ""
            for line in lines:
                if "adapter" in line.lower():
                    current_adapter = line.lower()
                if "IPv4 Address" in line or "IPv4" in line or "IP-Address" in line:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        ip = match.group(1)
                        if not ip.startswith("127."):
                            if not any(x in current_adapter for x in ['virtual', 'hyper-v', 'docker', 'vethernet', 'wsl', 'virtualbox', 'vmware', 'host-only']):
                                subnet = '.'.join(ip.split('.')[:-1])
                                subnets.add(subnet)
        except:
            pass

        # 4. Try running native ipconfig (Windows native check)
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            current_adapter = ""
            for line in lines:
                if "adapter" in line.lower():
                    current_adapter = line.lower()
                if "IPv4 Address" in line or "IPv4" in line or "IP-Address" in line:
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", line)
                    if match:
                        ip = match.group(1)
                        if not ip.startswith("127."):
                            if not any(x in current_adapter for x in ['virtual', 'hyper-v', 'docker', 'vethernet', 'wsl', 'virtualbox', 'vmware', 'host-only']):
                                subnet = '.'.join(ip.split('.')[:-1])
                                subnets.add(subnet)
        except:
            pass

        # 5. Try running ip route (Linux/WSL)
        try:
            result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5)
            match = re.search(r"via (\d+\.\d+\.\d+\.\d+)", result.stdout)
            if match:
                gateway = match.group(1)
                if not (gateway.startswith("172.") and 16 <= int(gateway.split('.')[1]) <= 31):
                    subnet = '.'.join(gateway.split('.')[:-1])
                    subnets.add(subnet)
        except:
            pass

        # 6. Try running ip addr show (Linux/WSL)
        try:
            result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True, timeout=5)
            lines = result.stdout.split('\n')
            current_interface = ""
            for line in lines:
                if ": " in line:
                    current_interface = line.split(": ")[1].split("@")[0].strip()
                if "inet " in line:
                    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/\d+", line)
                    if match:
                        ip = match.group(1)
                        if not ip.startswith("127."):
                            if not any(x in current_interface.lower() for x in ['docker', 'veth', 'br-', 'wsl', 'virtual', 'virbr', 'hyper-v']):
                                if not (ip.startswith("172.") and 16 <= int(ip.split('.')[1]) <= 31):
                                    subnet = '.'.join(ip.split('.')[:-1])
                                    subnets.add(subnet)
        except:
            pass

        # Filter out subnets to only keep valid private IP subnets and discard WSL/virtual ranges
        filtered = []
        has_physical_network = any(s.startswith("192.168.") or s.startswith("10.") for s in subnets)
        
        for s in subnets:
            parts = s.split('.')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                first_octet = int(parts[0])
                second_octet = int(parts[1])
                if has_physical_network and first_octet == 172 and 16 <= second_octet <= 31:
                    continue
                filtered.append(s)

        # Fallbacks if no physical subnets found
        if not filtered:
            filtered = ["192.168.1", "192.168.0", "192.168.10", "192.168.100", "10.0.0"]
            
        return list(set(filtered))
    
    def discover_devices_on_network(self, subnet: str = None) -> List[Tuple[str, int]]:
        """Automatically discover Android devices on the local network."""
        import concurrent.futures
        import socket
        
        discovered_devices = []
        ports_to_check = [5555, 5556]
        
        if not subnet:
            subnets = self.get_local_subnets()
            console.print(f"[cyan]🔍 Scanning {len(subnets)} network(s) for Android devices...[/]")
            
            for sub in subnets:
                console.print(f"[dim]   Scanning {sub}.0/24...[/]")
                devices = self._scan_subnet(sub, ports_to_check)
                discovered_devices.extend(devices)
        else:
            discovered_devices = self._scan_subnet(subnet, ports_to_check)
        
        seen = set()
        unique_devices = []
        for ip, port in discovered_devices:
            key = f"{ip}:{port}"
            if key not in seen:
                seen.add(key)
                unique_devices.append((ip, port))
        
        if unique_devices:
            console.print(f"[green]✓ Found {len(unique_devices)} device(s)![/]")
            for ip, port in unique_devices:
                temp_id = f"{ip}:{port}"
                model = subprocess.run(
                    ["adb", "-s", temp_id, "shell", "getprop ro.product.model 2>/dev/null"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip() or "Unknown"
                console.print(f"  [cyan]►[/] {ip}:{port} ({model})")
        else:
            console.print("[yellow]⚠ No devices found.[/]")
        
        return unique_devices
    
    def _scan_subnet(self, subnet: str, ports: List[int]) -> List[Tuple[str, int]]:
        """Scan a single subnet for ADB devices."""
        import concurrent.futures
        import socket
        
        discovered = []
        
        def check_host(host_ip):
            for port in ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.3)
                        result = sock.connect_ex((host_ip, port))
                        if result == 0:
                            try:
                                test_result = subprocess.run(
                                    ["adb", "connect", f"{host_ip}:{port}"],
                                    capture_output=True, text=True, timeout=2
                                )
                                if "connected" in test_result.stdout.lower():
                                    return (host_ip, port)
                            except:
                                pass
                except:
                    pass
            return None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = {executor.submit(check_host, f"{subnet}.{i}"): i for i in range(1, 255)}
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    discovered.append(result)
        
        return discovered
    
    def quick_connect_auto(self) -> bool:
        """Automatically discover and connect to an Android device."""
        console.print(Panel(
            "[bold cyan]🔍 Auto-Discover & Connect[/]\n\n"
            "Scanning your local network(s) for Android devices...\n"
            "Make sure your phone is on the same WiFi network!",
            border_style="cyan"
        ))
        
        discovered = self.discover_devices_on_network()
        
        if not discovered:
            console.print("[red]✗ No devices found.[/]")
            console.print("[yellow]Troubleshooting:[/]")
            console.print("  1. Make sure USB Debugging is enabled on your phone")
            console.print("  2. Ensure phone is on the same WiFi network")
            console.print("  3. First time? Connect via USB and run: axiom --remote-setup")
            return False
        
        if len(discovered) == 1:
            ip, port = discovered[0]
            console.print(f"[green]Auto-selected: {ip}:{port}[/]")
            return self.connect_wireless(ip, port)
        else:
            console.print("\n[cyan]Multiple devices found. Select one:[/]")
            for i, (ip, port) in enumerate(discovered, 1):
                temp_id = f"{ip}:{port}"
                model = subprocess.run(
                    ["adb", "-s", temp_id, "shell", "getprop ro.product.model 2>/dev/null"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip() or "Unknown"
                console.print(f"  [{i}] {ip}:{port} - {model}")
            
            choice = Prompt.ask("[cyan]Select device number[/]", 
                               choices=[str(i) for i in range(1, len(discovered) + 1)])
            idx = int(choice) - 1
            ip, port = discovered[idx]
            return self.connect_wireless(ip, port)
    
    def setup_wireless_adb(self, port: int = 5555) -> bool:
        """Enable ADB over WiFi on device (requires USB connection)."""
        console.print("[cyan]📡 Setting up ADB over WiFi...[/]")
        
        ip = self.get_device_ip()
        if not ip:
            console.print("[red]✗ Could not get device IP. Make sure WiFi is ON.[/]")
            return False
        
        self.device_ip = ip
        self.wifi_port = port
        self._run_adb(["tcpip", str(port)])
        time.sleep(2)
        
        console.print(f"[green]✓ ADB over WiFi enabled on port {port}[/]")
        console.print(f"[cyan]Device IP:[/] {ip}")
        
        return True
    
    def connect_wireless(self, ip: str = None, port: int = 5555) -> bool:
        """Connect to device wirelessly."""
        if not ip:
            ip = self.device_ip or self.get_device_ip()
        
        if not ip:
            console.print("[red]✗ Cannot determine device IP[/]")
            return False
        
        console.print(f"[cyan]Connecting to {ip}:{port}...[/]")
        
        subprocess.run(["adb", "kill-server"], capture_output=True)
        time.sleep(1)
        
        result = subprocess.run(["adb", "connect", f"{ip}:{port}"], 
                                capture_output=True, text=True)
        
        if "connected" in result.stdout.lower():
            self.device_id = f"{ip}:{port}"
            self.connected_wireless = True
            console.print(f"[bold green]✓ Connected to {self.device_id}[/]")
            return True
        
        console.print(f"[red]✗ Connection failed: {result.stdout}[/]")
        return False
    
    def disconnect_wireless(self):
        if self.device_id and ":" in self.device_id:
            subprocess.run(["adb", "disconnect", self.device_id], capture_output=True)
            console.print("[yellow]✓ Disconnected[/]")
            self.connected_wireless = False
    
    def capture_screen(self, output_path: str = None) -> Optional[str]:
        if not output_path:
            output_path = f"screenshot_{int(time.time())}.png"
        remote_path = "/sdcard/screen_temp.png"
        self._run_adb(["shell", "screencap", "-p", remote_path])
        self._run_adb(["pull", remote_path, output_path])
        self._run_adb(["shell", "rm", remote_path])
        console.print(f"[green]✓ Screenshot saved: {output_path}[/]")
        return output_path
    
    def send_touch(self, x: int, y: int):
        self._run_adb(["shell", f"input tap {x} {y}"])
        console.print(f"[dim]Tap at ({x}, {y})[/]")
    
    def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        self._run_adb(["shell", f"input swipe {x1} {y1} {x2} {y2} {duration}"])
        console.print(f"[dim]Swiped ({x1},{y1}) → ({x2},{y2})[/]")
    
    def send_text(self, text: str):
        text_escaped = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'")
        self._run_adb(["shell", f"input text '{text_escaped}'"])
        console.print(f"[dim]Typed: {text}[/]")
    
    def send_keyevent(self, keycode: str):
        key_map = {
            "home": "KEYCODE_HOME",
            "back": "KEYCODE_BACK",
            "menu": "KEYCODE_MENU",
            "recent": "KEYCODE_APP_SWITCH",
            "power": "KEYCODE_POWER",
            "volume_up": "KEYCODE_VOLUME_UP",
            "volume_down": "KEYCODE_VOLUME_DOWN",
            "enter": "KEYCODE_ENTER",
            "delete": "KEYCODE_DEL",
            "up": "KEYCODE_DPAD_UP",
            "down": "KEYCODE_DPAD_DOWN",
            "left": "KEYCODE_DPAD_LEFT",
            "right": "KEYCODE_DPAD_RIGHT",
        }
        key = key_map.get(keycode.lower(), keycode.upper())
        self._run_adb(["shell", f"input keyevent {key}"])
        console.print(f"[dim]Key: {keycode}[/]")
    
    def get_screen_size(self) -> Tuple[int, int]:
        out = self._run_adb(["shell", "wm size"])
        match = re.search(r"Physical size: (\d+)x(\d+)", out)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 1080, 2400
    
    def start_gui_remote(self):
        """Start GUI remote control directly."""
        try:
            from modules.gui_remote import start_gui_remote
            start_gui_remote(self.device_ip or self.device_id.split(':')[0] if self.device_id else None, self.wifi_port)
        except ImportError as e:
            console.print(f"[red]✗ Could not import GUI remote module: {e}[/]")
        except Exception as e:
            console.print(f"[red]✗ Error starting GUI remote: {e}[/]")


# ─── Remote Control Helper Functions ──────────────────────────────────────────

_REMOTE_SESSION_FILE = os.path.expanduser("~/.axiom_remote.json")

def _save_remote_session(controller: RemoteController):
    data = {
        "device_id": controller.device_id,
        "device_ip": controller.device_ip,
        "wifi_port": controller.wifi_port,
        "timestamp": time.time()
    }
    with open(_REMOTE_SESSION_FILE, "w") as f:
        json.dump(data, f)
    console.print("[dim]Session saved[/]")


def _load_remote_session() -> Optional[RemoteController]:
    if os.path.exists(_REMOTE_SESSION_FILE):
        try:
            with open(_REMOTE_SESSION_FILE, "r") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < 86400:
                controller = RemoteController()
                if controller.connect_wireless(data.get("device_ip"), data.get("wifi_port", 5555)):
                    return controller
        except:
            pass
    return None


def one_time_setup(device_id: str = None, port: int = 5555) -> Optional[RemoteController]:
    console.print(Panel(
        "[bold cyan]Axiom Remote Control Setup[/]\n\n"
        "This will:\n"
        "1. Check USB connection\n"
        "2. Enable ADB over WiFi on device\n"
        "3. Get device IP address\n"
        "4. Allow you to disconnect USB\n"
        "5. Reconnect wirelessly",
        border_style="magenta"
    ))
    
    controller = RemoteController(device_id)
    
    console.print("\n[1/5] Checking USB connection...")
    devices_out = controller._run_adb(["devices"])
    if "device" not in devices_out:
        console.print("[red]✗ No device connected via USB. Please connect your phone.[/]")
        return None
    
    console.print("[green]✓ Device connected via USB[/]")
    
    console.print("\n[2/5] Enabling ADB over WiFi...")
    if not controller.setup_wireless_adb(port):
        console.print("[red]✗ Failed to enable WiFi ADB[/]")
        return None
    
    console.print("\n[3/5] Getting device IP...")
    ip = controller.device_ip
    console.print(f"[green]✓ Device IP: {ip}[/]")
    
    console.print(f"""
[4/5] [bold yellow]ACTION REQUIRED[/]
1. Disconnect the USB cable from your device NOW
2. Make sure device is still connected to WiFi
3. Press Enter when ready to connect wirelessly
    """)
    input("Press Enter to continue...")
    
    console.print("\n[5/5] Connecting wirelessly...")
    if controller.connect_wireless(ip, port):
        console.print(Panel(
            f"[bold green]✓ Remote control ready![/]\n"
            f"Device: {controller.device_id}\n"
            f"IP: {ip}:{port}\n\n"
            f"Now you can use: python3 axiom.py --auto-connect",
            border_style="green"
        ))
        _save_remote_session(controller)
        return controller
    else:
        console.print("[red]✗ Wireless connection failed.[/]")
        return None


def quick_reconnect(ip: str = None, port: int = 5555) -> Optional[RemoteController]:
    controller = RemoteController()
    
    if not ip:
        ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
        if not ip:
            return None
    
    if controller.connect_wireless(ip, port):
        _save_remote_session(controller)
        return controller
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  BANNER & ANIMATION
# ═══════════════════════════════════════════════════════════════════════════════

BANNER_ART = r"""
    _    __  __ _   ___   __  __ 
   / \   \ \/ /| | / _ \ |  \/  |
  / _ \   \  / | || | | || |\/| |
 / ___ \   /  \| || |_| || |  | |
/_/   \_\ /_/\_\_| \___/ |_|  |_|
"""

BANNER_LINES_GRADIENT = [
    "magenta", "bright_magenta", "purple", "deep_pink3", "orchid", "violet"
]

def get_banner_status():
    try:
        devices = adb_manager.list_devices()
        device_count = len(devices)
        status_color = "green" if device_count > 0 else "red"
        device_text = f"[{status_color}]{device_count} Connected[/]"
    except:
        device_text = "[yellow]ADB Not Found[/]"

    now = datetime.now().strftime("%H:%M:%S")
    
    return (
        f"📅 [bold white]{now}[/]  |  "
        f"📱 [bold cyan]Devices:[/] {device_text}  |  "
        f"🚀 [bold green]v{VERSION}[/]"
    )

def animate_glitch_banner():
    from rich.markup import escape
    lines = BANNER_ART.strip("\n").split("\n")
    
    chars = "01$#!@%^&*()_+=-[]{}|;:,.<>?/"
    for _ in range(12):
        glitch_lines = []
        for line in lines:
            glitch_line = "".join(random.choice(chars) if c != " " else " " for c in line)
            color = random.choice(BANNER_LINES_GRADIENT)
            glitch_lines.append(f"[bold {color}]{escape(glitch_line)}[/]")
        
        console.clear()
        for gl in glitch_lines:
            console.print(Align.center(gl))
        time.sleep(0.06)

    console.clear()
    for i, line in enumerate(lines):
        color = BANNER_LINES_GRADIENT[i % len(BANNER_LINES_GRADIENT)]
        console.print(Align.center(f"[bold {color}]{line}[/]"))
        time.sleep(0.05)

def print_banner():
    animate_glitch_banner()

    tagline = Text("◈ ADVANCED ANDROID SECURITY FRAMEWORK ◈", style="bold italic bright_magenta")
    console.print(Align.center(tagline))
    console.print()
    name = Text("Salam.Cyber1", style="bold cyan")
    console.print(Align.center(name))
    # made_by = Text("Project by Salam.Cyber1", style="bold dim cyan")
    # console.print(Align.center(made_by))
    status_text = get_banner_status()
    console.print(Align.center(Panel(
        status_text,
        border_style="magenta",
        box=box.HORIZONTALS,
        padding=(0, 2),
        title="[bold magenta]System Status[/]",
        title_align="left"
    )))
    console.print()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

MENU_OPTIONS = [
    ("1",  "📱", "Device Manager",          "List & manage connected Android devices"),
    ("2",  "🔎", "APK Static Analyzer",     "Decompile & audit an APK file"),
    ("3",  "🌐", "Network Scanner",         "Port scan, WiFi info, host discovery"),
    ("4",  "🚨", "Vulnerability Scanner",   "CVE mapping, root check, insecure storage"),
    ("5",  "💥", "Exploit Engine",          "Launch activities, deep links, shell dropper"),
    ("6",  "🎯", "Payload Generator",       "APK payloads, reverse shells, obfuscation"),
    ("7",  "📋", "Report Generator",        "Generate HTML/JSON security report"),
    ("8",  "📡", "ADB WiFi Connect",        "Enable & connect ADB over WiFi"),
    ("9",  "📸", "Screenshot Capture",      "Capture device screenshot via ADB"),
    ("10", "📦", "Package Manager",         "Enumerate installed packages"),
    ("11", "🐛", "Logcat Analyzer",         "Capture & analyze logcat for secrets"),
    ("12", "🔐", "SSL Pinning Check",       "Detect SSL pinning in target app"),
    ("13", "📂", "File Transfer",           "Pull/push files from/to device"),
    ("14", "💻", "Interactive ADB Shell",   "Drop into live ADB shell"),
    ("15", "ℹ️ ", "About",                   "About Axiom"),
    ("16", "🎮", "Remote Control",          "Wireless control & screen mirroring"),
    ("17", "🔍", "Auto-Discover & Connect", "Find & connect to devices on network"),
    ("0",  "🚪", "Exit",                    "Exit Axiom"),
]


def print_main_menu():
    t = Table(
        title=f"\n[bold magenta]🔮  {TOOL_NAME}  —  Main Menu[/]\n",
        box=box.DOUBLE_EDGE,
        border_style="magenta",
        header_style="bold cyan",
        show_lines=True,
        min_width=70,
    )
    t.add_column("  #  ",   style="bold cyan",   width=5,  no_wrap=True)
    t.add_column("  ",      style="",             width=3,  no_wrap=True)
    t.add_column("Module",  style="bold white",   min_width=24)
    t.add_column("Description", style="dim",      min_width=38)

    for num, icon, name, desc in MENU_OPTIONS:
        style = "on #1a0030" if num == "0" else ""
        t.add_row(f"[bold cyan] {num} [/]", icon, name, desc, style=style)

    console.print(t)


# ═══════════════════════════════════════════════════════════════════════════════
#  DEVICE SELECTION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def select_device() -> Optional[str]:
    devices = adb_manager.list_devices()
    if not devices:
        return None
    if len(devices) == 1:
        dev = devices[0]["serial"]
        console.print(f"[green]Auto-selected device:[/] {dev}")
        return dev
    serial = Prompt.ask("[cyan]Enter device serial[/]")
    return serial


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════════

def handle_device_manager():
    console.rule("[bold magenta]📱 Device Manager[/]")
    adb_manager.check_adb()
    device_id = select_device()
    if not device_id:
        return
    adb_manager.device_info(device_id)


def handle_apk_analyzer():
    console.rule("[bold magenta]🔎 APK Static Analyzer[/]")
    apk_path = Prompt.ask("[cyan]APK file path[/]")
    findings = apk_analyzer.analyze_apk(apk_path)
    if Confirm.ask("[cyan]Save findings to report?[/]", default=True):
        _save_to_session(findings, "apk_analysis")
        console.print("[green]✓ Added to session report.[/]")


def handle_network_scanner():
    console.rule("[bold magenta]🌐 Network Scanner[/]")
    choice = Prompt.ask("[cyan]Scan mode[/]", choices=["device", "host", "wifi", "discover", "mitm"], default="device")

    if choice == "device":
        device_id = select_device()
        if not device_id:
            return
        ip = network_scanner.get_device_ip(device_id)
        if ip:
            console.print(f"[green]Device IP:[/] {ip}")
            network_scanner.port_scan(ip)
        else:
            console.print("[red]Could not determine device IP.[/]")

    elif choice == "host":
        target = Prompt.ask("[cyan]Target IP/hostname[/]")
        port_range = Prompt.ask("[cyan]Port range (comma-list or 'all')[/]", default="common")
        if port_range == "all":
            ports = list(range(1, 65536))
        elif port_range == "common":
            ports = None
        else:
            ports = [int(p.strip()) for p in port_range.split(",") if p.strip().isdigit()]
        network_scanner.port_scan(target, ports)

    elif choice == "wifi":
        device_id = select_device()
        if device_id:
            network_scanner.get_wifi_info(device_id)

    elif choice == "discover":
        subnet = Prompt.ask("[cyan]Subnet (e.g. 192.168.1)[/]")
        network_scanner.discover_devices(subnet)

    elif choice == "mitm":
        network_scanner.mitm_setup_guide()


def handle_vulnerability_scanner():
    console.rule("[bold magenta]🚨 Vulnerability Scanner[/]")
    device_id = select_device()
    if not device_id:
        return
    pkg = Prompt.ask("[cyan]Target package (leave blank for device-level only)[/]", default="")
    report = vulnerability_scanner.full_vulnerability_scan(device_id, pkg or None)
    _save_to_session(report, "vulnerability_scan")


def handle_exploit_engine():
    console.rule("[bold magenta]💥 Exploit Engine[/]")
    device_id = select_device()
    if not device_id:
        return

    exploit_engine.exploit_menu(device_id)
    choice = Prompt.ask("[red]Select exploit[/]", choices=[str(i) for i in range(10)])

    if choice == "1":
        pkg = Prompt.ask("[cyan]Package name[/]")
        act = Prompt.ask("[cyan]Activity class[/]")
        exploit_engine.launch_exported_activity(device_id, pkg, act)

    elif choice == "2":
        pkg = Prompt.ask("[cyan]Package name[/]")
        action = Prompt.ask("[cyan]Intent action[/]")
        exploit_engine.trigger_broadcast_receiver(device_id, pkg, action)

    elif choice == "3":
        uri = Prompt.ask("[cyan]Content provider URI (content://...)[/]")
        exploit_engine.extract_content_provider(device_id, uri)

    elif choice == "4":
        pkg = Prompt.ask("[cyan]Package name[/]")
        scheme = Prompt.ask("[cyan]Deep link scheme (e.g. myapp)[/]")
        exploit_engine.deep_link_fuzzer(device_id, pkg, scheme)

    elif choice == "5":
        pkg = Prompt.ask("[cyan]Package name[/]")
        exploit_engine.frida_injection_guide(pkg)

    elif choice == "6":
        lhost = Prompt.ask("[cyan]LHOST[/]")
        lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
        exploit_engine.shell_payload_dropper(device_id, lhost, lport)

    elif choice == "7":
        pkg = Prompt.ask("[cyan]Package name[/]")
        db = Prompt.ask("[cyan]Database filename[/]")
        exploit_engine.extract_database(device_id, pkg, db)

    elif choice == "8":
        exploit_engine.bypass_lock_screen(device_id)

    elif choice == "9":
        exploit_engine.enable_developer_options(device_id)


def handle_payload_generator():
    console.rule("[bold magenta]🎯 Payload Generator[/]")
    payload_generator.payload_menu()
    choice = Prompt.ask("[red]Select payload type[/]", choices=["1", "2", "3", "4", "5", "0"])

    if choice == "1":
        lhost = Prompt.ask("[cyan]LHOST[/]")
        lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
        ptype = Prompt.ask("[cyan]Payload type[/]",
                             choices=["reverse_tcp", "reverse_https", "reverse_http", "shell_tcp"],
                             default="reverse_tcp")
        output = Prompt.ask("[cyan]Output file[/]", default="payload.apk")
        payload_generator.generate_msfvenom_apk(lhost, lport, ptype, output)

    elif choice == "2":
        action = Prompt.ask("[cyan]Intent action[/]")
        comp = Prompt.ask("[cyan]Component (pkg/class or blank)[/]", default="")
        data = Prompt.ask("[cyan]Data URI (or blank)[/]", default="")
        payload_generator.generate_intent_payload(action, comp or None, data or None)

    elif choice == "3":
        lhost = Prompt.ask("[cyan]LHOST[/]")
        lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
        payload_generator.generate_reverse_shell_commands(lhost, lport)

    elif choice == "4":
        lhost = Prompt.ask("[cyan]LHOST[/]")
        lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
        output = Prompt.ask("[cyan]Script filename[/]", default="adb_payload.sh")
        payload_generator.generate_adb_payload_script(None, lhost, lport, output)

    elif choice == "5":
        raw = Prompt.ask("[cyan]Payload to obfuscate[/]")
        method = Prompt.ask("[cyan]Obfuscation method[/]", choices=["base64", "hex"], default="base64")
        payload_generator.obfuscate_payload(raw, method)


def handle_report_generator():
    console.rule("[bold magenta]📋 Report Generator[/]")
    target = Prompt.ask("[cyan]Target description (app/device name)[/]", default="Unknown Target")

    data = _get_session()
    data["target"] = target

    fmt = Prompt.ask("[cyan]Report format[/]", choices=["html", "json", "both", "table"], default="html")

    if fmt in ("html", "both"):
        out = Prompt.ask("[cyan]HTML output filename[/]", default="axiom_report.html")
        report_generator.generate_html_report(data, out)

    if fmt in ("json", "both"):
        out = Prompt.ask("[cyan]JSON output filename[/]", default="axiom_report.json")
        report_generator.generate_json_report(data, out)

    if fmt == "table":
        report_generator.print_summary_table(data)


def handle_adb_wifi():
    console.rule("[bold magenta]📡 ADB WiFi Connect[/]")
    device_id = select_device()
    if not device_id:
        return
    port = IntPrompt.ask("[cyan]Port[/]", default=5555)
    ip, p = adb_manager.enable_adb_wifi(device_id, port)


def handle_screenshot():
    console.rule("[bold magenta]📸 Screenshot Capture[/]")
    device_id = select_device()
    if not device_id:
        return
    path = adb_manager.take_screenshot(device_id)
    if path:
        console.print(f"[bold green]✓ Screenshot saved:[/] {path}")


def handle_package_manager():
    console.rule("[bold magenta]📦 Package Manager[/]")
    device_id = select_device()
    if not device_id:
        return
    pkg_type = Prompt.ask("[cyan]Package filter[/]",
                           choices=["all", "system", "third_party", "disabled"],
                           default="third_party")
    adb_manager.list_packages(device_id, pkg_type)


def handle_logcat():
    console.rule("[bold magenta]🐛 Logcat Analyzer[/]")
    device_id = select_device()
    if not device_id:
        return
    lines = IntPrompt.ask("[cyan]Lines to capture[/]", default=300)
    adb_manager.capture_logcat(device_id, lines)


def handle_ssl_check():
    console.rule("[bold magenta]🔐 SSL Pinning Check[/]")
    device_id = select_device()
    if not device_id:
        return
    pkg = Prompt.ask("[cyan]Package name[/]")
    network_scanner.check_ssl_pinning(device_id, pkg)


def handle_file_transfer():
    console.rule("[bold magenta]📂 File Transfer[/]")
    device_id = select_device()
    if not device_id:
        return
    direction = Prompt.ask("[cyan]Direction[/]", choices=["pull", "push"])
    if direction == "pull":
        remote = Prompt.ask("[cyan]Remote path (on device)[/]")
        local = Prompt.ask("[cyan]Local destination[/]", default=".")
        adb_manager.pull_file(device_id, remote, local)
    else:
        local = Prompt.ask("[cyan]Local file path[/]")
        remote = Prompt.ask("[cyan]Remote destination (on device)[/]")
        adb_manager.push_file(device_id, local, remote)


def handle_adb_shell():
    console.rule("[bold magenta]💻 Interactive ADB Shell[/]")
    device_id = select_device()
    if not device_id:
        return
    adb_manager.interactive_shell(device_id)


def handle_about():
    about = Panel(
        f"\n"
        f"  [bold magenta]🔮  {TOOL_NAME} v{VERSION}[/]\n\n"
        f"  [bold cyan]Advanced Android Security Assessment Framework[/]\n\n"
        f"  [white]A comprehensive tool for ethical hackers and security professionals.\n"
        f"  Covers static APK analysis, dynamic runtime analysis via ADB,\n"
        f"  network scanning, vulnerability mapping, exploit assistance,\n"
        f"  payload generation, professional report generation, and\n"
        f"  [bold green]wireless remote control with screen mirroring[/].\n\n"
        f"  [bold magenta]Author   :[/] [white]{AUTHOR}[/]\n"
        f"  [bold magenta]Website  :[/] [cyan]{WEBSITE}[/]\n"
        f"  [bold magenta]LinkedIn :[/] [cyan]{LINKEDIN}[/]\n"
        f"  [bold magenta]GitHub   :[/] [cyan]{GITHUB}[/]\n"
        f"  [bold magenta]Year     :[/] [white]{YEAR}[/]\n\n"
        f"  [bold red]⚠  For authorized penetration testing use only.[/]\n"
        f"  [dim]Unauthorized use is illegal and unethical.[/]\n",
        title="[bold]About Axiom[/]",
        border_style="magenta",
        padding=(0, 4),
    )
    console.print(about)


def handle_remote_control():
    """Handle remote control module."""
    console.rule("[bold magenta]🎮 Remote Control[/]")
    
    console.print(Panel(
        "[bold yellow]⚠ SECURITY WARNING[/]\n\n"
        "ADB over WiFi exposes your device to the network.\n"
        "Use on trusted networks ONLY.\n"
        "Disable when not in use: adb disconnect",
        border_style="yellow"
    ))
    
    if not Confirm.ask("\n[cyan]I understand the security implications[/]", default=False):
        console.print("[yellow]Returning to main menu.[/]")
        return
    
    from modules.remote_controller import remote_control_menu, one_time_setup, quick_reconnect, RemoteController
    remote_control_menu()
    choice = Prompt.ask("[cyan]Select option[/]", choices=[str(i) for i in range(9)])
    
    if choice == "1":
        device_id = select_device()
        if device_id:
            one_time_setup(device_id)
        else:
            console.print("[red]No device connected via USB.[/]")
    
    elif choice == "2":
        ip = Prompt.ask("[cyan]Enter device IP (or press Enter for auto)[/]", default="")
        if ip:
            controller = RemoteController()
            controller.connect_wireless(ip, 5555)
        else:
            controller = RemoteController()
            if controller.quick_connect_auto():
                if Confirm.ask("[cyan]Start GUI remote control?[/]", default=True):
                    controller.start_gui_remote()
    
    elif choice == "3":
        controller = RemoteController()
        ip = Prompt.ask("[cyan]Enter device IP (or press Enter for auto)[/]", default="")
        if ip:
            if controller.connect_wireless(ip, 5555):
                controller.start_gui_remote()
        else:
            if controller.quick_connect_auto():
                controller.start_gui_remote()
    
    elif choice == "4":
        controller = RemoteController()
        ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
        if controller.connect_wireless(ip, 5555):
            controller.capture_screen()
    
    elif choice == "5":
        controller = RemoteController()
        ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
        if controller.connect_wireless(ip, 5555):
            screen_w, screen_h = controller.get_screen_size()
            console.print(f"[dim]Screen: {screen_w}x{screen_h}[/]")
            action = Prompt.ask("[cyan]Action (tap/swipe)[/]", choices=["tap", "swipe"])
            if action == "tap":
                x = IntPrompt.ask("[cyan]X coordinate[/]", default=screen_w//2)
                y = IntPrompt.ask("[cyan]Y coordinate[/]", default=screen_h//2)
                controller.send_touch(x, y)
            else:
                x1 = IntPrompt.ask("[cyan]Start X[/]")
                y1 = IntPrompt.ask("[cyan]Start Y[/]")
                x2 = IntPrompt.ask("[cyan]End X[/]")
                y2 = IntPrompt.ask("[cyan]End Y[/]")
                controller.send_swipe(x1, y1, x2, y2)
    
    elif choice == "6":
        controller = RemoteController()
        ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
        if controller.connect_wireless(ip, 5555):
            text = Prompt.ask("[cyan]Text to type[/]")
            controller.send_text(text)
    
    elif choice == "7":
        controller = RemoteController()
        ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
        if controller.connect_wireless(ip, 5555):
            adb_manager.device_info(controller.device_id)
    
    elif choice == "8":
        ip = Prompt.ask("[cyan]Enter device IP[/]")
        port = IntPrompt.ask("[cyan]Port[/]", default=5555)
        controller = RemoteController()
        controller.connect_wireless(ip, port)
    
    elif choice == "0":
        controller = RemoteController()
        if controller.connected_wireless:
            controller.disconnect_wireless()


def handle_auto_discover():
    """Auto-discover and connect to device with GUI."""
    console.rule("[bold cyan]🔍 Auto-Discover & Connect[/]")
    controller = RemoteController()
    if controller.quick_connect_auto():
        console.print("[green]✓ Connected successfully![/]")
        if Confirm.ask("[cyan]Start GUI remote control?[/]", default=True):
            controller.start_gui_remote()
    else:
        console.print("[red]Failed to connect.[/]")


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STORE
# ═══════════════════════════════════════════════════════════════════════════════

_SESSION = {"findings": [], "permissions": [], "secrets": [], "urls": []}


def _save_to_session(data: dict, source: str):
    if isinstance(data, dict):
        for vuln in data.get("vulnerabilities", []):
            _SESSION["findings"].append(vuln)
        for vuln in data.get("cves", []):
            _SESSION["findings"].append({
                "name": vuln.get("cve", "CVE"),
                "severity": vuln.get("severity", "MEDIUM"),
                "detail": vuln.get("detail", ""),
                "cve": vuln.get("cve"),
            })
        _SESSION["permissions"].extend(data.get("dangerous_permissions", []))
        _SESSION["secrets"].extend(data.get("secrets", []))
        _SESSION["urls"].extend(data.get("urls", []))


def _get_session() -> dict:
    return _SESSION.copy()


# ═══════════════════════════════════════════════════════════════════════════════
#  INTERACTIVE MODE
# ═══════════════════════════════════════════════════════════════════════════════

HANDLER_MAP = {
    "1":  handle_device_manager,
    "2":  handle_apk_analyzer,
    "3":  handle_network_scanner,
    "4":  handle_vulnerability_scanner,
    "5":  handle_exploit_engine,
    "6":  handle_payload_generator,
    "7":  handle_report_generator,
    "8":  handle_adb_wifi,
    "9":  handle_screenshot,
    "10": handle_package_manager,
    "11": handle_logcat,
    "12": handle_ssl_check,
    "13": handle_file_transfer,
    "14": handle_adb_shell,
    "15": handle_about,
    "16": handle_remote_control,
    "17": handle_auto_discover,
}


def interactive_mode():
    print_banner()
    console.print(Panel(
        "[bold red]⚠  LEGAL DISCLAIMER[/]\n\n"
        "[white]Axiom is designed for authorized security testing ONLY.\n"
        "Use of this tool against systems you do not own or have explicit written\n"
        "permission to test is [bold red]ILLEGAL[/] and may result in criminal prosecution.\n"
        "The author assumes no liability for misuse.[/]",
        border_style="red", padding=(0, 2)))

    if not Confirm.ask("\n[bold red]I confirm I have authorization to test the target system[/]", default=False):
        console.print("[yellow]Exiting. Obtain proper authorization before testing.[/]")
        sys.exit(0)

    while True:
        console.print()
        print_main_menu()
        valid_choices = [str(i) for i in range(18)]  # 0-17
        choice = Prompt.ask("\n[bold cyan]Axiom ▶[/]", choices=valid_choices, show_choices=False)

        if choice == "0":
            if os.path.exists(_REMOTE_SESSION_FILE):
                try:
                    controller = _load_remote_session()
                    if controller:
                        controller.disconnect_wireless()
                except:
                    pass
            console.print("\n[bold magenta]🔮 Exiting Axiom. Stay ethical.[/]\n")
            sys.exit(0)

        handler = HANDLER_MAP.get(choice)
        if handler:
            try:
                console.print()
                handler()
            except KeyboardInterrupt:
                console.print("\n[yellow]↩ Returned to main menu.[/]")
            except Exception as e:
                console.print(f"\n[bold red]✗ Error:[/] {e}")
        else:
            console.print("[red]Invalid option.[/]")

        console.print()
        Prompt.ask("[dim]Press ENTER to continue[/]", default="")


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI MODE
# ═══════════════════════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="axiom",
        description=f"🔮 Axiom v{VERSION} — Advanced Android Security Framework by {AUTHOR}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 axiom.py --interactive
  python3 axiom.py --apk app.apk --report html
  python3 axiom.py --device ABC123 --vuln-scan --pkg com.example.app
  python3 axiom.py --device ABC123 --port-scan
  python3 axiom.py --payload reverse_tcp --lhost 10.0.0.1 --lport 4444
  python3 axiom.py --remote-setup
  python3 axiom.py --auto-connect
  python3 axiom.py --gui-remote --remote-ip 192.168.1.100
  python3 axiom.py --devices
        """
    )

    p.add_argument("--interactive", "-i",  action="store_true",    help="Launch interactive menu mode")
    p.add_argument("--version",     "-v",  action="store_true",    help="Show version")

    # Device
    dg = p.add_argument_group("Device")
    dg.add_argument("--devices",           action="store_true",    help="List connected devices")
    dg.add_argument("--device", "-d",      metavar="SERIAL",       help="Target device serial number")
    dg.add_argument("--info",              action="store_true",    help="Show device info")
    dg.add_argument("--shell",             metavar="CMD",          help="Run ADB shell command")
    dg.add_argument("--adb-shell",         action="store_true",    help="Drop into interactive ADB shell")
    dg.add_argument("--adb-wifi",          action="store_true",    help="Enable ADB over WiFi")
    dg.add_argument("--screenshot",        action="store_true",    help="Capture device screenshot")
    dg.add_argument("--logcat",            metavar="N", type=int,  help="Capture N lines of logcat", nargs="?", const=200)
    dg.add_argument("--packages",          choices=["all","system","third_party","disabled"],
                                                                   help="List installed packages")
    dg.add_argument("--pull",              metavar="REMOTE",       help="Pull file from device")
    dg.add_argument("--push",             nargs=2, metavar=("LOCAL","REMOTE"), help="Push file to device")

    # Remote Control
    rc = p.add_argument_group("Remote Control")
    rc.add_argument("--remote-setup",      action="store_true",    help="One-time USB to wireless setup")
    rc.add_argument("--remote-connect",    action="store_true",    help="Connect to saved wireless device")
    rc.add_argument("--remote-control",    action="store_true",    help="Start GUI remote control")
    rc.add_argument("--remote-screenshot", action="store_true",    help="Capture screenshot via wireless")
    rc.add_argument("--remote-tap",        nargs=2, metavar=("X","Y"), type=int, help="Send touch event")
    rc.add_argument("--remote-swipe",      nargs=5, metavar=("X1","Y1","X2","Y2","DUR"), help="Send swipe gesture")
    rc.add_argument("--remote-text",       metavar="TEXT",         help="Send text input")
    rc.add_argument("--remote-key",        metavar="KEY",          help="Send keyevent")
    rc.add_argument("--remote-ip",         metavar="IP",           help="Device IP for wireless connection")
    rc.add_argument("--remote-port",       type=int, default=5555, help="ADB over WiFi port")
    rc.add_argument("--gui-remote",        action="store_true",    help="Start GUI remote control")
    rc.add_argument("--auto-connect", "-a", action="store_true",   help="Auto-discover and connect to device")

    # APK Analysis
    ag = p.add_argument_group("APK Analysis")
    ag.add_argument("--apk",              metavar="FILE",          help="APK file to analyze")

    # Network
    ng = p.add_argument_group("Network")
    ng.add_argument("--port-scan",        action="store_true",    help="Port scan device IP")
    ng.add_argument("--target",           metavar="IP",           help="Explicit scan target IP")
    ng.add_argument("--ports",            metavar="PORTS",        help="Comma-separated ports or 'all'")
    ng.add_argument("--wifi-info",        action="store_true",    help="Show WiFi info")
    ng.add_argument("--discover",         metavar="SUBNET",       help="Discover hosts on subnet")
    ng.add_argument("--ssl-pinning",      metavar="PKG",          help="Check SSL pinning for package")
    ng.add_argument("--mitm-guide",       action="store_true",    help="Show MitM setup guide")

    # Vulnerability
    vg = p.add_argument_group("Vulnerability")
    vg.add_argument("--vuln-scan",        action="store_true",    help="Run full vulnerability scan")
    vg.add_argument("--pkg",             metavar="PKG",           help="Target package name")
    vg.add_argument("--cve-check",       action="store_true",     help="Check Android CVEs for device")
    vg.add_argument("--root-check",      action="store_true",     help="Check if device is rooted")

    # Exploit
    eg = p.add_argument_group("Exploit")
    eg.add_argument("--exploit",          metavar="MODULE",
                    choices=["activity","broadcast","provider","deep-link","frida","shell-drop","db-extract","lock-bypass","dev-options"],
                    help="Exploit module to run")
    eg.add_argument("--activity",         metavar="CLASS",        help="Activity class")
    eg.add_argument("--action",           metavar="ACTION",       help="Intent action")
    eg.add_argument("--uri",              metavar="URI",          help="URI for content provider")
    eg.add_argument("--scheme",           metavar="SCHEME",       help="Deep link scheme")
    eg.add_argument("--lhost",            metavar="IP",           help="Listener host")
    eg.add_argument("--lport",            metavar="PORT", type=int, default=4444, help="Listener port")
    eg.add_argument("--db-name",          metavar="DB",           help="Database filename")

    # Payload
    pg = p.add_argument_group("Payload")
    pg.add_argument("--payload",          metavar="TYPE",
                    choices=["reverse_tcp","reverse_https","reverse_http","shell_tcp",
                             "intent","reverse-shells","adb-script","obfuscate"],
                    help="Generate a payload")
    pg.add_argument("--payload-out",      metavar="FILE",         help="Output file for payload")
    pg.add_argument("--obfuscate-method", choices=["base64","hex"], default="base64",
                    help="Obfuscation method")
    pg.add_argument("--raw-payload",      metavar="CMD",          help="Payload string to obfuscate")

    # Report
    rg = p.add_argument_group("Report")
    rg.add_argument("--report",           choices=["html","json","both","table"],
                    help="Generate report after scan")
    rg.add_argument("--report-out",       metavar="FILE",         help="Report output filename")
    rg.add_argument("--target-name",      metavar="NAME",         help="Target name for report", default="Unknown Target")

    return p


def cli_mode(args):
    print_banner()

    device_id = args.device
    apk_data = {}
    
    if args.version:
        console.print(f"[bold magenta]{TOOL_NAME}[/] v[bold cyan]{VERSION}[/] by [bold]{AUTHOR}[/]")
        return

    if args.devices:
        adb_manager.check_adb()
        adb_manager.list_devices()
        return

    # Auto-connect (no IP needed!)
    if args.auto_connect:
        controller = RemoteController()
        if controller.quick_connect_auto():
            console.print("[green]✓ Connected! Starting GUI remote...[/]")
            controller.start_gui_remote()
        return

    # GUI Remote Control CLI
    if args.gui_remote or args.remote_control:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Enter device IP (or press Enter for auto)[/]", default="")
        if ip:
            if controller.connect_wireless(ip, args.remote_port):
                controller.start_gui_remote()
        else:
            if controller.quick_connect_auto():
                controller.start_gui_remote()
        return

    # Remote Setup
    if args.remote_setup:
        one_time_setup(args.device, args.remote_port)
        return
    
    # Remote Connect
    if args.remote_connect:
        controller = quick_reconnect(args.remote_ip, args.remote_port)
        if controller:
            console.print("[green]✓ Connected![/]")
            if Confirm.ask("[cyan]Start GUI remote?[/]", default=True):
                controller.start_gui_remote()
        return
    
    # Remote Screenshot
    if args.remote_screenshot:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
        if controller.connect_wireless(ip, args.remote_port):
            controller.capture_screen()
        return
    
    # Remote Tap
    if args.remote_tap:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
        if controller.connect_wireless(ip, args.remote_port):
            controller.send_touch(args.remote_tap[0], args.remote_tap[1])
        return
    
    # Remote Swipe
    if args.remote_swipe:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
        if controller.connect_wireless(ip, args.remote_port):
            duration = args.remote_swipe[4] if len(args.remote_swipe) > 4 else 300
            controller.send_swipe(args.remote_swipe[0], args.remote_swipe[1],
                                  args.remote_swipe[2], args.remote_swipe[3], duration)
        return
    
    # Remote Text
    if args.remote_text:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
        if controller.connect_wireless(ip, args.remote_port):
            controller.send_text(args.remote_text)
        return
    
    # Remote Key
    if args.remote_key:
        controller = RemoteController()
        ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
        if controller.connect_wireless(ip, args.remote_port):
            controller.send_keyevent(args.remote_key)
        return

    if args.info and device_id:
        adb_manager.device_info(device_id)

    if args.shell and device_id:
        adb_manager.shell_cmd(device_id, args.shell)

    if args.adb_shell and device_id:
        adb_manager.interactive_shell(device_id)

    if args.adb_wifi and device_id:
        adb_manager.enable_adb_wifi(device_id, args.lport)

    if args.screenshot and device_id:
        adb_manager.take_screenshot(device_id)

    if args.logcat is not None and device_id:
        adb_manager.capture_logcat(device_id, args.logcat)

    if args.packages and device_id:
        adb_manager.list_packages(device_id, args.packages)

    if args.pull and device_id:
        adb_manager.pull_file(device_id, args.pull)

    if args.push and device_id:
        adb_manager.push_file(device_id, args.push[0], args.push[1])

    if args.apk:
        apk_data = apk_analyzer.analyze_apk(args.apk)
        _save_to_session(apk_data, "apk")

    if args.port_scan:
        target = args.target
        if not target and device_id:
            target = network_scanner.get_device_ip(device_id)
        if target:
            ports = None
            if args.ports == "all":
                ports = list(range(1, 65536))
            elif args.ports:
                ports = [int(p) for p in args.ports.split(",") if p.strip().isdigit()]
            network_scanner.port_scan(target, ports)
        else:
            console.print("[red]Provide --target or --device for port scan.[/]")

    if args.wifi_info and device_id:
        network_scanner.get_wifi_info(device_id)

    if args.discover:
        network_scanner.discover_devices(args.discover)

    if args.ssl_pinning and device_id:
        network_scanner.check_ssl_pinning(device_id, args.ssl_pinning)

    if args.mitm_guide:
        network_scanner.mitm_setup_guide()

    if args.vuln_scan and device_id:
        report = vulnerability_scanner.full_vulnerability_scan(device_id, args.pkg)
        _save_to_session(report, "vuln")

    if args.cve_check and device_id:
        findings = vulnerability_scanner.check_android_version_cves(device_id)
        _save_to_session({"cves": findings}, "cve")

    if args.root_check and device_id:
        vulnerability_scanner.check_root_status(device_id)

    if args.exploit and device_id:
        ex = args.exploit
        if ex == "activity":
            exploit_engine.launch_exported_activity(device_id, args.pkg, args.activity)
        elif ex == "broadcast":
            exploit_engine.trigger_broadcast_receiver(device_id, args.pkg, args.action)
        elif ex == "provider":
            exploit_engine.extract_content_provider(device_id, args.uri)
        elif ex == "deep-link":
            exploit_engine.deep_link_fuzzer(device_id, args.pkg, args.scheme)
        elif ex == "frida":
            exploit_engine.frida_injection_guide(args.pkg)
        elif ex == "shell-drop":
            exploit_engine.shell_payload_dropper(device_id, args.lhost, args.lport)
        elif ex == "db-extract":
            exploit_engine.extract_database(device_id, args.pkg, args.db_name)
        elif ex == "lock-bypass":
            exploit_engine.bypass_lock_screen(device_id)
        elif ex == "dev-options":
            exploit_engine.enable_developer_options(device_id)

    if args.payload:
        out = args.payload_out
        if args.payload in ("reverse_tcp","reverse_https","reverse_http","shell_tcp"):
            payload_generator.generate_msfvenom_apk(args.lhost, args.lport, args.payload, out or "payload.apk")
        elif args.payload == "intent":
            payload_generator.generate_intent_payload(args.action, args.pkg, args.uri)
        elif args.payload == "reverse-shells":
            payload_generator.generate_reverse_shell_commands(args.lhost, args.lport)
        elif args.payload == "adb-script":
            payload_generator.generate_adb_payload_script(device_id, args.lhost, args.lport, out or "adb_payload.sh")
        elif args.payload == "obfuscate":
            payload_generator.obfuscate_payload(args.raw_payload or "", args.obfuscate_method)

    if args.report:
        data = _get_session()
        data["target"] = args.target_name
        if apk_data:
            data.update(apk_data)
        if args.report in ("html", "both"):
            out = args.report_out or "axiom_report.html"
            report_generator.generate_html_report(data, out)
        if args.report in ("json", "both"):
            out = args.report_out or "axiom_report.json"
            report_generator.generate_json_report(data, out)
        if args.report == "table":
            report_generator.print_summary_table(data)


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = build_parser()

    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    else:
        cli_mode(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold magenta]🔮 Axiom interrupted. Stay ethical.[/]\n")
        sys.exit(0)





# #!/usr/bin/env python3
# """
# ╔══════════════════════════════════════════════════════════════════╗
# ║          Axiom — Advanced Android Pentesting Tool                ║
# ║          Author : Abdul Salam                                    ║
# ║          Contact: Portfolio Salamcs.app                          ║
# ║          For authorized penetration testing use only             ║
# ╚══════════════════════════════════════════════════════════════════╝
# """

# import argparse
# import sys
# import os
# import time
# import json
# import random
# import subprocess
# import tempfile
# import re
# from datetime import datetime
# from typing import Optional, Tuple, List, Dict, Any

# # ── Rich UI ────────────────────────────────────────────────────────────────────
# try:
#     from rich.console import Console
#     from rich.panel import Panel
#     from rich.table import Table
#     from rich.text import Text
#     from rich.prompt import Prompt, Confirm, IntPrompt
#     from rich import box
#     from rich.align import Align
# except ImportError:
#     print("[!] 'rich' not installed. Run: pip install rich")
#     sys.exit(1)

# # ── Optional Dependencies ────────────────────────────────────────────────────
# try:
#     from PIL import Image
#     import numpy as np
#     PIL_AVAILABLE = True
# except ImportError:
#     PIL_AVAILABLE = False

# # ── Modules ────────────────────────────────────────────────────────────────────
# sys.path.insert(0, os.path.dirname(__file__))
# from modules import adb_manager, apk_analyzer, network_scanner
# from modules import vulnerability_scanner, exploit_engine, payload_generator, report_generator

# console = Console()

# VERSION     = "2.1.0"
# AUTHOR      = "Abdul Salam"
# WEBSITE     = "Salamcs.app"
# LINKEDIN    = "https://www.linkedin.com/in/abdul-salam-39467a274"
# GITHUB      = "https://github.com/abdulsalam401"
# TOOL_NAME   = "Axiom"
# YEAR        = "2026"

# # ── Remote Controller Class ──────────────────────────────────────────────────────

# class RemoteController:
#     """Handle remote control of Android device via ADB."""
    
#     def __init__(self, device_id: str = None):
#         self.device_id = device_id
#         self.wifi_port = 5555
#         self.device_ip = None
#         self.connected_wireless = False
        
#     def _run_adb(self, args: list, capture=True):
#         cmd = ["adb"]
#         if self.device_id:
#             cmd += ["-s", self.device_id]
#         cmd += args
#         try:
#             r = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
#             return r.stdout.strip() if capture else r.returncode
#         except Exception as e:
#             return str(e)
    
#     def get_device_ip(self) -> Optional[str]:
#         out = self._run_adb(["shell", "ip addr show wlan0"])
#         match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
#         if match:
#             return match.group(1)
#         out = self._run_adb(["shell", "ifconfig wlan0"])
#         match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", out)
#         return match.group(1) if match else None
    
#     def setup_wireless_adb(self, port: int = 5555) -> bool:
#         console.print("[cyan]📡 Setting up ADB over WiFi...[/]")
#         ip = self.get_device_ip()
#         if not ip:
#             console.print("[red]✗ Could not get device IP. Make sure WiFi is ON.[/]")
#             return False
#         self.device_ip = ip
#         self.wifi_port = port
#         self._run_adb(["tcpip", str(port)])
#         time.sleep(2)
#         console.print(f"[green]✓ ADB over WiFi enabled on port {port}[/]")
#         console.print(f"[cyan]Device IP:[/] {ip}")
#         return True
    
#     def connect_wireless(self, ip: str = None, port: int = 5555) -> bool:
#         if not ip:
#             ip = self.device_ip or self.get_device_ip()
#         if not ip:
#             console.print("[red]✗ Cannot determine device IP[/]")
#             return False
#         console.print(f"[cyan]Connecting to {ip}:{port}...[/]")
#         subprocess.run(["adb", "kill-server"], capture_output=True)
#         time.sleep(1)
#         result = subprocess.run(["adb", "connect", f"{ip}:{port}"], 
#                                 capture_output=True, text=True)
#         if "connected" in result.stdout.lower():
#             self.device_id = f"{ip}:{port}"
#             self.connected_wireless = True
#             console.print(f"[bold green]✓ Connected wirelessly to {self.device_id}[/]")
#             return True
#         console.print(f"[red]✗ Connection failed: {result.stdout}[/]")
#         return False
    
#     def disconnect_wireless(self):
#         if self.device_id and ":" in self.device_id:
#             subprocess.run(["adb", "disconnect", self.device_id], capture_output=True)
#             console.print("[yellow]✓ Disconnected wireless ADB[/]")
#             self.connected_wireless = False
    
#     def capture_screen(self, output_path: str = None) -> Optional[str]:
#         if not output_path:
#             output_path = f"screenshot_{int(time.time())}.png"
#         remote_path = "/sdcard/screen_temp.png"
#         self._run_adb(["shell", "screencap", "-p", remote_path])
#         self._run_adb(["pull", remote_path, output_path])
#         self._run_adb(["shell", "rm", remote_path])
#         console.print(f"[green]✓ Screenshot saved: {output_path}[/]")
#         return output_path
    
#     def _image_to_ascii(self, image_path: str, width: int = 70) -> str:
#         """Convert image to ASCII art with safe integer handling."""
#         if not PIL_AVAILABLE:
#             return "[Pillow not installed. Run: pip install Pillow numpy]"
        
#         try:
#             img = Image.open(image_path)
#             aspect = img.height / img.width
#             height = max(1, int(width * aspect * 0.55))
#             img = img.resize((width, height))
#             if img.mode != 'L':
#                 img = img.convert('L')
#             chars = "@%#*+=-:. "
#             num_chars = len(chars)
#             pixels = np.array(img, dtype=np.uint8)
#             ascii_lines = []
#             for row in pixels:
#                 indices = (row.astype(np.float32) * (num_chars - 1) / 255).astype(np.uint8)
#                 line = ''.join(chars[idx] for idx in indices)
#                 ascii_lines.append(line)
#             return '\n'.join(ascii_lines)
#         except Exception as e:
#             return f"[Screen conversion error: {str(e)[:50]}]"
    
#     def stream_screen(self, refresh_rate: float = 1.0):
#         """Stream screen to terminal as ASCII art."""
#         if not PIL_AVAILABLE:
#             console.print("[red]✗ Pillow not installed. Run: pip install Pillow numpy[/]")
#             return
        
#         console.print(f"[cyan]🎥 Starting screen stream (refresh: {refresh_rate}s)[/]")
#         console.print("[dim]Press Ctrl+C to stop[/]")
        
#         temp_dir = tempfile.gettempdir()
#         frame_count = 0
        
#         try:
#             while True:
#                 remote_path = "/sdcard/stream_temp.png"
#                 local_path = os.path.join(temp_dir, f"frame_{frame_count}.png")
                
#                 self._run_adb(["shell", "screencap", "-p", remote_path])
#                 self._run_adb(["pull", remote_path, local_path])
#                 self._run_adb(["shell", "rm", remote_path])
                
#                 ascii_art = self._image_to_ascii(local_path, width=70)
#                 console.clear()
#                 console.print(Panel(
#                     ascii_art, 
#                     title="📱 Screen Stream", 
#                     border_style="cyan",
#                     subtitle=f"Frame: {frame_count} | Refresh: {refresh_rate}s"
#                 ))
                
#                 try:
#                     os.remove(local_path)
#                 except:
#                     pass
                
#                 frame_count += 1
#                 time.sleep(refresh_rate)
                
#         except KeyboardInterrupt:
#             console.print("\n[yellow]✓ Screen streaming stopped[/]")
    
#     def send_touch(self, x: int, y: int):
#         self._run_adb(["shell", f"input tap {x} {y}"])
#         console.print(f"[dim]Tap at ({x}, {y})[/]")
    
#     def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
#         self._run_adb(["shell", f"input swipe {x1} {y1} {x2} {y2} {duration}"])
#         console.print(f"[dim]Swiped ({x1},{y1}) → ({x2},{y2})[/]")
    
#     def send_text(self, text: str):
#         text_escaped = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'")
#         self._run_adb(["shell", f"input text '{text_escaped}'"])
#         console.print(f"[dim]Typed: {text}[/]")
    
#     def send_keyevent(self, keycode: str):
#         key_map = {
#             "home": "KEYCODE_HOME",
#             "back": "KEYCODE_BACK",
#             "menu": "KEYCODE_MENU",
#             "recent": "KEYCODE_APP_SWITCH",
#             "power": "KEYCODE_POWER",
#             "volume_up": "KEYCODE_VOLUME_UP",
#             "volume_down": "KEYCODE_VOLUME_DOWN",
#             "enter": "KEYCODE_ENTER",
#             "delete": "KEYCODE_DEL",
#             "up": "KEYCODE_DPAD_UP",
#             "down": "KEYCODE_DPAD_DOWN",
#             "left": "KEYCODE_DPAD_LEFT",
#             "right": "KEYCODE_DPAD_RIGHT",
#         }
#         key = key_map.get(keycode.lower(), keycode.upper())
#         self._run_adb(["shell", f"input keyevent {key}"])
#         console.print(f"[dim]Key: {keycode}[/]")
    
#     def get_screen_size(self) -> Tuple[int, int]:
#         out = self._run_adb(["shell", "wm size"])
#         match = re.search(r"Physical size: (\d+)x(\d+)", out)
#         if match:
#             return int(match.group(1)), int(match.group(2))
#         return 1080, 2400
    
#     def interactive_remote_control(self):
#         """Interactive remote control session."""
#         console.rule("[bold magenta]🎮 Interactive Remote Control[/]")
        
#         screen_w, screen_h = self.get_screen_size()
#         console.print(f"[dim]Screen: {screen_w}x{screen_h}[/]")
        
#         console.print("""
# [bold cyan]Commands:[/]
#   [green]tap x y[/green]         → Touch at coordinates
#   [green]swipe x1 y1 x2 y2[/green] → Swipe gesture
#   [green]text "message"[/green]   → Type text
#   [green]home, back, menu[/green] → Navigation keys
#   [green]up, down, left, right[/green] → D-pad
#   [green]screenshot[/green]       → Capture screen
#   [green]stream [rate][/green]    → Start streaming (rate in seconds)
#   [green]info[/green]            → Show device info
#   [green]help[/green]            → Show this help
#   [green]exit[/green]            → Exit remote control
#         """)
        
#         while True:
#             try:
#                 cmd = input("\n[bold magenta]Remote[/] > ").strip().lower()
                
#                 if cmd == "exit":
#                     break
#                 elif cmd == "screenshot":
#                     self.capture_screen()
#                 elif cmd.startswith("stream"):
#                     parts = cmd.split()
#                     rate = float(parts[1]) if len(parts) > 1 else 1.0
#                     self.stream_screen(rate)
#                 elif cmd.startswith("tap "):
#                     parts = cmd.split()
#                     if len(parts) == 3:
#                         self.send_touch(int(parts[1]), int(parts[2]))
#                     else:
#                         console.print("[yellow]Usage: tap x y[/]")
#                 elif cmd.startswith("swipe "):
#                     parts = cmd.split()
#                     if len(parts) == 5:
#                         self.send_swipe(int(parts[1]), int(parts[2]), 
#                                         int(parts[3]), int(parts[4]))
#                     else:
#                         console.print("[yellow]Usage: swipe x1 y1 x2 y2[/]")
#                 elif cmd.startswith("text "):
#                     text = cmd[5:].strip('"\'')
#                     self.send_text(text)
#                 elif cmd in ["home", "back", "menu", "recent", "power", 
#                             "volume_up", "volume_down", "enter", "delete",
#                             "up", "down", "left", "right"]:
#                     self.send_keyevent(cmd)
#                 elif cmd == "info":
#                     adb_manager.device_info(self.device_id)
#                 elif cmd == "help":
#                     console.print("Commands: tap x y, swipe x1 y1 x2 y2, text 'msg', screenshot, stream [rate], home, back, menu, info, exit")
#                 elif cmd == "":
#                     continue
#                 else:
#                     console.print("[yellow]Unknown command. Type 'help' for options.[/]")
#             except KeyboardInterrupt:
#                 console.print("\n[yellow]Exiting remote control...[/]")
#                 break


# # ─── Remote Control Helper Functions ──────────────────────────────────────────

# _REMOTE_SESSION_FILE = os.path.expanduser("~/.axiom_remote.json")

# def _save_remote_session(controller: RemoteController):
#     """Save wireless session info."""
#     data = {
#         "device_id": controller.device_id,
#         "device_ip": controller.device_ip,
#         "wifi_port": controller.wifi_port,
#         "timestamp": time.time()
#     }
#     with open(_REMOTE_SESSION_FILE, "w") as f:
#         json.dump(data, f)
#     console.print("[dim]Session saved for next time[/]")


# def _load_remote_session() -> Optional[RemoteController]:
#     """Load saved wireless session."""
#     if os.path.exists(_REMOTE_SESSION_FILE):
#         try:
#             with open(_REMOTE_SESSION_FILE, "r") as f:
#                 data = json.load(f)
#             if time.time() - data.get("timestamp", 0) < 86400:
#                 controller = RemoteController()
#                 if controller.connect_wireless(data.get("device_ip"), data.get("wifi_port", 5555)):
#                     return controller
#         except:
#             pass
#     return None


# def _get_remote_controller() -> Optional[RemoteController]:
#     """Get existing remote controller or create new one."""
#     controller = _load_remote_session()
#     if not controller:
#         ip = Prompt.ask("[cyan]Enter device IP[/]")
#         port = IntPrompt.ask("[cyan]Port[/]", default=5555)
#         controller = RemoteController()
#         if controller.connect_wireless(ip, port):
#             _save_remote_session(controller)
#         else:
#             return None
#     return controller


# def one_time_setup(device_id: str = None, port: int = 5555) -> Optional[RemoteController]:
#     """Complete one-time setup: USB → Enable WiFi → Disconnect USB → Reconnect Wireless"""
#     console.print(Panel(
#         "[bold cyan]Axiom Remote Control Setup[/]\n\n"
#         "This will:\n"
#         "1. Check USB connection\n"
#         "2. Enable ADB over WiFi on device\n"
#         "3. Get device IP address\n"
#         "4. Allow you to disconnect USB\n"
#         "5. Reconnect wirelessly",
#         border_style="magenta"
#     ))
    
#     controller = RemoteController(device_id)
    
#     console.print("\n[1/5] Checking USB connection...")
#     devices_out = controller._run_adb(["devices"])
#     if "device" not in devices_out:
#         console.print("[red]✗ No device connected via USB. Please connect your phone.[/]")
#         return None
    
#     console.print("[green]✓ Device connected via USB[/]")
    
#     console.print("\n[2/5] Enabling ADB over WiFi...")
#     if not controller.setup_wireless_adb(port):
#         console.print("[red]✗ Failed to enable WiFi ADB[/]")
#         return None
    
#     console.print("\n[3/5] Getting device IP...")
#     ip = controller.device_ip
#     console.print(f"[green]✓ Device IP: {ip}[/]")
    
#     console.print(f"""
# [4/5] [bold yellow]ACTION REQUIRED[/]
# 1. Disconnect the USB cable from your device NOW
# 2. Make sure device is still connected to WiFi
# 3. Press Enter when ready to connect wirelessly
#     """)
#     input("Press Enter to continue...")
    
#     console.print("\n[5/5] Connecting wirelessly...")
#     if controller.connect_wireless(ip, port):
#         console.print(Panel(
#             f"[bold green]✓ Remote control ready![/]\n"
#             f"Device: {controller.device_id}\n"
#             f"IP: {ip}:{port}\n\n"
#             f"Use option 16 in interactive menu for remote control",
#             border_style="green"
#         ))
#         _save_remote_session(controller)
#         return controller
#     else:
#         console.print("[red]✗ Wireless connection failed. Make sure device is on same WiFi network.[/]")
#         return None


# def quick_reconnect(ip: str = None, port: int = 5555) -> Optional[RemoteController]:
#     """Quickly reconnect to a previously paired device."""
#     controller = RemoteController()
    
#     if not ip:
#         ip = Prompt.ask("[cyan]Enter device IP[/]", default="")
#         if not ip:
#             return None
    
#     if controller.connect_wireless(ip, port):
#         _save_remote_session(controller)
#         return controller
#     return None


# def remote_control_menu():
#     """Display remote control menu."""
#     options = [
#         ("1", "🔌 One-Time Setup (USB → Wireless)"),
#         ("2", "🔗 Quick Reconnect to Saved Device"),
#         ("3", "🎮 Interactive Remote Control"),
#         ("4", "📸 Screen Capture"),
#         ("5", "🎥 Screen Stream (ASCII)"),
#         ("6", "👆 Touch/Swipe Controls"),
#         ("7", "⌨️  Keyboard Input"),
#         ("8", "📱 Device Info"),
#         ("9", "🔄 Reconnect to Wireless Device"),
#         ("0", "🔌 Disconnect & Back"),
#     ]
    
#     table = Table(title="[bold magenta]🎮 Axiom Remote Control[/]",
#                   box=box.DOUBLE_EDGE, border_style="magenta")
#     table.add_column("Option", style="cyan", width=6)
#     table.add_column("Action", style="white")
    
#     for num, desc in options:
#         table.add_row(f"[{num}]", desc)
    
#     console.print(table)
#     return options


# # ═══════════════════════════════════════════════════════════════════════════════
# #  BANNER & ANIMATION
# # ═══════════════════════════════════════════════════════════════════════════════

# BANNER_ART = r"""
#     _    __  __ _   ___   __  __ 
#    / \   \ \/ /| | / _ \ |  \/  |
#   / _ \   \  / | || | | || |\/| |
#  / ___ \   /  \| || |_| || |  | |
# /_/   \_\ /_/\_\_| \___/ |_|  |_|
# """

# BANNER_LINES_GRADIENT = [
#     "magenta", "bright_magenta", "purple", "deep_pink3", "orchid", "violet"
# ]

# def get_banner_status():
#     """Gather live status info for the banner."""
#     try:
#         devices = adb_manager.list_devices()
#         device_count = len(devices)
#         status_color = "green" if device_count > 0 else "red"
#         device_text = f"[{status_color}]{device_count} Connected[/]"
#     except:
#         device_text = "[yellow]ADB Not Found[/]"

#     now = datetime.now().strftime("%H:%M:%S")
    
#     return (
#         f"📅 [bold white]{now}[/]  |  "
#         f"📱 [bold cyan]Devices:[/] {device_text}  |  "
#         f"🚀 [bold green]v{VERSION}[/]"
#     )

# def animate_glitch_banner():
#     """Display a matrix/glitch reveal for the banner."""
#     from rich.markup import escape
#     lines = BANNER_ART.strip("\n").split("\n")
    
#     chars = "01$#!@%^&*()_+=-[]{}|;:,.<>?/"
#     for _ in range(12):
#         glitch_lines = []
#         for line in lines:
#             glitch_line = "".join(random.choice(chars) if c != " " else " " for c in line)
#             color = random.choice(BANNER_LINES_GRADIENT)
#             glitch_lines.append(f"[bold {color}]{escape(glitch_line)}[/]")
        
#         console.clear()
#         for gl in glitch_lines:
#             console.print(Align.center(gl))
#         time.sleep(0.06)

#     console.clear()
#     for i, line in enumerate(lines):
#         color = BANNER_LINES_GRADIENT[i % len(BANNER_LINES_GRADIENT)]
#         console.print(Align.center(f"[bold {color}]{line}[/]"))
#         time.sleep(0.05)

# def print_banner():
#     """Print the animated Axiom banner with live status."""
#     animate_glitch_banner()

#     tagline = Text("◈ ADVANCED ANDROID PENTESTING FRAMEWORK ◈", style="bold italic bright_magenta")
#     console.print(Align.center(tagline))
#     console.print()

#     status_text = get_banner_status()
#     console.print(Align.center(Panel(
#         status_text,
#         border_style="magenta",
#         box=box.HORIZONTALS,
#         padding=(0, 2),
#         title="[bold magenta]System Status[/]",
#         title_align="left"
#     )))
#     console.print()


# # ═══════════════════════════════════════════════════════════════════════════════
# #  MAIN MENU
# # ═══════════════════════════════════════════════════════════════════════════════

# MENU_OPTIONS = [
#     ("1",  "📱", "Device Manager",          "List & manage connected Android devices"),
#     ("2",  "🔎", "APK Static Analyzer",     "Decompile & audit an APK file"),
#     ("3",  "🌐", "Network Scanner",         "Port scan, WiFi info, host discovery"),
#     ("4",  "🚨", "Vulnerability Scanner",   "CVE mapping, root check, insecure storage"),
#     ("5",  "💥", "Exploit Engine",          "Launch activities, deep links, shell dropper"),
#     ("6",  "🎯", "Payload Generator",       "APK payloads, reverse shells, obfuscation"),
#     ("7",  "📋", "Report Generator",        "Generate HTML/JSON security report"),
#     ("8",  "📡", "ADB WiFi Connect",        "Enable & connect ADB over WiFi"),
#     ("9",  "📸", "Screenshot Capture",      "Capture device screenshot via ADB"),
#     ("10", "📦", "Package Manager",         "Enumerate installed packages"),
#     ("11", "🐛", "Logcat Analyzer",         "Capture & analyze logcat for secrets"),
#     ("12", "🔐", "SSL Pinning Check",       "Detect SSL pinning in target app"),
#     ("13", "📂", "File Transfer",           "Pull/push files from/to device"),
#     ("14", "💻", "Interactive ADB Shell",   "Drop into live ADB shell"),
#     ("15", "ℹ️ ", "About",                   "About Axiom"),
#     ("16", "🎮", "Remote Control",          "Wireless control & screen mirroring"),
#     ("17", "🖥️", "GUI Remote Control",      "Real graphical screen mirroring"),
#     ("0",  "🚪", "Exit",                    "Exit Axiom"),
# ]


# def print_main_menu():
#     t = Table(
#         title=f"\n[bold magenta]🔮  {TOOL_NAME}  —  Main Menu[/]\n",
#         box=box.DOUBLE_EDGE,
#         border_style="magenta",
#         header_style="bold cyan",
#         show_lines=True,
#         min_width=70,
#     )
#     t.add_column("  #  ",   style="bold cyan",   width=5,  no_wrap=True)
#     t.add_column("  ",      style="",             width=3,  no_wrap=True)
#     t.add_column("Module",  style="bold white",   min_width=24)
#     t.add_column("Description", style="dim",      min_width=38)

#     for num, icon, name, desc in MENU_OPTIONS:
#         style = "on #1a0030" if num == "0" else ""
#         t.add_row(f"[bold cyan] {num} [/]", icon, name, desc, style=style)

#     console.print(t)


# # ═══════════════════════════════════════════════════════════════════════════════
# #  DEVICE SELECTION HELPER
# # ═══════════════════════════════════════════════════════════════════════════════

# def select_device() -> Optional[str]:
#     """Select a connected device; return its serial."""
#     devices = adb_manager.list_devices()
#     if not devices:
#         return None
#     if len(devices) == 1:
#         dev = devices[0]["serial"]
#         console.print(f"[green]Auto-selected device:[/] {dev}")
#         return dev
#     serial = Prompt.ask("[cyan]Enter device serial[/]")
#     return serial


# # ═══════════════════════════════════════════════════════════════════════════════
# #  MODULE HANDLERS
# # ═══════════════════════════════════════════════════════════════════════════════

# def handle_device_manager():
#     console.rule("[bold magenta]📱 Device Manager[/]")
#     adb_manager.check_adb()
#     device_id = select_device()
#     if not device_id:
#         return
#     adb_manager.device_info(device_id)


# def handle_apk_analyzer():
#     console.rule("[bold magenta]🔎 APK Static Analyzer[/]")
#     apk_path = Prompt.ask("[cyan]APK file path[/]")
#     findings = apk_analyzer.analyze_apk(apk_path)
#     if Confirm.ask("[cyan]Save findings to report?[/]", default=True):
#         _save_to_session(findings, "apk_analysis")
#         console.print("[green]✓ Added to session report.[/]")


# def handle_network_scanner():
#     console.rule("[bold magenta]🌐 Network Scanner[/]")
#     choice = Prompt.ask("[cyan]Scan mode[/]", choices=["device", "host", "wifi", "discover", "mitm"], default="device")

#     if choice == "device":
#         device_id = select_device()
#         if not device_id:
#             return
#         ip = network_scanner.get_device_ip(device_id)
#         if ip:
#             console.print(f"[green]Device IP:[/] {ip}")
#             network_scanner.port_scan(ip)
#         else:
#             console.print("[red]Could not determine device IP.[/]")

#     elif choice == "host":
#         target = Prompt.ask("[cyan]Target IP/hostname[/]")
#         port_range = Prompt.ask("[cyan]Port range (comma-list or 'all')[/]", default="common")
#         if port_range == "all":
#             ports = list(range(1, 65536))
#         elif port_range == "common":
#             ports = None
#         else:
#             ports = [int(p.strip()) for p in port_range.split(",") if p.strip().isdigit()]
#         network_scanner.port_scan(target, ports)

#     elif choice == "wifi":
#         device_id = select_device()
#         if device_id:
#             network_scanner.get_wifi_info(device_id)

#     elif choice == "discover":
#         subnet = Prompt.ask("[cyan]Subnet (e.g. 192.168.1)[/]")
#         network_scanner.discover_devices(subnet)

#     elif choice == "mitm":
#         network_scanner.mitm_setup_guide()


# def handle_vulnerability_scanner():
#     console.rule("[bold magenta]🚨 Vulnerability Scanner[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     pkg = Prompt.ask("[cyan]Target package (leave blank for device-level only)[/]", default="")
#     report = vulnerability_scanner.full_vulnerability_scan(device_id, pkg or None)
#     _save_to_session(report, "vulnerability_scan")


# def handle_exploit_engine():
#     console.rule("[bold magenta]💥 Exploit Engine[/]")
#     device_id = select_device()
#     if not device_id:
#         return

#     exploit_engine.exploit_menu(device_id)
#     choice = Prompt.ask("[red]Select exploit[/]", choices=[str(i) for i in range(10)])

#     if choice == "1":
#         pkg = Prompt.ask("[cyan]Package name[/]")
#         act = Prompt.ask("[cyan]Activity class[/]")
#         exploit_engine.launch_exported_activity(device_id, pkg, act)

#     elif choice == "2":
#         pkg = Prompt.ask("[cyan]Package name[/]")
#         action = Prompt.ask("[cyan]Intent action[/]")
#         exploit_engine.trigger_broadcast_receiver(device_id, pkg, action)

#     elif choice == "3":
#         uri = Prompt.ask("[cyan]Content provider URI (content://...)[/]")
#         exploit_engine.extract_content_provider(device_id, uri)

#     elif choice == "4":
#         pkg = Prompt.ask("[cyan]Package name[/]")
#         scheme = Prompt.ask("[cyan]Deep link scheme (e.g. myapp)[/]")
#         exploit_engine.deep_link_fuzzer(device_id, pkg, scheme)

#     elif choice == "5":
#         pkg = Prompt.ask("[cyan]Package name[/]")
#         exploit_engine.frida_injection_guide(pkg)

#     elif choice == "6":
#         lhost = Prompt.ask("[cyan]LHOST[/]")
#         lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
#         exploit_engine.shell_payload_dropper(device_id, lhost, lport)

#     elif choice == "7":
#         pkg = Prompt.ask("[cyan]Package name[/]")
#         db = Prompt.ask("[cyan]Database filename[/]")
#         exploit_engine.extract_database(device_id, pkg, db)

#     elif choice == "8":
#         exploit_engine.bypass_lock_screen(device_id)

#     elif choice == "9":
#         exploit_engine.enable_developer_options(device_id)


# def handle_payload_generator():
#     console.rule("[bold magenta]🎯 Payload Generator[/]")
#     payload_generator.payload_menu()
#     choice = Prompt.ask("[red]Select payload type[/]", choices=["1", "2", "3", "4", "5", "0"])

#     if choice == "1":
#         lhost = Prompt.ask("[cyan]LHOST[/]")
#         lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
#         ptype = Prompt.ask("[cyan]Payload type[/]",
#                              choices=["reverse_tcp", "reverse_https", "reverse_http", "shell_tcp"],
#                              default="reverse_tcp")
#         output = Prompt.ask("[cyan]Output file[/]", default="payload.apk")
#         payload_generator.generate_msfvenom_apk(lhost, lport, ptype, output)

#     elif choice == "2":
#         action = Prompt.ask("[cyan]Intent action[/]")
#         comp = Prompt.ask("[cyan]Component (pkg/class or blank)[/]", default="")
#         data = Prompt.ask("[cyan]Data URI (or blank)[/]", default="")
#         payload_generator.generate_intent_payload(action, comp or None, data or None)

#     elif choice == "3":
#         lhost = Prompt.ask("[cyan]LHOST[/]")
#         lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
#         payload_generator.generate_reverse_shell_commands(lhost, lport)

#     elif choice == "4":
#         lhost = Prompt.ask("[cyan]LHOST[/]")
#         lport = IntPrompt.ask("[cyan]LPORT[/]", default=4444)
#         output = Prompt.ask("[cyan]Script filename[/]", default="adb_payload.sh")
#         payload_generator.generate_adb_payload_script(None, lhost, lport, output)

#     elif choice == "5":
#         raw = Prompt.ask("[cyan]Payload to obfuscate[/]")
#         method = Prompt.ask("[cyan]Obfuscation method[/]", choices=["base64", "hex"], default="base64")
#         payload_generator.obfuscate_payload(raw, method)


# def handle_report_generator():
#     console.rule("[bold magenta]📋 Report Generator[/]")
#     target = Prompt.ask("[cyan]Target description (app/device name)[/]", default="Unknown Target")

#     data = _get_session()
#     data["target"] = target

#     fmt = Prompt.ask("[cyan]Report format[/]", choices=["html", "json", "both", "table"], default="html")

#     if fmt in ("html", "both"):
#         out = Prompt.ask("[cyan]HTML output filename[/]", default="axiom_report.html")
#         report_generator.generate_html_report(data, out)

#     if fmt in ("json", "both"):
#         out = Prompt.ask("[cyan]JSON output filename[/]", default="axiom_report.json")
#         report_generator.generate_json_report(data, out)

#     if fmt == "table":
#         report_generator.print_summary_table(data)


# def handle_adb_wifi():
#     console.rule("[bold magenta]📡 ADB WiFi Connect[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     port = IntPrompt.ask("[cyan]Port[/]", default=5555)
#     ip, p = adb_manager.enable_adb_wifi(device_id, port)


# def handle_screenshot():
#     console.rule("[bold magenta]📸 Screenshot Capture[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     path = adb_manager.take_screenshot(device_id)
#     if path:
#         console.print(f"[bold green]✓ Screenshot saved:[/] {path}")


# def handle_package_manager():
#     console.rule("[bold magenta]📦 Package Manager[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     pkg_type = Prompt.ask("[cyan]Package filter[/]",
#                            choices=["all", "system", "third_party", "disabled"],
#                            default="third_party")
#     adb_manager.list_packages(device_id, pkg_type)


# def handle_logcat():
#     console.rule("[bold magenta]🐛 Logcat Analyzer[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     lines = IntPrompt.ask("[cyan]Lines to capture[/]", default=300)
#     adb_manager.capture_logcat(device_id, lines)


# def handle_ssl_check():
#     console.rule("[bold magenta]🔐 SSL Pinning Check[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     pkg = Prompt.ask("[cyan]Package name[/]")
#     network_scanner.check_ssl_pinning(device_id, pkg)


# def handle_file_transfer():
#     console.rule("[bold magenta]📂 File Transfer[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     direction = Prompt.ask("[cyan]Direction[/]", choices=["pull", "push"])
#     if direction == "pull":
#         remote = Prompt.ask("[cyan]Remote path (on device)[/]")
#         local = Prompt.ask("[cyan]Local destination[/]", default=".")
#         adb_manager.pull_file(device_id, remote, local)
#     else:
#         local = Prompt.ask("[cyan]Local file path[/]")
#         remote = Prompt.ask("[cyan]Remote destination (on device)[/]")
#         adb_manager.push_file(device_id, local, remote)


# def handle_adb_shell():
#     console.rule("[bold magenta]💻 Interactive ADB Shell[/]")
#     device_id = select_device()
#     if not device_id:
#         return
#     adb_manager.interactive_shell(device_id)


# def handle_about():
#     about = Panel(
#         f"\n"
#         f"  [bold magenta]🔮  {TOOL_NAME} v{VERSION}[/]\n\n"
#         f"  [bold cyan]Advanced Android Penetration Testing Framework[/]\n\n"
#         f"  [white]A comprehensive tool for ethical hackers and security professionals.\n"
#         f"  Covers static APK analysis, dynamic runtime analysis via ADB,\n"
#         f"  network scanning, vulnerability mapping, exploit assistance,\n"
#         f"  payload generation, professional report generation, and\n"
#         f"  [bold green]wireless remote control with screen mirroring[/].\n\n"
#         f"  [bold magenta]Author   :[/] [white]{AUTHOR}[/]\n"
#         f"  [bold magenta]Website  :[/] [cyan]{WEBSITE}[/]\n"
#         f"  [bold magenta]LinkedIn :[/] [cyan]{LINKEDIN}[/]\n"
#         f"  [bold magenta]GitHub   :[/] [cyan]{GITHUB}[/]\n"
#         f"  [bold magenta]Year     :[/] [white]{YEAR}[/]\n\n"
#         f"  [bold red]⚠  For authorized penetration testing use only.[/]\n"
#         f"  [dim]Unauthorized use is illegal and unethical.[/]\n",
#         title="[bold]About Axiom[/]",
#         border_style="magenta",
#         padding=(0, 4),
#     )
#     console.print(about)


# def handle_remote_control():
#     """Handle remote control module."""
#     console.rule("[bold magenta]🎮 Remote Control[/]")
    
#     console.print(Panel(
#         "[bold yellow]⚠ SECURITY WARNING[/]\n\n"
#         "ADB over WiFi exposes your device to the network.\n"
#         "Anyone on the same WiFi can connect if port 5555 is open.\n\n"
#         "Recommended precautions:\n"
#         "• Use on trusted networks ONLY\n"
#         "• Disable ADB over WiFi when not in use\n"
#         "• Run 'adb disconnect' after finishing",
#         border_style="yellow"
#     ))
    
#     if not Confirm.ask("\n[cyan]I understand the security implications[/]", default=False):
#         console.print("[yellow]Returning to main menu.[/]")
#         return
    
#     remote_control_menu()
#     choice = Prompt.ask("[cyan]Select option[/]", choices=[str(i) for i in range(10)])
    
#     if choice == "1":
#         device_id = select_device()
#         if device_id:
#             one_time_setup(device_id)
#         else:
#             console.print("[red]No device connected via USB.[/]")
    
#     elif choice == "2":
#         controller = _load_remote_session()
#         if controller:
#             console.print("[green]✓ Reconnected to saved device![/]")
#         else:
#             console.print("[yellow]No saved session found. Use option 1 first or option 9 to connect manually.[/]")
    
#     elif choice == "3":
#         controller = _get_remote_controller()
#         if controller:
#             controller.interactive_remote_control()
    
#     elif choice == "4":
#         controller = _get_remote_controller()
#         if controller:
#             controller.capture_screen()
    
#     elif choice == "5":
#         controller = _get_remote_controller()
#         if controller:
#             if not PIL_AVAILABLE:
#                 console.print("[red]✗ Pillow not installed. Run: pip install Pillow numpy[/]")
#                 return
#             rate = float(Prompt.ask("[cyan]Refresh rate (seconds)[/]", default="1.0"))
#             controller.stream_screen(rate)
    
#     elif choice == "6":
#         controller = _get_remote_controller()
#         if controller:
#             screen_w, screen_h = controller.get_screen_size()
#             console.print(f"[dim]Screen: {screen_w}x{screen_h}[/]")
#             action = Prompt.ask("[cyan]Action (tap/swipe)[/]", choices=["tap", "swipe"])
#             if action == "tap":
#                 x = IntPrompt.ask("[cyan]X coordinate[/]", default=screen_w//2)
#                 y = IntPrompt.ask("[cyan]Y coordinate[/]", default=screen_h//2)
#                 controller.send_touch(x, y)
#             else:
#                 x1 = IntPrompt.ask("[cyan]Start X[/]")
#                 y1 = IntPrompt.ask("[cyan]Start Y[/]")
#                 x2 = IntPrompt.ask("[cyan]End X[/]")
#                 y2 = IntPrompt.ask("[cyan]End Y[/]")
#                 duration = IntPrompt.ask("[cyan]Duration (ms)[/]", default=300)
#                 controller.send_swipe(x1, y1, x2, y2, duration)
    
#     elif choice == "7":
#         controller = _get_remote_controller()
#         if controller:
#             text = Prompt.ask("[cyan]Text to type[/]")
#             controller.send_text(text)
    
#     elif choice == "8":
#         controller = _get_remote_controller()
#         if controller:
#             adb_manager.device_info(controller.device_id)
    
#     elif choice == "9":
#         ip = Prompt.ask("[cyan]Device IP[/]")
#         port = IntPrompt.ask("[cyan]Port[/]", default=5555)
#         controller = RemoteController()
#         if controller.connect_wireless(ip, port):
#             _save_remote_session(controller)
    
#     elif choice == "0":
#         controller = _load_remote_session()
#         if controller:
#             controller.disconnect_wireless()
#             if os.path.exists(_REMOTE_SESSION_FILE):
#                 os.remove(_REMOTE_SESSION_FILE)
#                 console.print("[dim]Saved session cleared[/]")


# def handle_gui_remote():
#     """Handle GUI remote control."""
#     console.rule("[bold magenta]🖥️ GUI Remote Control[/]")
    
#     console.print(Panel(
#         "[bold cyan]Real-time Graphical Remote Control[/]\n\n"
#         "This opens a window showing your phone screen in real-time.\n"
#         "You can click/tap and use keyboard to control your phone.",
#         border_style="cyan"
#     ))
    
#     ip = Prompt.ask("[cyan]Device IP (press Enter to auto-detect)[/]", default="")
#     port = IntPrompt.ask("[cyan]ADB port[/]", default=5555)
    
#     # Import and start GUI remote
#     try:
#         from modules.gui_remote import start_gui_remote
#         start_gui_remote(ip if ip else None, port)
#     except ImportError as e:
#         console.print(f"[red]✗ Could not import GUI remote module: {e}[/]")
#         console.print("[yellow]Make sure modules/gui_remote.py exists[/]")
#     except Exception as e:
#         console.print(f"[red]✗ Error starting GUI remote: {e}[/]")


# # ═══════════════════════════════════════════════════════════════════════════════
# #  SESSION STORE (in-memory findings accumulator)
# # ═══════════════════════════════════════════════════════════════════════════════

# _SESSION = {"findings": [], "permissions": [], "secrets": [], "urls": []}


# def _save_to_session(data: dict, source: str):
#     """Merge findings from a module into the session store."""
#     if isinstance(data, dict):
#         for vuln in data.get("vulnerabilities", []):
#             _SESSION["findings"].append(vuln)
#         for vuln in data.get("cves", []):
#             _SESSION["findings"].append({
#                 "name": vuln.get("cve", "CVE"),
#                 "severity": vuln.get("severity", "MEDIUM"),
#                 "detail": vuln.get("detail", ""),
#                 "cve": vuln.get("cve"),
#             })
#         _SESSION["permissions"].extend(data.get("dangerous_permissions", []))
#         _SESSION["secrets"].extend(data.get("secrets", []))
#         _SESSION["urls"].extend(data.get("urls", []))


# def _get_session() -> dict:
#     return _SESSION.copy()


# # ═══════════════════════════════════════════════════════════════════════════════
# #  INTERACTIVE MODE
# # ═══════════════════════════════════════════════════════════════════════════════

# HANDLER_MAP = {
#     "1":  handle_device_manager,
#     "2":  handle_apk_analyzer,
#     "3":  handle_network_scanner,
#     "4":  handle_vulnerability_scanner,
#     "5":  handle_exploit_engine,
#     "6":  handle_payload_generator,
#     "7":  handle_report_generator,
#     "8":  handle_adb_wifi,
#     "9":  handle_screenshot,
#     "10": handle_package_manager,
#     "11": handle_logcat,
#     "12": handle_ssl_check,
#     "13": handle_file_transfer,
#     "14": handle_adb_shell,
#     "15": handle_about,
#     "16": handle_remote_control,
#     "17": handle_gui_remote,
# }


# def interactive_mode():
#     print_banner()
#     console.print(Panel(
#         "[bold red]⚠  LEGAL DISCLAIMER[/]\n\n"
#         "[white]Axiom is designed for authorized security testing ONLY.\n"
#         "Use of this tool against systems you do not own or have explicit written\n"
#         "permission to test is [bold red]ILLEGAL[/] and may result in criminal prosecution.\n"
#         "The author assumes no liability for misuse.[/]",
#         border_style="red", padding=(0, 2)))

#     if not Confirm.ask("\n[bold red]I confirm I have authorization to test the target system[/]", default=False):
#         console.print("[yellow]Exiting. Obtain proper authorization before testing.[/]")
#         sys.exit(0)

#     while True:
#         console.print()
#         print_main_menu()
#         valid_choices = [str(i) for i in range(18)]  # 0-17
#         choice = Prompt.ask("\n[bold cyan]Axiom ▶[/]", choices=valid_choices, show_choices=False)

#         if choice == "0":
#             if os.path.exists(_REMOTE_SESSION_FILE):
#                 try:
#                     controller = _load_remote_session()
#                     if controller:
#                         controller.disconnect_wireless()
#                 except:
#                     pass
#             console.print("\n[bold magenta]🔮 Exiting Axiom. Stay ethical.[/]\n")
#             sys.exit(0)

#         handler = HANDLER_MAP.get(choice)
#         if handler:
#             try:
#                 console.print()
#                 handler()
#             except KeyboardInterrupt:
#                 console.print("\n[yellow]↩ Returned to main menu.[/]")
#             except Exception as e:
#                 console.print(f"\n[bold red]✗ Error:[/] {e}")
#         else:
#             console.print("[red]Invalid option.[/]")

#         console.print()
#         Prompt.ask("[dim]Press ENTER to continue[/]", default="")


# # ═══════════════════════════════════════════════════════════════════════════════
# #  CLI MODE (argparse)
# # ═══════════════════════════════════════════════════════════════════════════════

# def build_parser() -> argparse.ArgumentParser:
#     p = argparse.ArgumentParser(
#         prog="axiom",
#         description=f"🔮 Axiom v{VERSION} — Advanced Android Pentesting Tool by {AUTHOR}",
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Examples:
#   python3 axiom.py --interactive
#   python3 axiom.py --apk app.apk --report html
#   python3 axiom.py --device ABC123 --vuln-scan --pkg com.example.app
#   python3 axiom.py --device ABC123 --port-scan
#   python3 axiom.py --payload reverse_tcp --lhost 10.0.0.1 --lport 4444
#   python3 axiom.py --remote-setup
#   python3 axiom.py --remote-control --remote-ip 192.168.1.100
#   python3 axiom.py --remote-stream --remote-ip 192.168.1.100 --refresh 0.5
#   python3 axiom.py --gui-remote --remote-ip 192.168.1.100
#   python3 axiom.py --devices
#         """
#     )

#     p.add_argument("--interactive", "-i",  action="store_true",    help="Launch interactive menu mode")
#     p.add_argument("--version",     "-v",  action="store_true",    help="Show version")

#     # Device
#     dg = p.add_argument_group("Device")
#     dg.add_argument("--devices",           action="store_true",    help="List connected devices")
#     dg.add_argument("--device", "-d",      metavar="SERIAL",       help="Target device serial number")
#     dg.add_argument("--info",              action="store_true",    help="Show device info")
#     dg.add_argument("--shell",             metavar="CMD",          help="Run ADB shell command")
#     dg.add_argument("--adb-shell",         action="store_true",    help="Drop into interactive ADB shell")
#     dg.add_argument("--adb-wifi",          action="store_true",    help="Enable ADB over WiFi")
#     dg.add_argument("--screenshot",        action="store_true",    help="Capture device screenshot")
#     dg.add_argument("--logcat",            metavar="N", type=int,  help="Capture N lines of logcat", nargs="?", const=200)
#     dg.add_argument("--packages",          choices=["all","system","third_party","disabled"],
#                                                                    help="List installed packages")
#     dg.add_argument("--pull",              metavar="REMOTE",       help="Pull file from device")
#     dg.add_argument("--push",             nargs=2, metavar=("LOCAL","REMOTE"), help="Push file to device")

#     # Remote Control
#     rc = p.add_argument_group("Remote Control")
#     rc.add_argument("--remote-setup",      action="store_true",    help="One-time USB to wireless setup")
#     rc.add_argument("--remote-connect",    action="store_true",    help="Connect to saved wireless device")
#     rc.add_argument("--remote-control",    action="store_true",    help="Start interactive remote control")
#     rc.add_argument("--remote-screenshot", action="store_true",    help="Capture screenshot via wireless")
#     rc.add_argument("--remote-stream",     action="store_true",    help="Stream screen as ASCII")
#     rc.add_argument("--refresh",           type=float, default=1.0, help="Stream refresh rate (seconds)")
#     rc.add_argument("--remote-tap",        nargs=2, metavar=("X","Y"), type=int, help="Send touch event")
#     rc.add_argument("--remote-swipe",      nargs=5, metavar=("X1","Y1","X2","Y2","DUR"), help="Send swipe gesture")
#     rc.add_argument("--remote-text",       metavar="TEXT",         help="Send text input")
#     rc.add_argument("--remote-key",        metavar="KEY",          help="Send keyevent (home, back, menu, etc.)")
#     rc.add_argument("--remote-ip",         metavar="IP",           help="Device IP for wireless connection")
#     rc.add_argument("--remote-port",       type=int, default=5555, help="ADB over WiFi port")
#     rc.add_argument("--gui-remote",        action="store_true",    help="Start GUI remote control")

#     # APK Analysis
#     ag = p.add_argument_group("APK Analysis")
#     ag.add_argument("--apk",              metavar="FILE",          help="APK file to analyze")

#     # Network
#     ng = p.add_argument_group("Network")
#     ng.add_argument("--port-scan",        action="store_true",    help="Port scan device IP")
#     ng.add_argument("--target",           metavar="IP",           help="Explicit scan target IP")
#     ng.add_argument("--ports",            metavar="PORTS",        help="Comma-separated ports or 'all'")
#     ng.add_argument("--wifi-info",        action="store_true",    help="Show WiFi info")
#     ng.add_argument("--discover",         metavar="SUBNET",       help="Discover hosts on subnet")
#     ng.add_argument("--ssl-pinning",      metavar="PKG",          help="Check SSL pinning for package")
#     ng.add_argument("--mitm-guide",       action="store_true",    help="Show MitM setup guide")

#     # Vulnerability
#     vg = p.add_argument_group("Vulnerability")
#     vg.add_argument("--vuln-scan",        action="store_true",    help="Run full vulnerability scan")
#     vg.add_argument("--pkg",             metavar="PKG",           help="Target package name")
#     vg.add_argument("--cve-check",       action="store_true",     help="Check Android CVEs for device")
#     vg.add_argument("--root-check",      action="store_true",     help="Check if device is rooted")

#     # Exploit
#     eg = p.add_argument_group("Exploit")
#     eg.add_argument("--exploit",          metavar="MODULE",
#                     choices=["activity","broadcast","provider","deep-link","frida","shell-drop","db-extract","lock-bypass","dev-options"],
#                     help="Exploit module to run")
#     eg.add_argument("--activity",         metavar="CLASS",        help="Activity class for --exploit activity")
#     eg.add_argument("--action",           metavar="ACTION",       help="Intent action")
#     eg.add_argument("--uri",              metavar="URI",          help="URI for content provider / deep link")
#     eg.add_argument("--scheme",           metavar="SCHEME",       help="Deep link scheme")
#     eg.add_argument("--lhost",            metavar="IP",           help="Listener host")
#     eg.add_argument("--lport",            metavar="PORT", type=int, default=4444, help="Listener port")
#     eg.add_argument("--db-name",          metavar="DB",           help="Database filename to extract")

#     # Payload
#     pg = p.add_argument_group("Payload")
#     pg.add_argument("--payload",          metavar="TYPE",
#                     choices=["reverse_tcp","reverse_https","reverse_http","shell_tcp",
#                              "intent","reverse-shells","adb-script","obfuscate"],
#                     help="Generate a payload")
#     pg.add_argument("--payload-out",      metavar="FILE",         help="Output file for payload")
#     pg.add_argument("--obfuscate-method", choices=["base64","hex"], default="base64",
#                     help="Obfuscation method")
#     pg.add_argument("--raw-payload",      metavar="CMD",          help="Payload string to obfuscate")

#     # Report
#     rg = p.add_argument_group("Report")
#     rg.add_argument("--report",           choices=["html","json","both","table"],
#                     help="Generate report after scan")
#     rg.add_argument("--report-out",       metavar="FILE",         help="Report output filename")
#     rg.add_argument("--target-name",      metavar="NAME",         help="Target name for report", default="Unknown Target")

#     return p


# def cli_mode(args):
#     """Run CLI operations based on parsed arguments."""
#     print_banner()

#     device_id = args.device
#     apk_data = {}
    
#     if args.version:
#         console.print(f"[bold magenta]{TOOL_NAME}[/] v[bold cyan]{VERSION}[/] by [bold]{AUTHOR}[/]")
#         return

#     if args.devices:
#         adb_manager.check_adb()
#         adb_manager.list_devices()
#         return

#     # GUI Remote Control CLI
#     if args.gui_remote:
#         try:
#             from modules.gui_remote import start_gui_remote
#             start_gui_remote(args.remote_ip, args.remote_port)
#             return
#         except ImportError as e:
#             console.print(f"[red]✗ Could not import GUI remote module: {e}[/]")
#             console.print("[yellow]Make sure modules/gui_remote.py exists[/]")
#             return
#         except Exception as e:
#             console.print(f"[red]✗ Error starting GUI remote: {e}[/]")
#             return

#     # Remote Control CLI commands
#     if args.remote_setup:
#         one_time_setup(args.device, args.remote_port)
#         return
    
#     if args.remote_connect:
#         controller = quick_reconnect(args.remote_ip, args.remote_port)
#         if controller:
#             console.print("[green]✓ Connected wirelessly![/]")
#         return
    
#     if args.remote_control:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             controller.interactive_remote_control()
#         return
    
#     if args.remote_screenshot:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             controller.capture_screen()
#         return
    
#     if args.remote_stream:
#         if not PIL_AVAILABLE:
#             console.print("[red]✗ Pillow not installed. Run: pip install Pillow numpy[/]")
#         else:
#             controller = RemoteController()
#             ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#             if controller.connect_wireless(ip, args.remote_port):
#                 controller.stream_screen(args.refresh)
#         return
    
#     if args.remote_tap:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             controller.send_touch(args.remote_tap[0], args.remote_tap[1])
#         return
    
#     if args.remote_swipe:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             duration = args.remote_swipe[4] if len(args.remote_swipe) > 4 else 300
#             controller.send_swipe(args.remote_swipe[0], args.remote_swipe[1],
#                                   args.remote_swipe[2], args.remote_swipe[3], duration)
#         return
    
#     if args.remote_text:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             controller.send_text(args.remote_text)
#         return
    
#     if args.remote_key:
#         controller = RemoteController()
#         ip = args.remote_ip or Prompt.ask("[cyan]Device IP[/]")
#         if controller.connect_wireless(ip, args.remote_port):
#             controller.send_keyevent(args.remote_key)
#         return

#     if args.info and device_id:
#         adb_manager.device_info(device_id)

#     if args.shell and device_id:
#         adb_manager.shell_cmd(device_id, args.shell)

#     if args.adb_shell and device_id:
#         adb_manager.interactive_shell(device_id)

#     if args.adb_wifi and device_id:
#         adb_manager.enable_adb_wifi(device_id, args.lport)

#     if args.screenshot and device_id:
#         adb_manager.take_screenshot(device_id)

#     if args.logcat is not None and device_id:
#         adb_manager.capture_logcat(device_id, args.logcat)

#     if args.packages and device_id:
#         adb_manager.list_packages(device_id, args.packages)

#     if args.pull and device_id:
#         adb_manager.pull_file(device_id, args.pull)

#     if args.push and device_id:
#         adb_manager.push_file(device_id, args.push[0], args.push[1])

#     if args.apk:
#         apk_data = apk_analyzer.analyze_apk(args.apk)
#         _save_to_session(apk_data, "apk")

#     if args.port_scan:
#         target = args.target
#         if not target and device_id:
#             target = network_scanner.get_device_ip(device_id)
#         if target:
#             ports = None
#             if args.ports == "all":
#                 ports = list(range(1, 65536))
#             elif args.ports:
#                 ports = [int(p) for p in args.ports.split(",") if p.strip().isdigit()]
#             network_scanner.port_scan(target, ports)
#         else:
#             console.print("[red]Provide --target or --device for port scan.[/]")

#     if args.wifi_info and device_id:
#         network_scanner.get_wifi_info(device_id)

#     if args.discover:
#         network_scanner.discover_devices(args.discover)

#     if args.ssl_pinning and device_id:
#         network_scanner.check_ssl_pinning(device_id, args.ssl_pinning)

#     if args.mitm_guide:
#         network_scanner.mitm_setup_guide()

#     if args.vuln_scan and device_id:
#         report = vulnerability_scanner.full_vulnerability_scan(device_id, args.pkg)
#         _save_to_session(report, "vuln")

#     if args.cve_check and device_id:
#         findings = vulnerability_scanner.check_android_version_cves(device_id)
#         _save_to_session({"cves": findings}, "cve")

#     if args.root_check and device_id:
#         vulnerability_scanner.check_root_status(device_id)

#     if args.exploit and device_id:
#         ex = args.exploit
#         if ex == "activity":
#             exploit_engine.launch_exported_activity(device_id, args.pkg, args.activity)
#         elif ex == "broadcast":
#             exploit_engine.trigger_broadcast_receiver(device_id, args.pkg, args.action)
#         elif ex == "provider":
#             exploit_engine.extract_content_provider(device_id, args.uri)
#         elif ex == "deep-link":
#             exploit_engine.deep_link_fuzzer(device_id, args.pkg, args.scheme)
#         elif ex == "frida":
#             exploit_engine.frida_injection_guide(args.pkg)
#         elif ex == "shell-drop":
#             exploit_engine.shell_payload_dropper(device_id, args.lhost, args.lport)
#         elif ex == "db-extract":
#             exploit_engine.extract_database(device_id, args.pkg, args.db_name)
#         elif ex == "lock-bypass":
#             exploit_engine.bypass_lock_screen(device_id)
#         elif ex == "dev-options":
#             exploit_engine.enable_developer_options(device_id)

#     if args.payload:
#         out = args.payload_out
#         if args.payload in ("reverse_tcp","reverse_https","reverse_http","shell_tcp"):
#             payload_generator.generate_msfvenom_apk(args.lhost, args.lport, args.payload, out or "payload.apk")
#         elif args.payload == "intent":
#             payload_generator.generate_intent_payload(args.action, args.pkg, args.uri)
#         elif args.payload == "reverse-shells":
#             payload_generator.generate_reverse_shell_commands(args.lhost, args.lport)
#         elif args.payload == "adb-script":
#             payload_generator.generate_adb_payload_script(device_id, args.lhost, args.lport, out or "adb_payload.sh")
#         elif args.payload == "obfuscate":
#             payload_generator.obfuscate_payload(args.raw_payload or "", args.obfuscate_method)

#     if args.report:
#         data = _get_session()
#         data["target"] = args.target_name
#         if apk_data:
#             data.update(apk_data)
#         if args.report in ("html", "both"):
#             out = args.report_out or "axiom_report.html"
#             report_generator.generate_html_report(data, out)
#         if args.report in ("json", "both"):
#             out = args.report_out or "axiom_report.json"
#             report_generator.generate_json_report(data, out)
#         if args.report == "table":
#             report_generator.print_summary_table(data)


# # ═══════════════════════════════════════════════════════════════════════════════
# #  ENTRY POINT
# # ═══════════════════════════════════════════════════════════════════════════════

# def main():
#     parser = build_parser()

#     if len(sys.argv) == 1:
#         interactive_mode()
#         return

#     args = parser.parse_args()

#     if args.interactive:
#         interactive_mode()
#     else:
#         cli_mode(args)


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         console.print("\n\n[bold magenta]🔮 Axiom interrupted. Stay ethical.[/]\n")
#         sys.exit(0)
