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
const resetBtn = document.getElementById('resetBtn');
const imagePreview = document.getElementById('imagePreview');
const angleInput = document.getElementById('angleInput');
const intervalInput = document.getElementById('intervalInput');
const statusText = document.getElementById('statusText');
const progressText = document.getElementById('progressText');
const progressBar = document.getElementById('progressBar');
const projectModal = document.getElementById('projectModal');
const projectForm = document.getElementById('projectForm');
const cancelProjectBtn = document.getElementById('cancelProject');
const logBox = document.getElementById('logBox');

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

    // Projekte laden, wenn kein Projekt ausgewählt ist
    if (!currentProjectId && projectSelect) {
        debug("Kein Projekt ausgewählt, lade Projektliste...");
        loadProjects();

        // Event-Listener für Projekt-Auswahl
        projectSelect.addEventListener('change', function() {
            if (this.value) {
                if (this.value === 'new') {
                    debug("Neues Projekt erstellen ausgewählt");
                    showProjectModal();
                } else {
                    debug(`Projekt mit ID ${this.value} ausgewählt, lade Seite neu`);
                    window.location.href = '/?project_id=' + this.value;
                }
            }
        });
    }

    // Event-Listener für Buttons direkt als Funktionen definieren
    if (startBtn) {
        debug("Start-Button gefunden, füge Event-Listener hinzu");
        startBtn.onclick = function() {
            debug("Start-Button geklickt");
            startRotation();
        };
    } else {
        debug("WARNUNG: Start-Button nicht gefunden!");
    }
    
    if (stopBtn) {
        debug("Stop-Button gefunden, füge Event-Listener hinzu");
        stopBtn.onclick = function() {
            debug("Stop-Button geklickt");
            stopRotation();
        };
    } else {
        debug("WARNUNG: Stop-Button nicht gefunden!");
    }
    
    if (rotateBtn) {
        debug("Rotate-Button gefunden, füge Event-Listener hinzu");
        rotateBtn.onclick = function() {
            debug("Rotate-Button geklickt");
            singleRotation();
        };
    } else {
        debug("WARNUNG: Rotate-Button nicht gefunden!");
    }

    // Event-Listener für das Projektformular
    if (projectForm) {
        projectForm.addEventListener('submit', createProject);
    }

    // Event-Listener für den Abbrechen-Button im Modal
    if (cancelProjectBtn) {
        cancelProjectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            hideProjectModal();
        });
    }

    // Wenn kein Projekt ausgewählt ist, Modal anzeigen
    if (!currentProjectId && !projectSelect && projectModal) {
        showProjectModal();
    }
    
    // Stop-Button initial deaktivieren
    if (stopBtn) {
        stopBtn.disabled = true;
    }
    
    debug("Initialisierung abgeschlossen");
});

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
function singleRotation() {
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
    if (statusText) {
        statusText.textContent = "Nehme Foto auf und drehe dann...";
    }

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
        debug(`Server-Antwort: ${JSON.stringify(data)}`);
        if (data.status === 'success') {
            // Foto zur Liste hinzufügen
            capturedPhotos.push({
                path: data.photo,
                angle: data.angle
            });

            // Bild anzeigen
            displayImage(data.photo, angle);

            // Statusmeldung aktualisieren
            if (statusText) {
                statusText.textContent = `Foto aufgenommen bei ${angle}°`;
                setTimeout(() => {
                    statusText.textContent = "";
                }, 3000);
            }

            debug(`Erfolgreich Foto aufgenommen und gedreht: ${data.photo}`);
        } else {
            console.error('Fehler:', data.error);
            alert(`Fehler bei der Rotation: ${data.error}`);

            // Statusmeldung aktualisieren
            if (statusText) {
                statusText.textContent = `Fehler: ${data.error}`;
            }
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert(`Netzwerkfehler beim Drehen des Tellers: ${error.message}`);

        // Statusmeldung aktualisieren
        if (statusText) {
            statusText.textContent = `Netzwerkfehler: ${error.message}`;
        }
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
        this.src = '/static/img/error.jpg'; // Fallback-Bild
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
        
        if (document.getElementById('noProjectNotice')) {
            document.getElementById('noProjectNotice').style.display = 'block';
        }
        return;
    }

    const angle = parseInt(angleInput.value) || 15;
    const interval = parseInt(intervalInput.value) || 5;
    totalSteps = Math.floor(360 / angle);
    currentStep = 0;
    
    debug(`Starte 360° Rotation mit ${totalSteps} Schritten, Winkel=${angle}°, Intervall=${interval}s`);

    // UI aktualisieren
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    if (rotateBtn) rotateBtn.disabled = true;
    if (resetBtn) resetBtn.disabled = true;
    
    isRotating = true;

    // Statusmeldung und Fortschritt aktualisieren
    updateStatus("Rotation gestartet: Nehme erstes Foto auf");
    updateProgress(0, totalSteps);

    // Ersten Schritt starten - nehme erstes Foto auf der Position 0
    debug("Nehme erstes Foto auf");
    takePhotoAndContinue();
}

// Nehme Foto auf und fahre dann mit der Sequenz fort
function takePhotoAndContinue() {
    debug(`takePhotoAndContinue() - Schritt ${currentStep+1}/${totalSteps}`);
    
    if (!isRotating) {
        debug("Rotation wurde gestoppt, breche Sequenz ab");
        return;
    }
    
    // Der gewünschte Drehwinkel pro Schritt
    const angle = parseInt(angleInput.value) || 15;

    // Aktuelle Winkelposition berechnen (0, 15, 30, ...)
    const currentAngle = Math.max(1, currentStep * angle);
    
    // Statusmeldung aktualisieren
    updateStatus(`Nehme Foto ${currentStep+1}/${totalSteps} bei ${currentAngle}° auf`);
    updateProgress(currentStep, totalSteps);

    // Nur Foto aufnehmen - an der aktuellen Position
    debug(`Nehme Foto bei Position ${currentAngle}° auf`);
    const formData = new FormData();
    formData.append('degrees', currentAngle);  // Winkel für die Metadaten
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'photo_only');     // Nur Foto, keine Drehung
    
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Foto zur Liste hinzufügen
            capturedPhotos.push({
                path: data.photo,
                angle: currentAngle
            });

            // Bild anzeigen
            displayImage(data.photo, currentAngle);
            
            // Log-Eintrag hinzufügen
            addLogEntry(`Foto #${currentStep+1} bei ${currentAngle}° aufgenommen`);

            // Schritt abgeschlossen
            currentStep++;
            
            // Fortschritt aktualisieren
            updateProgress(currentStep, totalSteps);
            
            // Wenn alle Fotos gemacht wurden, fertig
            if (currentStep >= totalSteps) {
                debug("Alle Fotos aufgenommen, Sequenz abgeschlossen");
                completeRotation();
                return;
            }
            
            // Sonst: Zur nächsten Position drehen
            rotateToNextPosition();
        } else {
            console.error('Fehler beim Aufnehmen des Fotos:', data.error);
            alert(`Fehler beim Aufnehmen des Fotos: ${data.error}`);
            addLogEntry(`Fehler: ${data.error}`);
            stopRotation();
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler beim Aufnehmen des Fotos:', error);
        alert(`Netzwerkfehler beim Aufnehmen des Fotos: ${error.message}`);
        addLogEntry(`Netzwerkfehler: ${error.message}`);
        stopRotation();
    });
}

// Drehe zur nächsten Position
function rotateToNextPosition() {
    debug(`rotateToNextPosition() - Drehe zu Position ${currentStep+1}/${totalSteps}`);
    
    if (!isRotating) {
        debug("Rotation wurde gestoppt, breche Sequenz ab");
        return;
    }
    
    const angle = parseInt(angleInput.value) || 15;
    
    // Statusmeldung aktualisieren
    updateStatus(`Drehe um ${angle}° zur nächsten Position...`);
    updateProgress(currentStep, totalSteps);

    // Drehe um den eingestellten Winkel
    debug(`Drehe um ${angle}° weiter`);
    const formData = new FormData();
    formData.append('degrees', angle);          // Drehwinkel
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');     // Nur drehen, kein Foto
    
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            debug("Drehung erfolgreich, warte für Stabilisierung");
            
            // Kurze Pause für Stabilisierung
            setTimeout(() => {
                // Prüfen ob Rotation noch aktiv ist
                if (!isRotating) {
                    debug("Rotation wurde während der Stabilisierungspause gestoppt");
                    return;
                }
                
                // Intervall-Pause vor dem nächsten Foto
                const intervalTime = parseInt(intervalInput.value) || 5;
                debug(`Warte ${intervalTime} Sekunden bis zur nächsten Aufnahme...`);
                
                if (statusText) {
                    statusText.textContent = `Warte ${intervalTime}s für nächste Aufnahme...`;
                }
                
                setTimeout(() => {
                    // Erneut prüfen ob Rotation noch aktiv ist
                    if (!isRotating) {
                        debug("Rotation wurde während der Intervall-Pause gestoppt");
                        return;
                    }
                    
                    // Nächstes Foto aufnehmen
                    takePhotoAndContinue();
                }, intervalTime * 1000);
                
            }, 2000); // 2 Sekunden Pause für Stabilisierung
        } else {
            console.error('Fehler bei der Drehung:', data.error);
            alert(`Fehler bei der Drehung: ${data.error}`);
            addLogEntry(`Fehler: ${data.error}`);
            stopRotation();
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler bei der Drehung:', error);
        alert(`Netzwerkfehler bei der Drehung: ${error.message}`);
        addLogEntry(`Netzwerkfehler: ${error.message}`);
        stopRotation();
    });
}

// Beende die Rotation (Server-seitig UND client-seitig)
function stopRotation() {
    debug("stopRotation() aufgerufen");
    
    // Setze zuerst den Client-Status - SOFORT!
    isRotating = false;
    
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

    if (statusText) {
        statusText.textContent = 'Rotation wird gestoppt...';
    }
    
    // Dann den Server-Befehl senden
    debug("Sende Stop-Befehl an den Server");
    fetch('/stop_rotation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ project_id: currentProjectId })
    })
    .then(response => {
        debug(`Server-Antwort Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        debug(`Stop-Antwort vom Server: ${JSON.stringify(data)}`);
        
        if (statusText) {
            statusText.textContent = 'Rotation gestoppt';
            setTimeout(() => {
                statusText.textContent = "";
            }, 3000);
        }
    })
    .catch(error => {
        console.error("Fehler beim Stoppen der Rotation:", error);
        
        if (statusText) {
            statusText.textContent = `Fehler beim Stoppen: ${error.message}`;
            setTimeout(() => {
                statusText.textContent = "";
            }, 3000);
        }
    });
    
    debug("Rotation wurde gestoppt");
}

// Rotation abschließen
function completeRotation() {
    debug("completeRotation() aufgerufen - Rotation abgeschlossen");
    isRotating = false;

    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (rotateBtn) rotateBtn.disabled = false;

    if (statusText) {
        statusText.textContent = 'Rotation abgeschlossen!';
        setTimeout(() => {
            statusText.textContent = "";
        }, 3000);
    }

    // Nachfragen, ob ein 360°-Viewer erstellt werden soll
    if (confirm('Rotation abgeschlossen! Möchten Sie einen 360°-Viewer aus den aufgenommenen Fotos erstellen?')) {
        generateViewer();
    }
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
        debug(`Antwort vom Server: ${JSON.stringify(data)}`);
        if (data.status === 'success') {
            alert(`360°-CloudImage-Viewer erfolgreich erstellt! Sie werden weitergeleitet.`);
            window.location.href = data.url;
        } else {
            console.error('Fehler beim Generieren des Viewers:', data.error);
            alert(`Fehler beim Generieren des 360°-CloudImage-Viewers: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert(`Netzwerkfehler beim Generieren des 360°-CloudImage-Viewers: ${error.message}`);
    });
}

// Hilfsfunktion zum Aktualisieren des Status-Textes
function updateStatus(message) {
    debug(`Status: ${message}`);
    
    if (statusText) {
        statusText.textContent = message;
    }
}

// Hilfsfunktion zum Aktualisieren des Fortschritts
function updateProgress(current, total) {
    if (progressText) {
        progressText.textContent = `${current} / ${total} Fotos`;
    }
    
    if (progressBar) {
        const percentage = total > 0 ? (current / total) * 100 : 0;
        progressBar.style.width = `${percentage}%`;
    }
}

// Hilfsfunktion zum Hinzufügen von Log-Einträgen
function addLogEntry(message) {
    if (!logBox) return;
    
    const entry = document.createElement('div');
    entry.textContent = message;
    logBox.appendChild(entry);
    logBox.scrollTop = logBox.scrollHeight; // Zum Ende scrollen
}
