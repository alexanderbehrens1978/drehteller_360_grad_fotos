/**
 * settings.js
 * JavaScript für die Einstellungsseite - verbesserte Version
 */

document.addEventListener('DOMContentLoaded', function() {
    // Finde die wichtigen DOM-Elemente
    const settingsForm = document.getElementById('settingsForm');
    const statusMessage = document.getElementById('statusMessage');
    const whiteBalanceEnabled = document.getElementById('whiteBalanceEnabled');
    const whiteBalanceStrength = document.getElementById('whiteBalanceStrength');
    const strengthValue = document.getElementById('strengthValue');
    const referenceImageUpload = document.getElementById('referenceImageUpload');
    const referenceImagePreview = document.getElementById('referenceImagePreview');
    const referenceImageInfo = document.getElementById('referenceImageInfo');
    const useFirstProjectImage = document.getElementById('useFirstProjectImage');
    const correctProjectSelect = document.getElementById('correctProjectSelect');
    const applyCorrection = document.getElementById('applyCorrection');
    const projectCorrectSection = document.getElementById('projectCorrectSection');
    
    // Initialen Status ausblenden
    if (statusMessage) {
        statusMessage.style.display = 'none';
    }
    
    // Aktuelle Konfiguration laden
    console.log('Lade Konfiguration...');
    loadConfig();
    
    // Projekte für Weißabgleichkorrektur laden
    loadProjects();
    
    // Event Listener für KI-Weißabgleich-Aktivierung
    if (whiteBalanceEnabled) {
        whiteBalanceEnabled.addEventListener('change', function() {
            toggleWhiteBalanceSettings(this.checked);
        });
    }
    
    // Event Listener für Korrekturstärke
    if (whiteBalanceStrength && strengthValue) {
        whiteBalanceStrength.addEventListener('input', function() {
            strengthValue.textContent = this.value;
        });
    }
    
    // Event Listener für Referenzbild-Upload
    if (referenceImageUpload) {
        referenceImageUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                uploadReferenceImage(file);
            }
        });
    }
    
    // Event Listener für "Erstes Projektbild verwenden"
    if (useFirstProjectImage) {
        useFirstProjectImage.addEventListener('click', function() {
            useFirstImageAsReference();
        });
    }
    
    // Event Listener für "Weißabgleich anwenden"
    if (applyCorrection) {
        applyCorrection.addEventListener('click', function() {
            const projectId = correctProjectSelect.value;
            if (projectId) {
                applyWhiteBalanceCorrection(projectId);
            } else {
                showStatus('Bitte wählen Sie ein Projekt aus', 'error');
            }
        });
    }
    
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
                
                // Weißabgleich-Einstellungen aktivieren/deaktivieren
                const whiteBalanceEnabled = document.getElementById('whiteBalanceEnabled');
                if (whiteBalanceEnabled) {
                    toggleWhiteBalanceSettings(whiteBalanceEnabled.checked);
                }
                
                // Referenzbild anzeigen, falls vorhanden
                if (config.white_balance && config.white_balance.reference_image) {
                    updateReferenceImagePreview(config.white_balance.reference_image);
                }
                
                return true;
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
            showStatus('Fehler beim Laden der Konfiguration. Bitte versuchen Sie es später erneut.', 'error');
        });
        
    // Weißabgleich-Einstellungen laden
    fetch('/api/white_balance/settings')
        .then(response => response.json())
        .then(data => {
            // Weißabgleich aktivieren/deaktivieren
            const whiteBalanceEnabled = document.getElementById('whiteBalanceEnabled');
            if (whiteBalanceEnabled) {
                whiteBalanceEnabled.checked = data.enabled || false;
                toggleWhiteBalanceSettings(whiteBalanceEnabled.checked);
            }
            
            // Korrekturstärke setzen
            const whiteBalanceStrength = document.getElementById('whiteBalanceStrength');
            const strengthValue = document.getElementById('strengthValue');
            if (whiteBalanceStrength && data.strength !== undefined) {
                whiteBalanceStrength.value = data.strength;
                if (strengthValue) {
                    strengthValue.textContent = data.strength;
                }
            }
            
            // Referenzbild anzeigen, falls vorhanden
            if (data.reference_image_url) {
                updateReferenceImagePreview(data.reference_image_url);
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Weißabgleich-Einstellungen:', error);
        });
}

// Projekte für Weißabgleichkorrektur laden
function loadProjects() {
    fetch('/api/projects/list')
        .then(response => response.json())
        .then(data => {
            if (data.projects && data.projects.length > 0) {
                const correctProjectSelect = document.getElementById('correctProjectSelect');
                
                if (correctProjectSelect) {
                    // Bestehende Optionen entfernen (außer der ersten)
                    while (correctProjectSelect.options.length > 1) {
                        correctProjectSelect.remove(1);
                    }
                    
                    // Projekte hinzufügen
                    data.projects.forEach(project => {
                        const option = document.createElement('option');
                        option.value = project.id || project.uuid;
                        option.textContent = project.name;
                        correctProjectSelect.appendChild(option);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Projekte:', error);
        });
}

// Weißabgleich-Einstellungen aktivieren/deaktivieren
function toggleWhiteBalanceSettings(enabled) {
    const controls = document.querySelectorAll('.white-balance-control');
    
    controls.forEach(control => {
        control.disabled = !enabled;
    });
    
    const projectCorrectSection = document.getElementById('projectCorrectSection');
    if (projectCorrectSection) {
        projectCorrectSection.style.display = enabled ? 'flex' : 'none';
    }
}

// Referenzbild hochladen
function uploadReferenceImage(file) {
    const formData = new FormData();
    formData.append('reference_image', file);
    
    fetch('/api/white_balance/set_reference', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateReferenceImagePreview(data.image_url);
            showStatus('Referenzbild erfolgreich gesetzt', 'success');
        } else {
            showStatus('Fehler beim Setzen des Referenzbildes: ' + (data.error || 'Unbekannter Fehler'), 'error');
        }
    })
    .catch(error => {
        console.error('Fehler beim Hochladen des Referenzbildes:', error);
        showStatus('Fehler beim Hochladen des Referenzbildes', 'error');
    });
}

// Erstes Bild eines Projekts als Referenz verwenden
function useFirstImageAsReference() {
    const correctProjectSelect = document.getElementById('correctProjectSelect');
    
    if (!correctProjectSelect.value) {
        showStatus('Bitte wählen Sie ein Projekt aus', 'error');
        return;
    }
    
    fetch(`/api/white_balance/use_project_image/${correctProjectSelect.value}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateReferenceImagePreview(data.image_url);
            showStatus('Erstes Projektbild als Referenz gesetzt', 'success');
        } else {
            showStatus('Fehler beim Setzen des Referenzbildes: ' + (data.error || 'Unbekannter Fehler'), 'error');
        }
    })
    .catch(error => {
        console.error('Fehler beim Setzen des ersten Projektbildes als Referenz:', error);
        showStatus('Fehler beim Setzen des ersten Projektbildes als Referenz', 'error');
    });
}

// Referenzbild-Vorschau aktualisieren
function updateReferenceImagePreview(imagePath) {
    const referenceImagePreview = document.getElementById('referenceImagePreview');
    const referenceImageInfo = document.getElementById('referenceImageInfo');
    
    if (referenceImagePreview && referenceImageInfo) {
        if (imagePath && imagePath.startsWith('/')) {
            // Relative URL, muss mit der Basis-URL verbunden werden
            referenceImagePreview.src = imagePath;
        } else {
            // Vollständige URL
            referenceImagePreview.src = imagePath;
        }
        referenceImagePreview.style.display = 'block';
        referenceImageInfo.textContent = 'Referenzbild gesetzt';
    }
}

// Weißabgleichkorrektur auf ein Projekt anwenden
function applyWhiteBalanceCorrection(projectId) {
    const strength = document.getElementById('whiteBalanceStrength').value;
    
    fetch(`/api/white_balance/correct_project/${projectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ strength: parseFloat(strength) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus('Weißabgleichkorrektur erfolgreich angewendet', 'success');
        } else {
            showStatus('Fehler bei der Weißabgleichkorrektur: ' + (data.error || 'Unbekannter Fehler'), 'error');
        }
    })
    .catch(error => {
        console.error('Fehler bei der Weißabgleichkorrektur:', error);
        showStatus('Fehler bei der Weißabgleichkorrektur', 'error');
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
    
    // Weißabgleich-Einstellungen
    setValue('whiteBalanceEnabled', config?.white_balance?.enabled);
    setValue('whiteBalanceStrength', config?.white_balance?.strength);
    
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
        if (form.elements[key] && form.elements[key].type === 'checkbox') {
            value = form.elements[key].checked;
        }
        
        // Zahlen in numerische Werte umwandeln
        if (key.includes('resolution') || key.includes('degrees') || key.includes('interval') || key.includes('baudrate') || key.includes('strength')) {
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
    
    // Weißabgleich-Einstellungen hinzufügen
    if (!configData.white_balance) {
        configData.white_balance = {};
    }
    
    configData.white_balance.enabled = document.getElementById('whiteBalanceEnabled').checked;
    configData.white_balance.strength = parseFloat(document.getElementById('whiteBalanceStrength').value);
    
    console.log('Konfigurationsdaten:', configData);
    
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
