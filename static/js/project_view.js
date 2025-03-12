/**
 * project_view.js
 * JavaScript für die Projektdetailansicht
 */

document.addEventListener('DOMContentLoaded', function() {
    // Bilder laden, falls vorhanden
    loadImages();
    
    // Event-Listener für das Löschen von Bildern
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-image-btn')) {
            e.preventDefault();
            deleteImage(e.target.dataset.imageId);
        }
    });
});

// Bilder laden
function loadImages() {
    const imageGrid = document.querySelector('.image-grid');
    if (!imageGrid) return;
    
    // Bilder sind bereits im HTML und müssen nicht neu geladen werden
    // Diese Funktion kann jedoch verwendet werden, um zusätzliche
    // Interaktivität hinzuzufügen, z.B. Zoom-Funktionen oder Sortierung
}

// Bild löschen
function deleteImage(imageId) {
    if (!confirm('Möchten Sie dieses Bild wirklich löschen?')) {
        return;
    }
    
    const projectId = document.body.dataset.projectId;
    if (!projectId) return;
    
    fetch(`/projects/${projectId}/image/${imageId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            // Bild erfolgreich gelöscht, Element entfernen
            const imageElement = document.querySelector(`[data-image-id="${imageId}"]`).closest('.image-item');
            if (imageElement) {
                imageElement.remove();
            }
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && data.error) {
            alert(`Fehler beim Löschen des Bildes: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Löschen des Bildes:', error);
        alert('Fehler beim Löschen des Bildes');
    });
}
