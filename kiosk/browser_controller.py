import json
import websocket
import requests
import time
import threading

class BrowserController:
    def __init__(self, cdp_host='127.0.0.1', cdp_port=9222):
        self.cdp_host = cdp_host
        self.cdp_port = cdp_port
        self.ws_url = None
        self.ws = None
        self.msg_id = 1
        self.lock = threading.Lock()
        self.connected = False

    def connect(self, max_retries=10, retry_delay=2):
        for i in range(max_retries):
            try:
                response = requests.get(f"http://{self.cdp_host}:{self.cdp_port}/json")
                pages = response.json()
                
                # Find the main page
                page = next((p for p in pages if p['type'] == 'page'), None)
                if not page:
                    raise Exception("No page found")
                
                self.ws_url = page['webSocketDebuggerUrl']
                self.ws = websocket.create_connection(self.ws_url)
                self.connected = True
                print("Connected to Chromium CDP")
                return True
            except Exception as e:
                print(f"Failed to connect to CDP (attempt {i+1}/{max_retries}): {e}")
                time.sleep(retry_delay)
        return False

    def _send(self, method, params=None):
        if not self.connected or not self.ws:
            if not self.connect(max_retries=1):
                return None
                
        if params is None:
            params = {}
            
        with self.lock:
            payload = {
                "id": self.msg_id,
                "method": method,
                "params": params
            }
            try:
                self.ws.send(json.dumps(payload))
                response = json.loads(self.ws.recv())
                self.msg_id += 1
                return response
            except Exception as e:
                print(f"Error sending CDP command: {e}")
                self.connected = False
                return None

    def navigate(self, url):
        return self._send("Page.navigate", {"url": url})

    def wait_for_load(self):
        # We could implement a real listener here, but for simplicity we sleep a bit
        # Or evaluate a script to check document.readyState
        time.sleep(1) # Let it load a bit
        for _ in range(5):
            res = self._send("Runtime.evaluate", {"expression": "document.readyState"})
            if res and res.get('result', {}).get('result', {}).get('value') == 'complete':
                break
            time.sleep(0.5)

    def focus_and_type(self, selector, text, auto_submit=True):
        # We rely on the page's own focus logic if selector is empty
        if selector:
            # First focus the element if a selector is provided
            js_focus = f"document.querySelector('{selector}') && document.querySelector('{selector}').focus();"
            self._send("Runtime.evaluate", {"expression": js_focus})
            
        # Give it a tiny bit of time to focus
        time.sleep(0.1)
        
        # Then type the text using Input.dispatchKeyEvent for each char
        # It's more reliable to just evaluate JS to set value and dispatch events
        # But dispatchKeyEvent simulates real keyboard
        
        if selector:
            # If selector provided, just set the value and maybe dispatch event
            escaped_text = text.replace("'", "\\'")
            js_type = f"""
            var el = document.querySelector('{selector}');
            if(el) {{
                el.value = '{escaped_text}';
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            """
            self._send("Runtime.evaluate", {"expression": js_type})
        else:
            # If no selector, we simulate real keypresses to let the page catch it
            for char in text:
                self._send("Input.dispatchKeyEvent", {
                    "type": "char",
                    "text": char
                })
        
        if auto_submit:
            # Send Enter key
            self._send("Input.dispatchKeyEvent", {
                "type": "rawKeyDown",
                "windowsVirtualKeyCode": 13,
                "unmodifiedText": "\r",
                "text": "\r"
            })
            self._send("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "windowsVirtualKeyCode": 13
            })

    def capture_screenshot(self):
        res = self._send("Page.captureScreenshot", {"format": "png"})
        if res and 'result' in res and 'data' in res['result']:
            return res['result']['data']
        return None
