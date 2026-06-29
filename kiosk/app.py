import os
import sys
import threading
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

from config_manager import ConfigManager
from browser_controller import BrowserController
from input_monitor import InputMonitor
from idle_manager import IdleManager
from auth import AuthManager
import boot_logo

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Globals
config = None
browser = None
monitor = None
idle = None
auth = None

def get_system_status():
    status = {
        "browser_connected": browser.connected if browser else False,
        "input_monitoring": monitor.running if monitor else False,
        "active_devices": [d.name for d in monitor.monitors] if monitor else [],
        "current_state": idle.current_state if idle else "unknown"
    }
    return status

@app.before_request
def check_auth():
    if request.endpoint and request.endpoint not in ['login', 'static']:
        if not session.get('logged_in'):
            return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if auth.verify_password(password):
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Geçersiz şifre')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    all_config = config.get_all()
    status = get_system_status()
    # input_devices to display all available input devices
    available_devices = []
    if monitor:
        available_devices = [d.name for d in monitor._get_input_devices()]
    
    return render_template('dashboard.html', config=all_config, status=status, available_devices=available_devices)

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(config.get_all())

@app.route('/api/config', methods=['POST'])
def save_config():
    data = request.json
    config.update(data)
    
    # Reload primary URL immediately if we are in primary state
    if idle.current_state == 'primary' and 'primary_url' in data:
        browser.navigate(data['primary_url'])
        
    return jsonify({"success": True})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify(get_system_status())

@app.route('/api/password', methods=['POST'])
def change_password():
    data = request.json
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')
    
    if auth.verify_password(old_pass):
        if auth.set_password(new_pass):
            return jsonify({"success": True})
    return jsonify({"success": False, "error": "Geçersiz mevcut şifre"}), 400

@app.route('/api/bootlogo', methods=['POST'])
def upload_bootlogo():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Dosya bulunamadı"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Dosya seçilmedi"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = '/opt/kioskpi/uploads'
        os.makedirs(upload_folder, exist_ok=True)
        path = os.path.join(upload_folder, filename)
        file.save(path)
        
        # Apply logo
        success = boot_logo.apply_logo(path)
        if success:
            config.set('boot_logo_path', path)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Logo uygulanamadı"}), 500
            
    return jsonify({"success": False, "error": "Geçersiz dosya türü"}), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

@app.route('/api/reboot_app', methods=['POST'])
def reboot_app():
    # Restart the display service and app service gracefully if needed
    # But usually just exit(0) lets systemd restart it
    def restart():
        import time
        time.sleep(1)
        os.system("sudo systemctl restart kiosk-display.service kiosk-app.service")
    threading.Thread(target=restart).start()
    return jsonify({"success": True})

@app.route('/api/reboot_pi', methods=['POST'])
def reboot_pi():
    def restart():
        import time
        time.sleep(1)
        os.system("sudo reboot")
    threading.Thread(target=restart).start()
    return jsonify({"success": True})

@app.route('/api/screenshot', methods=['GET'])
def get_screenshot():
    if not browser or (not browser.connected and not browser.connect(max_retries=1, retry_delay=0.1)):
        return jsonify({"success": False, "error": "Tarayıcı bağlı değil"}), 400
    
    data = browser.capture_screenshot()
    if data:
        return jsonify({"success": True, "image": data})
    return jsonify({"success": False, "error": "Ekran görüntüsü alınamadı"}), 500

def main():
    global config, browser, monitor, idle, auth
    
    config = ConfigManager()
    auth = AuthManager()
    browser = BrowserController()
    
    # Initialize components
    idle = IdleManager(config, browser)
    monitor = InputMonitor(callback=idle.register_interaction, config_manager=config)
    
    # Start background threads
    monitor.start()
    idle.start()
    
    # Wait for Chromium to start
    print("Waiting for Chromium CDP...")
    browser.connect(max_retries=15, retry_delay=2)
    
    if browser.connected:
        print("Loading primary URL...")
        browser.navigate(config.get('primary_url', 'about:blank'))
    
    # Start web server
    port = config.get('admin_port', 8080)
    print(f"Starting admin server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
