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
    if (!element
