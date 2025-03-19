/**
 * pannellum-viewer.js
 * Integration von Pannellum für die 360-Grad-Ansicht
 */

document.addEventListener('DOMContentLoaded', function() {
    // Projekt-ID aus URL-Parameter holen
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    if (!projectId) {
        console.error('Keine Projekt-ID in der URL gefunden.');
        showError('Keine Projekt-ID angegeben');
        return;
    }
    
    // Viewer-Element und Spinner
    const viewerContainer = document.getElementById('pannellum-viewer');
    const spinner = document.getElementById('spinner');
    const projectNameElement = document.querySelector('#project-name span');
    const imageCountElement = document.querySelector('#image-count span');
    
    // Lade Projektdaten
    loadProject(projectId)
        .then(setupViewer)
        .catch(error => {
            console.error('Fehler beim Laden des Projekts:', error);
            showError(error.message);
        });
    
    /**
     * Lädt die Projektdaten vom Server
     */
    async function loadProject(projectId) {
        if (spinner) spinner.style.display = 'block';
        
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
            if (projectNameElement) projectNameElement.textContent = data.name || projectId;
            if (imageCountElement) imageCountElement.textContent = data.images.length;
            
            return data;
        } catch (error) {
            throw error;
        } finally {
            if (spinner) spinner.style.display = 'none';
        }
    }
    
    /**
     * Zeigt eine Fehlermeldung an
     */
    function showError(message) {
        if (spinner) spinner.style.display = 'none';
        
        if (viewerContainer) {
            viewerContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${message || 'Ein Fehler ist aufgetreten.'}
                </div>
            `;
        }
    }
    
    /**
     * Richtet den Pannellum-Viewer ein
     */
    function setupViewer(data) {
        // Bereite die Bilder für Pannellum vor
        const images = data.images.map(img => `/static/projects/${projectId}/${img}`);
        
        // Erstelle die Multi-Bild-Konfiguration für Pannellum
        // Wir erstellen eine equirectangular-ähnliche Ansicht mit mehreren Bildern
        const config = {
            type: "equirectangular",
            panorama: images[0], // Erstes Bild als Startbild
            autoLoad: true,
            showControls: false, // Wir steuern die Bedienelemente selbst
            compass: false,
            hotSpots: []
        };
        
        // Pannellum initialisieren
        const viewer = pannellum.viewer(viewerContainer.id, config);
        
        // Variable für den aktuellen Bildindex
        let currentIndex = 0;
        
        // Funktion zum Ändern des Bildes
        function changeImage(index) {
            if (index < 0) index = images.length - 1;
            if (index >= images.length) index = 0;
            
            currentIndex = index;
            viewer.loadScene('scene' + index, null, null, null);
        }
        
        // Szenen für jedes Bild erstellen
        images.forEach((image, index) => {
            viewer.addScene('scene' + index, {
                panorama: image,
                type: "equirectangular",
            });
        });
        
        // Event-Listener für die Steuerung
        const prevButton = document.getElementById('prev-btn');
        const nextButton = document.getElementById('next-btn');
        const playButton = document.getElementById('play-btn');
        
        if (prevButton) {
            prevButton.addEventListener('click', () => {
                changeImage(currentIndex - 1);
            });
        }
        
        if (nextButton) {
            nextButton.addEventListener('click', () => {
                changeImage(currentIndex + 1);
            });
        }
        
        // Auto-Rotation
        let autoRotateInterval = null;
        
        function startAutoRotate() {
            if (autoRotateInterval) return;
            
            autoRotateInterval = setInterval(() => {
                changeImage(currentIndex + 1);
            }, 1000); // Alle 1 Sekunde
            
            if (playButton) {
                playButton.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
                playButton.dataset.playing = 'true';
            }
        }
        
        function stopAutoRotate() {
            if (autoRotateInterval) {
                clearInterval(autoRotateInterval);
                autoRotateInterval = null;
                
                if (playButton) {
                    playButton.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
                    playButton.dataset.playing = 'false';
                }
            }
        }
        
        if (playButton) {
            playButton.addEventListener('click', () => {
                if (playButton.dataset.playing === 'true') {
                    stopAutoRotate();
                } else {
                    startAutoRotate();
                }
            });
        }
        
        // Mausrad-Handler für Zoom
        viewerContainer.addEventListener('wheel', (e) => {
            // Standardverhalten verhindern (Scrollen der Seite)
            e.preventDefault();
            
            // Zoom-Level bestimmen
            const hfov = viewer.getHfov();
            if (e.deltaY < 0) {
                // Rein-Zoomen
                viewer.setHfov(hfov - 5);
            } else {
                // Raus-Zoomen
                viewer.setHfov(hfov + 5);
            }
        });
        
        // Hotkeys für die Tastatursteuerung
        document.addEventListener('keydown', (e) => {
            switch (e.key) {
                case 'ArrowLeft':
                    changeImage(currentIndex - 1);
                    break;
                case 'ArrowRight':
                    changeImage(currentIndex + 1);
                    break;
                case ' ': // Leertaste
                    if (autoRotateInterval) {
                        stopAutoRotate();
                    } else {
                        startAutoRotate();
                    }
                    break;
            }
        });
        
        // Auto-Rotation standardmäßig starten
        startAutoRotate();
    }
});
