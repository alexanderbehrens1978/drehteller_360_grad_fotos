/**
 * settings.js
 * JavaScript für die Einstellungsseite
 */

document.addEventListener('DOMContentLoaded', function() {
    const settingsForm = document.getElementById('settingsForm');
    const statusMessage = document.getElementById('statusMessage');
    
    // Kamera-Typ-Auswahl
    const cameraType = document.getElementById('cameraType');
    const webcamOptions = document.querySelectorAll('.webcam-options');
    const gphoto2Options = document.querySelectorAll('.gphoto2-options');
    
    // Kamera-Buttons
    const refreshWebcams = document.getElementById('refreshWebcams');
    const refreshGphoto2 = document.getElementById('refreshGphoto2');
    const detectCamera = document.getElementById('detectCamera');
    const testCamera = document.getElementById('testCamera');
    const saveProfile = document.getElementById('saveProfile');
    
    // Kamera-Dropdown-Elemente
    const webcamDevice = document.getElementById('webcamDevice');
    const gphoto2Device = document.getElementById('gphoto2Device');
    const cameraProfile = document.getElementById('cameraProfile');
    
    // Kamera-Typ-Änderungen behandeln
    if (cameraType) {
        cameraType.addEventListener('change', function() {
            updateCameraOptions();
        });
    }
    
    // Aktualisierungsbuttons
    if (refreshWebcams) {
        refreshWebcams.addEventListener('click', function() {
            loadCameras('webcam');
        });
    }
    
    if (refreshGphoto2) {
        refreshGphoto2.addEventListener('click', function() {
            loadCameras('gphoto2');
        });
    }
    
    if (detectCamera) {
        detectCamera.addEventListener('click', function() {
            detectCurrentCamera();
        });
    }
    
    if (testCamera) {
        testCamera.addEventListener('click', function() {
            testCameraCapture();
        });
    }
    
    if (saveProfile) {
        saveProfile.addEventListener('click', function() {
            saveCurrentProfile();
        });
    }
    
    // Aktuelle Konfiguration laden
    loadConfig();
    
    // Kameras laden
    loadCameras();
    
    // Formular absenden
    if (settingsForm) {
        settingsForm.addEventListener('submit', saveConfig);
    }
    
    // Kamera-Optionen basierend auf Kameratyp anzeigen/ausblenden
    function updateCameraOptions() {
        const type = cameraType.value;
        
        // Webcam-Optionen
        webcamOptions.forEach(element => {
            element.style.display = type === 'webcam' ? 'flex' : 'none';
        });
        
        // gphoto2-Optionen
        gphoto2Options.forEach(element => {
            element.style.display = type === 'gphoto2' ? 'flex' : 'none';
        });
        
        // Kameras neu laden
        loadCameras(type);
    }
    
    // Verfügbare Kameras laden
    function loadCameras(type = null) {
        // Wenn kein Typ angegeben wurde, den aktuellen Typ verwenden
        if (!type && cameraType) {
            type = cameraType.value;
        }
        
        // Lade alle Kameras vom Server
        fetch('/api/devices')
            .then(response => response.json())
            .then(devices => {
                // Webcams laden
                if (type === 'webcam' || type === null) {
                    const webcams = devices.cameras.webcams;
                    
                    // Webcam-Dropdown füllen
                    if (webcamDevice) {
                        webcamDevice.innerHTML = '';
                        
                        if (webcams.length === 0) {
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'Keine Webcams gefunden';
                            webcamDevice.appendChild(option);
                        } else {
                            webcams.forEach(webcam => {
                                const option = document.createElement('option');
                                option.value = webcam.device;
                                option.textContent = webcam.name;
                                webcamDevice.appendChild(option);
                            });
                        }
                    }
                }
                
                // gphoto2-Kameras laden
                if (type === 'gphoto2' || type === null) {
                    const gphoto2Cameras = devices.cameras.gphoto2;
                    
                    // gphoto2-Dropdown füllen
                    if (gphoto2Device) {
                        gphoto2Device.innerHTML = '';
                        
                        if (gphoto2Cameras.length === 0) {
                            const option = document.createElement('option');
                            option.value = '';
                            option.textContent = 'Keine DSLR-Kameras gefunden';
                            gphoto2Device.appendChild(option);
                        } else {
                            gphoto2Cameras.forEach(camera => {
                                const option = document.createElement('option');
                                option.value = camera.device;
                                option.textContent = camera.name;
                                option.dataset.model = camera.model;
                                gphoto2Device.appendChild(option);
                            });
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Fehler beim Laden der Kameras:', error);
                showStatus('Fehler beim Laden der Kameras. Bitte versuchen Sie es später erneut.', 'error');
            });
    }
    
    // Kamera-Profile laden
    function loadCameraProfiles(config) {
        const profiles = config?.camera?.gphoto2_profiles || {};
        
        // Profil-Dropdown füllen
        if (cameraProfile) {
            cameraProfile.innerHTML = '';
            
            // Leere Option hinzufügen
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = 'Bitte wählen...';
            cameraProfile.appendChild(emptyOption);
            
            // Profile hinzufügen
            Object.keys(profiles).forEach(model => {
                const profile = profiles[model];
                const option = document.createElement('option');
                option.value = model;
                option.textContent = profile.name || model;
                cameraProfile.appendChild(option);
            });
            
            // "Neu" Option hinzufügen
            const newOption = document.createElement('option');
            newOption.value = 'new';
            newOption.textContent = '+ Neues Profil erstellen';
            cameraProfile.appendChild(newOption);
            
            // Event-Listener für Profiländerungen
            cameraProfile.addEventListener('change', function() {
                updateProfileDetails(this.value, profiles);
            });
        }
    }
    
    // Profildetails anzeigen
    function updateProfileDetails(profileKey, profiles) {
        const profileDetailsContainer = document.getElementById('currentProfileDetails');
        
        if (!profileDetailsContainer) return;
        
        // Container leeren
        profileDetailsContainer.innerHTML = '';
        
        // "Neu" wurde ausgewählt
        if (profileKey === 'new') {
            // Formular für neues Profil erstellen
            const nameInput = document.createElement('div');
            nameInput.className = 'profile-setting';
            nameInput.innerHTML = `
                <label for="profileName">Profilname:</label>
                <input type="text" id="profileName" placeholder="z.B. Canon EOS 1200D">
            `;
            profileDetailsContainer.appendChild(nameInput);
            
            // Hinweis
            const hint = document.createElement('p');
            hint.className = 'profile-hint';
            hint.textContent = 'Verbinden Sie Ihre Kamera und klicken Sie auf "Kamera erkennen", um die verfügbaren Einstellungen zu laden.';
            profileDetailsContainer.appendChild(hint);
            
            return;
        }
        
        // Kein Profil ausgewählt
        if (!profileKey || !profiles[profileKey]) {
            const hint = document.createElement('p');
            hint.textContent = 'Bitte wählen Sie ein Profil aus oder erstellen Sie ein neues.';
            profileDetailsContainer.appendChild(hint);
            return;
        }
        
        // Profil anzeigen
        const profile = profiles[profileKey];
        
        // Profilname
        const nameElement = document.createElement('div');
        nameElement.className = 'profile-name';
        nameElement.innerHTML = `<strong>Kamera:</strong> ${profile.name || profileKey}`;
        profileDetailsContainer.appendChild(nameElement);
        
        // Einstellungen
        const settings = profile.settings || {};
        
        if (Object.keys(settings).length === 0) {
            const noSettings = document.createElement('p');
            noSettings.textContent = 'Keine Einstellungen für dieses Profil definiert.';
            profileDetailsContainer.appendChild(noSettings);
        } else {
            const settingsTable = document.createElement('table');
            settingsTable.className = 'profile-settings-table';
            
            // Tabellenkopf
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Einstellung</th>
                    <th>Wert</th>
                </tr>
            `;
            settingsTable.appendChild(thead);
            
            // Tabellenkörper
            const tbody = document.createElement('tbody');
            
            Object.entries(settings).forEach(([key, value]) => {
                const row = document.createElement('tr');
                
                // Einstellungsname
                const nameCell = document.createElement('td');
                nameCell.textContent = key.split('/').pop(); // Nur den letzten Teil des Pfads anzeigen
                row.appendChild(nameCell);
                
                // Einstellungswert
                const valueCell = document.createElement('td');
                
                // Editierbarer Wert
                const valueInput = document.createElement('input');
                valueInput.type = 'text';
                valueInput.value = value;
                valueInput.dataset.setting = key;
                valueInput.className = 'profile-setting-value';
                
                valueCell.appendChild(valueInput);
                row.appendChild(valueCell);
                
                tbody.appendChild(row);
            });
            
            settingsTable.appendChild(tbody);
            profileDetailsContainer.appendChild(settingsTable);
        }
    }
    
    // Aktuelle Kamera erkennen
    function detectCurrentCamera() {
        const devicePath = cameraType.value === 'webcam' ? 
                          webcamDevice.value : 
                          gphoto2Device.value;
        
        if (!devicePath) {
            showStatus('Bitte wählen Sie zuerst ein Kameragerät aus.', 'error');
            return;
        }
        
        showStatus('Kamera wird erkannt...', 'info');
        
        fetch(`/api/camera_capabilities?device=${devicePath}&type=${cameraType.value}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'error') {
                    throw new Error(data.message);
                }
                
                // Kamerafähigkeiten verarbeiten
                const capabilities = data.capabilities;
                
                if (cameraType.value === 'gphoto2') {
                    // Neues Profil erstellen oder aktualisieren
                    const model = capabilities.model || 'Unbekannte Kamera';
                    const profileNameInput = document.getElementById('profileName');
                    
                    if (profileNameInput) {
                        profileNameInput.value = model;
                    }
                    
                    // Einstellungen anzeigen
                    const profileDetailsContainer = document.getElementById('currentProfileDetails');
                    
                    if (!profileDetailsContainer) return;
                    
                    // Container leeren
                    profileDetailsContainer.innerHTML = '';
                    
                    // Profilname
                    const nameElement = document.createElement('div');
                    nameElement.className = 'profile-name';
                    nameElement.innerHTML = `<strong>Erkannte Kamera:</strong> ${model}`;
                    profileDetailsContainer.appendChild(nameElement);
                    
                    // Einstellungstabelle
                    const settingsTable = document.createElement('table');
                    settingsTable.className = 'profile-settings-table';
                    
                    // Tabellenkopf
                    const thead = document.createElement('thead');
                    thead.innerHTML = `
                        <tr>
                            <th>Einstellung</th>
                            <th>Wert</th>
                        </tr>
                    `;
                    settingsTable.appendChild(thead);
                    
                    // Tabellenkörper
                    const tbody = document.createElement('tbody');
                    
                    // Wichtige Einstellungen anzeigen
                    const settings = capabilities.settings || {};
                    
                    Object.entries(settings).forEach(([key, values]) => {
                        const row = document.createElement('tr');
                        
                        // Einstellungsname
                        const nameCell = document.createElement('td');
                        nameCell.textContent = key.split('/').pop(); // Nur den letzten Teil des Pfads anzeigen
                        row.appendChild(nameCell);
                        
                        // Einstellungswert
                        const valueCell = document.createElement('td');
                        
                        const currentValue = values.Current || values.Value || '';
                        const choices = values.Choices;
                        
                        // Dropdown oder Textfeld basierend auf verfügbaren Optionen
                        if (choices && choices.includes(',')) {
                            const select = document.createElement('select');
                            select.dataset.setting = key;
                            select.className = 'profile-setting-value';
                            
                            choices.split(', ').forEach(choice => {
                                const option = document.createElement('option');
                                option.value = choice;
                                option.textContent = choice;
                                option.selected = choice === currentValue;
                                select.appendChild(option);
                            });
                            
                            valueCell.appendChild(select);
                        } else {
                            const valueInput = document.createElement('input');
                            valueInput.type = 'text';
                            valueInput.value = currentValue;
                            valueInput.dataset.setting = key;
                            valueInput.className = 'profile-setting-value';
                            
                            valueCell.appendChild(valueInput);
                        }
                        
                        row.appendChild(valueCell);
                        tbody.appendChild(row);
                    });
                    
                    settingsTable.appendChild(tbody);
                    profileDetailsContainer.appendChild(settingsTable);
                    
                    showStatus('Kamera erfolgreich erkannt. Bitte speichern Sie das Profil.', 'success');
                } else {
                    // Webcam-Eigenschaften anzeigen
                    showStatus(`Webcam erkannt: ${capabilities.max_width}x${capabilities.max_height}`, 'success');
                    
                    // Auflösung auf maximal verfügbare setzen
                    if (capabilities.max_width && capabilities.max_height) {
                        document.getElementById('resolutionWidth').value = capabilities.max_width;
                        document.getElementById('resolutionHeight').value = capabilities.max_height;
                    }
                }
            })
            .catch(error => {
                console.error('Fehler bei der Kameraerkennung:', error);
                showStatus(`Fehler bei der Kameraerkennung: ${error.message}`, 'error');
            });
    }
    
    // Aktuelles Profil speichern
    function saveCurrentProfile() {
        // Aktuelle Konfiguration abrufen
        fetch('/get_config')
            .then(response => response.json())
            .then(config => {
                // Neue Konfiguration erstellen
                const newConfig = { camera: { gphoto2_profiles: {} } };
                
                // Bestehende Profile übernehmen
                if (config.camera && config.camera.gphoto2_profiles) {
                    newConfig.camera.gphoto2_profiles = { ...config.camera.gphoto2_profiles };
                }
                
                // Neues oder bestehendes Profil?
                let profileKey = cameraProfile.value;
                let profileName = '';
                
                if (profileKey === 'new') {
                    const profileNameInput = document.getElementById('profileName');
                    if (!profileNameInput || !profileNameInput.value) {
                        showStatus('Bitte geben Sie einen Namen für das neue Profil ein.', 'error');
                        return;
                    }
                    
                    profileName = profileNameInput.value;
                    profileKey = profileName; // Verwende den Namen als Schlüssel
                } else {
                    // Bestehendes Profil aktualisieren
                    profileName = config.camera.gphoto2_profiles[profileKey]?.name || profileKey;
                }
                
                // Profileinstellungen sammeln
                const settings = {};
                const settingInputs = document.querySelectorAll('.profile-setting-value');
                
                settingInputs.forEach(input => {
                    const key = input.dataset.setting;
                    const value = input.value;
                    
                    if (key && value) {
                        settings[key] = value;
                    }
                });
                
                // Profil speichern
                newConfig.camera.gphoto2_profiles[profileKey] = {
                    name: profileName,
                    settings: settings
                };
                
                // Konfiguration speichern
                return fetch('/save_config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(newConfig)
                });
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showStatus('Kameraprofil erfolgreich gespeichert!', 'success');
                    
                    // Konfiguration neu laden
                    loadConfig();
                } else {
                    throw new Error(data.message || 'Unbekannter Fehler');
                }
            })
            .catch(error => {
                console.error('Fehler beim Speichern des Kameraprofils:', error);
                showStatus(`Fehler beim Speichern des Kameraprofils: ${error.message}`, 'error');
            });
    }
    
    // Testfoto mit aktuellen Einstellungen aufnehmen
    function testCameraCapture() {
        const cameraTypeValue = cameraType.value;
        let devicePath = '';
        
        if (cameraTypeValue === 'webcam') {
            devicePath = webcamDevice.value;
        } else if (cameraTypeValue === 'gphoto2') {
            devicePath = gphoto2Device.value;
        }
        
        if (!devicePath) {
            showStatus('Bitte wählen Sie zuerst ein Kameragerät aus.', 'error');
            return;
        }
        
        const width = document.getElementById('resolutionWidth').value;
        const height = document.getElementById('resolutionHeight').value;
        
        // Profil für gphoto2
        let profile = '';
        if (cameraTypeValue === 'gphoto2') {
            profile = cameraProfile.value;
        }
        
        showStatus('Testfoto wird aufgenommen...', 'info');
        
        fetch('/api/test/camera', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: cameraTypeValue,
                device: devicePath,
                resolution: `${width}x${height}`,
                profile: profile
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const testPhotoResult = document.getElementById('testPhotoResult');
                
                if (testPhotoResult) {
                    testPhotoResult.innerHTML = `
                        <div class="test-photo-success">
                            <p>Testfoto erfolgreich aufgenommen!</p>
                            <img src="${data.image_url}" alt="Testfoto" style="max-width: 100%; max-height: 300px;">
                        </div>
                    `;
                }
                
                showStatus('Testfoto erfolgreich aufgenommen!', 'success');
            } else {
                throw new Error(data.message || 'Unbekannter Fehler');
            }
        })
        .catch(error => {
            console.error('Fehler beim Aufnehmen des Testfotos:', error);
            showStatus(`Fehler beim Aufnehmen des Testfotos: ${error.message}`, 'error');
            
            const testPhotoResult = document.getElementById('testPhotoResult');
            
            if (testPhotoResult) {
                testPhotoResult.innerHTML = `
                    <div class="test-photo-error">
                        <p>Fehler beim Aufnehmen des Testfotos: ${error.message}</p>
                        <p>Überprüfen Sie die Kameraverbindung und -einstellungen.</p>
                    </div>
                `;
            }
        });
    }
    
    // Konfiguration laden
    function loadConfig() {
        fetch('/get_config')
            .then(response => response.json())
            .then(config => {
                // Formularwerte setzen
                setFormValues(config);
                
                // Kamera-Profile laden
                loadCameraProfiles(config);
                
                // Kamera-Optionen aktualisieren
                updateCameraOptions();
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
        setInputValue('resolutionWidth', config?.camera?.resolution?.width);
        setInputValue('resolutionHeight', config?.camera?.resolution?.height);
        
        // Arduino-Einstellungen
        setInputValue('arduinoPort', config?.arduino?.port);
        setInputValue('arduinoBaudrate', config?.arduino?.baudrate);
        
        // Drehteller-Einstellungen
        setInputValue('defaultDegrees', config?.rotation?.default_degrees);
        setInputValue('defaultInterval', config?.rotation?.default_interval);
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
        
        // FormData in JSON umwandeln
        try {
            // FormData in verschachtelte Objekte umwandeln
            formData.forEach((value, key) => {
                // Checkbox-Werte in boolesche Werte umwandeln
                if (element.type === 'checkbox') {
                    value = element.checked;
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
            
            // Konfiguration speichern
            fetch('/save_config', {
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
});
