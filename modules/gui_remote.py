"""
Axiom — GUI Remote Control Module
Author: Abdul Salam | Salamcs.app
Real-time screen mirroring with mouse control
"""

import subprocess
import threading
import time
import os
import tempfile
import re
from datetime import datetime
from typing import Optional, Tuple

# Import PIL globally with fallback
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageTk = None

# Import tkinter
try:
    import tkinter as tk
    from tkinter import ttk, Label, Canvas, Frame, Button, Scale, HORIZONTAL
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None

from rich.console import Console
from rich.panel import Panel
from rich import box

console = Console()


class ScreenMirrorGUI:
    """Graphical remote control window for Android device."""
    
    def __init__(self, device_id: str = None):
        self.device_id = device_id
        self.device_ip = None
        self.device_port = 5555
        self.connected = False
        self.streaming = False
        self.stream_thread = None
        
        # Screen dimensions
        self.device_width = 1080
        self.device_height = 2400
        
        # GUI dimensions
        self.gui_width = 400
        self.gui_height = 800
        self.scale_factor = 1.0
        
        # Frame buffer
        self.current_frame = None
        self.photo_image = None
        
        # Last touch position
        self.last_x = 0
        self.last_y = 0
        
        # Root window
        self.root = None
        self.canvas = None
        self.status_label = None
        self.fps_label = None
        
        # FPS tracking
        self.frame_count = 0
        self.last_fps_update = time.time()
        
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
    
    def connect_wireless(self, ip: str = None, port: int = 5555) -> bool:
        """Connect to device wirelessly."""
        if not ip:
            ip = self.get_device_ip()
        
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
            self.connected = True
            console.print(f"[bold green]✓ Connected to {self.device_id}[/]")
            return True
        
        console.print(f"[red]✗ Connection failed: {result.stdout}[/]")
        return False
    
    def get_screen_size(self) -> Tuple[int, int]:
        out = self._run_adb(["shell", "wm size"])
        match = re.search(r"Physical size: (\d+)x(\d+)", out)
        if match:
            self.device_width = int(match.group(1))
            self.device_height = int(match.group(2))
        return self.device_width, self.device_height
    
    def capture_frame(self):
        """Capture single frame from device."""
        if not PIL_AVAILABLE:
            return None
        
        try:
            remote_path = "/sdcard/frame_temp.png"
            local_path = os.path.join(tempfile.gettempdir(), f"frame_{int(time.time()*1000)}.png")
            
            self._run_adb(["shell", "screencap", "-p", remote_path])
            self._run_adb(["pull", remote_path, local_path])
            self._run_adb(["shell", "rm", remote_path])
            
            if os.path.exists(local_path):
                img = Image.open(local_path)
                os.remove(local_path)
                return img
        except Exception as e:
            pass
        return None
    
    def stream_frames(self):
        """Continuous frame streaming thread."""
        if not PIL_AVAILABLE:
            console.print("[red]✗ PIL not available[/]")
            return
            
        self.streaming = True
        frame_delay = 0.05  # ~20 FPS default
        
        while self.streaming and self.connected:
            try:
                start_time = time.time()
                
                img = self.capture_frame()
                if img:
                    # Resize for display
                    resized = img.resize((self.gui_width, self.gui_height), Image.Resampling.LANCZOS)
                    self.current_frame = ImageTk.PhotoImage(resized)
                    
                    # Update canvas (schedule in main thread)
                    if self.canvas and self.current_frame and self.root:
                        try:
                            self.root.after(0, self._update_canvas)
                        except:
                            pass
                    
                    # Update FPS
                    self.frame_count += 1
                    now = time.time()
                    if now - self.last_fps_update >= 1.0:
                        fps = self.frame_count / (now - self.last_fps_update)
                        if self.fps_label and self.root:
                            try:
                                self.root.after(0, lambda: self.fps_label.config(text=f"FPS: {fps:.1f}"))
                            except:
                                pass
                        self.frame_count = 0
                        self.last_fps_update = now
                
                # Control frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_delay - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                if self.streaming:
                    console.print(f"[dim]Stream warning: {e}[/]")
                time.sleep(0.5)
    
    def _update_canvas(self):
        """Update canvas with current frame (called from main thread)."""
        try:
            if self.canvas and self.current_frame:
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_frame)
        except:
            pass
    
    def on_mouse_click(self, event):
        """Handle mouse click - send touch to device."""
        # Scale GUI coordinates to device coordinates
        device_x = int(event.x * self.device_width / self.gui_width)
        device_y = int(event.y * self.device_height / self.gui_height)
        
        # Clamp coordinates
        device_x = max(0, min(device_x, self.device_width))
        device_y = max(0, min(device_y, self.device_height))
        
        console.print(f"[dim]Tap at ({device_x}, {device_y})[/]")
        self._run_adb(["shell", f"input tap {device_x} {device_y}"])
        
        # Update status
        if self.status_label:
            self.status_label.config(text=f"Tap: {device_x}, {device_y}")
    
    def on_mouse_drag(self, event):
        """Handle mouse drag - send swipe to device."""
        device_x = int(event.x * self.device_width / self.gui_width)
        device_y = int(event.y * self.device_height / self.gui_height)
        
        # Clamp coordinates
        device_x = max(0, min(device_x, self.device_width))
        device_y = max(0, min(device_y, self.device_height))
        
        if self.last_x != 0 and self.last_y != 0:
            device_last_x = int(self.last_x * self.device_width / self.gui_width)
            device_last_y = int(self.last_y * self.device_height / self.gui_height)
            
            device_last_x = max(0, min(device_last_x, self.device_width))
            device_last_y = max(0, min(device_last_y, self.device_height))
            
            self._run_adb(["shell", f"input swipe {device_last_x} {device_last_y} {device_x} {device_y} 50"])
            console.print(f"[dim]Swipe: ({device_last_x},{device_last_y}) → ({device_x},{device_y})[/]")
        
        self.last_x = event.x
        self.last_y = event.y
    
    def on_mouse_release(self, event):
        """Reset last position on release."""
        self.last_x = 0
        self.last_y = 0
    
    def on_key_press(self, event):
        """Handle keyboard input."""
        key_map = {
            'Home': 'KEYCODE_HOME',
            'End': 'KEYCODE_ENDCALL',
            'BackSpace': 'KEYCODE_BACK',
            'Delete': 'KEYCODE_DEL',
            'Return': 'KEYCODE_ENTER',
            'Up': 'KEYCODE_DPAD_UP',
            'Down': 'KEYCODE_DPAD_DOWN',
            'Left': 'KEYCODE_DPAD_LEFT',
            'Right': 'KEYCODE_DPAD_RIGHT',
            'Escape': 'KEYCODE_BACK',
            'space': 'KEYCODE_SPACE',
            'Tab': 'KEYCODE_TAB',
        }
        
        # Volume keys
        if event.keysym == 'plus' or event.keysym == 'equal':
            self._run_adb(["shell", "input keyevent KEYCODE_VOLUME_UP"])
            console.print("[dim]Volume Up[/]")
        elif event.keysym == 'minus' or event.keysym == 'underscore':
            self._run_adb(["shell", "input keyevent KEYCODE_VOLUME_DOWN"])
            console.print("[dim]Volume Down[/]")
        
        # Map special keys
        elif event.keysym in key_map:
            self._run_adb(["shell", f"input keyevent {key_map[event.keysym]}"])
            console.print(f"[dim]Key: {event.keysym}[/]")
        
        # Regular characters
        elif hasattr(event, 'char') and event.char and len(event.char) == 1 and event.char.isprintable():
            # Escape for shell
            char = event.char.replace(" ", "%s").replace("&", "\\&").replace("'", "\\'").replace('"', '\\"')
            self._run_adb(["shell", f"input text '{char}'"])
            console.print(f"[dim]Text: {event.char}[/]")
        
        if self.status_label:
            self.status_label.config(text=f"Key: {event.keysym}")
    
    def start_screen_mirror(self):
        """Start the GUI screen mirroring."""
        if not TKINTER_AVAILABLE:
            console.print("[red]✗ tkinter not available![/]")
            console.print("[yellow]On Ubuntu: sudo apt install python3-tk[/]")
            return
        
        if not PIL_AVAILABLE:
            console.print("[red]✗ PIL not available! Run: pip install Pillow[/]")
            return
        
        # Get screen size
        self.get_screen_size()
        
        # Calculate aspect ratio for window
        aspect = self.device_height / self.device_width
        self.gui_width = 450
        self.gui_height = int(self.gui_width * aspect)
        
        # Create root window
        self.root = tk.Tk()
        self.root.title(f"Axiom - Remote Control ({self.device_id})")
        self.root.geometry(f"{self.gui_width + 20}x{self.gui_height + 120}")
        self.root.configure(bg='#1a1a2e')
        
        # Set minimum window size
        self.root.minsize(300, 500)
        
        # Create canvas for screen display
        self.canvas = Canvas(self.root, width=self.gui_width, height=self.gui_height, 
                            bg='#000000', highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Bind keyboard events
        self.root.bind("<Key>", self.on_key_press)
        self.root.focus_set()
        
        # Status bar frame
        status_frame = Frame(self.root, bg='#1a1a2e')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Status label
        self.status_label = Label(status_frame, text="Connected | Click to tap | Drag to swipe", 
                                  bg='#1a1a2e', fg='#8888cc', font=('Arial', 10))
        self.status_label.pack(side=tk.LEFT)
        
        # FPS label
        self.fps_label = Label(status_frame, text="FPS: 0.0", 
                               bg='#1a1a2e', fg='#88cc88', font=('Arial', 10))
        self.fps_label.pack(side=tk.RIGHT)
        
        # Control buttons frame
        control_frame = Frame(self.root, bg='#1a1a2e')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Button styling
        button_style = {'bg': '#2a2a4e', 'fg': 'white', 'font': ('Arial', 10), 
                        'relief': tk.RAISED, 'bd': 1, 'padx': 10, 'pady': 5}
        
        buttons = [
            ("📱 Home", lambda: self._run_adb(["shell", "input keyevent KEYCODE_HOME"])),
            ("⬅️ Back", lambda: self._run_adb(["shell", "input keyevent KEYCODE_BACK"])),
            ("🔄 Recent", lambda: self._run_adb(["shell", "input keyevent KEYCODE_APP_SWITCH"])),
            ("📸 Screenshot", self.take_screenshot),
            ("🔌 Disconnect", self.disconnect),
        ]
        
        for text, command in buttons:
            btn = Button(control_frame, text=text, command=command, **button_style)
            btn.pack(side=tk.LEFT, padx=5)
        
        # Refresh rate slider frame
        slider_frame = Frame(self.root, bg='#1a1a2e')
        slider_frame.pack(fill=tk.X, padx=10, pady=5)
        
        Label(slider_frame, text="Refresh Rate:", bg='#1a1a2e', fg='#8888cc', 
              font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        
        self.refresh_slider = Scale(slider_frame, from_=0.3, to=3.0, resolution=0.1,
                                     orient=HORIZONTAL, length=150, bg='#1a1a2e', 
                                     fg='white', highlightthickness=0)
        self.refresh_slider.set(1.0)
        self.refresh_slider.pack(side=tk.LEFT, padx=5)
        
        Label(slider_frame, text="sec (lower = faster)", bg='#1a1a2e', fg='#6666aa',
              font=('Arial', 8)).pack(side=tk.LEFT)
        
        # Instructions
        help_text = "💡 Tips: Click/tap on screen to touch | Drag to swipe | Use keyboard to type"
        help_label = Label(self.root, text=help_text, bg='#1a1a2e', fg='#6666aa',
                          font=('Arial', 8))
        help_label.pack(pady=5)
        
        # Start streaming thread
        self.stream_thread = threading.Thread(target=self.stream_frames, daemon=True)
        self.stream_thread.start()
        
        # Set window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start GUI
        console.print(Panel(
            f"[bold green]✓ GUI Remote Control Started![/]\n"
            f"Device: {self.device_id}\n"
            f"Screen: {self.device_width}x{self.device_height}\n\n"
            f"[cyan]Controls:[/]\n"
            f"  • Click/Tap → Touch at that position\n"
            f"  • Drag → Swipe gesture\n"
            f"  • Keyboard → Type text / Navigation keys\n"
            f"  • Home/Back/Recent buttons → Navigation\n"
            f"  • Screenshot button → Capture screen",
            border_style="green"
        ))
        
        self.root.mainloop()
    
    def take_screenshot(self):
        """Capture and save screenshot."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        img = self.capture_frame()
        if img:
            img.save(filename)
            console.print(f"[green]✓ Screenshot saved: {filename}[/]")
            if self.status_label:
                self.status_label.config(text=f"Screenshot saved: {filename}")
    
    def disconnect(self):
        """Disconnect and close window."""
        console.print("[yellow]Disconnecting...[/]")
        self.streaming = False
        self.connected = False
        if self.root:
            self.root.quit()
    
    def on_closing(self):
        """Handle window close event."""
        self.disconnect()
        if self.root:
            self.root.destroy()


def start_gui_remote(ip: str = None, port: int = 5555):
    """Start GUI remote control."""
    if not TKINTER_AVAILABLE:
        console.print("[red]✗ tkinter not available![/]")
        console.print("[yellow]On Ubuntu/Debian: sudo apt install python3-tk[/]")
        console.print("[yellow]On Windows/Mac: tkinter comes with Python[/]")
        return
    
    if not PIL_AVAILABLE:
        console.print("[red]✗ Pillow not installed! Run: pip install Pillow[/]")
        return
    
    console.print(Panel(
        "[bold cyan]Axiom - GUI Remote Control[/]\n\n"
        "Starting graphical remote control interface...\n"
        "A new window will open showing your phone screen.\n\n"
        "[bold green]Features:[/]\n"
        "  • Real-time screen mirroring\n"
        "  • Mouse click → Touch screen\n"
        "  • Mouse drag → Swipe gesture\n"
        "  • Keyboard input → Type text\n"
        "  • Navigation buttons (Home, Back, Recent)\n"
        "  • Screenshot capture\n\n"
        "[dim]Press Ctrl+C in terminal to stop[/]",
        border_style="magenta"
    ))
    
    # Connect to device
    controller = ScreenMirrorGUI()
    
    if not ip:
        # Try to get IP from USB connection first
        ip = controller.get_device_ip()
        if not ip:
            console.print("[yellow]Could not auto-detect IP[/]")
            ip = input("Enter device IP: ").strip()
            if not ip:
                console.print("[red]No IP provided[/]")
                return
    
    if controller.connect_wireless(ip, port):
        console.print("[green]✓ Connected! Starting GUI...[/]")
        controller.start_screen_mirror()
    else:
        console.print("[red]✗ Failed to connect[/]")


def quick_gui_remote(ip: str = None):
    """Quick shortcut to start GUI remote."""
    start_gui_remote(ip)