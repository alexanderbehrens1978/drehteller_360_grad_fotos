/**
 * interactive-viewer.js
 * Interaktiver 360° Produkt-Viewer mit Maus-Steuerung
 */

document.addEventListener('DOMContentLoaded', function() {
    // Projekt-ID aus URL-Parameter holen
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    if (!projectId) {
        console.error('Keine Projekt-ID in der URL gefunden.');
        return;
    }
    
    // Viewer-Elemente
    const viewer = document.getElementById('product-viewer');
    const spinner = document.getElementById('spinner');
    
    // Viewer-Status
    let images = [];
    let currentIndex = 0;
    let isDragging = false;
    let startX = 0;
    let autoRotateTimer = null;
    let isAutoRotating = false;
    
    // Hilfsfunktionen
    function showSpinner() {
        if (spinner) spinner.style.display = 'block';
    }
    
    function hideSpinner() {
        if (spinner) spinner.style.display = 'none';
    }
    
    function showError(message) {
        hideSpinner();
        if (viewer) {
            viewer.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message || 'Ein Fehler ist aufgetreten.'}
                </div>
            `;
        }
    }
    
    // Lade Projektdaten und Bilder
    async function loadProject() {
        showSpinner();
        
        try {
            const response = await fetch(`/api/project/${projectId}`);
            
            if (!response.ok) {
                throw new Error(`Projekt konnte nicht geladen werden: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Prüfen, ob Bilder vorhanden sind
            if (!data.images || data.images.length === 0) {
                throw new Error('Keine Bilder im Projekt gefunden.');
            }
            
            // Projektinformationen anzeigen
            document.querySelector('#project-name span').textContent = data.name || projectId;
            document.querySelector('#image-count span').textContent = data.images.length;
            
            // Bilder vorbereiten
            images = data.images.map(img => `/static/projects/${projectId}/${img}`);
            
            // Viewer initialisieren
            initViewer();
            
        } catch (error) {
            console.error('Fehler beim Laden des Projekts:', error);
            showError(error.message);
        }
    }
    
    // Viewer initialisieren
    function initViewer() {
        hideSpinner();
        
        // Viewer-Container leeren
        viewer.innerHTML = '';
        
        // Alle Bilder vorladen
        const preloadPromises = images.map(src => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = resolve;
                img.onerror = reject;
                img.src = src;
                img.alt = `Produktansicht`;
                img.className = 'product-image';
                img.style.display = 'none';
                img.draggable = false;
                viewer.appendChild(img);
            });
        });
        
        // Wenn alle Bilder geladen sind, erstes Bild anzeigen
        Promise.all(preloadPromises)
            .then(() => {
                console.log('Alle Bilder geladen');
                showImage(0);
                setupEvents();
                startAutoRotate();
            })
            .catch(error => {
                console.error('Fehler beim Vorladen der Bilder:', error);
            });
    }
    
    // Bild anzeigen
    function showImage(index) {
        if (index < 0 || index >= images.length) return;
        
        // Aktuelles Bild ausblenden
        const currentImage = viewer.querySelector('.active');
        if (currentImage) {
            currentImage.classList.remove('active');
        }
        
        // Neues Bild anzeigen
        const viewerImages = viewer.querySelectorAll('img');
        if (viewerImages.length > 0) {
            viewerImages[index].classList.add('active');
            currentIndex = index;
        }
    }
    
    // Event-Listener einrichten
    function setupEvents() {
        // Maus-Events
        viewer.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', endDrag);
        
        // Touch-Events für mobile Geräte
        viewer.addEventListener('touchstart', startDrag);
        document.addEventListener('touchmove', drag);
        document.addEventListener('touchend', endDrag);
        
        // Steuerungs-Buttons
        const playButton = document.getElementById('play-btn');
        if (playButton) {
            playButton.addEventListener('click', toggleAutoRotate);
        }
        
        const resetButton = document.getElementById('reset-btn');
        if (resetButton) {
            resetButton.addEventListener('click', resetViewer);
        }
        
        // Zoom-Buttons
        const zoomInButton = document.getElementById('zoom-in-btn');
        if (zoomInButton) {
            zoomInButton.addEventListener('click', zoomIn);
        }
        
        const zoomOutButton = document.getElementById('zoom-out-btn');
        if (zoomOutButton) {
            zoomOutButton.addEventListener('click', zoomOut);
        }
        
        // Vollbild-Button
        const fullscreenButton = document.getElementById('fullscreen-btn');
        if (fullscreenButton) {
            fullscreenButton.addEventListener('click', toggleFullscreen);
        }
    }
    
    // Drag-Funktionen
    function startDrag(event) {
        event.preventDefault();
        
        isDragging = true;
        viewer.style.cursor = 'grabbing';
        
        // Auto-Rotation stoppen
        stopAutoRotate();
        
        // Startposition speichern
        if (event.type === 'touchstart') {
            startX = event.touches[0].clientX;
        } else {
            startX = event.clientX;
        }
    }
    
    function drag(event) {
        if (!isDragging) return;
        
        event.preventDefault();
        
        let currentX;
        if (event.type === 'touchmove') {
            currentX = event.touches[0].clientX;
        } else {
            currentX = event.clientX;
        }
        
        // Bewegungsrichtung ermitteln
        const deltaX = currentX - startX;
        startX = currentX;
        
        // Nur bei ausreichender Bewegung reagieren
        if (Math.abs(deltaX) > 5) {
            // Richtung bestimmen: nach rechts ziehen = nach links drehen
            const direction = Math.sign(deltaX);
            const newIndex = (currentIndex - direction + images.length) % images.length;
            
            showImage(newIndex);
        }
    }
    
    function endDrag() {
        isDragging = false;
        if (viewer) {
            viewer.style.cursor = 'grab';
        }
    }
    
    // Auto-Rotation
    function startAutoRotate() {
        if (autoRotateTimer) return;
        
        isAutoRotating = true;
        
        if (playButton) {
            playButton.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
        }
        
        autoRotateTimer = setInterval(() => {
            const newIndex = (currentIndex + 1) % images.length;
            showImage(newIndex);
        }, 100);
    }
    
    function stopAutoRotate() {
        if (!autoRotateTimer) return;
        
        clearInterval(autoRotateTimer);
        autoRotateTimer = null;
        isAutoRotating = false;
        
        if (playButton) {
            playButton.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
        }
    }
    
    function toggleAutoRotate() {
        if (isAutoRotating) {
            stopAutoRotate();
        } else {
            startAutoRotate();
        }
    }
    
    // Zoom-Funktionen
    function zoomIn() {
        const images = viewer.querySelectorAll('img');
        images.forEach(img => {
            const currentScale = parseFloat(img.style.transform.replace('scale(', '').replace(')', '') || 1);
            img.style.transform = `scale(${currentScale + 0.1})`;
        });
    }
    
    function zoomOut() {
        const images = viewer.querySelectorAll('img');
        images.forEach(img => {
            const currentScale = parseFloat(img.style.transform.replace('scale(', '').replace(')', '') || 1);
            const newScale = Math.max(0.5, currentScale - 0.1);
            img.style.transform = `scale(${newScale})`;
        });
    }
    
    // Viewer zurücksetzen
    function resetViewer() {
        // Zoom zurücksetzen
        const images = viewer.querySelectorAll('img');
        images.forEach(img => {
            img.style.transform = '';
        });
        
        // Erstes Bild anzeigen
        showImage(0);
        
        // Auto-Rotation stoppen
        stopAutoRotate();
    }
    
    // Vollbild-Modus
    function toggleFullscreen() {
        const container = document.querySelector('.container');
        
        if (container.classList.contains('fullscreen')) {
            // Vollbild beenden
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
            container.classList.remove('fullscreen');
            fullscreenButton.innerHTML = '<i class="bi bi-fullscreen"></i>';
        } else {
            // Vollbild starten
            if (container.requestFullscreen) {
                container.requestFullscreen();
            }
            container.classList.add('fullscreen');
            fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
        }
    }
    
    // Projekt laden, wenn vorhanden
    if (projectId) {
        loadProject();
    }
});
