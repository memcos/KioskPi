document.addEventListener('DOMContentLoaded', () => {
    // Show Toast Notification
    const showToast = (message, type = 'success') => {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.style.borderColor = type === 'error' ? 'var(--danger-color)' : 'var(--primary-color)';
        
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    };

    // Handle URL Config Form
    const urlForm = document.getElementById('url-config-form');
    if (urlForm) {
        urlForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(urlForm);
            const data = {
                primary_url: formData.get('primary_url'),
                enable_secondary_url: formData.get('enable_secondary_url') === 'on',
                secondary_url: formData.get('secondary_url'),
                idle_timeout: parseInt(formData.get('idle_timeout') || 0, 10),
                input_field_selector: formData.get('input_field_selector'),
                auto_submit: formData.get('auto_submit') === 'on'
            };

            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Ayarlar başarıyla kaydedildi');
                } else {
                    showToast('Ayarlar kaydedilemedi', 'error');
                }
            } catch (err) {
                showToast('Bağlantı hatası', 'error');
            }
        });
    }

    // Handle Device Selection
    const saveDevicesBtn = document.getElementById('save-devices');
    if (saveDevicesBtn) {
        saveDevicesBtn.addEventListener('click', async () => {
            const select = document.getElementById('input_devices');
            const selectedDevices = Array.from(select.selectedOptions).map(opt => opt.value);
            
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input_devices: selectedDevices })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Cihaz ayarları kaydedildi');
                    // Reload to reflect changes in active devices display
                    setTimeout(() => window.location.reload(), 1000);
                }
            } catch (err) {
                showToast('Bağlantı hatası', 'error');
            }
        });
    }

    // Handle Boot Logo Upload
    const logoInput = document.getElementById('boot_logo');
    const uploadBtn = document.getElementById('upload-btn');
    const fileNameSpan = document.getElementById('file-name');
    
    if (logoInput) {
        logoInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                fileNameSpan.textContent = e.target.files[0].name;
                uploadBtn.style.display = 'inline-block';
            }
        });
        
        document.getElementById('logo-upload-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (logoInput.files.length === 0) return;
            
            const formData = new FormData();
            formData.append('file', logoInput.files[0]);
            
            const originalText = uploadBtn.textContent;
            uploadBtn.textContent = 'Yükleniyor...';
            uploadBtn.disabled = true;
            
            try {
                const res = await fetch('/api/bootlogo', {
                    method: 'POST',
                    body: formData
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Logo başarıyla yüklendi ve uygulandı');
                    fileNameSpan.textContent = '';
                    logoInput.value = '';
                    uploadBtn.style.display = 'none';
                } else {
                    showToast(result.error || 'Yükleme başarısız', 'error');
                }
            } catch (err) {
                showToast('Bağlantı hatası', 'error');
            } finally {
                uploadBtn.textContent = originalText;
                uploadBtn.disabled = false;
            }
        });
    }

    // Handle Boot Mode
    const saveBootmodeBtn = document.getElementById('save-bootmode');
    if (saveBootmodeBtn) {
        saveBootmodeBtn.addEventListener('click', async () => {
            const mode = document.getElementById('boot_mode').value;
            const originalText = saveBootmodeBtn.textContent;
            saveBootmodeBtn.textContent = 'İşleniyor (Lütfen bekleyin)...';
            saveBootmodeBtn.disabled = true;
            try {
                const res = await fetch('/api/bootmode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode })
                });
                const result = await res.json();
                if (result.success) showToast('Açılış ekranı stili uygulandı');
                else showToast('Hata oluştu', 'error');
            } catch(e) { showToast('Bağlantı hatası', 'error'); }
            
            saveBootmodeBtn.textContent = originalText;
            saveBootmodeBtn.disabled = false;
        });
    }

    // Handle Password Change
    const passForm = document.getElementById('password-form');
    if (passForm) {
        passForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const old_password = document.getElementById('old_password').value;
            const new_password = document.getElementById('new_password').value;
            
            if (new_password.length < 6) {
                showToast('Yeni şifre en az 6 karakter olmalıdır', 'error');
                return;
            }
            
            try {
                const res = await fetch('/api/password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_password, new_password })
                });
                const result = await res.json();
                
                if (result.success) {
                    showToast('Şifre başarıyla değiştirildi');
                    passForm.reset();
                } else {
                    showToast(result.error || 'Şifre değiştirilemedi', 'error');
                }
            } catch (err) {
                showToast('Bağlantı hatası', 'error');
            }
        });
    }

    // Handle System Actions
    const rebootAppBtn = document.getElementById('reboot-app');
    const rebootPiBtn = document.getElementById('reboot-pi');

    if (rebootAppBtn) {
        rebootAppBtn.addEventListener('click', async () => {
            if (confirm('Kiosk uygulamasını yeniden başlatmak istediğinize emin misiniz?')) {
                try {
                    await fetch('/api/reboot_app', { method: 'POST' });
                    showToast('Uygulama yeniden başlatılıyor...');
                    setTimeout(() => window.location.reload(), 3000);
                } catch (err) {}
            }
        });
    }

    if (rebootPiBtn) {
        rebootPiBtn.addEventListener('click', async () => {
            if (confirm('Cihazı tamamen yeniden başlatmak istediğinize emin misiniz?')) {
                try {
                    await fetch('/api/reboot_pi', { method: 'POST' });
                    showToast('Cihaz yeniden başlatılıyor. Lütfen bekleyin...');
                } catch (err) {}
            }
        });
    }

    // Handle Screenshot Modal
    const screenshotBtn = document.getElementById('take-screenshot');
    const modal = document.getElementById('screenshot-modal');
    const closeModal = document.querySelector('.close-modal');
    const refreshBtn = document.getElementById('refresh-screenshot');
    const imgEl = document.getElementById('screenshot-img');
    const loader = document.getElementById('screenshot-loader');

    const loadScreenshot = async () => {
        imgEl.style.display = 'none';
        loader.style.display = 'block';
        loader.textContent = 'Yükleniyor...';
        
        try {
            const res = await fetch('/api/screenshot');
            const data = await res.json();
            
            if (data.success) {
                imgEl.src = 'data:image/png;base64,' + data.image;
                imgEl.style.display = 'block';
                loader.style.display = 'none';
            } else {
                loader.textContent = 'Hata: ' + data.error;
            }
        } catch (err) {
            loader.textContent = 'Bağlantı hatası!';
        }
    };

    if (screenshotBtn && modal) {
        screenshotBtn.addEventListener('click', () => {
            modal.classList.add('show');
            loadScreenshot();
        });

        closeModal.addEventListener('click', () => {
            modal.classList.remove('show');
        });

        refreshBtn.addEventListener('click', () => {
            loadScreenshot();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    }

    // Handle Display Rotation
    const saveRotationBtn = document.getElementById('save-rotation');
    if (saveRotationBtn) {
        saveRotationBtn.addEventListener('click', async () => {
            const rotation = document.getElementById('display_rotation').value;
            const originalText = saveRotationBtn.textContent;
            saveRotationBtn.textContent = 'Bekleyin...';
            try {
                const res = await fetch('/api/rotation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rotation })
                });
                const result = await res.json();
                if (result.success) showToast('Ekran döndürme uygulandı');
                else showToast('Hata oluştu', 'error');
            } catch(e) { showToast('Bağlantı hatası', 'error'); }
            saveRotationBtn.textContent = originalText;
        });
    }

    // Handle Network Settings
    const scanWifiBtn = document.getElementById('scan-wifi');
    const wifiContainer = document.getElementById('wifi-list-container');
    const connectWifiBtn = document.getElementById('connect-wifi');
    const wifiSelect = document.getElementById('wifi-ssid');
    
    if (scanWifiBtn) {
        scanWifiBtn.addEventListener('click', async () => {
            scanWifiBtn.textContent = 'Taranıyor...';
            scanWifiBtn.disabled = true;
            try {
                const res = await fetch('/api/wifi/scan');
                const result = await res.json();
                if (result.success) {
                    wifiSelect.innerHTML = '';
                    result.networks.forEach(n => {
                        const opt = document.createElement('option');
                        opt.value = n.ssid;
                        let sec = n.security ? (n.security !== '--' ? ' (Şifreli)' : ' (Açık)') : '';
                        opt.textContent = `${n.ssid} - ${n.signal}%${sec}`;
                        wifiSelect.appendChild(opt);
                    });
                    wifiContainer.style.display = 'block';
                    showToast(`${result.networks.length} ağ bulundu`);
                } else showToast('Ağlar taranamadı', 'error');
            } catch(e) { showToast('Bağlantı hatası', 'error'); }
            scanWifiBtn.textContent = 'Çevredeki Ağları Tara';
            scanWifiBtn.disabled = false;
        });
    }

    if (connectWifiBtn) {
        connectWifiBtn.addEventListener('click', async () => {
            const ssid = wifiSelect.value;
            const password = document.getElementById('wifi-password').value;
            if (!ssid) return;
            
            connectWifiBtn.textContent = 'Bağlanıyor...';
            connectWifiBtn.disabled = true;
            try {
                const res = await fetch('/api/wifi/connect', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ssid, password })
                });
                const result = await res.json();
                if (result.success) {
                    showToast('Bağlantı başarılı. IP adresiniz değişmiş olabilir.', 'success');
                    document.getElementById('wifi-password').value = '';
                } else showToast(result.error || 'Bağlantı başarısız', 'error');
            } catch(e) { showToast('Bağlantı koptuysa IP değişmiş olabilir, sayfayı yenileyin.', 'error'); }
            connectWifiBtn.textContent = 'Bağlan';
            connectWifiBtn.disabled = false;
        });
    }

    // Handle System Update
    const updateSystemBtn = document.getElementById('update-system');
    if (updateSystemBtn) {
        updateSystemBtn.addEventListener('click', async () => {
            if (confirm('Sistemi GitHub üzerinden güncelleyip cihazı yeniden başlatmak istediğinize emin misiniz?')) {
                try {
                    await fetch('/api/system_update', { method: 'POST' });
                    showToast('Güncelleme başlatıldı. Cihaz kapanıp açılacak...');
                } catch(e) {}
            }
        });
    }

    // Handle Cron Settings
    const cronToggle = document.getElementById('daily_reboot_enabled');
    const cronTimeContainer = document.getElementById('reboot-time-container');
    const saveCronBtn = document.getElementById('save-reboot-schedule');
    
    if (cronToggle) {
        cronToggle.addEventListener('change', function() {
            cronTimeContainer.style.display = this.checked ? 'block' : 'none';
        });
    }

    if (saveCronBtn) {
        saveCronBtn.addEventListener('click', async () => {
            const enabled = cronToggle.checked;
            const timeStr = document.getElementById('daily_reboot_time').value;
            
            try {
                const res = await fetch('/api/schedule_reboot', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled, time: timeStr })
                });
                const result = await res.json();
                if (result.success) showToast('Zamanlama kaydedildi');
                else showToast('Hata oluştu', 'error');
            } catch(e) { showToast('Bağlantı hatası', 'error'); }
        });
    }

    // Polling for Status Updates
    if (document.getElementById('active-screen')) {
        setInterval(async () => {
            try {
                const res = await fetch('/api/status');
                const status = await res.json();
                
                document.getElementById('active-screen').textContent = status.current_state;
                
                // Update indicator dot
                const dot = document.querySelector('.dot');
                const statusText = document.querySelector('.status-text');
                
                if (status.browser_connected) {
                    dot.classList.add('active');
                    statusText.textContent = 'Tarayıcı Aktif';
                } else {
                    dot.classList.remove('active');
                    statusText.textContent = 'Tarayıcı Pasif';
                }
            } catch (err) {
                // Ignore silent poll errors
            }
        }, 5000);
    }
});
