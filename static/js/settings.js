/**
 * settings.js
 * JavaScript für die Einstellungsseite - verbesserte Version
 */

document.addEventListener('DOMContentLoaded', function() {
    // Finde die wichtigen DOM-Elemente
    const settingsForm = document.getElementById('settingsForm');
    const statusMessage = document.getElementById('statusMessage');
    
    // Initialen Status ausblenden
    if (statusMessage) {
        statusMessage.style.display = 'none';
    }
    
    // Aktuelle Konfiguration laden
    console.log('Lade Konfiguration...');
    loadConfig();
    
    // Formular absenden
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveConfig(this);
        });
    }
});

// Konfiguration laden
function loadConfig() {
    fetch('/get_config')
        .then(response => {
            console.log('Antwort erhalten, Status:', response.status);
            return response.json();
        })
        .then(config => {
            console.log('Konfiguration geladen:', config);
            
            if (config) {
                // Formularwerte setzen
                setFormValues(config);
                return true;
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
            showStatus('Fehler beim Laden der Konfiguration. Bitte versuchen Sie es später erneut.', 'error');
        });
}

// Formularwerte setzen
function setFormValues(config) {
    // Kamera-Einstellungen
    setValue('cameraType', config?.camera?.type);
    setValue('cameraPath', config?.camera?.device_path);
    setValue('resolutionWidth', config?.camera?.resolution?.width);
    setValue('resolutionHeight', config?.camera?.resolution?.height);
    
    // Arduino-Einstellungen
    setValue('arduinoPort', config?.arduino?.port);
    setValue('arduinoBaudrate', config?.arduino?.baudrate);
    
    // Drehteller-Einstellungen
    setValue('defaultDegrees', config?.rotation?.default_degrees);
    setValue('defaultInterval', config?.rotation?.default_interval);
    
    console.log('Formularwerte wurden gesetzt');
}

// Wert in einem Formularfeld setzen
function setValue(id, value) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element mit ID ${id} nicht gefunden`);
        return;
    }
    
    // Je nach Elementtyp den Wert setzen
    if (element.type === 'checkbox') {
        element.checked = !!value;
    } else if (element.tagName === 'SELECT') {
        // Bei Select-Elementen versuchen wir, den passenden Wert zu finden
        const option = Array.from(element.options).find(opt => opt.value === String(value));
        if (option) {
            element.value = option.value;
        } else if (value !== undefined && value !== null) {
            // Wenn kein passender Wert gefunden wird, fügen wir einen hinzu
            const newOption = document.createElement('option');
            newOption.value = value;
            newOption.textContent = value;
            element.appendChild(newOption);
            element.value = value;
        }
    } else {
        // Für alle anderen Elemente den Wert direkt setzen
        element.value = value !== undefined && value !== null ? value : '';
    }
}

// Konfiguration speichern
function saveConfig(form) {
    console.log('Speichere Konfiguration...');
    
    // FormData in ein JSON-Objekt umwandeln
    const formData = new FormData(form);
    const configData = {};
    
    // FormData in verschachtelte Objekte umwandeln
    formData.forEach((value, key) => {
        // Checkbox-Werte in boolesche Werte umwandeln
        if (form.elements[key].type === 'checkbox') {
            value = form.elements[key].checked;
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
    
    // Konfiguration an den Server senden
    fetch('/settings/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(configData)
    })
    .then(response => response.json())
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
}

// Hilfsfunktion zum Anzeigen von Statusmeldungen
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
