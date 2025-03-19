// viewer-app.js - Hauptskript für die Viewer-Seite
import viewer from './modules/viewer.js';

document.addEventListener('DOMContentLoaded', () => {
    // Projekt-ID aus URL-Parametern holen
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    if (!projectId) {
        viewer.showError('Keine Projekt-ID angegeben');
        return;
    }
    
    // Viewer initialisieren
    viewer.init('product-viewer', projectId)
        .then(success => {
            if (success) {
                console.log('Viewer erfolgreich initialisiert');
            }
        })
        .catch(error => {
            console.error('Fehler beim Initialisieren des Viewers:', error);
        });
    
    // Vollbild-Button
    const fullscreenButton = document.getElementById('fullscreen-btn');
    if (fullscreenButton) {
        fullscreenButton.addEventListener('click', () => {
            const container = document.querySelector('.container');
            
            if (container.classList.contains('fullscreen')) {
                // Vollbild beenden
                document.exitFullscreen()
                    .catch(err => console.error('Fehler beim Beenden des Vollbildmodus:', err));
                
                container.classList.remove('fullscreen');
                fullscreenButton.innerHTML = '<i class="bi bi-fullscreen"></i>';
            } else {
                // Vollbild starten
                container.requestFullscreen()
                    .catch(err => console.error('Fehler beim Starten des Vollbildmodus:', err));
                
                container.classList.add('fullscreen');
                fullscreenButton.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
            }
        });
    }
});
