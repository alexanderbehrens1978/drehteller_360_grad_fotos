/**
 * photo-sphere-viewer.js
 * Integration von Photo Sphere Viewer für die 360-Grad-Ansicht
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
    const viewerContainer = document.getElementById('photo-sphere-container');
    const spinner = document.getElementById('spinner');
    const projectNameElement = document.querySelector('#project-name span');
    const imageCountElement = document.querySelector('#image-count span');
    
    // Lade Projektdaten
    loadProject(projectId)
        .then(setupPhotoSphereViewer)
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
     * Richtet den Photo Sphere Viewer ein
     */
    function setupPhotoSphereViewer(data) {
        // Bereite die Bilder für den Viewer vor
        const images = data.images.map(img => `/static/projects/${projectId}/${img}`);
        
        // Erstelle den Viewer
        const viewer = new PhotoSphereViewer.Viewer({
            container: viewerContainer,
            panorama: images[0],
            caption: data.name || 'Produktansicht',
            navbar: [
                'autorotate',
                'zoom',
                'fullscreen'
            ],
            plugins: [
                [PhotoSphereViewer.AutorotatePlugin, {
                    autorotateDelay: 1000,
                    autorotateSpeed: '1rpm',
                }],
                [PhotoSphereViewer.GalleryPlugin, {
                    thumbnails: images.map((img, i) => ({
                        id: i,
                        panorama: img,
                        thumbnail: img,
                        name: `Ansicht ${i+1}`
                    }))
                }]
            ]
        });
        
        // Event-Handler für den Vollbildmodus
        const fullscreenButton = document.getElementById('fullscreen-btn');
        if (fullscreenButton) {
            fullscreenButton.addEventListener('click', () => {
                viewer.toggleFullscreen();
            });
        }
        
        // Tastatur-Navigation
        document.addEventListener('keydown', (e) => {
            const galleryPlugin = viewer.getPlugin(PhotoSphereViewer.GalleryPlugin);
            if (!galleryPlugin) return;
            
            switch (e.key) {
                case 'ArrowLeft':
                    galleryPlugin.showPrevious();
                    break;
                case 'ArrowRight':
                    galleryPlugin.showNext();
                    break;
            }
        });
    }
});
