/**
 * index.js
 * JavaScript für die Startseite und Drehteller-Steuerung
 * Endgültige korrigierte Version mit korrekter Sequenz: Erst Drehwinkel, dann Foto
 */

// Globale Variablen
let currentProjectId = null;
let capturedPhotos = [];
let isRotating = false;
let currentStep = 0;
let totalSteps = 0;

// DOM-Elemente
const projectSelect = document.getElementById('projectSelect');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const rotateBtn = document.getElementById('rotateBtn');
const homeBtn = document.getElementById('homeBtn');
const imagePreview = document.getElementById('imagePreview');
const angleInput = document.getElementById('angleInput');
const intervalInput = document.getElementById('intervalInput');
const rotationStatus = document.getElementById('rotationStatus');
const currentPositionDisplay = document.getElementById('currentPosition');
const projectModal = document.getElementById('projectModal');
const projectForm = document.getElementById('projectForm');
const cancelProjectBtn = document.getElementById('cancelProject');

// Status-Variablen
let tellerPosition = 0; // Speichert die aktuelle Position des Tellers
let positionLost = false; // Wird auf true gesetzt, wenn die Position unsicher ist

// Debug-Funktion - wichtig zur Fehlerbehebung
function debug(message) {
    console.log(`[DEBUG] ${message}`);
}

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    debug("DOM geladen, initialisiere Anwendung...");
    
    // Initialisiere die Projekt-ID aus den Datenelementen
    currentProjectId = document.body.getAttribute('data-project-id') || '';
    debug(`Aktuelle Projekt-ID: ${currentProjectId}`);

    // Letzte bekannte Tellerposition aus dem localStorage laden
    loadTurntablePosition();
    
    // Wenn ein Projekt ausgewählt ist, lade die Projektposition
    if (currentProjectId) {
        loadProjectPosition();
    }

    // Projekte laden, wenn kein Projekt ausgewählt ist
    if (!currentProjectId && projectSelect) {
        debug("Kein Projekt ausgewählt, lade Projektliste...");
        loadProjects();
    }
    
    // Event-Listener für die Buttons einrichten
    if (startBtn) {
        startBtn.addEventListener('click', startRotation);
        debug("Event-Listener für Start-Button registriert");
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', () => stopRotation());
        debug("Event-Listener für Stop-Button registriert");
    }
    
    if (rotateBtn) {
        rotateBtn.addEventListener('click', startSingleRotation);
        debug("Event-Listener für Rotate-Button registriert");
    }
    
    if (homeBtn) {
        homeBtn.addEventListener('click', moveToHomePosition);
        debug("Event-Listener für Home-Button registriert");
    }
    
    if (projectSelect) {
        projectSelect.addEventListener('change', function() {
            const selectedProjectId = this.value;
            if (selectedProjectId) {
                // Neues Projekt ausgewählt -> laden
                window.location.href = `/?project_id=${selectedProjectId}`;
            }
        });
        debug("Event-Listener für Projekt-Auswahl registriert");
    }
    
    // Event-Listener für das Projekt-Modal
    if (projectModal && projectForm && cancelProjectBtn) {
        projectForm.addEventListener('submit', createProject);
        cancelProjectBtn.addEventListener('click', function() {
            projectModal.style.display = 'none';
        });
        debug("Event-Listener für Projekt-Modal registriert");
    }
    
    debug("Initialisierung abgeschlossen");
});

/**
 * Lädt die Position des Drehtellers aus dem localStorage
 */
function loadTurntablePosition() {
    const storedPosition = localStorage.getItem('turntablePosition');
    if (storedPosition) {
        tellerPosition = parseInt(storedPosition);
        debug(`Tellerposition aus localStorage geladen: ${tellerPosition}°`);
        updatePositionDisplay(tellerPosition, false);
        
        // Wenn ein Projekt ausgewählt ist, aktualisiere die Position im Projekt
        if (currentProjectId) {
            syncProjectPosition(tellerPosition);
        }
    } else {
        debug("Keine gespeicherte Tellerposition gefunden");
        tellerPosition = 0;
        updatePositionDisplay(tellerPosition, false);
    }
}

/**
 * Synchronisiere die Tellerposition mit dem Projekt
 * @param {number} position - Die aktuelle Position des Tellers
 */
function syncProjectPosition(position) {
    if (!currentProjectId) {
        debug("Kein Projekt ausgewählt, kann Position nicht synchronisieren");
        return;
    }
    
    debug(`Synchronisiere Tellerposition ${position}° mit Projekt ${currentProjectId}`);
    
    fetch(`/api/project/${currentProjectId}/update_position`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ position: position })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            debug(`Position im Projekt aktualisiert: ${position}°`);
        } else {
            debug(`Fehler beim Aktualisieren der Position: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        debug(`Fehler bei der Positionssynchronisierung: ${error}`);
    });
}

/**
 * Lädt die Position des Drehtellers aus dem aktuellen Projekt
 */
function loadProjectPosition() {
    if (!currentProjectId) {
        debug("Kein Projekt ausgewählt, kann Projektposition nicht laden");
        return;
    }
    
    debug(`Lade Projektposition für Projekt ${currentProjectId}`);
    
    fetch(`/api/project/${currentProjectId}`)
        .then(response => response.json())
        .then(project => {
            if (project && 'current_position' in project) {
                // Wenn die Tellerposition aus dem localStorage abweicht, 
                // verwenden wir die physische Position (localStorage)
                const storedPosition = localStorage.getItem('turntablePosition');
                if (storedPosition && parseInt(storedPosition) !== project.current_position) {
                    debug(`Unterschiedliche Positionen gefunden: Projekt=${project.current_position}°, Teller=${storedPosition}°`);
                    // Wir vertrauen dem localStorage für die tatsächliche Position
                    tellerPosition = parseInt(storedPosition);
                    // Synchronisieren diese mit dem Projekt
                    syncProjectPosition(tellerPosition);
                } else {
                    // Kein Unterschied oder kein localStorage, verwende Projektposition
                    tellerPosition = project.current_position;
                    // Aktualisiere den localStorage
                    localStorage.setItem('turntablePosition', tellerPosition);
                }
                
                debug(`Tellerposition aus Projekt geladen: ${tellerPosition}°`);
                
                // Anzeige aktualisieren
                updatePositionDisplay(tellerPosition, false);
                
                // Check if session needs to be resumed
                if (project.active_session && project.last_captured_angle !== null) {
                    showStatus(`Letzte Sitzung wurde bei ${project.last_captured_angle}° unterbrochen. Möchten Sie fortsetzen?`, 'warning');
                    
                    // Biete an, die Sitzung fortzusetzen
                    const resumeButton = document.createElement('button');
                    resumeButton.innerText = "Sitzung fortsetzen";
                    resumeButton.classList.add('btn', 'btn-primary', 'ml-2');
                    resumeButton.addEventListener('click', () => {
                        resumeSession(project.last_captured_angle);
                    });
                    
                    const statusContainer = document.getElementById('statusContainer');
                    if (statusContainer) {
                        statusContainer.appendChild(resumeButton);
                    }
                }
            }
        })
        .catch(error => {
            debug(`Fehler beim Laden der Projektposition: ${error}`);
        });
}

// Projekte laden
function loadProjects() {
    debug("Lade Projekte vom Server...");
    fetch('/api/projects')
        .then(response => {
            debug(`Server-Antwort Status: ${response.status}`);
            return response.json();
        })
        .then(projects => {
            debug(`${projects.length} Projekte geladen`);
            if (!projectSelect) return;

            projectSelect.innerHTML = '<option value="">Bitte wählen...</option>';
            projectSelect.innerHTML += '<option value="new">+ Neues Projekt erstellen</option>';

            if (projects.length === 0) {
                return;
            }

            // Projekte zum Dropdown hinzufügen
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.name;
                projectSelect.appendChild(option);
            });

            // Wenn eine Projekt-ID vorhanden ist, diese auswählen
            if (currentProjectId && projectSelect.querySelector(`option[value="${currentProjectId}"]`)) {
                projectSelect.value = currentProjectId;
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Projekte:', error);
            if (projectSelect) {
                projectSelect.innerHTML = '<option value="">Fehler beim Laden der Projekte</option>';
            }
        });
}

// Projekt-Modal anzeigen
function showProjectModal() {
    debug("Zeige Projekt-Modal an");
    if (projectModal) {
        projectModal.style.display = 'flex';
    }
}

// Projekt-Modal ausblenden
function hideProjectModal() {
    debug("Blende Projekt-Modal aus");
    if (projectModal) {
        projectModal.style.display = 'none';

        // Select zurücksetzen
        if (projectSelect) {
            projectSelect.value = currentProjectId || '';
        }
    }
}

// Neues Projekt erstellen
function createProject(e) {
    e.preventDefault();
    debug("Erstelle neues Projekt...");

    const formData = new FormData(projectForm);

    fetch('/projects/create', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
            debug(`Umleitung zu ${response.url}`);
            window.location.href = response.url;
        } else {
            return response.json().then(data => {
                throw new Error(data.error || 'Unbekannter Fehler');
            });
        }
    })
    .catch(error => {
        console.error('Fehler beim Erstellen des Projekts:', error);
        alert('Fehler beim Erstellen des Projekts: ' + error.message);
    });
}

// Einzelne Rotation und Fotoaufnahme
function startSingleRotation() {
    if (isRotating) {
        debug("Rotation bereits aktiv, ignoriere Anfrage");
        return;
    }
    
    // Überprüfen, ob ein Projekt ausgewählt wurde
    if (!currentProjectId) {
        debug("Kein Projekt ausgewählt");
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }

    const angle = parseInt(angleInput.value) || 15;
    debug(`Starte einzelne Rotation mit ${angle}°`);
    
    isRotating = true;
    if (rotateBtn) rotateBtn.disabled = true;

    // Statusmeldung anzeigen
    showStatus(`Drehe Teller um ${angle}°...`, 'info');
    
    // Formular-Daten vorbereiten
    const formData = new FormData();
    formData.append('degrees', angle);
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'photo_and_rotate'); // Beide Aktionen ausführen

    // Foto aufnehmen und dann rotieren
    debug("Sende Rotationsanfrage an den Server");
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        debug(`Server-Antwort Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Foto zur Liste hinzufügen
            capturedPhotos.push({
                path: data.photo,
                angle: data.angle
            });

            // Bild anzeigen
            displayImage(data.photo, angle);

            // Positionsanzeige aktualisieren
            updatePositionDisplay((tellerPosition + angle) % 360);

            // Statusmeldung aktualisieren
            showStatus(`Foto aufgenommen bei ${data.angle}°`, 'success');

            debug(`Erfolgreich Foto aufgenommen und gedreht: ${data.photo}`);
        } else {
            console.error('Fehler:', data.error);
            alert(`Fehler bei der Rotation: ${data.error}`);

            // Position als unsicher markieren
            updatePositionDisplay(tellerPosition, true);

            // Statusmeldung aktualisieren
            showStatus(`Fehler: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert(`Netzwerkfehler beim Drehen des Tellers: ${error.message}`);

        // Position als unsicher markieren
        updatePositionDisplay(tellerPosition, true);

        // Statusmeldung aktualisieren
        showStatus(`Netzwerkfehler: ${error.message}`, 'error');
    })
    .finally(() => {
        isRotating = false;
        if (rotateBtn) rotateBtn.disabled = false;
        debug("Einzelrotation abgeschlossen");
    });
}

// Zeigt ein Bild in der Vorschau an
function displayImage(imagePath, angle) {
    if (!imagePreview) {
        debug("WARNUNG: Image-Preview-Element nicht gefunden!");
        return;
    }

    debug(`Zeige Bild an: ${imagePath}`);

    // Bisherige Vorschau löschen
    imagePreview.innerHTML = '';

    // Bild-Element erstellen
    const img = document.createElement('img');
    
    // Stellen sicher, dass der Pfad korrekt ist
    if (!imagePath.startsWith('/')) {
        imagePath = '/' + imagePath;
    }
    
    img.src = imagePath;
    img.alt = `Foto bei ${angle}°`;
    img.className = 'captured-image';
    
    // Fehlerbehandlung für Bilder
    img.onerror = function() {
        console.error(`Fehler beim Laden des Bildes: ${imagePath}`);
        this.src = '/static/img/error.svg'; // Fallback-Bild (SVG für bessere Skalierbarkeit)
        this.alt = 'Fehler beim Laden des Bildes';
    };

    // Winkel-Anzeige erstellen
    const angleLabel = document.createElement('div');
    angleLabel.className = 'angle-label';
    angleLabel.textContent = `${angle}°`;

    // Container erstellen und Elemente hinzufügen
    const container = document.createElement('div');
    container.className = 'image-container';
    container.appendChild(img);
    container.appendChild(angleLabel);

    // Container zur Vorschau hinzufügen
    imagePreview.appendChild(container);
    debug("Bild erfolgreich angezeigt");
}

// Automatische Rotation und Fotoaufnahme - Verbesserte Version
// WICHTIG: Wir nehmen jetzt das erste Foto und beginnen danach mit der Sequenz
function startRotation() {
    debug("startRotation() aufgerufen");
    
    if (isRotating) {
        debug("Rotation bereits aktiv, ignoriere Start-Anfrage");
        return;
    }

    // Überprüfen, ob ein Projekt ausgewählt wurde
    if (!currentProjectId) {
        debug("Kein Projekt ausgewählt");
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }

    const angle = parseInt(angleInput.value) || 15;
    const interval = parseInt(intervalInput.value) || 5;
    totalSteps = Math.floor(360 / angle);
    currentStep = 0;
    
    debug(`Starte 360° Rotation mit ${totalSteps} Schritten, Winkel=${angle}°, Intervall=${interval}s`);

    // UI aktualisieren
    if (startBtn) {
        startBtn.disabled = true;
        debug("Start-Button deaktiviert");
    }
    
    if (stopBtn) {
        stopBtn.disabled = false;
        debug("Stop-Button aktiviert");
    }
    
    if (rotateBtn) {
        rotateBtn.disabled = true;
        debug("Rotate-Button deaktiviert");
    }
    
    if (homeBtn) {
        homeBtn.disabled = true;
        debug("Home-Button deaktiviert");
    }
    
    isRotating = true;

    // Statusmeldung anzeigen
    showStatus(`Rotation gestartet: Nehme erstes Foto auf`, 'info');

    // Ersten Schritt starten - nehme erstes Foto auf der Position 0
    debug("Nehme erstes Foto auf");
    takePhotoForSequence();
}

function takePhotoForSequence() {
    // Abbruch, wenn Rotation gestoppt
    
    if (!isRotating) {
        debug("Rotation wurde gestoppt, breche Sequenz ab");
        return;
    }
    
    // Der gewünschte Drehwinkel pro Schritt
    const angle = parseInt(angleInput.value) || 15;

    // Aktuelle Winkelposition berechnen (0, 15, 30, ...)
    // Winkel der ersten Position ist 0 Grad
    const currentAngle = currentStep * angle;
    
    // Statusmeldung aktualisieren
    showStatus(`Nehme Foto ${currentStep+1}/${totalSteps} bei ${currentAngle}° auf`, 'info');

    // Nur Foto aufnehmen - an der aktuellen Position
    debug(`Nehme Foto bei Position ${currentAngle}° auf`);
    const formData = new FormData();
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'photo_only');
    formData.append('degrees', currentAngle); // WICHTIG: Backend erwartet 'degrees', nicht 'angle'

    // Foto aufnehmen und dann rotieren
    debug("Sende Anfrage an den Server");
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        debug(`Server-Antwort Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Foto zur Liste hinzufügen
            capturedPhotos.push({
                path: data.photo,
                angle: data.angle
            });

            // Bild anzeigen
            displayImage(data.photo, angle);

            // Positionsanzeige aktualisieren
            updatePositionDisplay(currentAngle, false);
            
            // Nächstes Foto aufnehmen
            currentStep++;
            
            if (currentStep < totalSteps) {
                // Als nächstes drehen
                setTimeout(rotateForSequence, 500);
            } else {
                // Sequenz abschließen
                completedSequence();
            }
        } else {
            // Bei Fehler Position als unsicher markieren
            updatePositionDisplay(tellerPosition, true);
            showStatus(`Fehler beim Aufnehmen des Fotos: ${data.error}`, 'error');
            stopRotation(true);
        }
    })
    .catch(error => {
        debug(`Fehler beim Aufnehmen des Fotos: ${error}`);
        updatePositionDisplay(tellerPosition, true);
        showStatus(`Netzwerkfehler beim Aufnehmen des Fotos: ${error.message}`, 'error');
        stopRotation(true);
    });
}

function rotateForSequence() {
    // Abbruch, wenn Rotation gestoppt
    if (!isRotating) {
        debug("Rotation wurde gestoppt, breche Sequenz ab");
        return;
    }

    // Der gewünschte Drehwinkel pro Schritt
    const angle = parseInt(angleInput.value) || 15;

    if (rotationStatus) {
        showStatus(`Drehe um ${angle}° zur nächsten Position...`, 'info');
    }

    debug(`Drehe um ${angle}° weiter`);

    // Formular-Daten vorbereiten
    const formData = new FormData();
    formData.append('degrees', angle);          // Drehwinkel
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');    // Nur drehen ohne Foto

    // API-Anfrage zum Drehen des Tellers
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            debug("Rotation erfolgreich");
            
            // Position aktualisieren
            const newPosition = (tellerPosition + angle) % 360;
            updatePositionDisplay(newPosition, false);
            
            // Nach kurzer Pause das nächste Foto aufnehmen
            setTimeout(takePhotoForSequence, 500);
        } else {
            debug(`Fehler bei der Rotation: ${data.error}`);
            // Bei Fehler Position als unsicher markieren
            updatePositionDisplay(tellerPosition, true);
            showStatus(`Fehler bei der Rotation: ${data.error}`, 'error');
            stopRotation(true);
        }
    })
    .catch(error => {
        debug(`Netzwerkfehler bei der Rotation: ${error}`);
        // Bei Fehler Position als unsicher markieren
        updatePositionDisplay(tellerPosition, true);
        showStatus(`Netzwerkfehler bei der Rotation: ${error.message}`, 'error');
        stopRotation(true);
    });
}

function completedSequence() {
    debug("360°-Aufnahmesession abgeschlossen");
    showStatus("360°-Aufnahmesession erfolgreich abgeschlossen!", 'success');
    
    // Position aktualisieren - sollte bei 0 oder 360 sein
    updatePositionDisplay(0, false);
    
    // UI zurücksetzen
    isRotating = false;
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (rotateBtn) rotateBtn.disabled = false;
    if (homeBtn) homeBtn.disabled = false;

    // 360°-Viewer erstellen anbieten
    offerViewerCreation();
}

/**
 * Stoppt die laufende Rotation und Fotoaufnahme
 * @param {boolean} isError - Ob der Stopp aufgrund eines Fehlers erfolgt
 */
function stopRotation(isError = false) {
    if (!isRotating) {
        return;
    }

    debug(`Stoppe Rotation${isError ? ' (nach Fehler)' : ''}`);
    
    // Setze zuerst den Client-Status - SOFORT!
    isRotating = false;
    
    if (!isError) {
        showStatus("Rotation gestoppt", 'warning');
    }
    
    // UI zurücksetzen
    if (startBtn) {
        startBtn.disabled = false;
        debug("Start-Button aktiviert");
    }
    
    if (stopBtn) {
        stopBtn.disabled = true;
        debug("Stop-Button deaktiviert");
    }
    
    if (rotateBtn) {
        rotateBtn.disabled = false;
        debug("Rotate-Button aktiviert");
    }
    
    if (homeBtn) {
        homeBtn.disabled = false;
        debug("Home-Button aktiviert");
    }
    
    // Unsichere Position markieren, wenn wir in der Mitte abbrechen
    if (currentStep > 0 && currentStep < totalSteps) {
        updatePositionDisplay(tellerPosition, true);
    }
    
    // Server-seitige Anfrage zum Stoppen der Rotation
    fetch('/stop_rotation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project_id: currentProjectId })
    })
    .then(response => response.json())
    .then(data => {
        debug("Server-Antwort für Stop:", data);
    })
    .catch(error => {
        debug(`Fehler beim Stoppen der Rotation: ${error}`);
    });
}

function generateViewer() {
    debug("generateViewer() aufgerufen");
    debug(`Erfasste Fotos: ${capturedPhotos.length}`);
    
    if (capturedPhotos.length < 4) {
        alert('Es werden mindestens 4 Fotos für einen 360°-Viewer benötigt.');
        return;
    }

    // Prüfe die aktuelle Projekt-ID
    debug(`Aktuelle Projekt-ID: ${currentProjectId}`);

    if (!currentProjectId) {
        alert("Fehler: Keine Projekt-ID gefunden!");
        console.error("Fehler: currentProjectId ist null oder undefined!");
        return;
    }

    // Anfrage-Daten zusammenstellen
    const requestData = {
        project_id: currentProjectId,
        photos: capturedPhotos.map(photo => photo.path)
    };

    debug(`Sende Anfrage mit Daten: ${JSON.stringify(requestData)}`);

    fetch('/generate_360', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        debug(`Server-Antwort Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            debug(`Viewer erstellt: ${data.viewer_url}`);
            alert(`360°-Viewer erfolgreich erstellt! Sie können ihn unter folgendem Link aufrufen: ${data.viewer_url}`);
            window.open(data.viewer_url, '_blank');
        } else {
            console.error('Fehler beim Erstellen des Viewers:', data.error);
            alert(`Fehler beim Erstellen des 360°-Viewers: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler beim Erstellen des Viewers:', error);
        alert(`Netzwerkfehler beim Erstellen des 360°-Viewers: ${error.message}`);
    });
}

/**
 * Bietet dem Benutzer an, einen 360°-Viewer zu erstellen
 */
function offerViewerCreation() {
    debug("Biete Erstellung des 360°-Viewers an");
    
    // Prüfe, ob genügend Fotos aufgenommen wurden
    if (capturedPhotos.length < 4) {
        showStatus("Zu wenige Fotos für 360°-Viewer (mindestens 4 erforderlich)", 'warning');
        return;
    }
    
    // Frage Benutzer, ob ein Viewer erstellt werden soll
    if (confirm('360°-Aufnahme abgeschlossen! Möchten Sie einen 360°-Viewer aus den aufgenommenen Fotos erstellen?')) {
        showStatus("Erstelle 360°-Viewer...", 'info');
        generateViewer();
    }
}

/**
 * Dreht den Teller zur Home-Position (0°)
 */
function moveToHomePosition() {
    if (isRotating) {
        debug("Rotation bereits aktiv, kann nicht zur Heimposition fahren");
        showStatus('Bitte stoppen Sie zuerst die aktuelle Rotation.', 'warning');
        return;
    }
    
    // Berechne den kürzesten Weg zur Heimposition
    let degreesToMove = 0;
    
    if (tellerPosition > 180) {
        // Wenn wir über 180° sind, ist es kürzer, im Uhrzeigersinn weiterzudrehen
        degreesToMove = 360 - tellerPosition;
    } else {
        // Andernfalls gegen den Uhrzeigersinn zurück zu 0°
        degreesToMove = tellerPosition;
    }
    
    if (degreesToMove === 0) {
        debug("Teller bereits in Heimposition");
        showStatus('Teller befindet sich bereits in der Heimposition (0°).', 'success');
        return;
    }
    
    // Richtung festlegen (positiv für vorwärts, negativ für rückwärts)
    const direction = tellerPosition > 180 ? 1 : -1;
    
    debug(`Fahre zur Heimposition: ${Math.abs(degreesToMove)}° in Richtung ${direction > 0 ? 'vorwärts' : 'rückwärts'}`);
    showStatus(`Fahre zur Heimposition (0°)...`, 'info');
    
    // API-Anfrage zum Drehen des Tellers
    const formData = new FormData();
    formData.append('degrees', Math.abs(degreesToMove));
    
    // Stelle sicher, dass eine gültige Projekt-ID verwendet wird
    if (!currentProjectId) {
        debug("Keine Projekt-ID vorhanden, kann nicht zur Heimposition fahren");
        showStatus('Bitte wählen Sie zuerst ein Projekt aus.', 'warning');
        return;
    }
    
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');
    formData.append('reset_position', 'true'); // Spezielle Flagge für Heimposition
    
    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/rotate';
    debug(`Sende Home-Position Anfrage an: ${url}`);
    
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        debug(`Server-Antwort Status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        debug("Heimpositionierung erfolgreich");
        showStatus('Teller erfolgreich auf Heimposition (0°) gesetzt.', 'success');
        tellerPosition = 0; // Setze lokale Position auf 0
        localStorage.setItem('turntablePosition', 0); // Speichere in localStorage
        updatePositionDisplay(0, false);
    })
    .catch(error => {
        debug(`Fehler bei Heimpositionierung: ${error}`);
        showStatus(`Fehler beim Zurückfahren zur Heimposition: ${error.message}`, 'error');
    });
}

/**
 * Aktualisiert die Anzeige der Tellerposition
 * @param {number} position - Die aktuelle Position in Grad
 * @param {boolean} uncertain - Ob die Position unsicher ist
 */
function updatePositionDisplay(position, uncertain = false) {
    if (currentPositionDisplay) {
        // Position auf ganze Zahlen runden
        position = Math.round(position);
        
        // Anzeige aktualisieren
        currentPositionDisplay.textContent = `${position}°`;
        
        // Speichern im localStorage
        localStorage.setItem('turntablePosition', position.toString());
        
        // Aktualisieren der globalen Variable
        tellerPosition = position;
        
        // Visuelle Markierung für unsichere Position
        if (uncertain) {
            currentPositionDisplay.classList.add('uncertain');
            if (!positionLost) {
                showStatus('Die genaue Tellerposition ist möglicherweise nicht korrekt. Empfehlung: Zur Heimposition zurückfahren.', 'warning');
                positionLost = true;
            }
        } else {
            currentPositionDisplay.classList.remove('uncertain');
            positionLost = false;
        }
    }
}

/**
 * Zeigt eine Statusmeldung an
 * @param {string} message - Die anzuzeigende Nachricht
 * @param {string} type - Der Typ der Nachricht (success, error, warning, info)
 */
function showStatus(message, type = 'info') {
    if (rotationStatus) {
        // Klassen entfernen
        rotationStatus.classList.remove('success', 'error', 'warning', 'info');
        
        // Klasse für den Typ hinzufügen
        rotationStatus.classList.add(type);
        
        // Inhalt setzen
        rotationStatus.textContent = message;
        
        // Sichtbar machen
        rotationStatus.classList.add('visible');
    }
}
