/**
 * sphere_viewer.js
 * Verbesserte Integration von Photo Sphere Viewer für 360-Grad-Ansichten
 * 
 * Diese Datei speichern unter: /static/js/sphere_viewer.js
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
    
    // DOM-Elemente
    const viewerContainer = document.getElementById('viewer');
    const spinner = document.getElementById('spinner');
    const projectNameEl = document.getElementById('project-name');
    const selectedImagesCountEl = document.getElementById('selected-images-count');
    const exportBtn = document.getElementById('export-btn');
    const exportSection = document.getElementById('export-section');
    const embedCodeEl = document.getElementById('embed-code');
    const directLinkEl = document.getElementById('direct-link');
    const copyEmbedBtn = document.getElementById('copy-embed-btn');
    const copyLinkBtn = document.getElementById('copy-link-btn');
    const playBtn = document.getElementById('play-btn');
    const resetBtn = document.getElementById('reset-btn');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    
    // Viewer-Instanz
    let viewer = null;
    let autorotatePlugin = null;
    
    // Ausgewählte Bilder
    let selectedImages = [];
    
    // Status-Nachricht anzeigen
    function showStatus(message, isError = false) {
        const statusElement = document.getElementById('status-message') || document.createElement('div');
        
        if (!statusElement.id) {
            statusElement.id = 'status-message';
            statusElement.style.padding = '10px';
            statusElement.style.margin = '10px 0';
            statusElement.style.borderRadius = '4px';
            
            // Element einfügen, falls es nicht existiert
            if (viewerContainer.parentNode) {
                viewerContainer.parentNode.insertBefore(statusElement, viewerContainer);
            }
        }
        
        statusElement.textContent = message;
        statusElement.style.backgroundColor = isError ? '#f8d7da' : '#d1e7dd';
        statusElement.style.color = isError ? '#721c24' : '#155724';
        statusElement.style.display = 'block';
    }
    
    // Fehlermeldung anzeigen
    function showError(message) {
        console.error('Viewer-Fehler:', message);
        showStatus(message, true);
        
        if (spinner) spinner.style.display = 'none';
    }
    
    // Projekt laden
    async function loadProject() {
        if (spinner) spinner.style.display = 'block';
        
        try {
            const response = await fetch(`/api/project/${projectId}`);
            
            if (!response.ok) {
                throw new Error(`Projekt konnte nicht geladen werden (Status: ${response.status})`);
            }
            
            const data = await response.json();
            
            // Projektdaten prüfen
            if (!data.images || data.images.length === 0) {
                throw new Error('Keine Bilder im Projekt gefunden');
            }
            
            // UI aktualisieren
            if (projectNameEl) {
                const nameSpan = projectNameEl.querySelector('span');
                if (nameSpan) nameSpan.textContent = data.name;
            }
            
            if (selectedImagesCountEl) {
                selectedImagesCountEl.textContent = data.images.length;
            }
            
            // Bilder-Auswahl initialisieren
            setupImageSelection(data.images);
            
            return data;
        } catch (error) {
            showError(error.message);
            throw error;
        } finally {
            if (spinner) spinner.style.display = 'none';
        }
    }
    
    // Bildauswahl einrichten
    function setupImageSelection(images) {
        if (!images || images.length === 0) return;
        
        // Alle Bilder initial auswählen
        selectedImages = images;
        
        // Checkbox-Event-Listener
        const imageItems = document.querySelectorAll('.image-item');
        
        imageItems.forEach(item => {
            item.addEventListener('click', function() {
                const checkbox = this.querySelector('input[type="checkbox"]');
                this.classList.toggle('selected');
                checkbox.checked = !checkbox.checked;
                
                // Ausgewählte Bilder aktualisieren
                updateSelectedImages();
            });
        });
        
        // Viewer initialisieren
        initViewer();
    }
    
    // Ausgewählte Bilder aktualisieren
    function updateSelectedImages() {
        const checkedBoxes = document.querySelectorAll('input[name="selected_images"]:checked');
        selectedImages = Array.from(checkedBoxes).map(checkbox => {
            const item = checkbox.closest('.image-item');
            return {
                path: item.dataset.path,
                angle: parseFloat(item.dataset.angle || 0)
            };
        });
        
        // Nach Winkel sortieren
        selectedImages.sort((a, b) => a.angle - b.angle);
        
        // Zähler aktualisieren
        if (selectedImagesCountEl) {
            selectedImagesCountEl.textContent = selectedImages.length;
        }
        
        // Viewer aktualisieren
        updateViewer();
    }
    
    // Viewer initialisieren
    async function initViewer() {
        // Photo Sphere Viewer Module importieren
        try {
            // Module sind bereits im HTML als importmap definiert
            const { Viewer } = await import('@photo-sphere-viewer/core');
            const { AutorotatePlugin } = await import('@photo-sphere-viewer/autorotate-plugin');
            const { GalleryPlugin } = await import('@photo-sphere-viewer/gallery-plugin');
            
            // Viewer konfigurieren und initialisieren
            setupViewer(Viewer, AutorotatePlugin, GalleryPlugin);
        } catch (error) {
            console.error('Fehler beim Laden der Photo Sphere Viewer Module:', error);
            showError('Die Viewer-Module konnten nicht geladen werden: ' + error.message);
        }
    }
    
    // Viewer einrichten
    function setupViewer(ViewerClass, AutorotateClass, GalleryClass) {
        if (!viewerContainer || selectedImages.length === 0) return;
        
        // Spinner anzeigen während des Ladens
        if (spinner) spinner.style.display = 'block';
        
        try {
            // Bilder für den Viewer vorbereiten
            const galleryItems = selectedImages.map((img, index) => ({
                id: index,
                name: `Winkel ${img.angle}°`,
                panorama: `/projects/image/${projectId}/${img.path}`,
                thumbnail: `/projects/image/${projectId}/${img.path}`
            }));
            
            // Viewer erstellen
            if (viewer) {
                // Existierenden Viewer aktualisieren
                const galleryPlugin = viewer.getPlugin(GalleryClass);
                if (galleryPlugin) {
                    galleryPlugin.setItems(galleryItems);
                }
            } else {
                // Neuen Viewer erstellen
                viewer = new ViewerClass({
                    container: viewerContainer,
                    panorama: galleryItems[0].panorama,
                    caption: `${projectNameEl.querySelector('span').textContent} - ${galleryItems[0].name}`,
                    touchmoveTwoFingers: true,
                    mousewheelCtrlKey: true,
                    navbar: [
                        'autorotate',
                        'zoom',
                        'gallery',
                        'fullscreen'
                    ],
                    plugins: [
                        [AutorotateClass, {
                            autorotatePitch: 0,
                            autorotateSpeed: '2rpm',
                            autorotateDelay: 1000
                        }],
                        [GalleryClass, {
                            thumbnails: galleryItems
                        }]
                    ]
                });
                
                // Autorotate-Plugin speichern
                autorotatePlugin = viewer.getPlugin(AutorotateClass);
                
                // Event-Listener für "ready"
                viewer.addEventListener('ready', () => {
                    // Steuerelemente einrichten
                    setupControls();
                    
                    // Autorotation starten
                    if (autorotatePlugin) {
                        autorotatePlugin.start();
                    }
                });
                
                // Event-Listener für Galerie-Wechsel
                viewer.addEventListener('panorama-loaded', (e) => {
                    const currentImage = galleryItems.find(item => item.panorama === e.data.panorama);
                    if (currentImage) {
                        viewer.setCaption(`${projectNameEl.querySelector('span').textContent} - ${currentImage.name}`);
                    }
                });
            }
            
            // Export-Button aktivieren
            if (exportBtn) {
                exportBtn.disabled = false;
            }
            
        } catch (error) {
            console.error('Fehler beim Erstellen des Viewers:', error);
            showError('Der Viewer konnte nicht erstellt werden: ' + error.message);
        } finally {
            if (spinner) spinner.style.display = 'none';
        }
    }
    
    // Viewer aktualisieren (nach Änderung der Bildauswahl)
    function updateViewer() {
        // Viewer neustarten, falls er existiert
        if (viewer) {
            // Viewer muss neu erstellt werden
            viewer.destroy();
            viewer = null;
            
            // Viewer neu initialisieren
            initViewer();
        }
    }
    
    // Steuerelemente einrichten
    function setupControls() {
        // Play/Pause-Button
        if (playBtn && autorotatePlugin) {
            playBtn.addEventListener('click', function() {
                if (autorotatePlugin.isAutorotating()) {
                    autorotatePlugin.stop();
                    this.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
                } else {
                    autorotatePlugin.start();
                    this.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
                }
            });
        }
        
        // Reset-Button
        if (resetBtn && viewer) {
            resetBtn.addEventListener('click', function() {
                viewer.resetView();
            });
        }
        
        // Vollbild-Button
        if (fullscreenBtn && viewer) {
            fullscreenBtn.addEventListener('click', function() {
                if (document.fullscreenElement) {
                    document.exitFullscreen();
                    this.innerHTML = '<i class="bi bi-fullscreen"></i>';
                } else {
                    viewer.container.requestFullscreen();
                    this.innerHTML = '<i class="bi bi-fullscreen-exit"></i>';
                }
            });
        }
        
        // Export-Button
        if (exportBtn) {
            exportBtn.addEventListener('click', exportViewer);
        }
        
        // Kopier-Buttons
        setupCopyButtons();
    }
    
    // Viewer exportieren
    function exportViewer() {
        if (selectedImages.length === 0) {
            showError('Bitte wähle mindestens ein Bild aus.');
            return;
        }
        
        showStatus('Exportiere Viewer...');
        
        // Viewer-Export anfordern
        fetch('/viewer/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_id: projectId,
                selected_images: selectedImages.map(img => img.path)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStatus('Export erfolgreich');
                
                // Export-Bereich anzeigen
                if (exportSection) {
                    exportSection.style.display = 'block';
                }
                
                // Direktlink anzeigen
                if (directLinkEl) {
                    directLinkEl.textContent = data.export_url;
                }
                
                // Embed-Code anzeigen
                if (embedCodeEl) {
                    embedCodeEl.textContent = data.embed_code;
                }
            } else {
                showError('Fehler beim Exportieren: ' + (data.message || 'Unbekannter Fehler'));
            }
        })
        .catch(error => {
            console.error('Fehler beim Export:', error);
            showError('Fehler bei der Kommunikation mit dem Server: ' + error.message);
        });
    }
    
    // Kopier-Buttons einrichten
    function setupCopyButtons() {
        if (copyEmbedBtn) {
            copyEmbedBtn.addEventListener('click', function() {
                copyToClipboard(embedCodeEl.textContent);
                this.textContent = 'Kopiert!';
                setTimeout(() => { this.textContent = 'Kopieren'; }, 2000);
            });
        }
        
        if (copyLinkBtn) {
            copyLinkBtn.addEventListener('click', function() {
                copyToClipboard(directLinkEl.textContent);
                this.textContent = 'Kopiert!';
                setTimeout(() => { this.textContent = 'Kopieren'; }, 2000);
            });
        }
    }
    
    // Text in die Zwischenablage kopieren
    function copyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    }
    
    // Starte das Laden des Projekts
    loadProject().catch(error => {
        console.error('Fehler beim Initialisieren:', error);
    });
});
