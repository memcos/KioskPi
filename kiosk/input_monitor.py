import evdev
import threading
import time
import glob
import select

class InputMonitor:
    def __init__(self, callback, config_manager):
        self.callback = callback
        self.config_manager = config_manager
        self.running = False
        self.thread = None
        self.devices = {}
        self.monitors = []
        
        # Keyboard mapping for standard US layout
        self.keys_mapping = {
            # Numbers
            2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8', 10: '9', 11: '0',
            # Letters
            16: 'q', 17: 'w', 18: 'e', 19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p',
            30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k', 38: 'l',
            44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b', 49: 'n', 50: 'm',
            # Symbols
            12: '-', 13: '=', 26: '[', 27: ']', 28: '\n', 39: ';', 40: "'", 43: '\\', 51: ',', 52: '.', 53: '/',
            57: ' '
        }
        
        self.shift_mapping = {
            2: '!', 3: '@', 4: '#', 5: '$', 6: '%', 7: '^', 8: '&', 9: '*', 10: '(', 11: ')',
            12: '_', 13: '+', 26: '{', 27: '}', 39: ':', 40: '"', 43: '|', 51: '<', 52: '>', 53: '?',
        }

    def _get_input_devices(self):
        devices = []
        for path in glob.glob('/dev/input/event*'):
            try:
                device = evdev.InputDevice(path)
                # Check if it has keys (like a keyboard/barcode scanner)
                if evdev.ecodes.EV_KEY in device.capabilities():
                    devices.append(device)
            except Exception:
                pass
        return devices

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            
        for dev in self.monitors:
            try:
                dev.close()
            except:
                pass

    def _run(self):
        barcode_buffer = ""
        shift_pressed = False
        
        while self.running:
            # Refresh devices occasionally to handle hotplugging
            current_devices = self._get_input_devices()
            
            # Filter by config if specific devices are selected
            configured_devices = self.config_manager.get('input_devices', [])
            if configured_devices:
                active_devices = [d for d in current_devices if d.name in configured_devices]
                # If configured device not found, fallback to all key devices
                if not active_devices:
                    active_devices = current_devices
            else:
                active_devices = current_devices
                
            self.monitors = active_devices
            
            if not self.monitors:
                time.sleep(2)
                continue
                
            try:
                # Wait for input events with a timeout to allow checking self.running
                r, w, x = select.select(self.monitors, [], [], 1.0)
                
                for dev in r:
                    for event in dev.read():
                        if event.type == evdev.ecodes.EV_KEY:
                            data = evdev.categorize(event)
                            
                            # Shift key state
                            if data.scancode in [42, 54]: # L_SHIFT, R_SHIFT
                                shift_pressed = (data.keystate == 1 or data.keystate == 2)
                                continue
                                
                            # Key down (1) or hold (2)
                            if data.keystate == 1 or data.keystate == 2:
                                if data.scancode == 28: # Enter
                                    if barcode_buffer:
                                        self.callback(barcode_buffer)
                                        barcode_buffer = ""
                                else:
                                    char = None
                                    if shift_pressed:
                                        # Capital letter
                                        if 16 <= data.scancode <= 50:
                                            char = self.keys_mapping.get(data.scancode, '').upper()
                                        else:
                                            char = self.shift_mapping.get(data.scancode)
                                    else:
                                        char = self.keys_mapping.get(data.scancode)
                                        
                                    if char:
                                        barcode_buffer += char
                                        
            except Exception as e:
                print(f"Error reading input: {e}")
                time.sleep(1)
