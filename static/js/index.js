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
let homePositionTimer = null; // Timer für die Heimpositions-Bewegung
let homePositionStartTime = null; // Startzeit für die Heimpositions-Bewegung

// DOM-Elemente
const projectSelect = document.getElementById('projectSelect');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const rotateBtn = document.getElementById('rotateBtn');
const homeBtn = document.getElementById('homeBtn');
const projectPositionBtn = document.getElementById('projectPositionBtn');
const imagePreview = document.getElementById('imagePreview');
const angleInput = document.getElementById('angleInput');
const intervalInput = document.getElementById('intervalInput');
const rotationStatus = document.getElementById('rotationStatus');
const currentPositionDisplay = document.getElementById('currentPosition');
const savedProjectPositionDisplay = document.getElementById('savedProjectPosition');
const projectModal = document.getElementById('projectModal');
const projectForm = document.getElementById('projectForm');
const cancelProjectBtn = document.getElementById('cancelProject');

// Status-Variablen
let tellerPosition = 0; // Speichert die aktuelle Position des Tellers
let positionLost = false; // Wird auf true gesetzt, wenn die Position unsicher ist

// Debug-Funktion - wichtig zur Fehlerbehebung
function debug(message) {
    console.log(`[DEBUG] ${message}`);
    
    // Debug-Meldung auch im UI anzeigen, wenn ein Statuselement vorhanden ist
    if (rotationStatus) {
        const debugEntry = document.createElement('div');
        debugEntry.className = 'debug-message';
        debugEntry.innerHTML = `<span class="debug-time">[${new Date().toLocaleTimeString()}]</span> ${message}`;
        rotationStatus.appendChild(debugEntry);
        
        // Scrolle zum Ende des Debug-Bereichs
        rotationStatus.scrollTop = rotationStatus.scrollHeight;
        
        // Begrenze die Anzahl der Nachrichten (maximal 20)
        while (rotationStatus.children.length > 20) {
            rotationStatus.removeChild(rotationStatus.firstChild);
        }
    }
}

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    debug("DOM geladen, initialisiere Anwendung...");
    
    // Initialisiere die Projekt-ID aus den Datenelementen oder dem localStorage
    const bodyProjectId = document.body.getAttribute('data-project-id');
    
    if (bodyProjectId && bodyProjectId.trim() !== '') {
        currentProjectId = bodyProjectId;
        debug(`Aktuelle Projekt-ID aus Datenelement: ${currentProjectId}`);
        
        // Speichere die aktuelle Projekt-ID im localStorage
        saveCurrentProject(currentProjectId);
        
        // Lade die Projektposition
        loadProjectPosition();
    } else {
        // Wenn keine Projekt-ID im Body definiert ist, versuche sie aus dem localStorage zu laden
        loadCurrentProject();
    }

    // Letzte bekannte Tellerposition aus dem localStorage laden
    loadTurntablePosition();
    
    // Projekte laden, wenn kein Projekt ausgewählt ist aber ein Select vorhanden
    if (projectSelect) {
        debug("Lade Projektliste...");
        loadProjects();
    }
    
    // Event-Listener für die Buttons einrichten
    if (startBtn) {
        startBtn.addEventListener('click', startRotation);
        debug("Event-Listener für Start-Button registriert");
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', function() {
            debug("Stop-Button wurde geklickt");
            stopRotation(false);
        });
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
    
    if (projectPositionBtn) {
        projectPositionBtn.addEventListener('click', moveToProjectPosition);
        debug("Event-Listener für Projektpositions-Button registriert");
    }
    
    if (projectSelect) {
        projectSelect.addEventListener('change', function() {
            const selectedProjectId = this.value;
            if (selectedProjectId === 'new') {
                // Neues Projekt erstellen
                projectModal.style.display = 'block';
                this.selectedIndex = 0; // Zurücksetzen auf "Bitte wählen..."
            } else if (selectedProjectId) {
                // Bestehendes Projekt auswählen
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
 * oder setzt den Standardwert
 */
function loadTurntablePosition() {
    try {
        // Versuche Position aus localStorage zu laden
        const savedPosition = localStorage.getItem('tellerPosition');
        
        if (savedPosition !== null) {
            tellerPosition = parseInt(savedPosition);
            debug(`Tellerposition aus dem Speicher geladen: ${tellerPosition}°`);
        } else {
            tellerPosition = 0;
            debug("Keine gespeicherte Tellerposition gefunden, verwende 0°");
        }
        
        // Aktualisiere die Anzeige
        if (currentPositionDisplay) {
            currentPositionDisplay.textContent = `${tellerPosition}°`;
        }
    } catch (error) {
        debug(`Fehler beim Laden der Tellerposition: ${error}`);
        tellerPosition = 0;
    }
}

/**
 * Speichert die aktuelle Position im localStorage
 * @param {number} position - Die zu speichernde Position
 */
function saveTurntablePosition(position) {
    try {
        localStorage.setItem('tellerPosition', position);
        debug(`Tellerposition ${position}° im Speicher gespeichert`);
    } catch (error) {
        debug(`Fehler beim Speichern der Tellerposition: ${error}`);
    }
}

/**
 * Speichert die aktuelle Projekt-ID im localStorage
 * @param {string} projectId - Die zu speichernde Projekt-ID oder null, wenn kein Projekt ausgewählt ist
 */
function saveCurrentProject(projectId) {
    try {
        if (projectId) {
            localStorage.setItem('currentProjectId', projectId);
            debug(`Aktuelle Projekt-ID ${projectId} im Speicher gespeichert`);
        } else {
            localStorage.removeItem('currentProjectId');
            debug("Aktuelle Projekt-ID aus dem Speicher entfernt");
        }
    } catch (error) {
        debug(`Fehler beim Speichern der Projekt-ID: ${error}`);
    }
}

/**
 * Lädt die Projekt-ID aus dem localStorage
 */
function loadCurrentProject() {
    try {
        // Versuche Projekt-ID aus localStorage zu laden
        const savedProjectId = localStorage.getItem('currentProjectId');
        
        if (savedProjectId) {
            debug(`Projekt-ID aus dem Speicher geladen: ${savedProjectId}`);
            
            // Verifiziere, ob das Projekt noch existiert
            verifyProject(savedProjectId).then(exists => {
                if (exists) {
                    currentProjectId = savedProjectId;
                    debug(`Geladenes Projekt ${savedProjectId} existiert und wurde aktiviert`);
                    
                    // Wenn es ein Projekt-Select gibt, wähle es aus
                    if (projectSelect) {
                        projectSelect.value = currentProjectId;
                    }
                    
                    // Lade die Projektposition
                    loadProjectPosition();
                } else {
                    debug(`Geladenes Projekt ${savedProjectId} existiert nicht mehr, entferne es aus dem Speicher`);
                    localStorage.removeItem('currentProjectId');
                    currentProjectId = null;
                    
                    // Deaktiviere projektbezogene UI-Elemente
                    resetProjectUI();
                }
            });
        } else {
            debug("Keine gespeicherte Projekt-ID gefunden");
            currentProjectId = null;
            
            // Deaktiviere projektbezogene UI-Elemente, wenn kein Projekt geladen wurde
            resetProjectUI();
        }
    } catch (error) {
        debug(`Fehler beim Laden der Projekt-ID: ${error}`);
        currentProjectId = null;
    }
}

/**
 * Überprüft, ob ein Projekt existiert
 * @param {string} projectId - Die zu überprüfende Projekt-ID
 * @returns {Promise<boolean>} - True, wenn das Projekt existiert, sonst False
 */
function verifyProject(projectId) {
    return fetch(`/api/project/${projectId}`)
        .then(response => {
            if (response.ok) {
                return true;
            }
            if (response.status === 404) {
                return false;
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        })
        .catch(error => {
            debug(`Fehler bei der Projekt-Überprüfung: ${error}`);
            return false;
        });
}

/**
 * Setzt die projektbezogenen UI-Elemente zurück, wenn kein Projekt ausgewählt ist
 */
function resetProjectUI() {
    debug("Setze projektbezogene UI-Elemente zurück");
    
    // Deaktiviere den Projektpositions-Button
    if (projectPositionBtn) {
        projectPositionBtn.disabled = true;
        projectPositionBtn.classList.add('btn-secondary');
        projectPositionBtn.classList.remove('btn-info');
        projectPositionBtn.title = "Kein Projekt ausgewählt";
        projectPositionBtn.textContent = "📌 Projektposition";
    }
    
    // Aktualisiere die Anzeige der gespeicherten Position
    if (savedProjectPositionDisplay && savedProjectPositionDisplay.parentElement) {
        savedProjectPositionDisplay.parentElement.innerHTML = 
            '<div class="text-secondary">Kein Projekt ausgewählt</div>';
    }
    
    // Zeige Hinweis, wenn kein Projekt ausgewählt ist
    if (rotationStatus) {
        showStatus('Bitte wählen Sie ein Projekt aus, um die Aufnahme zu starten.', 'info');
    }
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
        .then(response => {
            if (!response.ok) {
                // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
                if (response.status === 404) {
                    throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
                }
                throw new Error(`Server-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(project => {
            if (project && 'current_position' in project) {
                debug(`Projektposition geladen: ${project.current_position}°`);
                
                // Aktualisiere die Anzeige der gespeicherten Projektposition
                if (savedProjectPositionDisplay) {
                    savedProjectPositionDisplay.textContent = `${project.current_position}°`;
                }
                
                // Aktualisiere auch den Projektpositions-Button
                if (projectPositionBtn) {
                    projectPositionBtn.title = `Teller auf die gespeicherte Projektposition drehen (${project.current_position}°)`;
                    // Extrahiere den ersten Teil des Textes (alles vor der Klammer)
                    const buttonText = projectPositionBtn.textContent.split('(')[0];
                    projectPositionBtn.textContent = `${buttonText}(${project.current_position}°)`;
                }
                
                // NICHT die tellerPosition aktualisieren oder syncProjectPosition aufrufen,
                // da dies die tatsächliche Position des Tellers ist, nicht die Projektposition
            }
        })
        .catch(error => {
            debug(`Fehler beim Laden der Projektposition: ${error}`);
            showStatus(`Fehler: ${error.message}`, 'error');
            
            // Bei Fehler: Deaktiviere den Projektpositions-Button oder markiere ihn als nicht verfügbar
            if (projectPositionBtn) {
                projectPositionBtn.disabled = true;
                projectPositionBtn.title = "Projektposition nicht verfügbar";
                projectPositionBtn.classList.add('btn-secondary');
                projectPositionBtn.classList.remove('btn-info');
            }
            
            // Bei Fehler: Anzeige der gespeicherten Position ausblenden oder als nicht verfügbar markieren
            if (savedProjectPositionDisplay) {
                savedProjectPositionDisplay.parentElement.innerHTML = 
                    '<div class="text-danger">Projektposition nicht verfügbar</div>';
            }
        });
}

// Projekte laden
function loadProjects() {
    if (!projectSelect) {
        debug("Kein Projekt-Select gefunden");
        return;
    }
    
    fetch('/api/projects')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Alle Optionen außer den ersten beiden entfernen (Placeholder und "Neues Projekt")
            while (projectSelect.options.length > 2) {
                projectSelect.remove(2);
            }
            
            if (Array.isArray(data)) {
                // Projekte hinzufügen
                data.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.id;
                    option.textContent = project.name;
                    projectSelect.appendChild(option);
                });
                
                // Wenn eine aktuelle Projekt-ID gesetzt ist, wähle sie aus
                if (currentProjectId) {
                    // Überprüfe, ob das Projekt in der Liste ist
                    let projectExists = false;
                    for (let i = 0; i < projectSelect.options.length; i++) {
                        if (projectSelect.options[i].value === currentProjectId) {
                            projectSelect.selectedIndex = i;
                            projectExists = true;
                            break;
                        }
                    }
                    
                    // Wenn das Projekt nicht in der Liste ist, entferne es aus dem Speicher
                    if (!projectExists) {
                        debug(`Aktuelles Projekt ${currentProjectId} nicht in der Projektliste gefunden, entferne es aus dem Speicher`);
                        saveCurrentProject(null);
                        currentProjectId = null;
                        
                        // Deaktiviere projektbezogene UI-Elemente
                        resetProjectUI();
                    }
                }
            }
        })
        .catch(error => {
            debug(`Fehler beim Laden der Projekte: ${error}`);
            showStatus(`Fehler: ${error.message}`, 'error');
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

    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/rotate';
    debug(`Sende Rotationsanfrage an: ${url} mit Projektion: ${currentProjectId}, Winkel: ${angle}°`);

    // Foto aufnehmen und dann rotieren
    fetch(url, {
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

    // Der gewünschte Drehwinkel pro Schritt
    const angle = parseInt(angleInput.value) || 15;
    debug(`Eingestellter Winkel: ${angle}°`);

    // Prüfen, ob eine pausierte Aufnahme fortgesetzt werden soll
    const savedStep = parseInt(localStorage.getItem('lastSequenceStep') || "0");
    const savedTotalSteps = parseInt(localStorage.getItem('lastSequenceTotalSteps') || "0");
    
    debug(`Gespeicherter Fortschritt gefunden: Schritt ${savedStep}/${savedTotalSteps}`);
    
    if (!isNaN(savedStep) && !isNaN(savedTotalSteps) && savedStep > 0 && savedStep < savedTotalSteps) {
        if (confirm(`Es gibt eine pausierte Aufnahme bei Schritt ${savedStep}/${savedTotalSteps}. Möchten Sie diese fortsetzen?`)) {
            // Werte wiederherstellen
            currentStep = savedStep;
            totalSteps = savedTotalSteps;
            debug(`Setze pausierte Aufnahme fort bei Schritt ${currentStep}/${totalSteps}`);
        } else {
            // Neue Aufnahme starten
            localStorage.removeItem('lastSequenceStep');
            localStorage.removeItem('lastSequenceTotalSteps');
            totalSteps = Math.floor(360 / angle);
            currentStep = 0;
            debug(`Starte neue 360° Rotation mit ${totalSteps} Schritten, Winkel=${angle}°`);
        }
    } else {
        // Neue Aufnahme starten
        localStorage.removeItem('lastSequenceStep');
        localStorage.removeItem('lastSequenceTotalSteps');
        const interval = parseInt(intervalInput.value) || 5;
        totalSteps = Math.floor(360 / angle);
        currentStep = 0;
        debug(`Starte 360° Rotation mit ${totalSteps} Schritten, Winkel=${angle}°, Intervall=${interval}s`);
    }

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
    if (currentStep === 0) {
        showStatus(`Rotation gestartet: Nehme erstes Foto auf`, 'info');
        // Ersten Schritt starten - nehme erstes Foto auf der Position 0
        debug("Nehme erstes Foto auf");
        takePhotoForSequence();
    } else {
        showStatus(`Rotation wird fortgesetzt ab Schritt ${currentStep+1}/${totalSteps}`, 'info');
        // Fortsetzen mit dem nächsten Schritt
        debug(`Setze mit Schritt ${currentStep+1}/${totalSteps} fort`);
        takePhotoForSequence();
    }
}

function stopRotation(withError = false) {
    debug("stopRotation() aufgerufen");
    
    // Setze die Rotation-Flag
    isRotating = false;
    
    // Speichere den aktuellen Fortschritt für spätere Fortsetzung
    localStorage.setItem('lastSequenceStep', currentStep.toString());
    localStorage.setItem('lastSequenceTotalSteps', totalSteps.toString());
    debug(`Fortschritt gespeichert: Schritt ${currentStep}/${totalSteps}`);
    
    // UI aktualisieren
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    if (rotateBtn) rotateBtn.disabled = false;
    if (homeBtn) homeBtn.disabled = false;
    
    // Statusmeldung aktualisieren
    if (!withError) {
        debug("Rotation gestoppt durch Benutzer");
        showStatus("Aufnahme pausiert. Drücken Sie 'Start', um die Aufnahme fortzusetzen.", 'warning');
    } else {
        debug("Rotation gestoppt wegen eines Fehlers");
    }
}

function takePhotoForSequence() {
    // Abbruch, wenn Rotation gestoppt
    
    if (!isRotating) {
        debug("Rotation wurde gestoppt, breche Sequenz ab");
        return;
    }
    
    // Der gewünschte Drehwinkel pro Schritt
    const angle = parseInt(angleInput.value) || 15;

    // Aktuelle Winkelposition berechnen basierend auf der aktuellen Tellerposition
    const currentAngle = tellerPosition;
    
    // Statusmeldung aktualisieren
    showStatus(`Nehme Foto ${currentStep+1}/${totalSteps} bei ${currentAngle}° auf`, 'info');

    // Nur Foto aufnehmen - an der aktuellen Position
    debug(`Nehme Foto bei Position ${currentAngle}° auf (Schritt ${currentStep+1}/${totalSteps})`);
    const formData = new FormData();
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'photo_only');
    formData.append('degrees', currentAngle); // WICHTIG: Backend erwartet 'degrees', nicht 'angle'
    formData.append('step', currentStep+1);  // Schrittnummer mitgeben
    formData.append('total_steps', totalSteps); // Gesamtschrittzahl mitgeben

    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/rotate';
    debug(`Sende Foto-Anfrage an: ${url} mit Projektion: ${currentProjectId}, Winkel: ${currentAngle}°, Schritt: ${currentStep+1}`);

    // Foto aufnehmen und dann rotieren
    fetch(url, {
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
                angle: data.angle || currentAngle, // Fallback auf currentAngle, wenn kein angle vom Server kommt
                step: currentStep+1
            });

            // Bild anzeigen
            displayImage(data.photo, currentAngle);

            debug(`Erfolgreich Foto aufgenommen: ${data.photo} (Schritt ${currentStep+1}/${totalSteps})`);

            // Nächsten Schritt vorbereiten
            currentStep++;
            
            // Sofort den Fortschritt speichern
            localStorage.setItem('lastSequenceStep', currentStep.toString());
            
            // Prüfen, ob wir alle Fotos aufgenommen haben
            if (currentStep < totalSteps) {
                // Weiter zum nächsten Schritt - zuerst drehen
                debug(`Schritt ${currentStep+1}/${totalSteps} - Drehe zur nächsten Position`);
                setTimeout(rotateForSequence, 1000);
            } else {
                // Sequenz abschließen, wenn wir alle Fotos haben
                debug(`Alle ${totalSteps} Fotos aufgenommen, schließe Sequenz ab`);
                // Fortschritt zurücksetzen
                localStorage.removeItem('lastSequenceStep');
                localStorage.removeItem('lastSequenceTotalSteps');
                completedSequence();
            }
        } else {
            console.error('Fehler:', data.error);
            alert(`Fehler bei der Fotoaufnahme: ${data.error}`);

            // Position als unsicher markieren
            updatePositionDisplay(tellerPosition, true);

            // Statusmeldung aktualisieren
            showStatus(`Fehler: ${data.error}`, 'error');
            debug(`Fehler vom Server bei Fotoaufnahme: ${JSON.stringify(data)}`);
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
    formData.append('degrees', angle);          // Drehwinkel (wichtig: hier den korrekten Winkelwert übergeben)
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');    // Nur drehen ohne Foto

    // API-Anfrage zum Drehen des Tellers
    fetch('/rotate', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
            if (response.status === 404) {
                throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            // Position aktualisieren
            const newPosition = (tellerPosition + angle) % 360;
            tellerPosition = newPosition; // Aktualisiere die globale Variable
            updatePositionDisplay(newPosition, false);
            
            // Nach kurzer Pause das nächste Foto aufnehmen
            setTimeout(takePhotoForSequence, 1000);
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
        
        // Prüfe, ob die Funktion existiert (könnte in turntable.js definiert sein)
        if (typeof generateViewer === 'function') {
            generateViewer();
        } else {
            // Fallback-Funktion zum Erstellen des 360°-Viewers (falls die Hauptfunktion nicht verfügbar ist)
            generateViewerFallback();
        }
    }
}

/**
 * Fallback-Funktion zum Erstellen des 360°-Viewers (falls die Hauptfunktion nicht verfügbar ist)
 */
function generateViewerFallback() {
    // Überprüfe, ob genügend Fotos vorhanden sind
    if (capturedPhotos.length < 4) {
        alert('Es werden mindestens 4 Fotos für einen 360°-Viewer benötigt.');
        return;
    }
    
    // Projektname abfragen
    const viewerName = prompt('Bitte geben Sie einen Namen für den 360°-Viewer ein:', 
                          `Projekt ${currentProjectId} - ${new Date().toLocaleDateString()}`);
    
    if (!viewerName) return;
    
    // Projekt-ID überprüfen
    if (!currentProjectId) {
        console.error("Fehler: project_id fehlt!");
        alert("Fehler: Keine Projekt-ID gefunden!");
        return;
    }
    
    // Anfrage zum Generieren des Viewers senden
    const requestData = {
        project_id: currentProjectId,
        name: viewerName,
        photos: capturedPhotos.map(photo => photo.path)
    };
    
    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/generate_360';
    debug(`Sende Viewer-Erstellungsanfrage an: ${url}`);
    
    // API-Anfrage senden
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        debug(`Antwort vom Server: ${JSON.stringify(data)}`);
        if (data.status === 'success' || data.message) {
            alert(`360°-Viewer erfolgreich erstellt! Sie werden weitergeleitet.`);
            // Zur Viewer-Seite weiterleiten
            if (data.url) {
                window.location.href = data.url;
            } else {
                // Fallback zur Viewer-Seite
                window.location.href = `/viewer/exports?project=${currentProjectId}`;
            }
        } else {
            debug('Fehler beim Generieren des Viewers:', data.error || 'Unbekannter Fehler');
            alert(`Fehler beim Generieren des 360°-Viewers: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        debug(`Netzwerkfehler: ${error}`);
        alert('Netzwerkfehler beim Generieren des 360°-Viewers: ' + error.message);
    });
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
    
    // Berechne den Weg zur Heimposition
    // HINWEIS: Motor kann nur vorwärts drehen, daher immer vorwärts bis zur 0-Position
    let degreesToMove = 0;
    
    // Da der Motor nur vorwärts drehen kann, immer im Uhrzeigersinn weiterdrehen
    if (tellerPosition > 0) {
        degreesToMove = 360 - tellerPosition;
    }
    
    if (degreesToMove === 0) {
        debug("Teller bereits in Heimposition");
        showStatus('Teller befindet sich bereits in der Heimposition (0°).', 'success');
        return;
    }
    
    // Setze die Startzeit und starte den Timer
    homePositionStartTime = new Date();
    startHomePositionTimer();
    
    debug(`Fahre zur Heimposition: ${degreesToMove}° in Richtung vorwärts`);
    showStatus(`Fahre zur Heimposition (0°)...`, 'info');
    
    // API-Anfrage zum Drehen des Tellers
    const formData = new FormData();
    formData.append('degrees', degreesToMove);
    formData.append('direction', 'cw'); // Immer im Uhrzeigersinn (cw) drehen
    
    // Stelle sicher, dass eine gültige Projekt-ID verwendet wird
    if (!currentProjectId) {
        debug("Keine Projekt-ID vorhanden, kann nicht zur Heimposition fahren");
        showStatus('Bitte wählen Sie zuerst ein Projekt aus.', 'warning');
        stopHomePositionTimer(); // Timer stoppen, falls ein Fehler auftritt
        return;
    }
    
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');
    formData.append('reset_position', 'true'); // Spezielle Flagge für Heimposition
    
    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/rotate';
    debug(`Sende Home-Position Anfrage an: ${url} mit ${degreesToMove}° Drehung`);
    
    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
            if (response.status === 404) {
                throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        stopHomePositionTimer(); // Timer stoppen
        debug("Heimpositionierung erfolgreich");
        showStatus('Teller erfolgreich auf Heimposition (0°) gesetzt.', 'success');
        tellerPosition = 0; // Setze lokale Position auf 0
        saveTurntablePosition(0); // Speichere in localStorage mit der neuen Funktion
        updatePositionDisplay(0, false); // false, da wir hier nicht mit dem Projekt synchronisieren wollen
    })
    .catch(error => {
        stopHomePositionTimer(); // Timer stoppen bei Fehler
        debug(`Fehler bei Heimpositionierung: ${error}`);
        showStatus(`Fehler beim Zurückfahren zur Heimposition: ${error.message}`, 'error');
    });
}

/**
 * Startet einen Timer, der jede Sekunde die Zeit seit Beginn der Heimpositionierung anzeigt
 */
function startHomePositionTimer() {
    // Alte Timer löschen, falls vorhanden
    stopHomePositionTimer();
    
    // Speichere die Ausgangsposition für die Berechnung
    const startPosition = tellerPosition;
    const degreesToMove = (startPosition > 0) ? 360 - startPosition : 0;
    
    // Timer starten, der jede Sekunde aktualisiert wird
    homePositionTimer = setInterval(() => {
        if (homePositionStartTime) {
            const currentTime = new Date();
            const elapsedSeconds = Math.floor((currentTime - homePositionStartTime) / 1000);
            
            // Schätze die aktuelle Position basierend auf der verstrichenen Zeit
            // Annahme: gleichmäßige Drehung über die Zeit (kann in der Realität abweichen)
            // Berechne Rotationsgeschwindigkeit (Grad pro Sekunde)
            const totalRotationTimeEstimate = 15; // Geschätzte Zeit für eine vollständige Umdrehung in Sekunden
            const degreesPerSecond = 360 / totalRotationTimeEstimate;
            
            // Schätze die aktuelle Position
            const movedDegrees = Math.min(elapsedSeconds * degreesPerSecond, degreesToMove);
            const estimatedCurrentPosition = (startPosition + movedDegrees) % 360;
            
            // Berechne die verbleibenden Grad bis zur Heimposition
            const remainingDegrees = degreesToMove - movedDegrees;
            
            debug(`Zeit seit Start der Heimpositionierung: ${elapsedSeconds} Sekunden, `
                + `Geschätzte Position: ${Math.round(estimatedCurrentPosition)}°, `
                + `Verbleibend bis Heimposition: ~${Math.max(0, Math.round(remainingDegrees))}°`);
        }
    }, 1000);
}

/**
 * Stoppt den Timer für die Heimpositionierung
 */
function stopHomePositionTimer() {
    if (homePositionTimer) {
        clearInterval(homePositionTimer);
        homePositionTimer = null;
    }
    homePositionStartTime = null;
}

/**
 * Dreht den Teller zur Projektposition
 */
function moveToProjectPosition() {
    if (isRotating) {
        debug("Rotation bereits aktiv, kann nicht zur Projektposition fahren");
        showStatus('Bitte stoppen Sie zuerst die aktuelle Rotation.', 'warning');
        return;
    }
    
    // Prüfe die aktuelle Projekt-ID
    if (!currentProjectId) {
        debug("Keine Projekt-ID vorhanden, kann nicht zur Projektposition fahren");
        showStatus('Bitte wählen Sie zuerst ein Projekt aus.', 'warning');
        return;
    }
    
    // Lade die Projektposition direkt vom Server, um die aktuellsten Daten zu haben
    fetch(`/api/project/${currentProjectId}`)
        .then(response => {
            if (!response.ok) {
                // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
                if (response.status === 404) {
                    throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
                }
                throw new Error(`Server-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(project => {
            if (project && 'current_position' in project) {
                const targetPosition = parseInt(project.current_position);
                const currentPosition = parseInt(tellerPosition);
                
                debug(`Zielposition aus Server: ${targetPosition}°, Aktuelle Position: ${currentPosition}°`);
                
                // Aktualisiere die Anzeige der Projekt-Position im UI
                if (savedProjectPositionDisplay) {
                    savedProjectPositionDisplay.textContent = `${targetPosition}°`;
                }
                
                // Aktualisiere auch den Projektpositions-Button
                if (projectPositionBtn) {
                    projectPositionBtn.title = `Teller auf die gespeicherte Projektposition drehen (${targetPosition}°)`;
                    // Extrahiere den ersten Teil des Textes (alles vor der Klammer)
                    const buttonText = projectPositionBtn.textContent.split('(')[0];
                    projectPositionBtn.textContent = `${buttonText}(${targetPosition}°)`;
                }
                
                // Prüfe, ob die aktuelle Position und die Zielposition wirklich identisch sind
                // Aufgrund von Rundungsfehlern oder anderen Problemen könnte die Gleichheitsüberprüfung fehlschlagen
                const positionTolerance = 0.1; // Toleranz von 0.1 Grad
                if (Math.abs(currentPosition - targetPosition) < positionTolerance) {
                    debug(`Teller bereits in Projektposition (${targetPosition}°)`);
                    showStatus(`Teller befindet sich bereits in der Projektposition (${targetPosition}°).`, 'success');
                    return;
                }
                
                // Berechne den Winkel zum Drehen (nur vorwärts möglich)
                let degreesToMove = 0;
                
                // Da der Motor nur vorwärts drehen kann, berechnen wir die Drehung im Uhrzeigersinn
                if (currentPosition < targetPosition) {
                    // Einfach vorwärts drehen
                    degreesToMove = targetPosition - currentPosition;
                } else {
                    // Muss einmal herum drehen
                    degreesToMove = 360 - currentPosition + targetPosition;
                }
                
                debug(`Fahre zur Projektposition: ${degreesToMove}° im Uhrzeigersinn (vorwärts)`);
                showStatus(`Fahre zur Projektposition (${targetPosition}°)...`, 'info');
                
                // API-Anfrage zum Drehen des Tellers
                const formData = new FormData();
                formData.append('degrees', degreesToMove);
                formData.append('direction', 'cw'); // Immer im Uhrzeigersinn (cw) drehen
                formData.append('target_position', targetPosition); // Zielposition mitgeben
                
                // Stelle sicher, dass eine gültige Projekt-ID verwendet wird
                formData.append('project_id', currentProjectId);
                formData.append('mode', 'rotate_only');
                
                // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
                const url = window.location.protocol + '//' + window.location.host + '/rotate';
                debug(`Sende Projektposition Anfrage an: ${url} (Zielposition: ${targetPosition}°)`);
                
                fetch(url, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
                        if (response.status === 404) {
                            throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
                        }
                        throw new Error(`Server-Fehler: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    debug(`Positionierung erfolgreich, Serverantwort: ${JSON.stringify(data)}`);
                    showStatus(`Teller erfolgreich auf Projektposition (${targetPosition}°) gesetzt.`, 'success');
                    
                    // Aktualisiere die lokale Position und speichere sie
                    tellerPosition = targetPosition;
                    saveTurntablePosition(targetPosition);
                    updatePositionDisplay(targetPosition, false); // false, da wir nicht wieder mit dem Projekt synchronisieren wollen
                })
                .catch(error => {
                    debug(`Fehler bei Projektpositionierung: ${error}`);
                    showStatus(`Fehler beim Fahren zur Projektposition: ${error.message}`, 'error');
                });
            } else {
                debug(`Ungültige Projektdaten, keine Position gefunden: ${JSON.stringify(project)}`);
                showStatus('Fehler: Keine gültige Projektkonfiguration gefunden.', 'error');
            }
        })
        .catch(error => {
            debug(`Fehler beim Laden der Projektposition: ${error}`);
            showStatus(`Fehler beim Laden der Projektdaten: ${error.message}`, 'error');
            
            // Wenn das Projekt nicht gefunden wurde, aus dem Speicher entfernen
            if (error.message.includes('nicht gefunden')) {
                saveCurrentProject(null);
                currentProjectId = null;
                
                // UI aktualisieren
                resetProjectUI();
            }
        });
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
    .then(response => {
        if (!response.ok) {
            // Wenn das Projekt nicht gefunden wurde (404) oder andere Fehler
            if (response.status === 404) {
                throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            debug(`Position im Projekt aktualisiert: ${position}°`);
            
            // Aktualisiere die Anzeige der gespeicherten Projektposition
            if (savedProjectPositionDisplay) {
                savedProjectPositionDisplay.textContent = `${position}°`;
            }
            
            // Aktualisiere auch den Projektpositions-Button
            if (projectPositionBtn) {
                projectPositionBtn.title = `Teller auf die gespeicherte Projektposition drehen (${position}°)`;
                // Extrahiere den ersten Teil des Textes (alles vor der Klammer)
                const buttonText = projectPositionBtn.textContent.split('(')[0];
                projectPositionBtn.textContent = `${buttonText}(${position}°)`;
            }
        } else {
            debug(`Fehler beim Aktualisieren der Position: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        debug(`Fehler bei der Positionssynchronisierung: ${error}`);
        showStatus(`Fehler: ${error.message}`, 'error');
        
        // Wenn das Projekt nicht gefunden wurde, entferne es aus dem Speicher
        if (error.message.includes('nicht gefunden')) {
            debug(`Projekt ${currentProjectId} wurde nicht gefunden, entferne es aus dem Speicher`);
            saveCurrentProject(null);
            currentProjectId = null;
            
            // UI aktualisieren
            resetProjectUI();
        }
    });
}

/**
 * Aktualisiert die Position des Tellers im UI und speichert sie lokal
 * @param {number} position - Die neue Position in Grad
 * @param {boolean} syncWithProject - Ob die Position mit dem Projekt synchronisiert werden soll
 * @param {boolean} uncertain - Ob die Position unsicher ist (z.B. nach Stromausfall)
 */
function updatePositionDisplay(position, syncWithProject = true, uncertain = false) {
    // Stelle sicher, dass die Position eine Zahl ist
    position = parseInt(position);
    
    // Aktualisiere die globale Variable
    tellerPosition = position;
    
    // Speichere die Position im localStorage
    saveTurntablePosition(position);
    
    // Aktualisiere die Anzeige
    if (currentPositionDisplay) {
        currentPositionDisplay.textContent = `${position}°`;
        
        // Visuelle Markierung für unsichere Position
        if (uncertain) {
            currentPositionDisplay.classList.add('uncertain');
            if (!positionLost) {
                showStatus('Die genaue Tellerposition ist möglicherweise nicht korrekt. Empfehlung: Zur Heimpositions-Bewegung zurückfahren.', 'warning');
                positionLost = true;
            }
        } else {
            currentPositionDisplay.classList.remove('uncertain');
            positionLost = false;
        }
    }
    
    // Synchronisiere die Position mit dem Projekt, wenn gewünscht und ein Projekt ausgewählt ist
    if (syncWithProject && currentProjectId) {
        syncProjectPosition(position);
    }
}

/**
 * Zeigt eine Statusmeldung an
 * @param {string} message - Die anzuzeigende Nachricht
 * @param {string} type - Der Typ der Nachricht (success, error, warning, info)
 */
function showStatus(message, type = 'info') {
    debug(`Status-Update: ${message} (Typ: ${type})`);
    
    if (rotationStatus) {
        // Klasse hinzufügen, um sicherzustellen, dass die Nachricht sichtbar ist
        rotationStatus.classList.add('visible');
        
        // Status-Klasse basierend auf Typ setzen
        rotationStatus.className = rotationStatus.className.replace(/status-\w+/g, '');
        rotationStatus.classList.add(`status-${type}`);
        
        // Nachricht anzeigen
        const statusMessage = document.createElement('div');
        statusMessage.textContent = message;
        rotationStatus.appendChild(statusMessage);
    }
}

/**
 * Projekt löschen
 * @param {string} projectId - Die ID des zu löschenden Projekts
 */
function deleteProject(projectId) {
    if (!confirm('Sind Sie sicher, dass Sie dieses Projekt löschen möchten? Diese Aktion kann nicht rückgängig gemacht werden.')) {
        return;
    }

    debug(`Lösche Projekt: ${projectId}`);
    
    fetch(`/projects/delete/${projectId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error(`Projekt mit ID ${projectId} wurde nicht gefunden`);
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        }
        return response;
    })
    .then(() => {
        debug(`Projekt ${projectId} erfolgreich gelöscht`);
        showStatus('Projekt erfolgreich gelöscht.', 'success');
        
        // Wenn das aktuelle Projekt gelöscht wurde, setze die aktuelle Projekt-ID zurück
        if (currentProjectId === projectId) {
            // Entferne es aus dem localStorage
            saveCurrentProject(null);
            currentProjectId = null;
            
            // UI aktualisieren
            resetProjectUI();
        }
        
        // Umleitung zur Projektübersicht oder Aktualisierung der Projektliste
        setTimeout(function() {
            window.location.href = '/projects';
        }, 1000);
    })
    .catch(error => {
        debug(`Fehler beim Löschen des Projekts: ${error}`);
        showStatus(`Fehler: ${error.message}`, 'error');
        
        // Wenn das Projekt nicht gefunden wurde, entferne es aus dem Speicher
        if (error.message.includes('nicht gefunden') && currentProjectId === projectId) {
            saveCurrentProject(null);
            currentProjectId = null;
            
            // UI aktualisieren
            resetProjectUI();
        }
    });
}

/**
 * Zeigt ein Bild in der Vorschau an
 * @param {string} imagePath - Der Pfad zum Bild
 * @param {number} angle - Der Winkel, bei dem das Bild aufgenommen wurde
 */
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
