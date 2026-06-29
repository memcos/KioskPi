import os
import sys
import threading
import socket
import io
import base64
import qrcode
import subprocess
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

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = None
    finally:
        s.close()
    return IP

@app.route('/setup_screen')
def setup_screen():
    return render_template('setup_screen.html')

@app.route('/api/setup_info')
def setup_info():
    ip = get_ip_address()
    if not ip:
        return jsonify({"ip": None})
    
    port = config.get('admin_port', 8080)
    url = f"http://{ip}:{port}"
    
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return jsonify({"ip": ip, "port": port, "qr_base64": qr_base64})

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
        new_url = data['primary_url']
        if new_url == 'about:blank' or new_url.strip() == '':
            port = config.get('admin_port', 8080)
            new_url = f"http://127.0.0.1:{port}/setup_screen"
        browser.navigate(new_url)
        
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

def apply_rotation(degrees):
    try:
        cmd_list = "XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-1 wlr-randr"
        out = subprocess.check_output(['su', 'kiosk', '-c', cmd_list], stderr=subprocess.STDOUT).decode()
        outputs = [line.split()[0] for line in out.split('\n') if line and not line.startswith(' ')]
        
        for output in outputs:
            rot_cmd = f"{cmd_list} --output {output} --transform {degrees}"
            subprocess.run(['su', 'kiosk', '-c', rot_cmd])
        return True
    except Exception as e:
        print("Rotation error:", e)
        return False

@app.route('/api/rotation', methods=['POST'])
def set_rotation():
    data = request.json
    rotation = data.get('rotation', '0')
    config.set('display_rotation', rotation)
    apply_rotation(rotation)
    return jsonify({"success": True})

@app.route('/api/wifi/scan', methods=['GET'])
def wifi_scan():
    try:
        out = subprocess.check_output(['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY', 'dev', 'wifi']).decode()
        networks = []
        for line in out.split('\n'):
            if line:
                parts = line.split(':')
                if len(parts) >= 3 and parts[0]:
                    networks.append({
                        "ssid": parts[0],
                        "signal": parts[1],
                        "security": parts[2]
                    })
        unique = {}
        for n in networks:
            if n['ssid'] not in unique or int(n['signal']) > int(unique[n['ssid']]['signal']):
                unique[n['ssid']] = n
        return jsonify({"success": True, "networks": list(unique.values())})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wifi/connect', methods=['POST'])
def wifi_connect():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password', '')
    try:
        if password:
            subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], check=True)
        else:
            subprocess.run(['nmcli', 'dev', 'wifi', 'connect', ssid], check=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/schedule_reboot', methods=['POST'])
def schedule_reboot():
    data = request.json
    enabled = data.get('enabled', False)
    time_str = data.get('time', '03:00')
    
    config.set('daily_reboot_enabled', enabled)
    config.set('daily_reboot_time', time_str)
    
    cron_file = '/etc/cron.d/kioskpi-reboot'
    try:
        if enabled:
            hour, minute = time_str.split(':')
            cron_content = f"{minute} {hour} * * * root /sbin/reboot\n"
            with open(cron_file, 'w') as f:
                f.write(cron_content)
        else:
            if os.path.exists(cron_file):
                os.remove(cron_file)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/system_update', methods=['POST'])
def system_update():
    def do_update():
        import time
        time.sleep(1)
        os.system("curl -sSL https://raw.githubusercontent.com/memcos/KioskPi/main/setup.sh | bash")
    threading.Thread(target=do_update).start()
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
    
    # Apply saved display rotation
    rotation = config.get('display_rotation', '0')
    if rotation != '0':
        apply_rotation(rotation)
    
    # Wait for Chromium to start
    print("Waiting for Chromium CDP...")
    browser.connect(max_retries=15, retry_delay=2)
    
    if browser.connected:
        print("Loading primary URL...")
        primary = config.get('primary_url', 'about:blank')
        if primary == 'about:blank' or primary.strip() == '':
            port = config.get('admin_port', 8080)
            primary = f"http://127.0.0.1:{port}/setup_screen"
        browser.navigate(primary)
    
    # Start web server
    port = config.get('admin_port', 8080)
    print(f"Starting admin server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
