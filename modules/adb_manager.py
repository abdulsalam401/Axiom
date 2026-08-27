"""
Axiom — ADB Manager Module
Author: Abdul Salam | Salamcs.app
"""

import subprocess
import re
import os
import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def get_adb_path():
    """Resolve the adb executable path, supporting local binaries in the virtual environment."""
    import shutil
    system_adb = shutil.which("adb")
    if system_adb:
        return system_adb

    # Check for local adb in virtual environment folders
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Windows venv Scripts folder
    win_venv_adb = os.path.join(base_dir, ".venv-win", "Scripts", "adb.exe")
    if os.path.exists(win_venv_adb):
        return win_venv_adb
        
    # Linux venv bin folder
    nix_venv_adb = os.path.join(base_dir, ".venv", "bin", "adb")
    if os.path.exists(nix_venv_adb):
        return nix_venv_adb
        
    # General local platform-tools folder
    local_tool_path = os.path.join(base_dir, ".platform-tools", "adb.exe" if os.name == "nt" else "adb")
    if os.path.exists(local_tool_path):
        return local_tool_path

    return "adb"


def run_adb(args: list, device_id: str = None, capture: bool = True):
    """Run an adb command and return stdout."""
    adb_path = get_adb_path()
    cmd = [adb_path]
    if device_id:
        cmd += ["-s", device_id]
    cmd += args
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
        return result.stdout.strip(), result.returncode
    except FileNotFoundError:
        return None, -1
    except subprocess.TimeoutExpired:
        return "TIMEOUT", -2


def check_adb():
    """Check if adb is installed, and offer automatic installation if missing."""
    from rich.prompt import Confirm
    import platform
    import urllib.request
    import zipfile
    import tempfile
    
    out, rc = run_adb(["version"])
    if rc == -1 or out is None:
        console.print("[bold red]✗ ADB not found![/]")
        
        if not Confirm.ask("[cyan]Would you like to automatically install Android Debug Bridge (ADB)?[/]", default=True):
            return False
            
        system_os = platform.system().lower()
        
        # Linux (Debian/Ubuntu/Kali) via apt-get
        if system_os == "linux":
            import shutil
            if shutil.which("apt-get"):
                console.print("[yellow]System detected: Linux (Debian/Ubuntu/Kali). Using apt-get...[/]")
                console.print("[cyan]Running: sudo apt-get update && sudo apt-get install -y adb[/]")
                try:
                    res = subprocess.run("sudo apt-get update && sudo apt-get install -y adb", shell=True)
                    if res.returncode == 0:
                        console.print("[green]✓ ADB installed successfully![/]")
                        return True
                    else:
                        console.print("[red]✗ Installation failed. Please run manually: sudo apt install adb[/]")
                        return False
                except Exception as e:
                    console.print(f"[red]✗ Error executing installation command: {e}[/]")
                    return False
            else:
                console.print("[red]✗ Could not find apt-get package manager. Please install 'adb' using your system's package manager.[/]")
                return False
                
        # macOS via Homebrew
        elif system_os == "darwin":
            import shutil
            if shutil.which("brew"):
                console.print("[yellow]System detected: macOS. Using Homebrew...[/]")
                console.print("[cyan]Running: brew install android-platform-tools[/]")
                try:
                    res = subprocess.run(["brew", "install", "android-platform-tools"])
                    if res.returncode == 0:
                        console.print("[green]✓ ADB installed successfully![/]")
                        return True
                    else:
                        console.print("[red]✗ Installation failed. Please run manually: brew install android-platform-tools[/]")
                        return False
                except Exception as e:
                    console.print(f"[red]✗ Error executing installation command: {e}[/]")
                    return False
            else:
                console.print("[red]✗ Homebrew not found. Please install Homebrew or manually download Android Platform Tools.[/]")
                return False
                
        # Windows via Google SDK download
        elif system_os == "windows":
            console.print("[yellow]System detected: Windows. Downloading official Google Platform Tools...[/]")
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_dir = os.path.join(base_dir, ".venv-win", "Scripts")
            if not os.path.exists(target_dir):
                target_dir = os.path.join(base_dir, ".platform-tools")
                os.makedirs(target_dir, exist_ok=True)
                
            url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
            
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_path = os.path.join(tmpdir, "platform-tools.zip")
                    console.print(f"[cyan]Downloading from: {url}...[/]")
                    urllib.request.urlretrieve(url, zip_path)
                    
                    console.print("[cyan]Extracting platform tools...[/]")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        for member in zip_ref.infolist():
                            parts = member.filename.split('/')
                            if len(parts) > 1 and parts[1]:
                                member.filename = os.path.join(*parts[1:])
                                zip_ref.extract(member, target_dir)
                                
                console.print(f"[green]✓ ADB installed successfully in local workspace: {target_dir}[/]")
                out, rc = run_adb(["version"])
                if rc == 0:
                    console.print(f"[green]✓ Verified ADB works:[/] {out.splitlines()[0]}")
                    return True
                else:
                    console.print("[red]✗ Download completed but ADB verification failed.[/]")
                    return False
            except Exception as e:
                console.print(f"[red]✗ Error downloading/extracting ADB: {e}[/]")
                return False
        else:
            console.print(f"[red]✗ Automatic installation not supported on operating system: {system_os}[/]")
            return False
            
    console.print(f"[green]✓ ADB found:[/] {out.splitlines()[0]}")
    return True


def list_devices():
    """List all connected Android devices."""
    out, rc = run_adb(["devices", "-l"])
    if out is None:
        console.print("[red]ADB not available.[/]")
        return []

    lines = out.strip().splitlines()
    devices = []
    table = Table(title="[bold #00ff66]📱 Connected Devices[/]", box=box.ROUNDED,
                  border_style="#00ff66", header_style="bold #00ffaa")
    table.add_column("Serial", style="bold #00ffcc")
    table.add_column("State", style="bold #00ff66")
    table.add_column("Model", style="yellow")
    table.add_column("Transport", style="dim white")

    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial = parts[0]
        state = parts[1]
        model = next((p.split(":")[1] for p in parts if p.startswith("model:")), "Unknown")
        transport = next((p.split(":")[1] for p in parts if p.startswith("transport_id:")), "N/A")
        devices.append({"serial": serial, "state": state, "model": model})
        table.add_row(serial, state, model, transport)

    console.print(table)
    if not devices:
        console.print("[yellow]⚠  No devices connected. Connect a device and enable USB Debugging.[/]")
    return devices


def device_info(device_id: str):
    """Gather comprehensive device info."""
    props = {
        "Brand": "ro.product.brand",
        "Model": "ro.product.model",
        "Android Version": "ro.build.version.release",
        "SDK Level": "ro.build.version.sdk",
        "Build ID": "ro.build.id",
        "Security Patch": "ro.build.version.security_patch",
        "Fingerprint": "ro.build.fingerprint",
        "CPU ABI": "ro.product.cpu.abi",
        "IMEI (if rooted)": "ril.serialnumber",
        "Serial": "ro.serialno",
    }

    table = Table(title=f"[bold #00ff66]🔎 Device Info [{device_id}][/]",
                  box=box.ROUNDED, border_style="#00ff66", header_style="bold #00ffaa")
    table.add_column("Property", style="bold #00ffcc")
    table.add_column("Value", style="white")

    for label, prop in props.items():
        val, _ = run_adb(["shell", f"getprop {prop}"], device_id)
        table.add_row(label, val or "[dim]N/A[/]")

    console.print(table)


def list_packages(device_id: str, pkg_filter: str = "all"):
    """List installed packages."""
    flags = {
        "all": [],
        "system": ["-s"],
        "third_party": ["-3"],
        "disabled": ["-d"],
    }
    flag = flags.get(pkg_filter, [])
    out, _ = run_adb(["shell", "pm", "list", "packages"] + flag, device_id)
    if not out:
        console.print("[red]Could not fetch packages.[/]")
        return []

    packages = [line.replace("package:", "").strip() for line in out.splitlines() if line.startswith("package:")]

    table = Table(title=f"[bold #00ff66]📦 Packages ({pkg_filter}) — {len(packages)} found[/]",
                  box=box.ROUNDED, border_style="#00ff66", header_style="bold #00ffaa")
    table.add_column("#", style="dim green", width=5)
    table.add_column("Package Name", style="white")

    for i, pkg in enumerate(packages, 1):
        table.add_row(str(i), pkg)

    console.print(table)
    return packages


def dumpsys(device_id: str, service: str = "package"):
    """Run dumpsys for a given service."""
    console.print(f"[cyan]Running dumpsys {service}...[/]")
    out, _ = run_adb(["shell", "dumpsys", service], device_id)
    if out:
        console.print(Panel(out[:3000] + ("..." if len(out) > 3000 else ""),
                            title=f"[bold]dumpsys {service}[/]", border_style="cyan"))
    return out


def capture_logcat(device_id: str, lines: int = 200):
    """Capture last N lines of logcat."""
    console.print(f"[cyan]Capturing last {lines} lines of logcat...[/]")
    out, _ = run_adb(["shell", f"logcat -d -t {lines}"], device_id)
    filename = f"axiom_logcat_{int(time.time())}.txt"
    if out:
        with open(filename, "w") as f:
            f.write(out)
        console.print(f"[green]✓ Logcat saved to:[/] {filename}")

    # Highlight security-sensitive patterns
    patterns = ["password", "token", "secret", "api_key", "auth", "credential", "private"]
    hits = []
    for line in out.splitlines():
        low = line.lower()
        for p in patterns:
            if p in low:
                hits.append(line)
                break

    if hits:
        console.print(f"\n[bold red]⚠  {len(hits)} sensitive pattern(s) found in logcat:[/]")
        for h in hits[:20]:
            console.print(f"  [red]►[/] {h}")
    return out


def pull_file(device_id: str, remote_path: str, local_path: str = "."):
    """Pull a file from device."""
    out, rc = run_adb(["pull", remote_path, local_path], device_id)
    if rc == 0:
        console.print(f"[green]✓ Pulled:[/] {remote_path} → {local_path}")
    else:
        console.print(f"[red]✗ Failed to pull {remote_path}[/]")


def push_file(device_id: str, local_path: str, remote_path: str):
    """Push a file to device."""
    out, rc = run_adb(["push", local_path, remote_path], device_id)
    if rc == 0:
        console.print(f"[green]✓ Pushed:[/] {local_path} → {remote_path}")
    else:
        console.print(f"[red]✗ Failed to push {local_path}[/]")


def take_screenshot(device_id: str):
    """Take a screenshot and pull it."""
    remote = "/sdcard/axiom_screen.png"
    local = f"screenshot_{int(time.time())}.png"
    run_adb(["shell", "screencap", "-p", remote], device_id)
    pull_file(device_id, remote, local)
    run_adb(["shell", "rm", remote], device_id)
    return local


def enable_adb_wifi(device_id: str, port: int = 5555):
    """Enable ADB over WiFi."""
    console.print(f"[cyan]Enabling ADB over WiFi on port {port}...[/]")
    run_adb(["shell", f"setprop service.adb.tcp.port {port}"], device_id)
    run_adb(["shell", "stop adbd && start adbd"], device_id)
    ip_out, _ = run_adb(["shell", "ip addr show wlan0"], device_id)
    ip_match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", ip_out or "")
    if ip_match:
        ip = ip_match.group(1)
        console.print(f"[green]✓ ADB WiFi enabled![/] Connect with: [bold yellow]adb connect {ip}:{port}[/]")
        return ip, port
    else:
        console.print("[yellow]⚠  Could not determine device IP. Connect manually.[/]")
        return None, port


def shell_cmd(device_id: str, cmd: str):
    """Execute a raw shell command."""
    out, rc = run_adb(["shell", cmd], device_id)
    console.print(Panel(out or "(no output)", title=f"[dim]$ {cmd}[/]", border_style="dim"))
    return out


def interactive_shell(device_id: str):
    """Drop into an interactive ADB shell."""
    console.print("[bold yellow]Dropping into ADB shell. Type 'exit' to return.[/]")
    cmd = ["adb"]
    if device_id:
        cmd += ["-s", device_id]
    cmd += ["shell"]
    subprocess.call(cmd)