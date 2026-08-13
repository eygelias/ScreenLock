"""
ScreenLock v6.0 - GUI, Portable, Dark Mode Perfected, Icon, Force Kill, Key Capture
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys
import atexit
import winsound
import subprocess
import winreg as reg

# ── Win32 API ────────────────────────────────────────────────────────────────
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
KEYEVENTF_KEYUP = 0x0002

VK_MAP = {
    'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
    'space': 0x20, 'tab': 0x09, 'esc': 0x1B, 'enter': 0x0D,
    'backspace': 0x08, 'delete': 0x2E, 'insert': 0x2D,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'capslock': 0x14, 'numlock': 0x90, 'printscreen': 0x2C,
}
for c in 'abcdefghijklmnopqrstuvwxyz0123456789':
    VK_MAP[c] = ord(c.upper())
for i in range(1, 13):
    VK_MAP[f'f{i}'] = 0x70 + i - 1

MOD_FLAGS = {'ctrl': 0x0002, 'shift': 0x0004, 'alt': 0x0001}

ICONINFO = type('ICONINFO', (ctypes.Structure,), {
    '_fields_': [
        ('fIcon', wt.BOOL), ('xHotspot', wt.DWORD), ('yHotspot', wt.DWORD),
        ('hbmMask', wt.HBITMAP), ('hbmColor', wt.HBITMAP),
    ]
})

class KBDLLHOOK(ctypes.Structure):
    _fields_ = [
        ('vkCode', wt.DWORD), ('scanCode', wt.DWORD),
        ('flags', wt.DWORD), ('time', wt.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]

class MSLLHOOK(ctypes.Structure):
    _fields_ = [
        ('pt', wt.POINT), ('mouseData', wt.DWORD),
        ('flags', wt.DWORD), ('time', wt.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]

HOOKPROC_KB = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wt.WPARAM, ctypes.POINTER(KBDLLHOOK))
HOOKPROC_MS = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wt.WPARAM, ctypes.POINTER(MSLLHOOK))

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wt.HINSTANCE, wt.DWORD]
user32.SetWindowsHookExW.restype = wt.HHOOK
user32.CallNextHookEx.argtypes = [wt.HHOOK, ctypes.c_int, wt.WPARAM, ctypes.c_void_p]
user32.CallNextHookEx.restype = ctypes.c_long
user32.UnhookWindowsHookEx.argtypes = [wt.HHOOK]
user32.UnhookWindowsHookEx.restype = wt.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wt.MSG), wt.HWND, ctypes.c_uint, ctypes.c_uint]
user32.GetMessageW.restype = wt.BOOL
user32.GetKeyState.argtypes = [ctypes.c_int]
user32.GetKeyState.restype = ctypes.c_short
user32.keybd_event.argtypes = [wt.BYTE, wt.BYTE, wt.DWORD, ctypes.POINTER(ctypes.c_ulong)]
user32.keybd_event.restype = None
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]
kernel32.GetModuleHandleW.restype = wt.HINSTANCE
user32.ShowCursor.argtypes = [wt.BOOL]
user32.ShowCursor.restype = ctypes.c_int
user32.SetCursor.argtypes = [wt.HICON]
user32.SetCursor.restype = wt.HICON
user32.LoadCursorW.argtypes = [wt.HINSTANCE, wt.LPCWSTR]
user32.LoadCursorW.restype = wt.HICON
gdi32.CreateBitmap.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
gdi32.CreateBitmap.restype = wt.HBITMAP
user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
user32.CreateIconIndirect.restype = wt.HICON
user32.DestroyIcon.argtypes = [wt.HICON]
user32.DestroyIcon.restype = wt.BOOL
user32.SetSystemCursor.argtypes = [wt.HICON, wt.DWORD]
user32.SetSystemCursor.restype = wt.BOOL
user32.SystemParametersInfoW.argtypes = [wt.UINT, wt.UINT, ctypes.c_void_p, wt.UINT]
user32.SystemParametersInfoW.restype = wt.BOOL
gdi32.DeleteObject.argtypes = [wt.HANDLE]
gdi32.DeleteObject.restype = wt.BOOL

IDC_ARROW = wt.LPCWSTR(32512)
OCR_NORMAL = 32512
SPI_SETCURSORS = 0x0057

# ── State ────────────────────────────────────────────────────────────────────
app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(app_dir, 'config.txt')
PID_PATH = os.path.join(app_dir, 'pid.txt')

state = {
    'locked': False,
    'password': 'desbloquear',
    'progress': 0,
    'hotkey_mods': 0,
    'hotkey_vk': 0,
    'hotkey_str': 'ctrl+shift+f',
}
kb_hook = None
ms_hook = None

# ── Cursor ───────────────────────────────────────────────────────────────────
def hide_cursor():
    mask = gdi32.CreateBitmap(1, 1, 1, 1, None)
    color = gdi32.CreateBitmap(1, 1, 1, 1, None)
    info = ICONINFO()
    info.fIcon = False
    info.xHotspot = 0
    info.yHotspot = 0
    info.hbmMask = mask
    info.hbmColor = color
    inv = user32.CreateIconIndirect(ctypes.byref(info))
    
    # CreateIconIndirect makes a copy of the bitmaps, we can delete them now.
    gdi32.DeleteObject(mask)
    gdi32.DeleteObject(color)
    
    user32.SetSystemCursor(inv, OCR_NORMAL)
    # DO NOT DestroyIcon(inv) here. SetSystemCursor takes ownership and destroys it later.

def show_cursor():
    user32.SystemParametersInfoW(SPI_SETCURSORS, 0, None, 0)

# ── Helpers ──────────────────────────────────────────────────────────────────
def vk_to_char(vk):
    if 0x30 <= vk <= 0x39:
        return chr(vk)
    if 0x41 <= vk <= 0x5A:
        return chr(vk).lower()
    if 0x60 <= vk <= 0x69:
        return chr(vk - 0x60 + 0x30)
    if 0x70 <= vk <= 0x7B:
        return f'f{vk - 0x6F}'
    if vk == 0x20:
        return ' '
    return None

def parse_hotkey(s):
    if not s: return 0, 0
    parts = [p.strip().lower() for p in s.split('+')]
    mods, key = 0, 0
    for p in parts:
        if p in MOD_FLAGS:
            mods |= MOD_FLAGS[p]
        elif p in VK_MAP:
            key = VK_MAP[p]
    return mods, key

def get_mod_flags():
    f = 0
    if user32.GetKeyState(0x10) & 0x8000: f |= MOD_FLAGS['shift']
    if user32.GetKeyState(0x11) & 0x8000: f |= MOD_FLAGS['ctrl']
    if user32.GetKeyState(0x12) & 0x8000: f |= MOD_FLAGS['alt']
    return f

def release_mods():
    for vk in (0x10, 0x11, 0x12):
        if user32.GetKeyState(vk) & 0x8000:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, None)

# ── Hooks ────────────────────────────────────────────────────────────────────
def kb_proc(nCode, wParam, lParam):
    try:
        if nCode == HC_ACTION and wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            vk = lParam.contents.vkCode

            if state['hotkey_vk'] and vk == state['hotkey_vk'] and get_mod_flags() == state['hotkey_mods']:
                toggle_lock()
                return -1

            if state['locked']:
                ch = vk_to_char(vk)
                if ch and state['progress'] < len(state['password']):
                    if ch == state['password'][state['progress']]:
                        state['progress'] += 1
                        play_sound('key')
                        if state['progress'] >= len(state['password']):
                            toggle_lock()
                    else:
                        state['progress'] = 0
                return -1
    except Exception as e:
        import traceback
        with open(os.path.join(app_dir, 'error.log'), 'a') as f:
            f.write("kb_proc: " + traceback.format_exc() + '\n')

    return user32.CallNextHookEx(kb_hook, nCode, wParam, lParam)

def ms_proc(nCode, wParam, lParam):
    try:
        if nCode == HC_ACTION and state['locked']:
            return -1
    except Exception:
        pass
    return user32.CallNextHookEx(ms_hook, nCode, wParam, lParam)

# ── Sound ────────────────────────────────────────────────────────────────────
def play_sound(kind):
    try:
        if kind == 'lock':
            winsound.Beep(600, 200)
        elif kind == 'unlock':
            winsound.Beep(1200, 150)
            winsound.Beep(1500, 150)
        elif kind == 'key':
            winsound.Beep(1000, 80)
    except Exception:
        pass

# ── Toggle ───────────────────────────────────────────────────────────────────
def toggle_lock():
    state['locked'] = not state['locked']
    state['progress'] = 0
    if state['locked']:
        release_mods()
        hide_cursor()
        play_sound('lock')
    else:
        show_cursor()
        play_sound('unlock')

# ── Config ───────────────────────────────────────────────────────────────────
def load_config():
    vals = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    vals[k.strip()] = v.strip()

    state['password'] = vals.get('PASSWORD', 'desbloquear').lower()
    hk = vals.get('HOTKEY', 'ctrl+shift+f').lower()
    state['hotkey_str'] = hk
    mods, vk = parse_hotkey(hk)
    state['hotkey_mods'] = mods
    state['hotkey_vk'] = vk

# ── Cleanup ──────────────────────────────────────────────────────────────────
def cleanup():
    global kb_hook, ms_hook
    if state['locked']:
        show_cursor()
    if ms_hook:
        user32.UnhookWindowsHookEx(ms_hook)
    if kb_hook:
        user32.UnhookWindowsHookEx(kb_hook)

# ── GUI AND PROCESS MANAGEMENT ───────────────────────────────────────────────
def check_pid(pid):
    PROCESS_QUERY_INFORMATION = 0x0400
    h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
    if h_process:
        exit_code = wt.DWORD()
        kernel32.GetExitCodeProcess(h_process, ctypes.byref(exit_code))
        kernel32.CloseHandle(h_process)
        return exit_code.value == 259 # STILL_ACTIVE
    return False

def terminate_pid(pid):
    PROCESS_TERMINATE = 0x0001
    h_process = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if h_process:
        kernel32.TerminateProcess(h_process, 0)
        kernel32.CloseHandle(h_process)

def run_gui():
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.title("ScreenLock Configuración")
    root.geometry("460x530")
    root.resizable(False, False)
    
    icon_path = os.path.join(app_dir, 'icon.ico')
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except:
            pass
            
    password = tk.StringVar(value='desbloquear')
    hotkey = tk.StringVar(value='ctrl+shift+f')
    gui_theme = tk.StringVar(value='auto')
    
    def load_gui_config():
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip()
                        if k == 'PASSWORD':
                            password.set(v)
                        elif k == 'HOTKEY':
                            hotkey.set(v)
                        elif k == 'THEME':
                            gui_theme.set(v)
    load_gui_config()
    
    REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    def is_startup_enabled():
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_PATH, 0, reg.KEY_READ)
            value, _ = reg.QueryValueEx(key, "ScreenLock")
            reg.CloseKey(key)
            return True
        except WindowsError:
            return False
            
    startup_var = tk.BooleanVar(value=is_startup_enabled())
    
    def toggle_startup():
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, REG_PATH, 0, reg.KEY_SET_VALUE)
            if startup_var.get():
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = f'pythonw.exe "{sys.argv[0]}"'
                cmd = f'"{exe_path}" --hidden'
                reg.SetValueEx(key, "ScreenLock", 0, reg.REG_SZ, cmd)
            else:
                try:
                    reg.DeleteValue(key, "ScreenLock")
                except FileNotFoundError:
                    pass
            reg.CloseKey(key)
        except Exception:
            pass

    def save_config():
        try:
            os.makedirs(app_dir, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write("# ScreenLock Config\n")
                f.write(f"PASSWORD={password.get()}\n")
                f.write(f"HOTKEY={hotkey.get()}\n")
                f.write(f"THEME={gui_theme.get()}\n")
            
            toggle_startup()
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.\nSi el servicio está corriendo, reinícialo para aplicar los cambios.")
            update_status()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
        
    def get_service_pid():
        if os.path.exists(PID_PATH):
            try:
                with open(PID_PATH, 'r') as f:
                    pid = int(f.read().strip())
                if check_pid(pid):
                    return pid
            except:
                pass
        return None

    def start_service():
        if not hotkey.get().strip():
            messagebox.showwarning("Atención", "Debes definir una tecla para bloquear.")
            return

        if get_service_pid():
            messagebox.showinfo("Info", "El servicio ya está corriendo.")
            return
            
        try:
            env = {k: v for k, v in os.environ.items() if not k.startswith('_MEI') and not k.startswith('_PYI')}
            
            # DETACHED_PROCESS | CREATE_NO_WINDOW
            cflags = 0x00000008 | 0x08000000
            
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, "--hidden"], env=env, creationflags=cflags, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.dirname(sys.executable))
            else:
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                subprocess.Popen([python_exe, sys.argv[0], "--hidden"], env=env, creationflags=cflags, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=os.path.dirname(sys.executable))
            
            root.after(1000, update_status)
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar el servicio:\n{e}")

    def stop_service():
        pid = get_service_pid()
        if os.path.exists(PID_PATH):
            try:
                os.remove(PID_PATH)
            except:
                pass
                
        # Wait for graceful exit triggered by PID_PATH deletion
        if pid:
            import time
            for _ in range(20):
                if not check_pid(pid):
                    break
                time.sleep(0.1)
                
            # Fallback force kill
            if check_pid(pid):
                try:
                    terminate_pid(pid)
                except Exception:
                    pass
        
        root.after(100, update_status)
        
    def restart_service():
        stop_service()
        root.after(1000, start_service)

    def uninstall_completely():
        if not messagebox.askyesno("Confirmar", "¿Seguro que quieres detener el servicio y desactivarlo del inicio de Windows?\n(El archivo ScreenLock.exe NO se borrará, solo dejará de afectar tu PC)"):
            return
            
        stop_service()
        
        # Failsafe: force kill any other instances of ScreenLock except this GUI
        try:
            my_pid = os.getpid()
            exe_name = os.path.basename(sys.executable)
            cmd = f'Get-CimInstance Win32_Process | Where-Object {{ ($_.Name -like "*ScreenLock*") -and $_.ProcessId -ne {my_pid} }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}'
            subprocess.run(['powershell', '-Command', cmd], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            pass

        startup_var.set(False)
        toggle_startup()
        
        messagebox.showinfo("Desactivado", "El servicio ha sido detenido forzosamente.\nEl programa ya no se iniciará con Windows y tu PC no se verá afectada.")

    def get_windows_theme():
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = reg.QueryValueEx(key, "AppsUseLightTheme")
            reg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except:
            return "light"
            
    is_dark = False
    t = gui_theme.get()
    if t == 'dark':
        is_dark = True
    elif t == 'light':
        is_dark = False
    else:
        is_dark = (get_windows_theme() == 'dark')
        gui_theme.set("dark" if is_dark else "light")
    
    def update_widget_colors(widget, bg, fg, input_bg, input_fg, btn_bg, btn_fg):
        try:
            wtype = widget.winfo_class()
            if wtype in ('Frame', 'Tk', 'Toplevel'):
                widget.config(bg=bg)
            elif wtype in ('Labelframe', 'Label'):
                widget.config(bg=bg, fg=fg)
            elif wtype == 'Checkbutton':
                widget.config(bg=bg, fg=fg, selectcolor=input_bg, activebackground=bg, activeforeground=fg)
            elif wtype == 'Entry':
                widget.config(bg=input_bg, fg=input_fg, insertbackground=input_fg)
            elif wtype == 'Button':
                # Skip main colored buttons
                if widget not in (btn_save, btn_uninstall, btn_clear_pass, btn_clear_hotkey):
                    widget.config(bg=btn_bg, fg=btn_fg, activebackground=input_bg, activeforeground=btn_fg)
        except Exception:
            pass
            
        for child in widget.winfo_children():
            update_widget_colors(child, bg, fg, input_bg, input_fg, btn_bg, btn_fg)

    def apply_theme():
        if is_dark:
            bg_color = "#2E2E2E"
            fg_color = "#FFFFFF"
            input_bg = "#404040"
            input_fg = "#FFFFFF"
            btn_bg = "#4A4A4A"
            btn_fg = "#FFFFFF"
            btn_theme.config(text="Modo Claro")
        else:
            bg_color = "#F0F0F0"
            fg_color = "#000000"
            input_bg = "#FFFFFF"
            input_fg = "#000000"
            btn_bg = "#E0E0E0"
            btn_fg = "#000000"
            btn_theme.config(text="Modo Oscuro")
            
        root.config(bg=bg_color)
        update_widget_colors(root, bg_color, fg_color, input_bg, input_fg, btn_bg, btn_fg)

    def toggle_theme():
        nonlocal is_dark
        is_dark = not is_dark
        gui_theme.set("dark" if is_dark else "light")
        apply_theme()

    def show_help():
        msg = ("ScreenLock te permite bloquear tu teclado y ratón sin apagar tu pantalla ni suspender la PC.\n\n"
               "• Contraseña de Desbloqueo: Escríbela en tu teclado (a ciegas) cuando la PC esté bloqueada para desbloquearla automáticamente.\n\n"
               "• Teclas para Bloquear: La combinación exacta (ej. ctrl+shift+f) que debes presionar para bloquear o desbloquear la PC de forma rápida.\n\n"
               "Nota: Una vez bloqueada, nadie podrá usar la PC (el ratón y el teclado quedan congelados) hasta que ingreses la contraseña secreta o vuelvas a presionar la combinación de teclas.")
        messagebox.showinfo("¿Cómo funciona ScreenLock?", msg)

    # UI Design
    header = tk.Frame(root)
    header.pack(fill="x", padx=10, pady=10)
    
    lbl_title = tk.Label(header, text="ScreenLock Config", font=("Arial", 16, "bold"))
    lbl_title.pack(side="left", expand=True, fill="x")
    
    btn_help = tk.Button(header, text="?", command=show_help, width=3, font=("Arial", 10, "bold"))
    btn_help.pack(side="right", padx=(5, 0))
    
    btn_theme = tk.Button(header, text="Modo Oscuro", command=toggle_theme, width=12)
    btn_theme.pack(side="right")

    frame_config = tk.LabelFrame(root, text="Configuración", padx=10, pady=10)
    frame_config.pack(padx=20, pady=10, fill="x")
    
    tk.Label(frame_config, text="Contraseña de Desbloqueo:").grid(row=0, column=0, sticky="w", pady=5)
    tk.Entry(frame_config, textvariable=password, width=25).grid(row=0, column=1, pady=5, padx=(5, 5), sticky="w")
    btn_clear_pass = tk.Button(frame_config, text="X", command=lambda: password.set(""), width=2, bg="#F44336", fg="white", font=("Arial", 8, "bold"))
    btn_clear_pass.grid(row=0, column=2, padx=(0, 5))
    
    tk.Label(frame_config, text="Teclas para Bloquear:").grid(row=1, column=0, sticky="w", pady=5)
    entry_hotkey = tk.Entry(frame_config, textvariable=hotkey, width=25)
    entry_hotkey.grid(row=1, column=1, pady=5, padx=(5, 5), sticky="w")
    btn_clear_hotkey = tk.Button(frame_config, text="X", command=lambda: hotkey.set(""), width=2, bg="#F44336", fg="white", font=("Arial", 8, "bold"))
    btn_clear_hotkey.grid(row=1, column=2, padx=(0, 5))
    
    def catch_hotkey(event):
        ignore = ('control_l', 'control_r', 'shift_l', 'shift_r', 'alt_l', 'alt_r', 'win_l', 'win_r', 'caps_lock', 'num_lock', 'scroll_lock')
        if event.keysym.lower() in ignore:
            return "break"
            
        mods = []
        real_mods = get_mod_flags()
        if real_mods & MOD_FLAGS['ctrl']: mods.append('ctrl')
        if real_mods & MOD_FLAGS['shift']: mods.append('shift')
        if real_mods & MOD_FLAGS['alt']: mods.append('alt')
        
        ks = event.keysym.lower()
        if ks == 'return': ks = 'enter'
        elif ks == 'prior': ks = 'pageup'
        elif ks == 'next': ks = 'pagedown'
        elif ks == 'escape': ks = 'esc'
        
        if ks == 'backspace' and not mods:
            hotkey.set('')
            return "break"
            
        if ks not in VK_MAP:
            return "break"
            
        final_str = "+".join(mods + [ks])
        hotkey.set(final_str)
        return "break"
        
    entry_hotkey.bind("<KeyPress>", catch_hotkey)
    # Prevent default typing so they don't type normal text
    entry_hotkey.bind("<KeyRelease>", lambda e: "break")
    
    tk.Label(frame_config, text="(Haz clic, pulsa tus teclas para atraparlas.\n Usa Backspace o la X para borrar)", font=("Arial", 8), fg="gray").grid(row=2, column=1, sticky="w", padx=(5, 5))
    
    chk_startup = tk.Checkbutton(frame_config, text="Iniciar automáticamente con Windows", variable=startup_var)
    chk_startup.grid(row=3, column=0, columnspan=3, sticky="w", pady=10)
    
    btn_save = tk.Button(frame_config, text="Guardar Cambios", command=save_config, bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), activebackground="#45a049", activeforeground="white")
    btn_save.grid(row=4, column=0, columnspan=3, pady=10)
    
    frame_status = tk.LabelFrame(root, text="Estado del Servicio", padx=10, pady=10)
    frame_status.pack(padx=20, pady=10, fill="x")
    
    lbl_status = tk.Label(frame_status, text="Estado: Desconocido", font=("Arial", 10, "bold"))
    lbl_status.pack(pady=5)
    
    btn_frame = tk.Frame(frame_status)
    btn_frame.pack()
    
    btn_start = tk.Button(btn_frame, text="Iniciar", command=start_service, width=10)
    btn_start.pack(side="left", padx=5)
    
    btn_stop = tk.Button(btn_frame, text="Detener", command=stop_service, width=10)
    btn_stop.pack(side="left", padx=5)
    
    btn_restart = tk.Button(btn_frame, text="Reiniciar", command=restart_service, width=10)
    btn_restart.pack(side="left", padx=5)

    frame_danger = tk.LabelFrame(root, text="Opciones Avanzadas", padx=10, pady=10)
    frame_danger.pack(padx=20, pady=10, fill="x")
    
    btn_uninstall = tk.Button(frame_danger, text="Detener y desactivar servicio de Windows", command=uninstall_completely, bg="#F44336", fg="white", font=("Arial", 9, "bold"), activebackground="#da190b", activeforeground="white")
    btn_uninstall.pack(pady=5)
    
    def update_status():
        pid = get_service_pid()
        if pid:
            lbl_status.config(text="Estado: CORRIENDO (Protegido)", fg="#4CAF50")
            btn_start.config(state="disabled")
            btn_stop.config(state="normal")
            btn_restart.config(state="normal")
        else:
            lbl_status.config(text="Estado: DETENIDO", fg="#F44336")
            btn_start.config(state="normal")
            btn_stop.config(state="disabled")
            btn_restart.config(state="disabled")
            
    # Apply initial colors
    apply_theme()
    update_status()
    root.mainloop()


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    if '--hidden' not in sys.argv:
        run_gui()
        return

    PROCESS_QUERY_INFORMATION = 0x0400
    if os.path.exists(PID_PATH):
        try:
            with open(PID_PATH, 'r') as f:
                old_pid = int(f.read().strip())
            h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, old_pid)
            if h_process:
                exit_code = wt.DWORD()
                kernel32.GetExitCodeProcess(h_process, ctypes.byref(exit_code))
                kernel32.CloseHandle(h_process)
                if exit_code.value == 259:
                    return
        except:
            pass

    try:
        os.makedirs(app_dir, exist_ok=True)
        with open(PID_PATH, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

    load_config()
    atexit.register(cleanup)
    
    def remove_pid():
        if os.path.exists(PID_PATH):
            try:
                os.remove(PID_PATH)
            except:
                pass
    atexit.register(remove_pid)

    if not state['hotkey_vk']:
        return

    hmod = kernel32.GetModuleHandleW(None)
    kb_cb = HOOKPROC_KB(kb_proc)
    ms_cb = HOOKPROC_MS(ms_proc)

    global kb_hook, ms_hook
    kb_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, kb_cb, hmod, 0)
    ms_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, ms_cb, hmod, 0)

    if not kb_hook or not ms_hook:
        return

    # Timer to gracefully exit when PID_PATH is deleted
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.SetTimer.argtypes = [wt.HWND, wt.WPARAM, wt.UINT, ctypes.c_void_p]
    user32.SetTimer.restype = wt.WPARAM

    TIMERPROC = ctypes.WINFUNCTYPE(None, wt.HWND, wt.UINT, wt.WPARAM, wt.DWORD)
    def check_alive(hwnd, msg, timer_id, time):
        if not os.path.exists(PID_PATH):
            user32.PostQuitMessage(0)
            
    timer_cb = TIMERPROC(check_alive)
    user32.SetTimer(0, 0, 1000, ctypes.cast(timer_cb, ctypes.c_void_p))

    msg = wt.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        pass


if __name__ == '__main__':
    main()
