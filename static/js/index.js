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
let rotationEndTime = null; // Berechnete Endzeit für die aktuelle Rotation

// DOM-Elemente
let startBtn, stopBtn, rotateBtn, homeBtn, projectPositionBtn;
let angleInput, intervalInput, rotationTimeInput;
let currentPositionDisplay, savedProjectPositionDisplay, rotationStatus, imagePreview;
let projectSelect, projectModal, projectForm, cancelProjectBtn;
let rotationProgress, progressBar, progressText, remainingTime;

// Status-Variablen
let tellerPosition = 0; // Speichert die aktuelle Position des Tellers
let positionLost = false; // Wird auf true gesetzt, wenn die Position unsicher ist

// Timer für die regelmäßige Speicherung der Position
let positionSyncTimer = null;

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

// Initialisierung nach Seitenladung
document.addEventListener('DOMContentLoaded', function() {
    debug("DOM geladen, initialisiere Anwendung...");
    
    // Status des Debug-Modus prüfen
    checkDebugMode();
    
    // Projekt-ID aus dem body-Attribut holen
    const projectId = document.body.getAttribute('data-project-id');
    if (projectId) {
        currentProjectId = projectId;
        debug(`Projekt-ID aus HTML geladen: ${currentProjectId}`);
    }
    
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
    
    // UI-Elemente laden
    startBtn = document.getElementById('startBtn');
    stopBtn = document.getElementById('stopBtn');
    rotateBtn = document.getElementById('rotateBtn');
    homeBtn = document.getElementById('homeBtn');
    projectPositionBtn = document.getElementById('projectPositionBtn');
    
    angleInput = document.getElementById('angleInput');
    intervalInput = document.getElementById('intervalInput');
    rotationTimeInput = document.getElementById('rotationTimeInput');
    
    currentPositionDisplay = document.getElementById('currentPosition');
    savedProjectPositionDisplay = document.getElementById('savedProjectPosition');
    rotationStatus = document.getElementById('rotationStatus');
    imagePreview = document.getElementById('imagePreview');
    
    projectSelect = document.getElementById('projectSelect');
    projectModal = document.getElementById('projectModal');
    projectForm = document.getElementById('projectForm');
    cancelProjectBtn = document.getElementById('cancelProject');
    
    rotationProgress = document.getElementById('rotationProgress');
    progressBar = document.getElementById('progressBar');
    progressText = document.getElementById('progressText');
    remainingTime = document.getElementById('remainingTime');

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
    
    // Starte Timer für regelmäßige Positionssynchronisierung
    startPositionSyncTimer();
    
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
                    projectPositionBtn.disabled = false;
                    projectPositionBtn.classList.remove('btn-secondary');
                    projectPositionBtn.classList.add('btn-info');
                }
                
                // Prüfe, ob es ein neu geladenes Projekt ist
                const lastLoadedProject = localStorage.getItem('lastLoadedProject');
                if (lastLoadedProject !== currentProjectId) {
                    debug(`Neues Projekt geladen (${currentProjectId}), früheres Projekt war: ${lastLoadedProject || 'keins'}`);
                    
                    // Aktuelles Projekt als letztes verwendetes Projekt speichern
                    localStorage.setItem('lastLoadedProject', currentProjectId);
                    
                    // Bei neuem Projekt immer zur Heimposition fahren, unabhängig davon ob Fotos existieren
                    debug("Neues Projekt ausgewählt. Fahre zur Heimposition.");
                    showStatus("Neues Projekt geladen. Fahre zur Heimposition (0°) bevor die 360°-Aufnahme startet...", 'info');
                    
                    // Fahre zur Heimposition und setze dann fort
                    moveToHomePositionAndContinue(angle);
                    return;
                }
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

    // Prüfen, ob es ein neues/frisches Projekt ist
    checkProjectIsNewAndContinue(angle);
}

/**
 * Prüft, ob das aktuelle Projekt ein neues/frisches Projekt ist
 * und setzt die Sequenz entsprechend fort
 * @param {number} angle - Der eingestellte Winkel für die Rotation
 */
function checkProjectIsNewAndContinue(angle) {
    // API-Anfrage, um Projektdaten zu laden
    fetch(`/api/project/${currentProjectId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
                }
                throw new Error(`Server-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(project => {
            debug(`Projektdaten geladen: ${JSON.stringify(project)}`);
            
            // Prüfen, ob bereits Fotos im Projekt vorhanden sind
            const existingPhotos = project.photos || [];
            debug(`Anzahl vorhandener Fotos im Projekt: ${existingPhotos.length}`);
            
            // Prüfen, ob das letzte Projekt-Datum im localStorage gespeichert ist
            const lastUsedProject = localStorage.getItem('lastUsedProject');
            const isNewProjectSession = lastUsedProject !== currentProjectId;
            
            if (isNewProjectSession) {
                debug(`Neues Projekt ausgewählt (${currentProjectId}), früheres Projekt war: ${lastUsedProject || 'keins'}`);
                
                // Aktuelles Projekt als letztes verwendetes Projekt speichern
                localStorage.setItem('lastUsedProject', currentProjectId);
                
                // Bei neuem Projekt immer zur Heimposition fahren, unabhängig davon ob Fotos existieren
                debug("Neues Projekt ausgewählt. Fahre zur Heimposition.");
                showStatus("Neues Projekt geladen. Fahre zur Heimposition (0°) bevor die 360°-Aufnahme startet...", 'info');
                
                // Fahre zur Heimposition und setze dann fort
                moveToHomePositionAndContinue(angle);
                return;
            }
            
            // Falls es kein neues Projekt ist oder keine Heimfahrt nötig ist, prüfe, ob Fotos existieren
            if (existingPhotos.length > 0) {
                // Sortiere Fotos nach Winkel
                existingPhotos.sort((a, b) => parseFloat(a.angle) - parseFloat(b.angle));
                
                // Finde das Foto mit dem höchsten Winkel
                const lastPhoto = existingPhotos[existingPhotos.length - 1];
                const lastAngle = parseFloat(lastPhoto.angle || 0);
                
                debug(`Letztes vorhandenes Foto bei ${lastAngle}°`);
                
                // Berechne den nächsten Winkel für das Foto
                const nextAngle = (lastAngle + angle) % 360;
                
                // Anzahl der bereits vorhandenen Fotos
                const existingCount = existingPhotos.length;
                
                debug(`Fahre zur nächsten Position: ${nextAngle}° (nach dem ${existingCount}. Foto)`);
                showStatus(`${existingCount} Fotos gefunden. Fahre zur nächsten Position (${nextAngle}°)...`, 'info');
                
                // Rotieren zur nächsten Position bevor die Sequenz fortgesetzt wird
                rotateToSpecificAngle(nextAngle, () => {
                    // Nach der Rotation die Sequenz starten
                    continueSequenceAfterRotation(angle, existingCount);
                });
            } else {
                // Keine vorhandenen Fotos - normale Sequenz starten
                debug("Keine vorhandenen Fotos gefunden. Starte neue Sequenz.");
                continueNormalSequence(angle);
            }
        })
        .catch(error => {
            debug(`Fehler beim Laden der Projektdaten: ${error}`);
            alert(`Fehler: ${error.message}`);
            
            // Fallback: Starte normale Sequenz
            continueNormalSequence(angle);
        });
}

/**
 * Bewegt den Teller zur Heimposition und setzt dann die Rotation fort
 * @param {number} angle - Der eingestellte Winkel für die Rotation
 */
function moveToHomePositionAndContinue(angle) {
    // Bewege zur Heimposition
    rotateToSpecificAngle(0, () => {
        debug("Teller zur Heimposition bewegt. Starte nun die Aufnahme.");
        showStatus("Heimposition erreicht (0°). Starte 360°-Aufnahme...", 'success');
        
        // Starte normale Sequenz von 0° aus
        continueNormalSequence(angle);
    });
}

/**
 * Setzt die Sequenz fort, nachdem der Teller zur spezifischen Position gedreht wurde
 * @param {number} angle - Der Drehwinkel pro Schritt
 * @param {number} existingPhotos - Anzahl der bereits vorhandenen Fotos
 */
function continueSequenceAfterRotation(angle, existingPhotos) {
    // Berechne Gesamtschritte basierend auf dem eingestellten Winkel
    totalSteps = Math.floor(360 / angle);
    
    // Setze den aktuellen Schritt auf die Anzahl der vorhandenen Fotos
    currentStep = existingPhotos;
    
    debug(`Setze Sequenz fort bei Schritt ${currentStep}/${totalSteps} (${existingPhotos} Fotos vorhanden)`);
    
    // UI aktualisieren
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    if (rotateBtn) rotateBtn.disabled = true;
    if (homeBtn) homeBtn.disabled = true;
    
    isRotating = true;
    
    // Nehme Foto an der aktuellen Position auf
    takePhotoForSequence();
}

/**
 * Führt eine normale Sequenz ohne vorhandene Fotos durch
 * @param {number} angle - Der Drehwinkel pro Schritt
 */
function continueNormalSequence(angle) {
    // Bei einem neuen Projekt immer den gespeicherten Fortschritt löschen
    const lastUsedProject = localStorage.getItem('lastUsedProject');
    const isNewProjectSession = lastUsedProject !== currentProjectId;
    
    if (isNewProjectSession) {
        debug("Neues Projekt erkannt, lösche gespeicherten Fortschritt");
        localStorage.removeItem('lastSequenceStep');
        localStorage.removeItem('lastSequenceTotalSteps');
    }
    
    // Prüfen, ob eine pausierte Aufnahme fortgesetzt werden soll
    const savedStep = parseInt(localStorage.getItem('lastSequenceStep') || "0");
    const savedTotalSteps = parseInt(localStorage.getItem('lastSequenceTotalSteps') || "0");
    
    debug(`Gespeicherter Fortschritt gefunden: Schritt ${savedStep}/${savedTotalSteps}`);
    
    if (!isNewProjectSession && !isNaN(savedStep) && !isNaN(savedTotalSteps) && savedStep > 0 && savedStep < savedTotalSteps) {
        if (confirm(`Möchten Sie die gespeicherte Position übernehmen?`)) {
            // Werte wiederherstellen
            currentStep = savedStep;
            totalSteps = savedTotalSteps;
            debug(`Setze pausierte Aufnahme fort bei Schritt ${currentStep}/${totalSteps}`);
            
            // UI aktualisieren und Sequenz direkt starten
            prepareUIForRotation();
            takePhotoForSequence();
            return;
        } else {
            // Neue Aufnahme starten, aber erst zur Heimposition fahren
            localStorage.removeItem('lastSequenceStep');
            localStorage.removeItem('lastSequenceTotalSteps');
            totalSteps = Math.floor(360 / angle);
            currentStep = 0;
            debug(`Neue Aufnahme gewählt. Fahre erst zur Heimposition (0°).`);
            
            // Zur Heimposition fahren und dann von dort starten
            moveToHomePositionAndStart(angle);
            return;
        }
    } else {
        // Prüfen, ob Tellerposition von 0° abweicht
        if (tellerPosition !== 0) {
            debug(`Tellerposition (${tellerPosition}°) weicht von Heimposition ab. Fahre zur Heimposition.`);
            moveToHomePositionAndStart(angle);
            return;
        }
        
        // Neue Aufnahme starten
        localStorage.removeItem('lastSequenceStep');
        localStorage.removeItem('lastSequenceTotalSteps');
        const interval = parseInt(intervalInput.value) || 5;
        totalSteps = Math.floor(360 / angle);
        currentStep = 0;
        debug(`Starte 360° Rotation mit ${totalSteps} Schritten, Winkel=${angle}°, Intervall=${interval}s`);
        
        // UI aktualisieren und Sequenz starten
        prepareUIForRotation();
        takePhotoForSequence();
    }
}

/**
 * Bereitet die UI für eine Rotation vor
 */
function prepareUIForRotation() {
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
}

/**
 * Fährt zur Heimposition und startet dann eine neue Aufnahmesequenz
 * @param {number} angle - Der Drehwinkel pro Schritt
 */
function moveToHomePositionAndStart(angle) {
    showStatus("Fahre zur Heimposition (0°) vor Beginn der Aufnahme...", 'info');
    
    // Fahre zur Heimposition und starte dann
    rotateToSpecificAngle(0, () => {
        debug("Heimposition erreicht. Starte neue Aufnahmesequenz.");
        showStatus("Heimposition erreicht (0°). Starte neue Aufnahmesequenz...", 'success');
        
        // Neue Werte setzen
        totalSteps = Math.floor(360 / angle);
        currentStep = 0;
        
        // UI aktualisieren
        prepareUIForRotation();
        
        // Erstes Foto aufnehmen
        takePhotoForSequence();
    });
}

/**
 * Dreht den Teller zu einem bestimmten Winkel und ruft dann den Callback auf
 * @param {number} targetAngle - Der Zielwinkel
 * @param {Function} callback - Funktion, die nach erfolgreicher Drehung aufgerufen wird
 */
function rotateToSpecificAngle(targetAngle, callback) {
    debug(`Drehe zu spezifischem Winkel: ${targetAngle}°`);
    
    // Berechne kürzesten Weg zum Zielwinkel
    let degreesToMove = 0;
    
    // Da der Motor nur vorwärts drehen kann, immer im Uhrzeigersinn weiterdrehen
    if (targetAngle > tellerPosition) {
        degreesToMove = targetAngle - tellerPosition;
    } else {
        degreesToMove = 360 - (tellerPosition - targetAngle);
    }
    
    debug(`Drehung um ${degreesToMove}° erforderlich, um Winkel ${targetAngle}° zu erreichen`);
    
    // Formular-Daten vorbereiten
    const formData = new FormData();
    formData.append('degrees', degreesToMove);
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');
    formData.append('target_angle', targetAngle); // Zielwinkel mitgeben

    // Rotationsdauer
    const rotationTime = parseInt(rotationTimeInput?.value || 15);
    formData.append('rotation_time', rotationTime);
    
    // Berechne die erwartete Zeit für diese spezifische Bewegung
    const estimatedTime = Math.ceil((degreesToMove / 360) * rotationTime * 1.2);
    
    // Zeige Fortschrittsbalken
    const startTime = new Date();
    const endTime = new Date(startTime.getTime() + (estimatedTime * 1000));
    showAndUpdateProgressBar(startTime, endTime, `Drehe zu Position ${targetAngle}° - ${degreesToMove}°`);
    
    // API-Anfrage zum Drehen des Tellers
    fetch('/rotate', {
        method: 'POST',
        body: formData,
        timeout: (estimatedTime + 5) * 1000
    })
    .then(response => {
        if (!response.ok) {
            hideProgressBar();
            if (response.status === 404) {
                throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
            }
            throw new Error(`Server-Fehler: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        hideProgressBar();
        if (data.status === 'success') {
            // Aktualisiere die Tellerposition auf den neuen Wert
            tellerPosition = targetAngle;
            updatePositionDisplay(targetAngle, false);
            showStatus(`Teller wurde auf Position ${targetAngle}° gedreht`, 'success');
            
            // Rufe den Callback auf
            if (typeof callback === 'function') {
                callback();
            }
        } else {
            debug(`Fehler bei der Rotation: ${data.error}`);
            showStatus(`Fehler bei der Rotation: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        hideProgressBar();
        debug(`Fehler bei der Rotation zu spezifischem Winkel: ${error}`);
        showStatus(`Fehler: ${error.message}`, 'error');
    });
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

            // Position im Projekt speichern
            syncProjectPosition(currentAngle);
            debug(`Position nach Fotoaufnahme im Projekt gespeichert: ${currentAngle}°`);

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
    
    // Benutze die vom Benutzer eingegebenen Werte für die Rotationszeit oder Standardwert 15
    const rotationTime = parseInt(rotationTimeInput?.value || 15);
    // Berechne die erwartete Zeit für diese spezifische Bewegung (plus etwas Puffer)
    const estimatedTimeForMovement = Math.ceil((degreesToMove / 360) * rotationTime * 1.5); // 50% Puffer
    
    debug(`Geschätzte Zeit für Drehung um ${degreesToMove}°: ca. ${estimatedTimeForMovement} Sekunden`);
    
    // Setze die Startzeit und starte den Timer
    homePositionStartTime = new Date();
    
    // Berechne die erwartete Endzeit
    const expectedEndTime = new Date(homePositionStartTime.getTime() + (estimatedTimeForMovement * 1000));
    rotationEndTime = expectedEndTime;
    
    // Zeige Fortschrittsbalken
    showAndUpdateProgressBar(
        homePositionStartTime, 
        expectedEndTime, 
        `Fahre zur Heimposition (0°) - ${degreesToMove}°`
    );
    
    // Starte auch den ursprünglichen Timer (für Debug-Ausgaben)
    startHomePositionTimer();
    
    debug(`Fahre zur Heimposition: ${degreesToMove}° in Richtung vorwärts`);
    showStatus(`Fahre zur Heimposition (0°)... (ca. ${estimatedTimeForMovement} Sekunden)`, 'info');
    
    // API-Anfrage zum Drehen des Tellers
    const formData = new FormData();
    formData.append('degrees', degreesToMove);
    formData.append('direction', 'cw'); // Immer im Uhrzeigersinn (cw) drehen
    
    // Stelle sicher, dass eine gültige Projekt-ID verwendet wird
    if (!currentProjectId) {
        debug("Keine Projekt-ID vorhanden, kann nicht zur Heimposition fahren");
        showStatus('Bitte wählen Sie zuerst ein Projekt aus.', 'warning');
        stopHomePositionTimer(); // Timer stoppen, falls ein Fehler auftritt
        hideProgressBar(); // Fortschrittsbalken ausblenden
        return;
    }
    
    formData.append('project_id', currentProjectId);
    formData.append('mode', 'rotate_only');
    formData.append('reset_position', 'true'); // Spezielle Flagge für Heimposition
    formData.append('rotation_time', rotationTime); // Übergebe die Rotationszeit an den Server
    
    // URL direkt definieren, um sicherzustellen, dass wir den richtigen Endpunkt ansprechen
    const url = window.location.protocol + '//' + window.location.host + '/rotate';
    debug(`Sende Home-Position Anfrage an: ${url} mit ${degreesToMove}° Drehung, Rotationszeit: ${rotationTime}s`);
    
    fetch(url, {
        method: 'POST',
        body: formData,
        // Setze längeren Timeout basierend auf der erwarteten Bewegungszeit
        timeout: (estimatedTimeForMovement + 10) * 1000 // In Millisekunden + 10 Sekunden Puffer
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
        hideProgressBar(); // Fortschrittsbalken ausblenden
        debug("Heimpositionierung erfolgreich");
        showStatus('Teller erfolgreich auf Heimposition (0°) gesetzt.', 'success');
        tellerPosition = 0; // Setze lokale Position auf 0
        saveTurntablePosition(0); // Speichere in localStorage mit der neuen Funktion
        updatePositionDisplay(0, false); // false, da wir hier nicht mit dem Projekt synchronisieren wollen
        
        // Zusätzlich: Setze alle Foto-Zähler zurück
        currentStep = 0;
        capturedPhotos = [];
        totalSteps = 0;
        
        // Aktualisiere die Statusanzeige, um falsche Foto-Informationen zu vermeiden
        document.getElementById('rotationStatus').innerHTML = ''; // Leere die Statusanzeige
        debug("Alle Foto-Zähler wurden zurückgesetzt");
    })
    .catch(error => {
        stopHomePositionTimer(); // Timer stoppen bei Fehler
        hideProgressBar(); // Fortschrittsbalken ausblenden
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
            
            // Wenn die Endzeit erreicht oder überschritten wurde, stoppe den Timer
            if (currentTime >= rotationEndTime) {
                clearInterval(homePositionTimer);
                
                if (rotationProgress) {
                    setTimeout(() => {
                        rotationProgress.classList.add('hidden');
                        rotationProgress.classList.remove('visible');
                    }, 1000); // Eine Sekunde warten, damit der Benutzer sieht, dass 100% erreicht wurden
                }
                
                return;
            }
            
            // Berechne verstrichene Zeit und verbleibende Zeit
            const elapsedSeconds = Math.floor((currentTime - homePositionStartTime) / 1000);
            
            // Schätze die aktuelle Position basierend auf der verstrichenen Zeit
            // Annahme: gleichmäßige Drehung über die Zeit (kann in der Realität abweichen)
            // Berechne Rotationsgeschwindigkeit (Grad pro Sekunde)
            
            // Benutze den vom Benutzer eingegebenen Wert für die Rotationszeit oder Standardwert 15
            const totalRotationTimeEstimate = parseInt(rotationTimeInput?.value || 15);
            
            debug(`Verwende Rotationszeit: ${totalRotationTimeEstimate} Sekunden für 360°`);
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
    rotationEndTime = null; // Zurücksetzen der Endzeit
}

/**
 * Dreht den Teller zur Projektposition
 */
function moveToProjectPosition() {
    if (!currentProjectId) {
        debug("Kein Projekt ausgewählt, kann nicht zur Projektposition fahren");
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }
    
    // Prüfen, ob bereits eine Rotation läuft
    if (isRotating) {
        debug("Rotation läuft bereits, ignoriere Anfrage zur Projektposition");
        alert('Eine Rotation ist bereits aktiv. Bitte stoppen Sie die aktuelle Rotation zuerst.');
        return;
    }
    
    // Projektposition laden
    fetch(`/api/project/${currentProjectId}`)
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error(`Projekt mit ID ${currentProjectId} wurde nicht gefunden`);
                }
                throw new Error(`Server-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(project => {
            if (project && 'current_position' in project) {
                const targetPosition = parseFloat(project.current_position);
                debug(`Fahre zur Projektposition: ${targetPosition}°`);
                
                // Statusmeldung anzeigen
                showStatus(`Fahre zur Projektposition (${targetPosition}°)...`, 'info');
                
                // Rotieren zur Projektposition
                rotateToSpecificAngle(targetPosition, () => {
                    showStatus(`Teller ist nun an der Projektposition (${targetPosition}°)`, 'success');
                });
            } else {
                throw new Error('Keine Projektposition definiert.');
            }
        })
        .catch(error => {
            debug(`Fehler beim Fahren zur Projektposition: ${error}`);
            showStatus(`Fehler: ${error.message}`, 'error');
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
    
    // Synchronisiere mit dem Projekt, wenn gewünscht
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
 * Zeigt den Fortschrittsbalken für die Rotation an und aktualisiert ihn
 * @param {Date} startTime - Startzeitpunkt
 * @param {Date} endTime - Erwarteter Endzeitpunkt
 * @param {string} message - Anzuzeigende Nachricht
 */
function showAndUpdateProgressBar(startTime, endTime, message) {
    // Fortschrittsbalken anzeigen
    if (rotationProgress) {
        rotationProgress.classList.remove('hidden');
        rotationProgress.classList.add('visible');
    }
    
    // Text setzen
    if (progressText) {
        progressText.textContent = message || 'Drehung läuft...';
    }
    
    // Berechne Gesamtzeit in Millisekunden
    const totalTime = endTime - startTime;
    
    // Starte Aktualisierungstimer
    const updateTimer = setInterval(() => {
        const now = new Date();
        
        // Wenn die Endzeit erreicht oder überschritten wurde, stoppe den Timer
        if (now >= endTime) {
            clearInterval(updateTimer);
            
            if (rotationProgress) {
                setTimeout(() => {
                    rotationProgress.classList.add('hidden');
                    rotationProgress.classList.remove('visible');
                }, 1000); // Eine Sekunde warten, damit der Benutzer sieht, dass 100% erreicht wurden
            }
            
            return;
        }
        
        // Berechne verstrichene Zeit und verbleibende Zeit
        const elapsedTime = now - startTime;
        const remainingTimeMs = endTime - now;
        
        // Berechne Fortschritt in Prozent
        const progressPercent = Math.min(100, Math.round((elapsedTime / totalTime) * 100));
        
        // Aktualisiere Fortschrittsbalken
        if (progressBar) {
            progressBar.style.width = progressPercent + '%';
            progressBar.textContent = progressPercent + '%';
        }
        
        // Aktualisiere verbleibende Zeit
        if (remainingTime) {
            const minutes = Math.floor(remainingTimeMs / 60000);
            const seconds = Math.floor((remainingTimeMs % 60000) / 1000);
            remainingTime.textContent = `Verbleibende Zeit: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
        }
    }, 200); // Aktualisiere alle 200ms
    
    // Speichere Timer-ID für mögliche spätere Bereinigung
    return updateTimer;
}

/**
 * Versteckt den Fortschrittsbalken
 */
function hideProgressBar() {
    if (rotationProgress) {
        rotationProgress.classList.add('hidden');
        rotationProgress.classList.remove('visible');
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

/**
 * Überprüft, ob die Anwendung im Debug-Modus läuft
 */
function checkDebugMode() {
    // Anfrage an den Server senden
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            const isDebugMode = data.debug_mode || false;
            debug(`Anwendung läuft ${isDebugMode ? 'mit' : 'ohne'} Debug-Parameter (debug_mode: ${isDebugMode})`);
            
            // Optional: Visuelles Feedback für Debug-Modus anzeigen
            if (isDebugMode) {
                // Füge Klasse zum body-Element hinzu
                document.body.classList.add('debug-active');
                
                // Zeige kleine Meldung an
                const debugIndicator = document.createElement('div');
                debugIndicator.className = 'debug-indicator';
                debugIndicator.textContent = 'DEBUG';
                document.body.appendChild(debugIndicator);
            }
        })
        .catch(error => {
            console.error('Fehler beim Abrufen des Debug-Status:', error);
        });
}

/**
 * Startet einen Timer, der regelmäßig die aktuelle Position im Projekt speichert
 */
function startPositionSyncTimer() {
    if (positionSyncTimer) {
        clearInterval(positionSyncTimer);
    }
    
    // Synchronisiere alle 5 Sekunden die Position mit dem Projekt
    positionSyncTimer = setInterval(() => {
        if (currentProjectId && !isRotating) {
            debug("Regelmäßige Synchronisierung der Tellerposition");
            syncProjectPosition(tellerPosition);
        }
    }, 5000); // 5 Sekunden
    
    debug("Timer für regelmäßige Positionssynchronisierung gestartet (alle 5 Sekunden)");
}

/**
 * Stoppt den Timer für die Positionssynchronisierung
 */
function stopPositionSyncTimer() {
    if (positionSyncTimer) {
        clearInterval(positionSyncTimer);
        positionSyncTimer = null;
        debug("Timer für Positionssynchronisierung gestoppt");
    }
}
