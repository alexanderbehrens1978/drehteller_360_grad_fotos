/**
 * pannellum-integration.js
 * Integration des Pannellum-Viewers in die Webseite
 */

document.addEventListener('DOMContentLoaded', function() {
    // Button zum Erstellen des Pannellum-Viewers
    const createViewerBtn = document.getElementById('create-pannellum-btn');
    const viewerContainer = document.getElementById('pannellum-container');
    const exportViewerBtn = document.getElementById('export-pannellum-btn');
    
    if (createViewerBtn) {
        createViewerBtn.addEventListener('click', createPannellumViewer);
    }
    
    if (exportViewerBtn) {
        exportViewerBtn.addEventListener('click', exportPannellumViewer);
    }
    
    /**
     * Erstellt einen Pannellum-Viewer für das aktuelle Projekt
     */
    function createPannellumViewer() {
        // Projekt-ID aus URL oder DOM-Attribut holen
        const projectId = getProjectId();
        
        if (!projectId) {
            showMessage('Fehler: Keine Projekt-ID gefunden', 'error');
            return;
        }
        
        // UI aktualisieren
        showMessage('Erstelle 360° Viewer...', 'info');
        if (createViewerBtn) createViewerBtn.disabled = true;
        
        // API-Anfrage senden
        fetch('/api/pannellum/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ project_id: projectId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage('360° Viewer erfolgreich erstellt!', 'success');
                
                // Viewer-URL anzeigen
                if (viewerContainer) {
                    viewerContainer.innerHTML = `
                        <div class="viewer-success">
                            <p>Der 360° Viewer wurde erfolgreich erstellt.</p>
                            <a href="${data.viewer_url}" class="btn btn-primary" target="_blank">
                                360° Viewer öffnen
                            </a>
                        </div>
                    `;
                }
                
                // Export-Button aktivieren
                if (exportViewerBtn) {
                    exportViewerBtn.disabled = false;
                    exportViewerBtn.style.display = 'inline-block';
                }
            } else {
                showMessage(`Fehler: ${data.message}`, 'error');
                if (createViewerBtn) createViewerBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Fehler beim Erstellen des Viewers:', error);
            showMessage('Netzwerkfehler beim Erstellen des Viewers', 'error');
            if (createViewerBtn) createViewerBtn.disabled = false;
        });
    }
    
    /**
     * Exportiert den Pannellum-Viewer als ZIP-Datei
     */
    function exportPannellumViewer() {
        // Projekt-ID aus URL oder DOM-Attribut holen
        const projectId = getProjectId();
        
        if (!projectId) {
            showMessage('Fehler: Keine Projekt-ID gefunden', 'error');
            return;
        }
        
        // UI aktualisieren
        showMessage('Exportiere 360° Viewer...', 'info');
        if (exportViewerBtn) exportViewerBtn.disabled = true;
        
        // API-Anfrage senden
        fetch(`/api/pannellum/export/${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showMessage('360° Viewer erfolgreich exportiert!', 'success');
                
                // Automatisch den Download starten
                window.location.href = data.download_url;
                
                // Download-Link anzeigen
                if (viewerContainer) {
                    // Bestehenden Inhalt erweitern
                    viewerContainer.innerHTML += `
                        <div class="export-success mt-3">
                            <p>Der 360° Viewer wurde erfolgreich exportiert.</p>
                            <a href="${data.download_url}" class="btn btn-secondary">
                                ZIP-Datei erneut herunterladen
                            </a>
                        </div>
                    `;
                }
                
                // Export-Button reaktivieren
                if (exportViewerBtn) exportViewerBtn.disabled = false;
            } else {
                showMessage(`Fehler: ${data.message}`, 'error');
                if (exportViewerBtn) exportViewerBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Fehler beim Exportieren des Viewers:', error);
            showMessage('Netzwerkfehler beim Exportieren des Viewers', 'error');
            if (exportViewerBtn) exportViewerBtn.disabled = false;
        });
    }
    
    /**
     * Zeigt eine Nachricht auf der Benutzeroberfläche an
     */
    function showMessage(message, type = 'info') {
        const messageContainer = document.getElementById('message-container');
        
        if (!messageContainer) {
            // Wenn kein Container existiert, erstelle einen
            const container = document.createElement('div');
            container.id = 'message-container';
            container.style.marginBottom = '20px';
            
            // Container vor dem Viewer einfügen
            if (viewerContainer) {
                viewerContainer.parentNode.insertBefore(container, viewerContainer);
            } else if (createViewerBtn) {
                createViewerBtn.parentNode.insertBefore(container, createViewerBtn);
            }
        }
        
        // Nachricht erstellen
        const messageElement = document.createElement('div');
        messageElement.className = `alert alert-${type === 'error' ? 'danger' : (type === 'success' ? 'success' : 'info')}`;
        messageElement.textContent = message;
        
        // Bestehende Nachrichten entfernen
        const container = document.getElementById('message-container');
        container.innerHTML = '';
        container.appendChild(messageElement);
        
        // Nachricht nach 5 Sekunden ausblenden (nur Info/Success)
        if (type !== 'error') {
            setTimeout(() => {
                messageElement.style.opacity = '0';
                messageElement.style.transition = 'opacity 0.5s';
                
                // Nach Ausblenden entfernen
                setTimeout(() => {
                    if (container.contains(messageElement)) {
                        container.removeChild(messageElement);
                    }
                }, 500);
            }, 5000);
        }
    }
    
    /**
     * Ruft die Projekt-ID aus URL-Parametern oder einem Datenelement ab
     */
    function getProjectId() {
        // Versuche, die Projekt-ID aus URL-Parametern zu lesen
        const urlParams = new URLSearchParams(window.location.search);
        let projectId = urlParams.get('project_id');
        
        // Wenn nicht in URL, versuche es aus dem data-Attribut des body-Elements
        if (!projectId) {
            projectId = document.body.getAttribute('data-project-id');
        }
        
        // Oder aus einem dedizierten Hidden-Input
        if (!projectId) {
            const hiddenInput = document.querySelector('input[name="project_id"]');
            if (hiddenInput) {
                projectId = hiddenInput.value;
            }
        }
        
        return projectId;
    }
});
