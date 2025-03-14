/**
 * settings.js
 * JavaScript für die Einstellungsseite
 */

document.addEventListener('DOMContentLoaded', function() {
    const settingsForm = document.getElementById('settingsForm');
    const statusMessage = document.getElementById('statusMessage');
    
    // Aktuelle Konfiguration laden
    loadConfig();
    
    // Formular absenden
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveConfig);
    }
});

// Konfiguration laden
function loadConfig() {
    fetch('/get_config')
        .then(response => response.json())
        .then(config => {
            setFormValues(config);
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
            showStatus('Fehler beim Laden der Konfiguration. Bitte versuchen Sie es später erneut.', 'error');
        });
}

// Formularwerte setzen
function setFormValues(config) {
    // Kamera-Einstellungen
    setInputValue('cameraType', config?.camera?.type);
    setInputValue('cameraPath', config?.camera?.device_path);
    setInputValue('resolutionWidth', config?.camera?.resolution?.width);
    setInputValue('resolutionHeight', config?.camera?.resolution?.height);
    
    // Arduino-Einstellungen
    setInputValue('arduinoPort', config?.arduino?.port);
    setInputValue('arduinoBaudrate', config?.arduino?.baudrate);
    
    // Drehteller-Einstellungen
    setInputValue('defaultDegrees', config?.rotation?.default_degrees);
    setInputValue('defaultInterval', config?.rotation?.default_interval);
    
    // Simulator-Einstellungen
    setInputValue('simulatorEnabled', config?.simulator?.enabled);
}

// Inputwert setzen (mit Fallback für Checkboxen)
function setInputValue(id, value) {
    const element = document.getElementById(id);
    if (!element) return;
    
    if (element.type === 'checkbox') {
        element.checked = Boolean(value);
    } else {
        element.value = value !== undefined ? value : '';
    }
}

// Konfiguration speichern
function saveConfig(event) {
    event.preventDefault();
    
    // Formulardaten sammeln
    const formData = new FormData(event.target);
    const configData = {};
    
    // FormData in JSON umwandeln mit besserer Fehlerbehandlung
    try {
        // FormData in verschachtelte Objekte umwandeln
        formData.forEach((value, key) => {
            // Checkbox-Werte in boolesche Werte umwandeln
            if (key === 'simulator.enabled') {
                value = document.getElementById('simulatorEnabled').checked;
            }
            
            // Zahlen in numerische Werte umwandeln
            if (key.includes('resolution') || key.includes('degrees') || key.includes('interval') || key.includes('baudrate')) {
                value = Number(value);
            }
            
            // Punkt-Notation in verschachtelte Objekte umwandeln
            const keys = key.split('.');
            let current = configData;
            
            for (let i = 0; i < keys.length - 1; i++) {
                if (!current[keys[i]]) {
                    current[keys[i]] = {};
                }
                current = current[keys[i]];
            }
            
            current[keys[keys.length - 1]] = value;
        });
        
        console.log('Konfiguration zum Speichern:', JSON.stringify(configData, null, 2));
        
        // Konfiguration speichern
        fetch('/save_config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showStatus('Einstellungen erfolgreich gespeichert!', 'success');
            } else {
                showStatus('Fehler beim Speichern der Einstellungen: ' + (data.message || 'Unbekannter Fehler'), 'error');
            }
        })
        .catch(error => {
            console.error('Fehler beim Speichern der Konfiguration:', error);
            showStatus('Fehler beim Speichern der Konfiguration. Bitte versuchen Sie es später erneut.', 'error');
        });
    } catch (e) {
        console.error('Fehler beim Erstellen der Konfigurationsdaten:', e);
        showStatus('Fehler beim Erstellen der Konfigurationsdaten: ' + e.message, 'error');
    }
}

// Statusmeldung anzeigen
function showStatus(message, type) {
    const statusMessage = document.getElementById('statusMessage');
    if (!statusMessage) return;
    
    statusMessage.textContent = message;
    statusMessage.className = 'status-message status-' + type;
    statusMessage.style.display = 'block';
    
    // Nach 5 Sekunden ausblenden
    setTimeout(() => {
        statusMessage.style.display = 'none';
    }, 5000);
}
