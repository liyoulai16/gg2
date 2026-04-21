import sys
import ctypes
from ctypes import wintypes
from PyQt6.QtCore import QObject, pyqtSignal, QAbstractNativeEventFilter, QCoreApplication
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


if sys.platform == 'win32':
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    WM_HOTKEY = 0x0312
    
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    MOD_NOREPEAT = 0x4000
    
    class NativeEventFilter(QAbstractNativeEventFilter):
        def __init__(self, hotkey_id, callback):
            super().__init__()
            self.hotkey_id = hotkey_id
            self.callback = callback
        
        def nativeEventFilter(self, eventType, message):
            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == self.hotkey_id:
                    self.callback()
                    return True, 0
            except:
                pass
            return False, 0


class GlobalHotkey(QObject):
    activated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey_id = 1
        self.registered = False
        self.native_filter = None
        
    def register(self, modifier, key_code):
        if sys.platform != 'win32':
            print("Global hotkeys only supported on Windows")
            return False
        
        if self.registered:
            self.unregister()
        
        try:
            result = user32.RegisterHotKey(
                None,
                self.hotkey_id,
                modifier | MOD_NOREPEAT,
                key_code
            )
            
            if result:
                self.registered = True
                
                def on_activated():
                    self.activated.emit()
                
                self.native_filter = NativeEventFilter(self.hotkey_id, on_activated)
                QCoreApplication.instance().installNativeEventFilter(self.native_filter)
                
                print(f"Global hotkey registered successfully (Alt+Ctrl+J)")
                return True
            else:
                error = ctypes.get_last_error()
                print(f"Failed to register hotkey. Error code: {error}")
                if error == 1409:
                    print("Hotkey is already registered by another application")
                return False
                
        except Exception as e:
            print(f"Error registering hotkey: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unregister(self):
        if self.registered:
            try:
                if self.native_filter:
                    QCoreApplication.instance().removeNativeEventFilter(self.native_filter)
                    self.native_filter = None
                
                user32.UnregisterHotKey(None, self.hotkey_id)
                print("Global hotkey unregistered")
            except Exception as e:
                print(f"Error unregistering hotkey: {e}")
            self.registered = False
    
    def is_registered(self):
        return self.registered
    
    def __del__(self):
        self.unregister()


class HotkeyManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hotkey = GlobalHotkey(self)
        self._fallback_shortcut = None
        
    def setup_default_hotkey(self):
        if sys.platform == 'win32':
            success = self.hotkey.register(
                MOD_ALT | MOD_CONTROL,
                0x4A
            )
            if not success:
                print("Warning: Global hotkey registration failed, using application-level fallback")
                self._setup_fallback_shortcut()
            return success
        else:
            print("Global hotkeys not supported on this platform")
            return False
    
    def _setup_fallback_shortcut(self):
        parent_widget = self.parent()
        if parent_widget and isinstance(parent_widget, QWidget):
            self._fallback_shortcut = QShortcut(
                QKeySequence("Alt+Ctrl+J"),
                parent_widget
            )
            self._fallback_shortcut.activated.connect(self._on_activated)
    
    def _on_activated(self):
        self.hotkey.activated.emit()
    
    def connect_activated(self, callback):
        self.hotkey.activated.connect(callback)
    
    def is_available(self):
        return sys.platform == 'win32'
    
    def cleanup(self):
        self.hotkey.unregister()
        if self._fallback_shortcut:
            self._fallback_shortcut.setEnabled(False)
