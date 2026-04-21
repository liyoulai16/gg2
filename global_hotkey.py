import sys
import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QApplication


class GlobalHotkey(QObject):
    activated = pyqtSignal()
    
    WM_HOTKEY = 0x0312
    
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey_id = 1
        self.registered = False
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_messages)
        
        self.user32 = ctypes.windll.user32
        
        self.WNDPROC = ctypes.CFUNCTYPE(
            ctypes.c_int,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM
        )
        
        self._hwnd = None
        self._old_wnd_proc = None
        self._wnd_proc_instance = None
        
    def register(self, modifier, key_code):
        if self.registered:
            self.unregister()
        
        try:
            result = self.user32.RegisterHotKey(
                None,
                self.hotkey_id,
                modifier | self.MOD_NOREPEAT,
                key_code
            )
            
            if result:
                self.registered = True
                self._check_timer.start(100)
                return True
            else:
                error = ctypes.get_last_error()
                print(f"Failed to register hotkey. Error: {error}")
                return False
                
        except Exception as e:
            print(f"Error registering hotkey: {e}")
            return False
    
    def unregister(self):
        if self.registered:
            try:
                self.user32.UnregisterHotKey(None, self.hotkey_id)
                self._check_timer.stop()
            except:
                pass
            self.registered = False
    
    def _check_messages(self):
        msg = wintypes.MSG()
        
        while self.user32.PeekMessageW(
            ctypes.byref(msg),
            None,
            self.WM_HOTKEY,
            self.WM_HOTKEY,
            0x0001
        ):
            if msg.message == self.WM_HOTKEY and msg.wParam == self.hotkey_id:
                self.activated.emit()
            
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
    
    def is_registered(self):
        return self.registered
    
    def __del__(self):
        self.unregister()


class HotkeyManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey = GlobalHotkey(self)
        
    def setup_default_hotkey(self):
        return self.hotkey.register(
            GlobalHotkey.MOD_ALT | GlobalHotkey.MOD_CONTROL,
            0x4A
        )
    
    def connect_activated(self, callback):
        self.hotkey.activated.connect(callback)
    
    def is_available(self):
        return sys.platform == 'win32'
    
    def cleanup(self):
        self.hotkey.unregister()
