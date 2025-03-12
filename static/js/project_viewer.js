/**
 * project_viewer.js
 * JavaScript-Code für die 360°-Viewer-Funktionalität
 */

// DOM-Elemente
const imageViewer = document.getElementById('image-viewer');
const currentImage = document.getElementById('current-image');
const sessionSelect = document.getElementById('session-select');
const playbackSpeedInput = document.getElementById('playback-speed');
const playButton = document.getElementById('play-button');
const stopButton = document.getElementById('stop-button');
const zoomInButton = document.getElementById('zoom-in');
const zoomOutButton = document.getElementById('zoom-out');
const exportButton = document.getElementById('export-button');
const exportFormatSelect = document.getElementById('export-format');

// Viewer-Zustand
let currentSessionId = null;
let sessionImages = [];
let currentImageIndex = 0;
let isPlaying = false;
let playbackInterval = null;
let zoomLevel = 1;
let isDragging = false;
let startX = 0;
let dragSensitivity = 1; // Einstellbare Empfindlichkeit für die Drehung

// Sichert die ursprüngliche Bildgröße
let originalImageWidth = 0;
let originalImageHeight = 0;

/**
 * Initialisiert den Viewer mit den Projektdaten
 */
function initViewer() {
    // Standardmäßig die erste Session laden, wenn vorhanden
    if (projectData && projectData.sessions && projectData.sessions.length > 0) {
        currentSessionId = projectData.sessions[0].id;
        loadSession(currentSessionId);
    }
}

/**
 * Lädt die Bilder einer Session
 * 
 * @param {string} sessionId - ID der zu ladenden Session
 */
function loadSession(sessionId) {
    currentSessionId = sessionId;
    
    // Session-Daten finden
    const session = projectData.sessions.find(s => s.id === sessionId);
    if (!session) return;
    
    // Bilder sortieren nach Winkel
    sessionImages = Object.entries(session.photos)
        .map(([angle, path]) => ({
            angle: parseFloat(angle),
            path: path
        }))
        .sort((a, b) => a.angle - b.angle);
    
    // Erstes Bild laden
    currentImageIndex = 0;
    loadImage(currentImageIndex);
}

/**
 * Lädt ein Bild
 * 
 * @param {number} index - Index des zu ladenden Bildes
 */
function loadImage(index) {
    if (index < 0 || index >= sessionImages.length) return;
    
    const imagePath = sessionImages[index].path;
    
    // Relative Pfade in absolute Pfade umwandeln
    const absolutePath = imagePath.startsWith('/') 
        ? imagePath 
        : `/projects/image/${projectData.id}/${imagePath}`;
    
    currentImage.src = absolutePath;
    currentImageIndex = index;
    
    // Bildgröße für Zoom zurücksetzen
    currentImage.onload = function() {
        if (originalImageWidth === 0) {
            originalImageWidth = currentImage.naturalWidth;
            originalImageHeight = currentImage.naturalHeight;
        }
        
        // Zoom-Level anwenden
        applyZoom();
    };
}

/**
 * Spielt die Bilder automatisch ab
 */
function startPlayback() {
    if (isPlaying) return;
    
    // Aktuelle Wiedergabegeschwindigkeit holen
    const playbackSpeed = parseFloat(playbackSpeedInput.value) || 0.5;
    
    isPlaying = true;
    playButton.disabled = true;
    stopButton.disabled = false;
    
    // Bilder in regelmäßigen Abständen durchschalten
    playbackInterval = setInterval(() => {
        currentImageIndex = (currentImageIndex + 1) % sessionImages.length;
        loadImage(currentImageIndex);
        
        // Wenn wir wieder beim ersten Bild sind, Wiedergabe stoppen
        if (currentImageIndex === 0) {
            stopPlayback();
        }
    }, playbackSpeed * 1000);
}

/**
 * Stoppt die automatische Wiedergabe
 */
function stopPlayback() {
    if (!isPlaying) return;
    
    clearInterval(playbackInterval);
    isPlaying = false;
    playButton.disabled = false;
    stopButton.disabled = true;
}

/**
 * Wendet das aktuelle Zoom-Level auf das Bild an
 */
function applyZoom() {
    currentImage.style.transform = `scale(${zoomLevel})`;
}

/**
 * Zoomt in das Bild hinein
 */
function zoomIn() {
    if (zoomLevel < 3) {
        zoomLevel += 0.2;
        applyZoom();
    }
}

/**
 * Zoomt aus dem Bild heraus
 */
function zoomOut() {
    if (zoomLevel > 0.5) {
        zoomLevel -= 0.2;
        applyZoom();
    }
}

/**
 * Exportiert die 360°-Ansicht im gewählten Format
 */
function exportViewer() {
    const format = exportFormatSelect.value;
    
    // API-Anfrage zum Exportieren
    fetch(`/api/projects/${projectData.id}/export`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            format: format,
            sessionId: currentSessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Download-Link erstellen und klicken
            const downloadLink = document.createElement('a');
            downloadLink.href = data.downloadUrl;
            downloadLink.download = `${projectData.name}_360_viewer.${format === 'html' ? 'zip' : format}`;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        } else {
            alert('Fehler beim Exportieren: ' + (data.message || 'Unbekannter Fehler'));
        }
    })
    .catch(error => {
        console.error('Fehler beim Exportieren:', error);
        alert('Fehler beim Exportieren: ' + error.message);
    });
}

/**
 * Behandelt das Drehen des Bildes durch Ziehen
 * 
 * @param {number} dragDistance - Abstand, um den gezogen wurde
 */
function handleDrag(dragDistance) {
    // Richtungswechsel je nach Zeichenrichtung
    const direction = dragDistance > 0 ? -1 : 1;
    
    // Empfindlichkeit für die Drehung
    const dragThreshold = 20;
    
    // Abstand in Bilderwechsel umrechnen
    const absDistance = Math.abs(dragDistance);
    const imagesToMove = Math.floor(absDistance / dragThreshold);
    
    if (imagesToMove > 0) {
        // Neue Bildposition berechnen (in Grenzen halten)
        let newIndex = currentImageIndex + (direction * imagesToMove);
        
        // Zirkuläre Navigation sicherstellen
        while (newIndex < 0) newIndex += sessionImages.length;
        newIndex = newIndex % sessionImages.length;
        
        // Neues Bild laden, wenn es sich geändert hat
        if (newIndex !== currentImageIndex) {
            loadImage(newIndex);
            return imagesToMove * dragThreshold * direction;
        }
    }
    
    return 0;
}

// Event-Listener einrichten

// Session-Auswahl
sessionSelect.addEventListener('change', () => {
    stopPlayback();
    loadSession(sessionSelect.value);
});

// Wiedergabe-Steuerung
playButton.addEventListener('click', startPlayback);
stopButton.addEventListener('click', stopPlayback);

// Zoom-Steuerung
zoomInButton.addEventListener('click', zoomIn);
zoomOutButton.addEventListener('click', zoomOut);

// Export-Button
exportButton.addEventListener('click', exportViewer);

// Touch- und Maus-Events für die Drehung
imageViewer.addEventListener('mousedown', e => {
    if (isPlaying) return;
    
    isDragging = true;
    startX = e.clientX;
    imageViewer.classList.add('grabbing');
    e.preventDefault();
});

imageViewer.addEventListener('touchstart', e => {
    if (isPlaying) return;
    
    isDragging = true;
    startX = e.touches[0].clientX;
    imageViewer.classList.add('grabbing');
});

window.addEventListener('mousemove', e => {
    if (!isDragging) return;
    
    const dragDistance = e.clientX - startX;
    const consumed = handleDrag(dragDistance);
    startX += consumed;
});

window.addEventListener('touchmove', e => {
    if (!isDragging) return;
    
    const dragDistance = e.touches[0].clientX - startX;
    const consumed = handleDrag(dragDistance);
    startX += consumed;
    
    // Verhindern, dass die Seite beim Wischen scrollt
    e.preventDefault();
}, { passive: false });

window.addEventListener('mouseup', () => {
    isDragging = false;
    imageViewer.classList.remove('grabbing');
});

window.addEventListener('touchend', () => {
    isDragging = false;
    imageViewer.classList.remove('grabbing');
});

// Beim Laden der Seite den Viewer initialisieren
document.addEventListener('DOMContentLoaded', initViewer);

// Hinzufügen der Grab-Klasse für besseres visuelles Feedback
imageViewer.classList.add('grab');
