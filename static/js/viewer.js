/**
 * 360° Produktansicht Viewer
 * Interaktiver Viewer für 360-Grad-Produktansichten
 */

// DOM-Elemente
const viewerContainer = document.getElementById('product-viewer');
const spinner = document.getElementById('spinner');
const playButton = document.getElementById('play-btn');
const resetButton = document.getElementById('reset-btn');
const zoomInButton = document.getElementById('zoom-in-btn');
const zoomOutButton = document.getElementById('zoom-out-btn');
const fullscreenButton = document.getElementById('fullscreen-btn');
const projectNameElement = document.querySelector('#project-name span');
const imageCountElement = document.querySelector('#image-count span');

// Viewer-Konfiguration
let config = {
    images: [],            // Bildpfade
    currentImageIndex: 0,  // Aktueller Bildindex
    autoRotate: false,     // Automatische Rotation
    autoRotateSpeed: 100,  // Rotationsgeschwindigkeit in ms
    zoom: 1.0,             // Zoomstufe
    maxZoom: 2.5,          // Maximale Zoomstufe
    minZoom: 1.0,          // Minimale Zoomstufe
    zoomStep: 0.1,         // Zoom-Schritt pro Klick
    dragging: false,       // Maus/Touch-Status
    lastX: 0,              // Letzte X-Position
    autoRotateTimer: null  // Timer für Auto-Rotation
};

// Projekt-ID aus URL-Parametern holen
const urlParams = new URLSearchParams(window.location.search);
const projectId = urlParams.get('project');

/**
 * Lädt die Projektdaten vom Server
 */
async function loadProject() {
    console.log("Lade Projekt mit ID:", projectId);
    
    if (!projectId) {
        showError('Keine Projekt-ID angegeben');
        return;
    }
    
    try {
        const response = await fetch(`/api/project/${projectId}`);
        
        if (!response.ok) {
            throw new Error(`Projekt konnte nicht geladen werden (Status: ${response.status})`);
        }
        
        const projectData = await response.json();
        console.log("Projektdaten geladen:", projectData);
        
        // Projektdaten anzeigen
        projectNameElement.textContent = projectData.name || projectId;
        imageCountElement.textContent = projectData.image_count || projectData.images.length;
        
        // Bilder laden
        config.images = projectData.images.map(img => `/static/projects/${projectId}/${img}`);
        console.log("Bildpfade:", config.images);
        
        if (config.images.length > 0) {
            initViewer();
        } else {
            showError('Keine Bilder im Projekt gefunden');
        }
    } catch (error) {
        console.error('Fehler beim Laden des Projekts:', error);
        showError(`Fehler beim Laden des Projekts: ${error.message}`);
    }
}

/**
 * Initialisiert den 360° Viewer
 */
function initViewer() {
    console.log("Initialisiere Viewer mit", config.images.length, "Bildern");
    
    // Bilder vorladen
    preloadImages().then(() => {
        console.log("Alle Bilder vorgeladen");
        
        // Spinner ausblenden
        spinner.style.display = 'none';
        
        // Erstes Bild anzeigen
        showImage(0);
        
        // Event-Listener hinzufügen
        setupEventListeners();
        
        // Automatische Rotation starten
        startAutoRotate();
    }).catch(error => {
        console.error("Fehler beim Vorladen der Bilder:", error);
        showError("Fehler beim Laden der Bilder. Bitte prüfen Sie die Browser-Konsole.");
    });
}

/**
 * Lädt alle Bilder vor
 */
async function preloadImages() {
    console.log("Lade", config.images.length, "Bilder vor");
    
    // Zuerst alle vorhandenen Bilder entfernen
    const existingImages = viewerContainer.querySelectorAll('img');
    existingImages.forEach(img => img.remove());
    
    const preloadPromises = config.images.map((src, index) => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            
            img.onload = () => {
                console.log(`Bild ${index + 1}/${config.images.length} geladen:`, src);
                resolve();
            };
            
            img.onerror = (err) => {
                console.error(`Fehler beim Laden von Bild ${index + 1}/${config.images.length}:`, src, err);
                // Trotz Fehler als geladen markieren, um die Anzeige nicht zu blockieren
                resolve();
            };
            
            img.src = src;
            img.alt = `Ansicht ${index + 1}`;
            img.className = 'product-image';
            img.style.display = 'none';
            img.draggable = false;
            
            viewerContainer.appendChild(img);
        });
    });
    
    return Promise.all(preloadPromises);
}

/**
 * Zeigt das Bild mit dem angegebenen Index an
 */
function showImage(index) {
    console.log("Zeige Bild", index + 1, "von", config.images.length);
    
    // Aktuelles Bild ausblenden
    const currentImage = viewerContainer.querySelector('.active');
    if (currentImage) {
        currentImage.classList.remove('active');
    }
    
    // Neues Bild anzeigen
    const images = viewerContainer.querySelectorAll('img');
    if (images.length > 0 && index >= 0 && index < images.length) {
        images[index].classList.add('active');
        config.currentImageIndex = index;
    } else {
        console.error("Ungültiger Bildindex:", index, "Verfügbare Bilder:", images.length);
    }
}

/**
 * Richtet Event-Listener für Maus/Touch-Interaktionen ein
 */
function setupEventListeners() {
    // Maus-Events
    viewerContainer.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag);
    
    // Touch-Events
    viewerContainer.addEventListener('touchstart', startDrag);
    document.addEventListener('touchmove', drag);
    document.addEventListener('touchend', endDrag);
    
    // Zoom-Events
    zoomInButton.addEventListener('click', zoomIn);
    zoomOutButton.addEventListener('click', zoomOut);
    viewerContainer.addEventListener('wheel', handleWheel);
    
    // Steuerungs-Buttons
    playButton.addEventListener('click', toggleAutoRotate);
    resetButton.addEventListener('click', resetViewer);
    fullscreenButton.addEventListener('click', toggleFullscreen);
    
    console.log("Event-Listener eingerichtet");
}

/**
 * Startet den Drag-Vorgang
 */
function startDrag(event) {
    event.preventDefault();
    
    config.dragging = true;
    viewerContainer.style.cursor = 'grabbing';
    
    // Auto-Rotation stoppen
    stopAutoRotate();
    
    // Letzte Position speichern
    if (event.type === 'touchstart') {
        config.lastX = event.touches[0].clientX;
    } else {
        config.lastX = event.clientX;
    }
}

/**
 * Verarbeitet Drag-Bewegung
 */
function drag(event) {
    if (!config.dragging) return;
    
    event.preventDefault();
    
    let currentX;
    if (event.type === 'touchmove') {
        currentX = event.touches[0].clientX;
    } else {
        currentX = event.clientX;
    }
    
    // Bewegungsrichtung und -stärke ermitteln
    const deltaX = currentX - config.lastX;
    config.lastX = currentX;
    
    // Anzahl der Bilder berücksichtigen
    const imageCount = config.images.length;
    const step = Math.sign(deltaX);
    
    if (Math.abs(deltaX) > 5) { // Mindestbewegung für Bildwechsel
        let newIndex = config.currentImageIndex - step;
        
        // Grenzen beachten
        if (newIndex < 0) newIndex = imageCount - 1;
        if (newIndex >= imageCount) newIndex = 0;
        
        showImage(newIndex);
    }
}

/**
 * Beendet den Drag-Vorgang
 */
function endDrag() {
    config.dragging = false;
    viewerContainer.style.cursor = 'grab';
}

/**
 * Startet die automatische Rotation
 */
function startAutoRotate() {
    if (config.autoRotateTimer) return;
    
    config.autoRotate = true;
    playButton.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
    
    config.autoRotateTimer = setInterval(() => {
        let newIndex = (config.currentImageIndex + 1) % config.images.length;
        showImage(newIndex);
    }, config.autoRotateSpeed);
    
    console.log("Auto-Rotation gestartet");
}

/**
 * Stoppt die automatische Rotation
 */
function stopAutoRotate() {
    if (!config.autoRotateTimer) return;
    
    clearInterval(config.autoRotateTimer);
    config.autoRotateTimer = null;
    config.autoRotate = false;
    playButton.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
    
    console.log("Auto-Rotation gestoppt");
}

/**
 * Wechselt zwischen automatischer Rotation und Pause
 */
function toggleAutoRotate() {
    if (config.autoRotate) {
        stopAutoRotate();
    } else {
        startAutoRotate();
    }
}

/**
 * Vergrößert die Ansicht
 */
function zoomIn() {
    if (config.zoom < config.maxZoom) {
        config.zoom += config.zoomStep;
        applyZoom();
    }
}

/**
 * Verkleinert die Ansicht
 */
function zoomOut() {
    if (config.zoom > config.minZoom) {
        config.zoom -= config.zoomStep;
        applyZoom();
    }
}

/**
 * Wendet den aktuellen Zoom-Wert auf die Bilder an
 */
function applyZoom() {
    const images = viewerContainer.querySelectorAll('img');
    images.forEach(img => {
        img.style.transform = `translate(-50%, -50%) scale(${config.zoom})`;
    });
    
    console.log("Zoom angewendet:", config.zoom);
}

/**
 * Behandelt Mausrad-Events für Zoom
 */
function handleWheel(event) {
    event.preventDefault();
    
    if (event.deltaY < 0) {
        zoomIn();
    } else {
        zoomOut();
    }
}

/**
 * Setzt den Viewer zurück
 */
function resetViewer() {
    showImage(0);
    config.zoom = 1.0;
    applyZoom();
    stopAutoRotate();
    
    console.log("Viewer zurückgesetzt");
}

/**
 * Wechselt in den Vollbildmodus und zurück
 */
function toggleFullscreen() {
    const container = document.querySelector('.container');
    container.classList.toggle('fullscreen');
    
    if (container.classList.contains('fullscreen')) {
        fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
    } else {
        fullscreenButton.innerHTML = '<i class="bi bi-fullscreen"></i>';
    }
    
    console.log("Vollbildmodus umgeschaltet");
}

/**
 * Zeigt eine Fehlermeldung an
 */
function showError(message) {
    console.error("Fehlermeldung:", message);
    
    // Spinner ausblenden, falls noch sichtbar
    spinner.style.display = 'none';
    
    // Bestehende Fehlermeldungen entfernen
    const existingErrors = viewerContainer.querySelectorAll('.alert');
    existingErrors.forEach(error => error.remove());
    
    // Neue Fehlermeldung anzeigen
    const errorElement = document.createElement('div');
    errorElement.className = 'alert alert-danger m-3';
    errorElement.textContent = message;
    
    viewerContainer.appendChild(errorElement);
}

// Projekt laden, wenn die Seite geladen ist
document.addEventListener('DOMContentLoaded', loadProject);

// Ein zusätzlicher Debug-Handler
window.addEventListener('error', (event) => {
    console.error('Globaler JavaScript-Fehler:', event.error);
});
