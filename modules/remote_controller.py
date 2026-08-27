"""
Axiom — Remote Controller Module
Author: Abdul Salam | Salamcs.app
"""

import subprocess
import socket
import threading
import time
import tempfile
import os
import re
from datetime import datetime
from typing import Optional, Tuple, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()


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
    
    def get_network_subnets(self) -> List[str]:
        """Get actual network subnets, prioritizing physical networks and excluding virtual ones."""
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
                        console.print(f"[dim]   Found connected device subnet: {subnet}.0/24[/]")
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
                    console.print(f"[dim]   Found USB device {serial} WiFi subnet: {subnet}.0/24[/]")
                else:
                    out = subprocess.run(["adb", "-s", serial, "shell", "ifconfig wlan0"], capture_output=True, text=True, timeout=5).stdout
                    match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", out)
                    if match:
                        subnet = '.'.join(match.group(1).split('.')[:-1])
                        subnets.add(subnet)
                        console.print(f"[dim]   Found USB device {serial} WiFi subnet: {subnet}.0/24[/]")
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
                                console.print(f"[dim]   Found Windows adapter ({current_adapter.strip()}): {subnet}.0/24[/]")
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
                                console.print(f"[dim]   Found Windows adapter ({current_adapter.strip()}): {subnet}.0/24[/]")
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
                    console.print(f"[dim]   Found gateway subnet: {subnet}.0/24[/]")
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
                                    console.print(f"[dim]   Found interface {current_interface}: {subnet}.0/24[/]")
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
            filtered = ["192.168.1", "192.168.0", "192.168.10"]
            
        return list(set(filtered))
    
    def discover_devices_on_network(self, subnet: str = None) -> List[Tuple[str, int]]:
        """Automatically discover Android devices on the local network."""
        import concurrent.futures
        import socket
        
        discovered_devices = []
        ports_to_check = [5555, 5556]
        
        if not subnet:
            subnets = self.get_network_subnets()
            console.print(f"[cyan]🔍 Scanning {len(subnets)} network(s) for Android devices...[/]")
            
            for sub in subnets:
                console.print(f"[cyan]   Scanning {sub}.0/24...[/]")
                devices = self._scan_subnet(sub, ports_to_check)
                if devices:
                    console.print(f"[bold #00ff66]   ✓ Found {len(devices)} device(s) on {sub}.0/24[/]")
                discovered_devices.extend(devices)
        else:
            discovered_devices = self._scan_subnet(subnet, ports_to_check)
        
        # Remove duplicates
        seen = set()
        unique_devices = []
        for ip, port in discovered_devices:
            key = f"{ip}:{port}"
            if key not in seen:
                seen.add(key)
                unique_devices.append((ip, port))
        
        if unique_devices:
            console.print(f"[bold #00ff66]✓ Found {len(unique_devices)} device(s)![/]")
            for ip, port in unique_devices:
                temp_id = f"{ip}:{port}"
                model = subprocess.run(
                    ["adb", "-s", temp_id, "shell", "getprop ro.product.model 2>/dev/null"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip() or "Unknown"
                console.print(f"  [bold #00ffcc]►[/] {ip}:{port} ({model})")
        else:
            console.print("[yellow]⚠ No devices found.[/]")
            console.print("[dim green]Tip: Make sure your phone and computer are on the same WiFi network.[/]")
            console.print("[dim green]      Your phone IP should start with 192.168.x.x[/]")
        
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
            "[bold #00ff66]⚡ Auto-Discover & Connect[/]\n\n"
            "Scanning your local network(s) for Android devices...\n"
            "Make sure your phone is on the same WiFi network!\n"
            "Looking for subnets like 192.168.1.x or 192.168.10.x",
            border_style="#00ff66", box=box.ROUNDED
        ))
        
        discovered = self.discover_devices_on_network()
        
        if not discovered:
            console.print("[red]✗ No devices found.[/]")
            console.print("[yellow]Troubleshooting:[/]")
            console.print("  1. Make sure USB Debugging is enabled on your phone")
            console.print("  2. Ensure phone is on the same WiFi network")
            console.print("  3. Check your phone's IP address in WiFi settings")
            console.print("  4. First time? Connect via USB and run: axiom --remote-setup")
            return False
        
        if len(discovered) == 1:
            ip, port = discovered[0]
            console.print(f"[bold #00ff66]Auto-selected: {ip}:{port}[/]")
            return self.connect_wireless(ip, port)
        else:
            console.print("\n[bold #00ffcc]Multiple devices found. Select one:[/]")
            for i, (ip, port) in enumerate(discovered, 1):
                temp_id = f"{ip}:{port}"
                model = subprocess.run(
                    ["adb", "-s", temp_id, "shell", "getprop ro.product.model 2>/dev/null"],
                    capture_output=True, text=True, timeout=2
                ).stdout.strip() or "Unknown"
                console.print(f"  [{i}] {ip}:{port} - {model}")
            
            choice = Prompt.ask("[#00ffcc]Select device number[/]", 
                               choices=[str(i) for i in range(1, len(discovered) + 1)])
            idx = int(choice) - 1
            ip, port = discovered[idx]
            return self.connect_wireless(ip, port)
    
    def _get_connected_devices(self) -> List[Tuple[str, int]]:
        """Get already connected ADB devices."""
        devices = []
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                if line.strip() and "device" in line and ":" in line:
                    parts = line.split()
                    device_id = parts[0]
                    if ":" in device_id:
                        ip_port = device_id.split(':')
                        if len(ip_port) == 2:
                            devices.append((ip_port[0], int(ip_port[1])))
        except:
            pass
        return devices
    
    def setup_wireless_adb(self, port: int = 5555) -> bool:
        """Enable ADB over WiFi on device (requires USB connection)."""
        console.print("[#00ffcc]📡 Setting up ADB over WiFi...[/]")
        
        ip = self.get_device_ip()
        if not ip:
            console.print("[red]✗ Could not get device IP. Make sure WiFi is ON.[/]")
            return False
        
        self.device_ip = ip
        self.wifi_port = port
        self._run_adb(["tcpip", str(port)])
        time.sleep(2)
        
        console.print(f"[bold #00ff66]✓ ADB over WiFi enabled on port {port}[/]")
        console.print(f"[bold #00ff66]Device IP:[/] [bold #00ffcc]{ip}[/]")
        
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
            ip = self.device_ip
            if not ip and self.device_id and ":" in self.device_id:
                ip = self.device_id.split(':')[0]
            start_gui_remote(ip, self.wifi_port)
        except ImportError as e:
            console.print(f"[red]✗ Could not import GUI remote module: {e}[/]")
        except Exception as e:
            console.print(f"[red]✗ Error starting GUI remote: {e}[/]")


def one_time_setup(device_id: str = None, port: int = 5555) -> Optional[RemoteController]:
    """Complete one-time setup: USB → Enable WiFi → Disconnect USB → Reconnect Wireless"""
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
        return controller
    else:
        console.print("[red]✗ Wireless connection failed.[/]")
        return None


def quick_reconnect(ip: str = None, port: int = 5555) -> Optional[RemoteController]:
    controller = RemoteController()
    
    if not ip:
        ip = Prompt.ask("[cyan]Enter device IP (e.g., 192.168.10.5)[/]", default="")
        if not ip:
            return None
    
    if controller.connect_wireless(ip, port):
        return controller
    return None


def remote_control_menu():
    """Display remote control menu."""
    options = [
        ("1", "🔌", "One-Time Setup (USB → Wireless)", "First time wireless setup"),
        ("2", "🔗", "Quick Reconnect", "Reconnect to saved device"),
        ("3", "🖥️", "GUI Remote Control", "Real graphical screen mirroring"),
        ("4", "📸", "Screen Capture", "Take a screenshot"),
        ("5", "👆", "Touch/Swipe Controls", "Send touch or swipe gestures"),
        ("6", "⌨️", "Keyboard Input", "Send text to device"),
        ("7", "📱", "Device Info", "Show device information"),
        ("8", "🔄", "Reconnect to IP", "Manual reconnect to IP"),
        ("0", "🔌", "Disconnect & Back", "Disconnect and return"),
    ]
    
    table = Table(title="[bold magenta]🎮 Axiom Remote Control[/]",
                  box=box.DOUBLE_EDGE, border_style="magenta")
    table.add_column("Option", style="cyan", width=6)
    table.add_column("Icon", style="magenta", width=4)
    table.add_column("Action", style="bold white", min_width=28)
    table.add_column("Description", style="dim", min_width=35)
    
    for num, icon, name, desc in options:
        table.add_row(f"[bold cyan]{num}[/]", icon, name, desc)
    
    console.print(table)
    return options

# """
# Axiom — Remote Controller Module
# Author: Abdul Salam | Salamcs.app
# """

# import subprocess
# import socket
# import threading
# import time
# import base64
# import struct
# import tempfile
# import os
# import re
# from datetime import datetime
# from typing import Optional, Tuple
# from rich.console import Console
# from rich.table import Table
# from rich.panel import Panel
# from rich.live import Live
# from rich.layout import Layout
# from rich import box

# console = Console()

# # Try to import optional dependencies
# try:
#     from PIL import Image
#     import numpy as np
#     PIL_AVAILABLE = True
# except ImportError:
#     PIL_AVAILABLE = False
#     console.print("[yellow]⚠ Install Pillow for screen mirroring: pip install Pillow numpy[/]")

# try:
#     import keyboard
#     KEYBOARD_AVAILABLE = True
# except ImportError:
#     KEYBOARD_AVAILABLE = False


# class RemoteController:
#     """Handle remote control of Android device via ADB."""
    
#     def __init__(self, device_id: str = None):
#         self.device_id = device_id
#         self.wifi_port = 5555
#         self.device_ip = None
#         self.connected_wireless = False
#         self.screen_streaming = False
#         self.streaming_thread = None
        
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
#         """Get device IP address."""
#         out = self._run_adb(["shell", "ip addr show wlan0"])
#         match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
#         if match:
#             return match.group(1)
        
#         # Alternative method
#         out = self._run_adb(["shell", "ifconfig wlan0"])
#         match = re.search(r"inet addr:(\d+\.\d+\.\d+\.\d+)", out)
#         return match.group(1) if match else None
    
#     def setup_wireless_adb(self, port: int = 5555) -> bool:
#         """Enable ADB over WiFi on device."""
#         console.print("[cyan]📡 Setting up ADB over WiFi...[/]")
        
#         # Get device IP first (while still connected via USB)
#         ip = self.get_device_ip()
#         if not ip:
#             console.print("[red]✗ Could not get device IP. Make sure WiFi is ON.[/]")
#             return False
        
#         self.device_ip = ip
#         self.wifi_port = port
        
#         # Enable ADB over TCP (using tcpip command is more reliable)
#         self._run_adb(["tcpip", str(port)])
#         time.sleep(2)
        
#         console.print(f"[green]✓ ADB over WiFi enabled on port {port}[/]")
#         console.print(f"[cyan]Device IP:[/] {ip}")
        
#         return True
    
#     def connect_wireless(self, ip: str = None, port: int = 5555) -> bool:
#         """Connect to device wirelessly."""
#         if not ip:
#             ip = self.device_ip or self.get_device_ip()
        
#         if not ip:
#             console.print("[red]✗ Cannot determine device IP[/]")
#             return False
        
#         console.print(f"[cyan]Connecting to {ip}:{port}...[/]")
        
#         # Kill existing server to avoid conflicts
#         subprocess.run(["adb", "kill-server"], capture_output=True)
#         time.sleep(1)
        
#         result = subprocess.run(["adb", "connect", f"{ip}:{port}"], 
#                                 capture_output=True, text=True)
        
#         if "connected" in result.stdout.lower():
#             # Extract the wireless device ID (format: ip:port)
#             wireless_id = f"{ip}:{port}"
            
#             # Test connection
#             test = subprocess.run(["adb", "-s", wireless_id, "shell", "echo", "test"],
#                                   capture_output=True, text=True)
            
#             if "test" in test.stdout:
#                 self.device_id = wireless_id
#                 self.connected_wireless = True
#                 console.print(f"[bold green]✓ Connected wirelessly to {wireless_id}[/]")
#                 return True
        
#         console.print(f"[red]✗ Connection failed: {result.stdout}[/]")
#         return False
    
#     def disconnect_wireless(self):
#         """Disconnect wireless ADB connection."""
#         if self.device_id and ":" in self.device_id:
#             subprocess.run(["adb", "disconnect", self.device_id], capture_output=True)
#             console.print("[yellow]✓ Disconnected wireless ADB[/]")
#             self.connected_wireless = False
    
#     def capture_screen(self, output_path: str = None) -> Optional[str]:
#         """Capture device screen as PNG."""
#         if not output_path:
#             output_path = f"screenshot_{int(time.time())}.png"
        
#         remote_path = "/sdcard/screen_temp.png"
#         self._run_adb(["shell", "screencap", "-p", remote_path])
#         self._run_adb(["pull", remote_path, output_path])
#         self._run_adb(["shell", "rm", remote_path])
        
#         console.print(f"[green]✓ Screenshot saved: {output_path}[/]")
#         return output_path
    
#     def _image_to_ascii(self, image_path: str, width: int = 70) -> str:
#         """
#         Convert image to ASCII art with safe integer handling.
        
#         This fixed version uses float conversion to avoid integer overflow
#         and handles edge cases properly.
#         """
#         if not PIL_AVAILABLE:
#             return "[Pillow not installed. Run: pip install Pillow numpy]"
        
#         try:
#             img = Image.open(image_path)
            
#             # Calculate dimensions maintaining aspect ratio
#             aspect = img.height / img.width
#             height = max(1, int(width * aspect * 0.55))
            
#             # Resize image
#             img = img.resize((width, height), Image.Resampling.LANCZOS)
            
#             # Convert to grayscale
#             if img.mode != 'L':
#                 img = img.convert('L')
            
#             # ASCII characters from dark to light (more detailed)
#             chars = "@%#*+=-:. "
#             num_chars = len(chars)
            
#             # Get pixel data as numpy array with proper type
#             pixels = np.array(img, dtype=np.uint8)
            
#             ascii_lines = []
#             for row in pixels:
#                 # Use float conversion to avoid overflow
#                 # Map 0-255 to 0 to num_chars-1
#                 indices = (row.astype(np.float32) * (num_chars - 1) / 255).astype(np.uint8)
#                 line = ''.join(chars[idx] for idx in indices)
#                 ascii_lines.append(line)
            
#             return '\n'.join(ascii_lines)
            
#         except Exception as e:
#             return f"[Screen conversion error: {str(e)[:50]}]"
    
#     def stream_screen(self, refresh_rate: float = 1.0, terminal_mode: bool = True):
#         """
#         Stream screen to terminal or open in external viewer.
        
#         Args:
#             refresh_rate: Seconds between captures (min 0.5)
#             terminal_mode: If True, show ASCII art; if False, open image viewer
#         """
#         if not PIL_AVAILABLE:
#             console.print("[red]✗ Pillow not installed. Run: pip install Pillow numpy[/]")
#             return
        
#         console.print(f"[cyan]🎥 Starting screen stream (refresh: {refresh_rate}s)[/]")
#         console.print("[dim]Press Ctrl+C to stop[/]")
        
#         temp_dir = tempfile.gettempdir()
#         frame_count = 0
        
#         try:
#             while True:
#                 # Capture screen
#                 remote_path = "/sdcard/stream_temp.png"
#                 local_path = os.path.join(temp_dir, f"frame_{frame_count}.png")
                
#                 self._run_adb(["shell", "screencap", "-p", remote_path])
#                 self._run_adb(["pull", remote_path, local_path])
#                 self._run_adb(["shell", "rm", remote_path])
                
#                 if terminal_mode:
#                     # Convert to ASCII art
#                     ascii_art = self._image_to_ascii(local_path, width=70)
#                     console.clear()
#                     console.print(Panel(
#                         ascii_art, 
#                         title="📱 Screen Stream", 
#                         border_style="cyan",
#                         subtitle=f"Frame: {frame_count} | Refresh: {refresh_rate}s"
#                     ))
#                 else:
#                     # Open image in default viewer
#                     self._open_image(local_path)
                
#                 # Cleanup old frame
#                 try:
#                     os.remove(local_path)
#                 except:
#                     pass
                
#                 frame_count += 1
#                 time.sleep(refresh_rate)
                
#         except KeyboardInterrupt:
#             console.print("\n[yellow]✓ Screen streaming stopped[/]")
    
#     def _open_image(self, image_path: str):
#         """Open image in system viewer."""
#         if os.name == 'nt':  # Windows
#             os.startfile(image_path)
#         elif os.name == 'posix':  # Linux/Mac
#             subprocess.run(["xdg-open", image_path], capture_output=True)
    
#     def send_touch(self, x: int, y: int):
#         """Send touch event to device."""
#         self._run_adb(["shell", f"input tap {x} {y}"])
#         console.print(f"[dim]Tap at ({x}, {y})[/]")
    
#     def send_swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300):
#         """Send swipe gesture."""
#         self._run_adb(["shell", f"input swipe {x1} {y1} {x2} {y2} {duration}"])
#         console.print(f"[dim]Swiped ({x1},{y1}) → ({x2},{y2})[/]")
    
#     def send_text(self, text: str):
#         """Send text input."""
#         # Escape special characters for shell
#         text_escaped = text.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'").replace('"', '\\"')
#         self._run_adb(["shell", f"input text '{text_escaped}'"])
#         console.print(f"[dim]Typed: {text}[/]")
    
#     def send_keyevent(self, keycode: str):
#         """Send Android key event."""
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
#             "camera": "KEYCODE_CAMERA",
#             "search": "KEYCODE_SEARCH",
#         }
        
#         key = key_map.get(keycode.lower(), keycode.upper())
#         self._run_adb(["shell", f"input keyevent {key}"])
#         console.print(f"[dim]Key: {keycode}[/]")
    
#     def get_screen_size(self) -> Tuple[int, int]:
#         """Get device screen dimensions."""
#         out = self._run_adb(["shell", "wm size"])
#         match = re.search(r"Physical size: (\d+)x(\d+)", out)
#         if match:
#             return int(match.group(1)), int(match.group(2))
#         return 1080, 2400  # Default for modern phones
    
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
#   [green]up, down, left, right[/green] → D-pad navigation
#   [green]recent[/green]          → Show recent apps
#   [green]power[/green]           → Power button
#   [green]volume_up/down[/green]   → Volume control
#   [green]screenshot[/green]       → Capture screen
#   [green]stream [rate][/green]    → Start streaming (rate in seconds)
#   [green]info[/green]            → Show device info
#   [green]help[/green]            → Show this help
#   [green]exit[/green]            → Exit remote control

# [dim]Tip: Use 'stream 0.5' for faster refresh, 'stream 2.0' for slower[/]
#         """)
        
#         while True:
#             try:
#                 cmd = input("\n[bold magenta]Remote[/] > ").strip().lower()
                
#                 if cmd == "exit" or cmd == "quit":
#                     break
#                 elif cmd == "screenshot":
#                     self.capture_screen()
#                 elif cmd.startswith("stream"):
#                     parts = cmd.split()
#                     rate = float(parts[1]) if len(parts) > 1 else 1.0
#                     rate = max(0.3, min(rate, 5.0))  # Clamp between 0.3 and 5 seconds
#                     self.stream_screen(rate)
#                 elif cmd.startswith("tap "):
#                     parts = cmd.split()
#                     if len(parts) == 3:
#                         x = int(parts[1])
#                         y = int(parts[2])
#                         # Validate coordinates
#                         if 0 <= x <= screen_w and 0 <= y <= screen_h:
#                             self.send_touch(x, y)
#                         else:
#                             console.print(f"[yellow]Coordinates out of range (0-{screen_w}, 0-{screen_h})[/]")
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
#                             "up", "down", "left", "right", "camera", "search"]:
#                     self.send_keyevent(cmd)
#                 elif cmd == "info":
#                     self._show_device_info()
#                 elif cmd == "help":
#                     self._show_help()
#                 elif cmd == "":
#                     continue
#                 else:
#                     console.print("[yellow]Unknown command. Type 'help' for options.[/]")
                    
#             except KeyboardInterrupt:
#                 console.print("\n[yellow]Exiting remote control...[/]")
#                 break
#             except ValueError as e:
#                 console.print(f"[red]Invalid number: {e}[/]")
#             except Exception as e:
#                 console.print(f"[red]Error: {e}[/]")
    
#     def _show_device_info(self):
#         """Show detailed device information."""
#         console.rule("[cyan]Device Information[/]")
        
#         props = {
#             "Model": "ro.product.model",
#             "Manufacturer": "ro.product.manufacturer",
#             "Android Version": "ro.build.version.release",
#             "SDK Level": "ro.build.version.sdk",
#             "Security Patch": "ro.build.version.security_patch",
#             "Build ID": "ro.build.id",
#             "Screen Size": f"{self.get_screen_size()[0]}x{self.get_screen_size()[1]}",
#         }
        
#         table = Table(title="📱 Device Info", box=box.SIMPLE, border_style="cyan")
#         table.add_column("Property", style="cyan")
#         table.add_column("Value", style="white")
        
#         for label, prop in props.items():
#             if prop.startswith("ro."):
#                 val = self._run_adb(["shell", f"getprop {prop}"])
#                 table.add_row(label, val or "[dim]N/A[/]")
#             else:
#                 table.add_row(label, prop)
        
#         console.print(table)
        
#         # Show battery info
#         battery = self._run_adb(["shell", "dumpsys battery | grep -E 'level|status|temperature'"])
#         if battery:
#             console.print(Panel(battery, title="🔋 Battery Info", border_style="green"))
    
#     def _show_help(self):
#         """Show help information."""
#         help_text = """
# [bold cyan]Available Commands:[/]

# [bold green]Touch Controls:[/]
#   tap <x> <y>           - Tap at screen coordinates
#   swipe <x1> <y1> <x2> <y2> - Swipe from (x1,y1) to (x2,y2)
#   text "<message>"      - Type text (use quotes for spaces)

# [bold yellow]Navigation Keys:[/]
#   home, back, menu, recent, power
#   up, down, left, right
#   volume_up, volume_down
#   enter, delete, camera, search

# [bold magenta]Screen Capture:[/]
#   screenshot            - Take a single screenshot
#   stream [rate]         - Start live streaming (rate = seconds per frame, default 1.0)

# [bold cyan]Information:[/]
#   info                  - Show device information
#   help                  - Show this help
#   exit                  - Exit remote control

# [dim]Examples:[/]
#   tap 540 960
#   swipe 500 1500 500 500
#   text "Hello World"
#   stream 0.5
#         """
#         console.print(Panel(help_text, title="📖 Help", border_style="cyan"))


# def one_time_setup(device_id: str = None, port: int = 5555) -> Optional[RemoteController]:
#     """
#     Complete one-time setup: USB → Enable WiFi → Disconnect USB → Reconnect Wireless
#     """
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
    
#     # Step 1: Verify USB connection
#     console.print("\n[1/5] Checking USB connection...")
#     devices_out = controller._run_adb(["devices"])
#     if "device" not in devices_out:
#         console.print("[red]✗ No device connected via USB. Please connect your phone.[/]")
#         return None
    
#     console.print("[green]✓ Device connected via USB[/]")
    
#     # Step 2: Enable WiFi ADB
#     console.print("\n[2/5] Enabling ADB over WiFi...")
#     if not controller.setup_wireless_adb(port):
#         console.print("[red]✗ Failed to enable WiFi ADB[/]")
#         return None
    
#     # Step 3: Get IP
#     console.print("\n[3/5] Getting device IP...")
#     ip = controller.device_ip
#     console.print(f"[green]✓ Device IP: {ip}[/]")
    
#     # Step 4: Wait for USB disconnect
#     console.print(f"""
# [4/5] [bold yellow]ACTION REQUIRED[/]
# 1. Disconnect the USB cable from your device NOW
# 2. Make sure device is still connected to WiFi
# 3. Press Enter when ready to connect wirelessly
#     """)
#     input("Press Enter to continue...")
    
#     # Step 5: Connect wirelessly
#     console.print("\n[5/5] Connecting wirelessly...")
#     if controller.connect_wireless(ip, port):
#         console.print(Panel(
#             f"[bold green]✓ Remote control ready![/]\n"
#             f"Device: {controller.device_id}\n"
#             f"IP: {ip}:{port}\n\n"
#             f"Use 'python axiom.py --remote-control --remote-ip {ip}' for control",
#             border_style="green"
#         ))
#         return controller
#     else:
#         console.print("[red]✗ Wireless connection failed. Make sure device is on same WiFi network.[/]")
#         return None


# def quick_reconnect(ip: str = None, port: int = 5555) -> Optional[RemoteController]:
#     """Quickly reconnect to a previously paired device."""
#     controller = RemoteController()
    
#     if not ip:
#         ip = input("Enter device IP (e.g., 192.168.1.100): ").strip()
#         if not ip:
#             return None
    
#     if controller.connect_wireless(ip, port):
#         return controller
#     return None


# def remote_control_menu():
#     """Display remote control menu."""
#     options = [
#         ("1", "🔌", "One-Time Setup (USB → Wireless)", "First time wireless setup"),
#         ("2", "🔗", "Quick Reconnect to Saved Device", "Reconnect to last device"),
#         ("3", "🎮", "Interactive Remote Control", "Full control with commands"),
#         ("4", "📸", "Screen Capture", "Take a single screenshot"),
#         ("5", "🎥", "Screen Stream (ASCII)", "Live ASCII screen streaming"),
#         ("6", "👆", "Touch/Swipe Controls", "Send touch or swipe gestures"),
#         ("7", "⌨️", "Keyboard Input", "Send text to device"),
#         ("8", "📱", "Device Info", "Show device information"),
#         ("9", "🔄", "Reconnect to Wireless Device", "Manual reconnect to IP"),
#         ("0", "🔌", "Disconnect & Back", "Disconnect and return to main menu"),
#     ]
    
#     table = Table(title="[bold magenta]🎮 Axiom Remote Control[/]",
#                   box=box.DOUBLE_EDGE, border_style="magenta")
#     table.add_column("Option", style="cyan", width=6)
#     table.add_column("Icon", style="magenta", width=4)
#     table.add_column("Action", style="bold white", min_width=28)
#     table.add_column("Description", style="dim", min_width=35)
    
#     for num, icon, name, desc in options:
#         table.add_row(f"[bold cyan]{num}[/]", icon, name, desc)
    
#     console.print(table)
#     return options