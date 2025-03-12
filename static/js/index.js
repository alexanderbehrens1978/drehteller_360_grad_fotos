/**
 * index.js
 * JavaScript für die Startseite und Drehteller-Steuerung
 */

// Globale Variablen
let currentProjectId = null;
let capturedPhotos = [];
let isRotating = false;

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

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    // Initialisiere die Projekt-ID aus den Datenelementen
    currentProjectId = document.body.getAttribute('data-project-id') || '';
    
    // Projekte laden, wenn kein Projekt ausgewählt ist
    if (!currentProjectId && projectSelect) {
        loadProjects();
        
        // Event-Listener für Projekt-Auswahl
        projectSelect.addEventListener('change', function() {
            const selectedValue = this.value;
            
            if (selectedValue === 'new') {
                // Modal für Projekterstellung anzeigen
                showProjectModal();
            } else if (selectedValue) {
                // Zu einem bestehenden Projekt navigieren
                window.location.href = '/?project_id=' + selectedValue;
            }
        });
    }
    
    // Event-Listener für Buttons
    if (startBtn) startBtn.addEventListener('click', startRotation);
    if (stopBtn) stopBtn.addEventListener('click', stopRotation);
    if (rotateBtn) rotateBtn.addEventListener('click', singleRotation);
    
    // Event-Listener für das Projektformular
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createProject();
            return false;
        });
    }
    
    // Event-Listener für den Abbrechen-Button im Modal
    if (cancelProjectBtn) {
        cancelProjectBtn.addEventListener('click', function(e) {
            e.preventDefault();
            hideProjectModal();
        });
    }
    
    // Wenn kein Projekt ausgewählt ist, Modal nicht automatisch anzeigen
    // (Dies würde die Benutzer zu sehr einschränken)
});

// Projekte laden
function loadProjects() {
    fetch('/api/projects')
        .then(response => response.json())
        .then(projects => {
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
            projectSelect.innerHTML = '<option value="">Fehler beim Laden der Projekte</option>';
        });
}

// Projekt-Modal anzeigen
function showProjectModal() {
    if (projectModal) {
        projectModal.style.display = 'flex';
    }
}

// Projekt-Modal ausblenden
function hideProjectModal() {
    if (projectModal) {
        projectModal.style.display = 'none';
        
        // Dropdown zurücksetzen
        if (projectSelect) {
            projectSelect.value = currentProjectId || "";
        }
    }
}

// Neues Projekt erstellen
function createProject() {
    const formData = new FormData(projectForm);
    
    fetch('/projects/create', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.redirected) {
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
        hideProjectModal();
    });
}


// Einzelne Rotation und Fotoaufnahme
function singleRotation() {
    if (isRotating) return;
    
    // Überprüfen, ob ein Projekt ausgewählt wurde
    if (!currentProjectId) {
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }
    
    const angle = parseInt(angleInput.value) || 15;
    
    isRotating = true;
    if (rotateBtn) rotateBtn.disabled = true;
    
    // Statusmeldung anzeigen
    if (rotationStatus) {
        rotationStatus.textContent = "Drehe und nehme Foto auf...";
        rotationStatus.style.display = "block";
    }
    
    // Formular-Daten vorbereiten
    const formData = new FormData();
    formData.append('degrees', angle);
    formData.append('project_id', currentProjectId);
    
    // Rotation und Fotoaufnahme starten
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
                angle: data.angle
            });
            
            // Bild anzeigen
            displayImage(data.photo, data.angle);
            
            // Statusmeldung aktualisieren
            if (rotationStatus) {
                rotationStatus.textContent = `Foto aufgenommen bei ${data.angle}°`;
                setTimeout(() => {
                    rotationStatus.style.display = "none";
                }, 3000);
            }
            
            console.log(`Erfolgreich gedreht und Foto aufgenommen: ${data.photo}`);
        } else {
            console.error('Fehler:', data.error);
            alert(`Fehler bei der Rotation: ${data.error}`);
            
            // Statusmeldung aktualisieren
            if (rotationStatus) {
                rotationStatus.textContent = `Fehler: ${data.error}`;
            }
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert('Netzwerkfehler beim Drehen des Tellers.');
        
        // Statusmeldung aktualisieren
        if (rotationStatus) {
            rotationStatus.textContent = `Netzwerkfehler: ${error.message}`;
        }
    })
    .finally(() => {
        isRotating = false;
        if (rotateBtn) rotateBtn.disabled = false;
    });
}

// Zeigt ein Bild in der Vorschau an
function displayImage(imagePath, angle) {
    if (!imagePreview) return;
    
    // Bisherige Vorschau löschen
    imagePreview.innerHTML = '';
    
    // Bild-Element erstellen
    const img = document.createElement('img');
    img.src = imagePath;
    img.alt = `Foto bei ${angle}°`;
    img.className = 'captured-image';
    
    // Winkel-Anzeige erstellen
    const angleLabel = document.createElement('div');
    angleLabel.className = 'image-info';
    angleLabel.textContent = `${angle}°`;
    
    // Container erstellen und Elemente hinzufügen
    const container = document.createElement('div');
    container.className = 'image-item';
    container.appendChild(img);
    container.appendChild(angleLabel);
    
    // Container zur Vorschau hinzufügen
    imagePreview.appendChild(container);
}

// Automatische Rotation und Fotoaufnahme
function startRotation() {
    if (isRotating) return;
    
    // Überprüfen, ob ein Projekt ausgewählt wurde
    if (!currentProjectId) {
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }
    
    const angle = parseInt(angleInput.value) || 15;
    const interval = parseInt(intervalInput.value) || 5;
    const totalSteps = Math.floor(360 / angle);
    
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    isRotating = true;
    
    // Statusmeldung anzeigen
    if (rotationStatus) {
        rotationStatus.textContent = `Rotation gestartet: 0/${totalSteps} Schritte`;
        rotationStatus.style.display = "block";
    }
    
    // Startwert für den Fortschritt
    let currentStep = 0;
    
    // Funktion für jeden Rotationsschritt
    function rotateStep() {
        if (!isRotating) return;
        
        currentStep++;
        
        // Statusmeldung aktualisieren
        if (rotationStatus) {
            rotationStatus.textContent = `Rotation: ${currentStep}/${totalSteps} Schritte`;
        }
        
        // Formular-Daten vorbereiten
        const formData = new FormData();
        formData.append('degrees', angle);
        formData.append('project_id', currentProjectId);
        
        // Rotation und Fotoaufnahme durchführen
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
                    angle: currentStep * angle
                });
                
                // Bild anzeigen
                displayImage(data.photo, currentStep * angle);
                
                // Nächsten Schritt planen, wenn nicht fertig
                if (currentStep < totalSteps && isRotating) {
                    setTimeout(rotateStep, interval * 1000);
                } else {
                    completeRotation();
                }
            } else {
                console.error('Fehler:', data.error);
                alert(`Fehler bei der Rotation: ${data.error}`);
                stopRotation();
            }
        })
        .catch(error => {
            console.error('Netzwerkfehler:', error);
            alert('Netzwerkfehler beim Drehen des Tellers.');
            stopRotation();
        });
    }
    
    // Starte den ersten Schritt
    rotateStep();
}

// Beende die Rotation
function stopRotation() {
    isRotating = false;
    
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    
    if (rotationStatus) {
        rotationStatus.textContent = 'Rotation gestoppt';
        setTimeout(() => {
            rotationStatus.style.display = "none";
        }, 3000);
    }
}

// Rotation abschließen
function completeRotation() {
    stopRotation();
    
    if (rotationStatus) {
        rotationStatus.textContent = 'Rotation abgeschlossen!';
        setTimeout(() => {
            rotationStatus.style.display = "none";
        }, 3000);
    }
    
    // Nachfragen, ob ein 360°-Viewer erstellt werden soll
    if (confirm('Rotation abgeschlossen! Möchten Sie einen 360°-Viewer aus den aufgenommenen Fotos erstellen?')) {
        generateViewer();
    }
}

// 360°-Viewer generieren
function generateViewer() {
    // Überprüfe, ob genügend Fotos vorhanden sind
    if (capturedPhotos.length < 4) {
        alert('Es werden mindestens 4 Fotos für einen 360°-Viewer benötigt.');
        return;
    }
    
    // Anfrage zum Generieren des Viewers senden
    const requestData = {
        project_id: currentProjectId,
        photos: capturedPhotos.map(photo => photo.path)
    };
    
    fetch('/generate_360', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(`360°-Viewer erfolgreich erstellt! Sie werden weitergeleitet.`);
            // Zur Viewer-Seite weiterleiten
            window.location.href = data.url;
        } else {
            console.error('Fehler beim Generieren des Viewers:', data.error);
            alert(`Fehler beim Generieren des 360°-Viewers: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert('Netzwerkfehler beim Generieren des 360°-Viewers.');
    });
}
