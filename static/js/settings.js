// Camera Resolution Preset Handling
const cameraWidthInput = document.getElementById('camera-width');
const cameraHeightInput = document.getElementById('camera-height');
const cameraResolutionPreset = document.getElementById('camera-resolution-preset');
const simulatorOnBtn = document.getElementById('simulator-on');
const simulatorOffBtn = document.getElementById('simulator-off');

// Resolution preset change handler
cameraResolutionPreset.addEventListener('change', (e) => {
    const preset = e.target.value;
    
    switch(preset) {
        case '640x480':
            cameraWidthInput.value = 640;
            cameraHeightInput.value = 480;
            break;
        case '1280x720':
            cameraWidthInput.value = 1280;
            cameraHeightInput.value = 720;
            break;
        case '1920x1080':
            cameraWidthInput.value = 1920;
            cameraHeightInput.value = 1080;
            break;
        case '2560x1440':
            cameraWidthInput.value = 2560;
            cameraHeightInput.value = 1440;
            break;
        case '3840x2160':
            cameraWidthInput.value = 3840;
            cameraHeightInput.value = 2160;
            break;
        case 'custom':
            // Clear inputs or keep current values
            break;
    }
});

// Geräteliste laden
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const devices = await response.json();
        
        updateDeviceUI(devices);
    } catch (error) {
        console.error('Fehler beim Laden der Geräte:', error);
    }
}

// Geräte-UI aktualisieren
function updateDeviceUI(devices) {
    // Bestehende Listen entfernen (um Duplikate zu vermeiden)
    document.querySelectorAll('.device-list').forEach(el => el.remove());
    
    // Webcams anzeigen
    const webcamList = document.createElement('div');
    webcamList.className = 'mt-2 small device-list';
    
    if (devices.cameras.webcams.length > 0) {
        devices.cameras.webcams.forEach(webcam => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary clickable-device';
            option.innerHTML = `<i class="bi bi-camera-video"></i> ${webcam}`;
            option.addEventListener('click', () => {
                document.getElementById('camera-device-path').value = webcam;
            });
            webcamList.appendChild(option);
        });
    } else {
        webcamList.innerHTML = '<div class="form-text text-muted">Keine Webcams gefunden</div>';
    }
    
    // Nach dem Kamera-Device-Pfad einfügen
    const cameraInput = document.getElementById('camera-device-path');
    cameraInput.parentNode.appendChild(webcamList);
    
    // gPhoto2-Kameras anzeigen
    const gphotoList = document.createElement('div');
    gphotoList.className = 'mt-2 small device-list';
    
    if (devices.cameras.gphoto2.length > 0) {
        devices.cameras.gphoto2.forEach(camera => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary';
            option.innerHTML = `<i class="bi bi-camera"></i> ${camera}`;
            gphotoList.appendChild(option);
        });
    } else {
        gphotoList.innerHTML = '<div class="form-text text-muted">Keine gphoto2-Kameras gefunden</div>';
    }
    
    // Nach dem Kameratyp einfügen
    const cameraType = document.getElementById('camera-type');
    cameraType.parentNode.appendChild(gphotoList);
    
    // Arduino-Geräte anzeigen
    const arduinoList = document.createElement('div');
    arduinoList.className = 'mt-2 small device-list';
    
    if (devices.arduinos.length > 0) {
        devices.arduinos.forEach(arduino => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary clickable-device';
            option.innerHTML = `<i class="bi bi-cpu"></i> ${arduino.port} - ${arduino.description}`;
            option.addEventListener('click', () => {
                document.getElementById('arduino-port').value = arduino.port;
            });
            arduinoList.appendChild(option);
        });
    } else {
        arduinoList.innerHTML = '<div class="form-text text-muted">Keine Arduino-Geräte gefunden</div>';
    }
    
    // Nach dem Arduino-Port einfügen
    const arduinoInput = document.getElementById('arduino-port');
    arduinoInput.parentNode.appendChild(arduinoList);
}

// Add existing code from previous settings.js here...
document.addEventListener('DOMContentLoaded', () => {
    // Geräteliste laden
    loadDevices();
    
    // Konfiguration vom Server laden
    fetch('/get_config')
        .then(response => response.json())
        .then(config => {
            console.log('Geladene Konfiguration:', config);
            
            // Kamera-Einstellungen
            if (config.camera) {
                document.getElementById('camera-device-path').value = config.camera.device_path || '';
                document.getElementById('camera-type').value = config.camera.type || 'webcam';
                
                // Kamera-Auflösung setzen
                const cameraWidth = config.camera.resolution?.width;
                const cameraHeight = config.camera.resolution?.height;
                
                if (cameraWidth && cameraHeight) {
                    cameraWidthInput.value = cameraWidth;
                    cameraHeightInput.value = cameraHeight;
                    
                    // Set preset dropdown
                    const presetValue = `${cameraWidth}x${cameraHeight}`;
                    const presetOption = Array.from(cameraResolutionPreset.options)
                        .find(option => option.value === presetValue);
                    
                    if (presetOption) {
                        cameraResolutionPreset.value = presetValue;
                    } else {
                        cameraResolutionPreset.value = 'custom';
                    }
                }
            }
            
            // Arduino-Einstellungen
            if (config.arduino) {
                document.getElementById('arduino-port').value = config.arduino.port || '';
                document.getElementById('arduino-baudrate').value = config.arduino.baudrate || 9600;
            }
            
            // Rotations-Einstellungen
            if (config.rotation) {
                document.getElementById('rotation-degrees').value = config.rotation.default_degrees || 15;
                document.getElementById('rotation-interval').value = config.rotation.default_interval || 5;
            }
            
            // Simulator-Einstellungen
            if (config.simulator !== undefined) {
                // Hier ist der Fehler - wir müssen den richtigen Radio-Button auswählen
                if (config.simulator.enabled) {
                    simulatorOnBtn.checked = true;
                } else {
                    simulatorOffBtn.checked = true;
                }
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
        });
});

// Aktualisierungsknopf für Geräteliste
const deviceRefreshButton = document.createElement('button');
deviceRefreshButton.type = 'button';
deviceRefreshButton.className = 'btn btn-outline-secondary mt-3';
deviceRefreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Geräte aktualisieren';
deviceRefreshButton.addEventListener('click', loadDevices);

// CSS für klickbare Geräte
const style = document.createElement('style');
style.textContent = `
    .clickable-device {
        cursor: pointer;
        transition: color 0.2s;
    }
    .clickable-device:hover {
        color: #0056b3 !important;
        text-decoration: underline;
    }
`;
document.head.appendChild(style);

// Knopf zum Formular hinzufügen (nach dem Laden der Seite)
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('settings-form').insertBefore(
        deviceRefreshButton,
        document.querySelector('.d-grid.gap-2.d-md-flex')
    );
});

// Debug-Button für Konfigurationstest hinzufügen
const debugButton = document.createElement('button');
debugButton.type = 'button';
debugButton.className = 'btn btn-outline-info mt-3 ms-2';
debugButton.innerHTML = '<i class="bi bi-bug"></i> Konfiguration testen';
debugButton.addEventListener('click', async (e) => {
    e.preventDefault();
    
    // Aktuelle Konfiguration abrufen und anzeigen
    try {
        const response = await fetch('/get_config');
        const config = await response.json();
        
        // Config-Nachricht erstellen
        const configMsg = document.createElement('div');
        configMsg.className = 'alert alert-info mt-3';
        configMsg.innerHTML = '<strong>Aktuelle Konfiguration:</strong><pre>' + 
                             JSON.stringify(config, null, 2) + '</pre>';
        
        // Vorhandene Nachrichten entfernen
        const existingMsg = document.querySelector('.debug-config-msg');
        if (existingMsg) existingMsg.remove();
        
        // Nachricht zur Seite hinzufügen
        configMsg.classList.add('debug-config-msg');
        document.getElementById('settings-form').appendChild(configMsg);
        
        console.log('Aktuelle Konfiguration:', config);
    } catch (error) {
        console.error('Fehler beim Laden der Konfiguration:', error);
        alert('Fehler beim Laden der Konfiguration: ' + error.message);
    }
});

// Zum Formular hinzufügen, direkt nach dem Geräte-Aktualisierungsbutton
document.addEventListener('DOMContentLoaded', () => {
    const refreshButton = document.querySelector('[id="settings-form"] button[type="button"]');
    if (refreshButton) {
        refreshButton.parentNode.insertBefore(debugButton, refreshButton.nextSibling);
    } else {
        const formActions = document.querySelector('.d-grid.gap-2.d-md-flex');
        formActions.parentNode.insertBefore(debugButton, formActions);
    }
});

// Formular-Abschicken
document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Prepare configuration object
    const config = {
        camera: {
            device_path: document.getElementById('camera-device-path').value,
            type: document.getElementById('camera-type').value,
            resolution: {
                width: parseInt(cameraWidthInput.value || 0),
                height: parseInt(cameraHeightInput.value || 0)
            }
        },
        arduino: {
            port: document.getElementById('arduino-port').value,
            baudrate: parseInt(document.getElementById('arduino-baudrate').value)
        },
        rotation: {
            default_degrees: parseInt(document.getElementById('rotation-degrees').value),
            default_interval: parseInt(document.getElementById('rotation-interval').value)
        },
        simulator: {
            enabled: document.getElementById('simulator-on').checked
        }
    };

    console.log("Einstellungen zum Speichern:", config);

    try {
        // Statusnachricht anzeigen
        const statusMsg = document.createElement('div');
        statusMsg.className = 'alert alert-info mt-3';
        statusMsg.textContent = 'Einstellungen werden gespeichert...';
        
        const existingMsg = document.querySelector('.save-status-msg');
        if (existingMsg) existingMsg.remove();
        
        statusMsg.classList.add('save-status-msg');
        document.getElementById('settings-form').appendChild(statusMsg);
        
        // Send configuration to server
        const response = await fetch('/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        // Antwort parsen
        const data = await response.json();
        console.log("Server-Antwort:", data);
        
        if (response.ok && data.status === 'success') {
            // Show success message
            statusMsg.className = 'alert alert-success mt-3 save-status-msg';
            statusMsg.textContent = 'Einstellungen erfolgreich gespeichert!';
            
            // Redirect to main page after a short delay
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            // Show error message
            statusMsg.className = 'alert alert-danger mt-3 save-status-msg';
            statusMsg.textContent = 'Fehler beim Speichern der Einstellungen: ' + 
                                  (data.message || 'Unbekannter Fehler');
            console.error('Fehler vom Server:', data);
        }
    } catch (error) {
        console.error('Verbindungsfehler:', error);
        
        const statusMsg = document.querySelector('.save-status-msg') || 
                         document.createElement('div');
        statusMsg.className = 'alert alert-danger mt-3 save-status-msg';
        statusMsg.textContent = 'Verbindungsfehler: ' + error.message;
        
        if (!document.querySelector('.save-status-msg')) {
            document.getElementById('settings-form').appendChild(statusMsg);
        }
    }
});
