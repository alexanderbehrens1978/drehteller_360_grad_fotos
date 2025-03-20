/**
 * index.js
 * JavaScript für die Startseite und Drehteller-Steuerung
 * Korrigierte Version mit richtiger Sequenz: Erst drehen, dann Foto
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
const imagePreview = document.getElementById('imagePreview');
const angleInput = document.getElementById('angleInput');
const intervalInput = document.getElementById('intervalInput');
const rotationStatus = document.getElementById('rotationStatus');
const projectModal = document.getElementById('projectModal');
const projectForm = document.getElementById('projectForm');
const cancelProjectBtn = document.getElementById('cancelProject');

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

// KORRIGIERTE FUNKTION: Erst drehen, dann fotografieren
async function singleRotation() {
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
    if (rotationStatus) {
        rotationStatus.textContent = "Drehe Teller...";
        rotationStatus.style.display = "block";
    }

    // SCHRITT 1: Erst den Motor drehen
    try {
        debug("Schritt 1: Drehe Motor");
        
        // Formular-Daten für die Drehung
        const rotateFormData = new FormData();
        rotateFormData.append('degrees', angle);
        rotateFormData.append('project_id', currentProjectId);
        rotateFormData.append('mode', 'rotate_only'); // Nur Rotation
        
        // Rotation durchführen
        const rotateResponse = await fetch('/rotate', {
            method: 'POST',
            body: rotateFormData
        });
        
        const rotateData = await rotateResponse.json();
        
        if (rotateData.status !== 'success') {
            throw new Error(`Fehler bei der Rotation: ${rotateData.error || 'Unbekannter Fehler'}`);
        }
        
        debug("Rotation abgeschlossen, warte 2 Sekunden zur Stabilisierung");
        
        // Kurze Pause für Stabilisierung
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // SCHRITT 2: Jetzt das Foto aufnehmen
        if (rotationStatus) {
            rotationStatus.textContent = "Nehme Foto auf...";
        }
        
        debug("Schritt 2: Nehme Foto auf");
        
        // Formular-Daten für die Fotoaufnahme
        const photoFormData = new FormData();
        photoFormData.append('degrees', angle);
        photoFormData.append('project_id', currentProjectId);
        photoFormData.append('mode', 'photo_only'); // Nur Foto
        
        // Foto aufnehmen
        const photoResponse = await fetch('/rotate', {
            method: 'POST',
            body: photoFormData
        });
        
        const photoData = await photoResponse.json();
        
        if (photoData.status !== 'success') {
            throw new Error(`Fehler bei der Fotoaufnahme: ${photoData.error || 'Unbekannter Fehler'}`);
        }
        
        // Foto zur Liste hinzufügen
        capturedPhotos.push({
            path: photoData.photo,
            angle: angle
        });
        
        // Bild anzeigen
        displayImage(photoData.photo, angle);
        
        // Statusmeldung aktualisieren
        if (rotationStatus) {
            rotationStatus.textContent = `Erfolgreich: Teller um ${angle}° gedreht und Foto aufgenommen`;
            setTimeout(() => {
                rotationStatus.style.display = "none";
            }, 3000);
        }
        
        debug(`Erfolgreich gedreht und Foto aufgenommen: ${photoData.photo}`);
    } catch (error) {
        console.error('Fehler:', error);
        if (rotationStatus) {
            rotationStatus.textContent = `Fehler: ${error.message}`;
        }
        alert(`Fehler: ${error.message}`);
    } finally {
        isRotating = false;
        if (rotateBtn) rotateBtn.disabled = false;
        debug("Einzelrotation abgeschlossen");
    }
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

// Automatische Rotation und Fotoaufnahme - Korrigierte Version
// WICHTIG: Korrekte Sequenz: 1) Drehen, 2) Warten, 3) Foto aufnehmen, 4) Warten, Wiederholen
async function startRotation() {
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
    
    isRotating = true;

    // Hauptschleife für die 360°-Sequenz
    try {
        for (currentStep = 0; currentStep < totalSteps; currentStep++) {
            // Abbruch prüfen
            if (!isRotating) {
                debug("Rotation wurde gestoppt, breche Sequenz ab");
                break;
            }
            
            const currentAngle = (currentStep * angle) % 360;
            
            // Statusmeldung aktualisieren
            if (rotationStatus) {
                rotationStatus.textContent = `Schritt ${currentStep+1}/${totalSteps}: Drehe zu Position ${currentAngle}°`;
                rotationStatus.style.display = "block";
            }
            
            // SCHRITT 1: Motor drehen (aber nicht beim ersten Schritt, da wir von 0° starten)
            if (currentStep > 0) {
                debug(`Drehe um ${angle}° weiter zu Position ${currentAngle}°`);
                
                // Formular-Daten für die Drehung
                const rotateFormData = new FormData();
                rotateFormData.append('degrees', angle);
                rotateFormData.append('project_id', currentProjectId);
                rotateFormData.append('mode', 'rotate_only'); // Nur Rotation
                
                // Rotation durchführen
                const rotateResponse = await fetch('/rotate', {
                    method: 'POST',
                    body: rotateFormData
                });
                
                const rotateData = await rotateResponse.json();
                
                if (rotateData.status !== 'success') {
                    throw new Error(`Fehler bei der Rotation: ${rotateData.error || 'Unbekannter Fehler'}`);
                }
                
                // Kurze Pause für Stabilisierung (2 Sekunden)
                debug("Warte 2 Sekunden zur Stabilisierung...");
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
            
            // Abbruch prüfen nach Drehung
            if (!isRotating) {
                debug("Rotation wurde während der Stabilisierungspause gestoppt");
                break;
            }
            
            // SCHRITT 2: Foto aufnehmen
            if (rotationStatus) {
                rotationStatus.textContent = `Schritt ${currentStep+1}/${totalSteps}: Nehme Foto bei ${currentAngle}° auf`;
            }
            
            debug(`Nehme Foto bei Position ${currentAngle}° auf`);
            
            // Formular-Daten für die Fotoaufnahme
            const photoFormData = new FormData();
            photoFormData.append('degrees', currentAngle);
            photoFormData.append('project_id', currentProjectId);
            photoFormData.append('mode', 'photo_only'); // Nur Foto
            
            // Foto aufnehmen
            const photoResponse = await fetch('/rotate', {
                method: 'POST',
                body: photoFormData
            });
            
            const photoData = await photoResponse.json();
            
            if (photoData.status !== 'success') {
                throw new Error(`Fehler bei der Fotoaufnahme: ${photoData.error || 'Unbekannter Fehler'}`);
            }
            
            // Foto zur Liste hinzufügen
            capturedPhotos.push({
                path: photoData.photo,
                angle: currentAngle
            });
            
            // Bild anzeigen
            displayImage(photoData.photo, currentAngle);
            
            // Abbruch prüfen nach Foto
            if (!isRotating) {
                debug("Rotation wurde nach Fotoaufnahme gestoppt");
                break;
            }
            
            // SCHRITT 3: Warten für das eingestellte Intervall vor dem nächsten Schritt
            if (currentStep < totalSteps - 1) {
                if (rotationStatus) {
                    rotationStatus.textContent = `Warte ${interval} Sekunden für nächsten Schritt...`;
                }
                
                debug(`Warte ${interval} Sekunden vor nächstem Schritt...`);
                await new Promise(resolve => setTimeout(resolve, interval * 1000));
            }
        }
        
        // Sequenz abgeschlossen oder abgebrochen
        if (isRotating) {
            debug("360° Sequenz erfolgreich abgeschlossen");
            if (rotationStatus) {
                rotationStatus.textContent = "360° Aufnahme erfolgreich abgeschlossen!";
            }
            
            // Nachfragen, ob ein 360°-Viewer erstellt werden soll
            if (confirm('360° Aufnahme abgeschlossen! Möchten Sie einen 360°-Viewer aus den aufgenommenen Fotos erstellen?')) {
                generateViewer();
            }
        } else {
            debug("360° Sequenz wurde manuell abgebrochen");
            if (rotationStatus) {
                rotationStatus.textContent = "360° Aufnahme wurde gestoppt";
            }
        }
    } catch (error) {
        console.error('Fehler während der 360°-Aufnahme:', error);
        if (rotationStatus) {
            rotationStatus.textContent = `Fehler: ${error.message}`;
        }
        alert(`Fehler während der 360°-Aufnahme: ${error.message}`);
    } finally {
        isRotating = false;
        
        // UI zurücksetzen
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (rotateBtn) rotateBtn.disabled = false;
        
        debug("360° Sequenz beendet");
    }
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

    if (rotationStatus) {
        rotationStatus.textContent = 'Rotation wird gestoppt...';
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
        
        if (rotationStatus) {
            rotationStatus.textContent = 'Rotation gestoppt';
            setTimeout(() => {
                rotationStatus.style.display = "none";
            }, 3000);
        }
    })
    .catch(error => {
        console.error("Fehler beim Stoppen der Rotation:", error);
        
        if (rotationStatus) {
            rotationStatus.textContent = `Fehler beim Stoppen: ${error.message}`;
            setTimeout(() => {
                rotationStatus.style.display = "none";
            }, 3000);
        }
    });
    
    debug("Rotation wurde gestoppt");
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
            alert(`360°-Viewer erfolgreich erstellt! Sie werden weitergeleitet.`);
            window.location.href = data.url;
        } else {
            console.error('Fehler beim Generieren des Viewers:', data.error);
            alert(`Fehler beim Generieren des 360°-Viewers: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert(`Netzwerkfehler beim Generieren des 360°-Viewers: ${error.message}`);
    });
}
