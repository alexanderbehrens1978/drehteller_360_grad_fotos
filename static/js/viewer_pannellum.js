// Dateipfad: static/js/viewer_pannellum.js
// Funktionen für den Pannellum-Viewer

let viewer = null;

document.addEventListener('DOMContentLoaded', function() {
    // Projekt-Selektor initialisieren
    $('#project-selector').on('change', function() {
        const projectId = $(this).val();
        if (projectId) {
            loadProject(projectId);
        }
    });
});

/**
 * Lädt ein Projekt für die Anzeige im Pannellum-Viewer
 * @param {string} projectId - Die ID des zu ladenden Projekts
 */
function loadProject(projectId) {
    $.getJSON(`/api/project/${projectId}`, function(project) {
        if (project && project.images && project.images.length > 0) {
            // Wenn bereits ein Viewer existiert, diesen zerstören
            if (viewer) {
                viewer.destroy();
                viewer = null;
            }
            
            // Pfad zum ersten Bild
            const firstImage = `/projects/${projectId}/images/${project.images[0]}`;
            
            // Pannellum-Viewer initialisieren
            viewer = pannellum.viewer('panorama', {
                type: 'equirectangular',
                panorama: firstImage,
                autoLoad: true,
                showZoomCtrl: true,
                showFullscreenCtrl: true,
                hotSpotDebug: false
            });
            
            // Für jedes Bild im Projekt einen Hotspot hinzufügen
            if (project.images.length > 1) {
                setupViewerWithMultipleImages(project, projectId);
            }
        } else {
            alert('Keine Bilder im ausgewählten Projekt gefunden.');
        }
    }).fail(function() {
        alert('Fehler beim Laden des Projekts.');
    });
}

/**
 * Richtet den Viewer für mehrere Bilder ein
 * @param {Object} project - Das Projektobjekt
 * @param {string} projectId - Die ID des Projekts
 */
function setupViewerWithMultipleImages(project, projectId) {
    // Hotspots für Bildnavigation vorbereiten
    const scenes = {};
    
    project.images.forEach((image, index) => {
        const sceneId = `scene_${index}`;
        const imagePath = `/projects/${projectId}/images/${image}`;
        
        // Szene definieren
        scenes[sceneId] = {
            type: 'equirectangular',
            panorama: imagePath,
            hotSpots: []
        };
        
        // Hotspots für Navigation zu anderen Bildern hinzufügen
        if (index > 0) {
            scenes[sceneId].hotSpots.push({
                type: 'scene',
                text: 'Vorheriges Bild',
                sceneId: `scene_${index - 1}`,
                pitch: 0,
                yaw: -90
            });
        }
        
        if (index < project.images.length - 1) {
            scenes[sceneId].hotSpots.push({
                type: 'scene',
                text: 'Nächstes Bild',
                sceneId: `scene_${index + 1}`,
                pitch: 0,
                yaw: 90
            });
        }
    });
    
    // Viewer mit mehreren Szenen konfigurieren
    viewer.destroy();
    viewer = pannellum.viewer('panorama', {
        default: {
            firstScene: 'scene_0',
            sceneFadeDuration: 1000
        },
        scenes: scenes
    });
}
