import time
import threading

class IdleManager:
    def __init__(self, config_manager, browser_controller):
        self.config = config_manager
        self.browser = browser_controller
        self.last_interaction = time.time()
        self.current_state = 'primary' # 'primary' or 'secondary'
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def register_interaction(self, barcode=None):
        self.last_interaction = time.time()
        
        if self.current_state == 'secondary':
            print("Interaction detected, switching to primary URL")
            primary_url = self.config.get('primary_url', 'about:blank')
            self.browser.navigate(primary_url)
            self.current_state = 'primary'
            
            # If we received a barcode while idle, we need to wait for page load and type it
            if barcode:
                self.browser.wait_for_load()
                selector = self.config.get('input_field_selector', '')
                auto_submit = self.config.get('auto_submit', True)
                self.browser.focus_and_type(selector, barcode, auto_submit)
        else:
            # Already on primary URL, just handle the barcode if any
            if barcode:
                selector = self.config.get('input_field_selector', '')
                auto_submit = self.config.get('auto_submit', True)
                # Ensure we are focused before typing
                self.browser.focus_and_type(selector, barcode, auto_submit)

    def _run(self):
        while self.running:
            time.sleep(1)
            
            idle_timeout = self.config.get('idle_timeout', 60)
            primary_url = self.config.get('primary_url', 'about:blank')
            enable_secondary = self.config.get('enable_secondary_url', False)
            secondary_url = self.config.get('secondary_url', 'about:blank')
            
            if idle_timeout <= 0 or not enable_secondary:
                continue # Disable idle switching if timeout is 0 or less, or disabled
                
            elapsed = time.time() - self.last_interaction
            
            if elapsed >= idle_timeout and self.current_state == 'primary':
                if secondary_url and secondary_url != 'about:blank':
                    print(f"Idle for {elapsed:.1f}s, switching to secondary URL")
                    self.browser.navigate(secondary_url)
                    self.current_state = 'secondary'
