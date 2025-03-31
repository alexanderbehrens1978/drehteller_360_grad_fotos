/**
 * turntable.js
 * JavaScript für die Drehtellersteuerung und Fotoaufnahme
 */

// Globale Variablen
let currentProjectId = null;
let capturedPhotos = [];
let isRotating = false;

// DOM-Elemente
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const rotateBtn = document.getElementById('rotateBtn');
const imagePreview = document.getElementById('imagePreview');
const angleInput = document.getElementById('angleInput');
const intervalInput = document.getElementById('intervalInput');
const projectSelect = document.getElementById('projectSelect');

// Initialisierung
document.addEventListener('DOMContentLoaded', function() {
    // Projekte laden
    loadProjects();
    
    // Event-Listener für Buttons
    if (startBtn) startBtn.addEventListener('click', startRotation);
    if (stopBtn) stopBtn.addEventListener('click', stopRotation);
    if (rotateBtn) rotateBtn.addEventListener('click', singleRotation);
    
    // Projekt-ID aus URL-Parameter lesen, falls vorhanden
    const urlParams = new URLSearchParams(window.location.search);
    const projectIdParam = urlParams.get('project_id');
    if (projectIdParam) {
        currentProjectId = projectIdParam;
        if (projectSelect) projectSelect.value = projectIdParam;
    }
});

/**
 * Lädt verfügbare Projekte und füllt das Dropdown-Menü
 */
function loadProjects() {
    if (!projectSelect) return;
    
    fetch('/api/projects')
        .then(response => response.json())
        .then(data => {
            projectSelect.innerHTML = '<option value="">Bitte wählen...</option>';
            data.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.name;
                projectSelect.appendChild(option);
            });
            
            // Wenn bereits ein Projekt ausgewählt wurde, setze es im Dropdown
            if (currentProjectId) {
                projectSelect.value = currentProjectId;
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Projekte:', error);
            alert('Fehler beim Laden der Projekte. Bitte versuchen Sie es später erneut.');
        });
        
    // Event-Listener für Projekt-Auswahl
    projectSelect.addEventListener('change', function() {
        currentProjectId = this.value;
    });
}

/**
 * Startet eine einzelne Rotation und nimmt ein Foto auf
 */
function singleRotation() {
    if (isRotating) return;
    
    // Überprüfe, ob ein Projekt ausgewählt wurde
    if (!currentProjectId) {
        alert('Bitte wählen Sie zuerst ein Projekt aus.');
        return;
    }
    
    const angle = parseInt(angleInput.value) || 15;
    
    isRotating = true;
    if (rotateBtn) rotateBtn.disabled = true;
    
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
            
            console.log(`Erfolgreich gedreht und Foto aufgenommen: ${data.photo}`);
        } else {
            console.error('Fehler:', data.error);
            alert(`Fehler bei der Rotation: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert('Netzwerkfehler beim Drehen des Tellers.');
    })
    .finally(() => {
        isRotating = false;
        if (rotateBtn) rotateBtn.disabled = false;
    });
}

/**
 * Zeigt ein Bild in der Vorschau an
 * @param {string} imagePath - Pfad zum Bild
 * @param {number} angle - Winkel, bei dem das Bild aufgenommen wurde
 */
function displayImage(imagePath, angle) {
    if (!imagePreview) return;
    
    // Bildpfad korrigieren, um sicherzustellen, dass er zum Projektverzeichnis führt
    const imgUrl = getImageUrl(imagePath, currentProjectId);
    
    // Bisherige Vorschau löschen
    imagePreview.innerHTML = '';
    
    // Bild-Container erstellen
    const container = document.createElement('div');
    container.className = 'image-container';
    
    // Bild-Element erstellen
    const img = document.createElement('img');
    img.src = imgUrl;
    img.alt = `Foto bei ${angle}°`;
    img.className = 'captured-image';
    
    // Winkelbeschriftung hinzufügen
    const angleLabel = document.createElement('div');
    angleLabel.className = 'angle-label';
    angleLabel.textContent = `${angle}°`;
    
    // Elemente zum Container hinzufügen
    container.appendChild(img);
    container.appendChild(angleLabel);
    
    // Container zur Vorschau hinzufügen
    imagePreview.appendChild(container);
}

/**
 * Korrigiert Bildpfade für Projektbilder
 * @param {string} imagePath - Der ursprüngliche Bildpfad
 * @param {string} projectId - Die Projekt-ID
 * @returns {string} Der korrigierte Bildpfad
 */
function getImageUrl(imagePath, projectId) {
    // Falls der Pfad bereits mit "/projects" beginnt, nichts ändern
    if (imagePath.startsWith('/projects/')) {
        return imagePath;
    }
    
    // Falls der Pfad bereits einen Projektpfad enthält
    if (imagePath.includes('/project/')) {
        return imagePath;
    }
    
    // Bei relativen Pfaden den vollständigen Pfad erstellen
    if (imagePath.startsWith('/')) {
        // Bei absoluten Pfaden den Projektteil vorne anfügen
        return `/projects/image/${projectId}${imagePath}`;
    } else {
        // Bei vollständig relativen Pfaden nur den Dateinamen verwenden
        return `/projects/image/${projectId}/${imagePath.split('/').pop()}`;
    }
}

/**
 * Startet automatische Rotation und Fotoaufnahme
 */
function startRotation() {
    if (isRotating) return;
    
    // Überprüfe, ob ein Projekt ausgewählt wurde
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
    
    // Status-Element erstellen
    const statusEl = document.createElement('div');
    statusEl.id = 'rotationStatus';
    statusEl.className = 'status-message';
    statusEl.textContent = `Rotation gestartet: 0/${totalSteps} Schritte`;
    document.querySelector('.controls').appendChild(statusEl);
    
    // Startwert für den Fortschritt
    let currentStep = 0;
    
    // Funktion für jeden Rotationsschritt
    function rotateStep() {
        if (!isRotating) return;
        
        currentStep++;
        statusEl.textContent = `Rotation: ${currentStep}/${totalSteps} Schritte`;
        
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

/**
 * Beendet die automatische Rotation
 */
function stopRotation() {
    isRotating = false;
    
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    
    const statusEl = document.getElementById('rotationStatus');
    if (statusEl) {
        statusEl.textContent = 'Rotation gestoppt';
        setTimeout(() => {
            statusEl.remove();
        }, 3000);
    }
}

/**
 * Schließt die Rotation ab und bietet die Generierung eines 360°-Viewers an
 */
function completeRotation() {
    stopRotation();
    
    const statusEl = document.getElementById('rotationStatus');
    if (statusEl) {
        statusEl.textContent = 'Rotation abgeschlossen!';
        statusEl.className = 'status-message success';
    }
    
    // Option zum Generieren des 360°-Viewers anbieten
    const createViewerBtn = document.createElement('button');
    createViewerBtn.textContent = '360° Viewer generieren';
    createViewerBtn.className = 'btn btn-primary mt-3';
    createViewerBtn.addEventListener('click', () => {
        generateViewer();
    });
    
    document.querySelector('.controls').appendChild(createViewerBtn);
}

/**
 * Generiert einen 360°-Viewer aus den aufgenommenen Fotos
 */
function generateViewer() {
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
    console.log(`Sende Viewer-Erstellungsanfrage an: ${url}`);
    
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
        console.log("Antwort vom Server:", data);
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
            console.error('Fehler beim Generieren des Viewers:', data.error || 'Unbekannter Fehler');
            alert(`Fehler beim Generieren des 360°-Viewers: ${data.error || 'Unbekannter Fehler'}`);
        }
    })
    .catch(error => {
        console.error('Netzwerkfehler:', error);
        alert('Netzwerkfehler beim Generieren des 360°-Viewers: ' + error.message);
    });
}
