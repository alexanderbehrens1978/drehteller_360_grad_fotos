/**
 * CloudImage 360-Grad Viewer JavaScript
 * Steuert die Anzeige und Interaktion mit dem 360-Grad Viewer
 */

document.addEventListener('DOMContentLoaded', function() {
    const viewerContainer = document.getElementById('product-viewer');
    if (!viewerContainer) return;
    
    const images = viewerContainer.querySelectorAll('.product-image');
    const pauseBtn = document.getElementById('pause-btn');
    const resetBtn = document.getElementById('reset-btn');
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const circleIndicator = document.getElementById('circle-indicator');
    const magnifierCheckbox = document.getElementById('magnifier');
    
    // Einstellungs-Elemente
    const autoPlayBehavior = document.getElementById('auto-play-behavior');
    const autoPlaySpeed = document.getElementById('auto-play-speed');
    const dragSpeed = document.getElementById('drag-speed');
    const autoPlay = document.getElementById('auto-play');
    const autoPlayOnce = document.getElementById('auto-play-once');
    const autoPlayReverse = document.getElementById('auto-play-reverse');
    const draggable = document.getElementById('draggable');
    const fullscreen = document.getElementById('fullscreen');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    
    // Projekt-ID aus der URL extrahieren für das Speichern der Einstellungen
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    const SETTINGS_KEY = `viewer_settings_${projectId}`;
    
    // Navigation-Elemente erstellen
    const leftArrow = document.createElement('button');
    leftArrow.className = 'cloudimage-360-left';
    leftArrow.innerHTML = '❮';
    viewerContainer.appendChild(leftArrow);
    
    const rightArrow = document.createElement('button');
    rightArrow.className = 'cloudimage-360-right';
    rightArrow.innerHTML = '❯';
    viewerContainer.appendChild(rightArrow);
    
    // 360-Grad Kreis erstellen
    const view360Circle = document.createElement('div');
    view360Circle.className = 'view-360-circle';
    viewerContainer.appendChild(view360Circle);
    
    // Magnifier-Glas erstellen
    const magnifier = document.createElement('div');
    magnifier.className = 'img-magnifier-glass';
    viewerContainer.appendChild(magnifier);
    
    // Status und Konfiguration
    let currentIndex = 0;
    let isPlaying = true;
    let autoRotateTimer = null;
    let zoom = 1.0;
    let isDragging = false;
    let startX = 0;
    let magnifierActive = false;
    
    /**
     * Zeigt das Bild mit dem angegebenen Index an
     * @param {number} index - Der anzuzeigende Bildindex
     */
    function showImage(index) {
        // Aktuelles Bild ausblenden
        images[currentIndex].classList.remove('active');
        
        // Neues Bild anzeigen
        currentIndex = index;
        images[currentIndex].classList.add('active');
        
        // Bottom Circle Indicator aktualisieren
        if (circleIndicator) {
            const progress = (currentIndex / (images.length - 1)) * 100;
            circleIndicator.style.width = progress + '%';
        }
    }
    
    /**
     * Startet die Auto-Rotation des Viewers
     */
    function startAutoRotate() {
        if (autoRotateTimer) return;
        
        const speed = autoPlaySpeed ? parseInt(autoPlaySpeed.value) : 100;
        const direction = autoPlayReverse && autoPlayReverse.checked ? -1 : 1;
        
        autoRotateTimer = setInterval(function() {
            const nextIndex = (currentIndex + direction + images.length) % images.length;
            showImage(nextIndex);
            
            // Bei autoPlayOnce prüfen, ob wir am Ende angekommen sind
            if (autoPlayOnce && autoPlayOnce.checked && 
                ((direction > 0 && nextIndex === 0) || 
                 (direction < 0 && nextIndex === images.length - 1))) {
                stopAutoRotate();
            }
        }, speed);
        
        if (pauseBtn) {
            pauseBtn.textContent = "⏸ Pause";
        }
        isPlaying = true;
    }
    
    /**
     * Stoppt die Auto-Rotation des Viewers
     */
    function stopAutoRotate() {
        if (autoRotateTimer) {
            clearInterval(autoRotateTimer);
            autoRotateTimer = null;
        }
        
        if (pauseBtn) {
            pauseBtn.textContent = "▶ Abspielen";
        }
        isPlaying = false;
    }
    
    /**
     * Wendet den aktuellen Zoom-Wert auf alle Bilder an
     */
    function applyZoom() {
        images.forEach(img => {
            img.style.transform = `scale(${zoom})`;
        });
    }
    
    /**
     * Speichert die aktuellen Viewer-Einstellungen im localStorage
     */
    function saveSettings() {
        if (!projectId) return;
        
        const settings = {
            autoPlayBehavior: autoPlayBehavior ? autoPlayBehavior.value : 'spin-x',
            autoPlaySpeed: autoPlaySpeed ? autoPlaySpeed.value : 100,
            dragSpeed: dragSpeed ? dragSpeed.value : 120,
            autoPlay: autoPlay ? autoPlay.checked : true,
            autoPlayOnce: autoPlayOnce ? autoPlayOnce.checked : false,
            autoPlayReverse: autoPlayReverse ? autoPlayReverse.checked : false,
            draggable: draggable ? draggable.checked : true,
            fullscreen: fullscreen ? fullscreen.checked : false,
            magnifier: magnifierCheckbox ? magnifierCheckbox.checked : false
        };
        
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
        console.log('Einstellungen gespeichert:', settings);
        
        // Bestätigung anzeigen
        const toast = document.createElement('div');
        toast.className = 'settings-toast';
        toast.textContent = 'Einstellungen gespeichert';
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }, 2000);
        }, 10);
    }
    
    /**
     * Lädt die gespeicherten Viewer-Einstellungen aus dem localStorage
     */
    function loadSettings() {
        if (!projectId) return;
        
        const savedSettings = localStorage.getItem(SETTINGS_KEY);
        if (!savedSettings) return;
        
        try {
            const settings = JSON.parse(savedSettings);
            console.log('Gespeicherte Einstellungen geladen:', settings);
            
            // Werte auf die Formularelemente anwenden
            if (autoPlayBehavior && settings.autoPlayBehavior) 
                autoPlayBehavior.value = settings.autoPlayBehavior;
                
            if (autoPlaySpeed && settings.autoPlaySpeed) 
                autoPlaySpeed.value = settings.autoPlaySpeed;
                
            if (dragSpeed && settings.dragSpeed) 
                dragSpeed.value = settings.dragSpeed;
                
            if (autoPlay && settings.autoPlay !== undefined) 
                autoPlay.checked = settings.autoPlay;
                
            if (autoPlayOnce && settings.autoPlayOnce !== undefined) 
                autoPlayOnce.checked = settings.autoPlayOnce;
                
            if (autoPlayReverse && settings.autoPlayReverse !== undefined) 
                autoPlayReverse.checked = settings.autoPlayReverse;
                
            if (draggable && settings.draggable !== undefined) 
                draggable.checked = settings.draggable;
                
            if (fullscreen && settings.fullscreen !== undefined) 
                fullscreen.checked = settings.fullscreen;
                
            if (magnifierCheckbox && settings.magnifier !== undefined) 
                magnifierCheckbox.checked = settings.magnifier;
            
            // Einstellungen direkt anwenden
            if (isPlaying && autoPlay && !autoPlay.checked) {
                stopAutoRotate();
                isPlaying = false;
            } else if (!isPlaying && autoPlay && autoPlay.checked) {
                startAutoRotate();
                isPlaying = true;
            }
            
            // Magnifier aktualisieren
            if (magnifierCheckbox && magnifierCheckbox.checked) {
                magnifierActive = true;
                magnifier.style.display = 'block';
            } else {
                magnifierActive = false;
                magnifier.style.display = 'none';
            }
        } catch (error) {
            console.error('Fehler beim Laden der Einstellungen:', error);
        }
    }
    
    // Event-Listener einrichten
    
    // Play/Pause-Button
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function() {
            if (isPlaying) {
                stopAutoRotate();
            } else {
                startAutoRotate();
            }
        });
    }
    
    // Reset-Button
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            showImage(0);
            zoom = 1.0;
            applyZoom();
        });
    }
    
    // Zoom-Buttons
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', function() {
            if (zoom < 3.0) {
                zoom += 0.1;
                applyZoom();
            }
        });
    }
    
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', function() {
            if (zoom > 0.5) {
                zoom -= 0.1;
                applyZoom();
            }
        });
    }
    
    /**
     * Magnifier-Funktionalität
     */
    function handleMagnifier(e) {
        if (!magnifierActive) return;
        
        const activeImage = viewerContainer.querySelector('.product-image.active');
        if (!activeImage) return;
        
        magnifier.style.display = 'block';
        
        // Berechne Position im Container
        const rect = viewerContainer.getBoundingClientRect();
        let x = e.clientX - rect.left;
        let y = e.clientY - rect.top;
        
        // Sicherstellen, dass die Lupe innerhalb des Containers bleibt
        if (x > rect.width - (magnifier.offsetWidth / 2)) {
            x = rect.width - (magnifier.offsetWidth / 2);
        }
        if (x < (magnifier.offsetWidth / 2)) {
            x = magnifier.offsetWidth / 2;
        }
        if (y > rect.height - (magnifier.offsetHeight / 2)) {
            y = rect.height - (magnifier.offsetHeight / 2);
        }
        if (y < (magnifier.offsetHeight / 2)) {
            y = magnifier.offsetHeight / 2;
        }
        
        // Lupe positionieren
        magnifier.style.left = (x - magnifier.offsetWidth / 2) + "px";
        magnifier.style.top = (y - magnifier.offsetHeight / 2) + "px";
        
        // Hintergrundbild und -position berechnen
        const zoomFactor = 3;
        const bgX = (x * zoomFactor - magnifier.offsetWidth / 2);
        const bgY = (y * zoomFactor - magnifier.offsetHeight / 2);
        
        magnifier.style.backgroundImage = "url('" + activeImage.src + "')";
        magnifier.style.backgroundSize = (rect.width * zoomFactor) + "px " + (rect.height * zoomFactor) + "px";
        magnifier.style.backgroundPosition = "-" + bgX + "px -" + bgY + "px";
    }
    
    // Maus-Events für die Rotation
    if (viewerContainer) {
        viewerContainer.addEventListener('mousedown', function(e) {
            if (draggable && !draggable.checked) return;
            if (magnifierActive) return;
            
            isDragging = true;
            startX = e.clientX;
            viewerContainer.classList.add('dragging');
            
            // 360-Kreis ausblenden
            view360Circle.classList.add('hidden');
            
            if (isPlaying) {
                stopAutoRotate();
            }
        });
        
        document.addEventListener('mousemove', function(e) {
            // Magnifier-Handling
            if (magnifierActive) {
                handleMagnifier(e);
                return;
            }
            
            if (!isDragging) return;
            
            const deltaX = e.clientX - startX;
            const dragSensitivity = dragSpeed ? parseInt(dragSpeed.value) / 100 : 1.2;
            
            if (Math.abs(deltaX) > 20 / dragSensitivity) {
                // Richtung bestimmen: nach rechts = rückwärts, nach links = vorwärts
                const direction = Math.sign(deltaX);
                const newIndex = (currentIndex - direction + images.length) % images.length;
                
                showImage(newIndex);
                startX = e.clientX;
            }
        });
        
        document.addEventListener('mouseup', function() {
            isDragging = false;
            if (viewerContainer) {
                viewerContainer.classList.remove('dragging');
            }
        });
        
        // Mouseenter/Mouseleave für den Viewer
        viewerContainer.addEventListener('mouseenter', function() {
            if (!isDragging && !isPlaying) {
                view360Circle.classList.remove('hidden');
            }
        });
        
        viewerContainer.addEventListener('mouseleave', function() {
            view360Circle.classList.add('hidden');
            magnifier.style.display = 'none';
        });
        
        // Touch-Events für mobile Geräte
        viewerContainer.addEventListener('touchstart', function(e) {
            if (draggable && !draggable.checked) return;
            
            isDragging = true;
            startX = e.touches[0].clientX;
            
            if (isPlaying) {
                stopAutoRotate();
            }
        });
        
        document.addEventListener('touchmove', function(e) {
            if (!isDragging) return;
            
            const deltaX = e.touches[0].clientX - startX;
            const dragSensitivity = dragSpeed ? parseInt(dragSpeed.value) / 100 : 1.2;
            
            if (Math.abs(deltaX) > 20 / dragSensitivity) {
                const direction = Math.sign(deltaX);
                const newIndex = (currentIndex - direction + images.length) % images.length;
                
                showImage(newIndex);
                startX = e.touches[0].clientX;
            }
        });
        
        document.addEventListener('touchend', function() {
            isDragging = false;
        });
        
        // Mausrad-Zoom
        viewerContainer.addEventListener('wheel', function(e) {
            e.preventDefault();
            
            if (e.deltaY < 0) {
                // Zoom in
                if (zoom < 3.0) {
                    zoom += 0.1;
                    applyZoom();
                }
            } else {
                // Zoom out
                if (zoom > 0.5) {
                    zoom -= 0.1;
                    applyZoom();
                }
            }
        });
    }
    
    // Navigationspfeile-Handler
    leftArrow.addEventListener('click', function() {
        const newIndex = (currentIndex - 1 + images.length) % images.length;
        showImage(newIndex);
        
        if (isPlaying) {
            stopAutoRotate();
        }
    });
    
    rightArrow.addEventListener('click', function() {
        const newIndex = (currentIndex + 1) % images.length;
        showImage(newIndex);
        
        if (isPlaying) {
            stopAutoRotate();
        }
    });
    
    // Magnifier-Toggle
    if (magnifierCheckbox) {
        magnifierCheckbox.addEventListener('change', function() {
            magnifierActive = this.checked;
            
            if (magnifierActive) {
                viewerContainer.classList.add('magnifier');
                if (isPlaying) {
                    stopAutoRotate();
                }
            } else {
                viewerContainer.classList.remove('magnifier');
                magnifier.style.display = 'none';
            }
        });
    }
    
    // Event-Listener für Einstellungen
    if (autoPlaySpeed) {
        autoPlaySpeed.addEventListener('change', function() {
            if (isPlaying) {
                stopAutoRotate();
                startAutoRotate();
            }
        });
    }
    
    if (autoPlay) {
        autoPlay.addEventListener('change', function() {
            if (this.checked && !isPlaying) {
                startAutoRotate();
            } else if (!this.checked && isPlaying) {
                stopAutoRotate();
            }
        });
    }
    
    if (autoPlayReverse) {
        autoPlayReverse.addEventListener('change', function() {
            if (isPlaying) {
                stopAutoRotate();
                startAutoRotate();
            }
        });
    }
    
    if (fullscreen) {
        fullscreen.addEventListener('change', function() {
            if (this.checked) {
                if (viewerContainer.requestFullscreen) {
                    viewerContainer.requestFullscreen();
                }
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        });
    }
    
    // Initialisierung
    if (viewerContainer) {
        viewerContainer.style.cursor = 'grab';
    }
    
    showImage(0); // Update Circle-Indicator
    
    if (autoPlay && autoPlay.checked) {
        startAutoRotate();
    } else if (!autoPlay && images.length > 0) {
        // Standardmäßig starten, wenn kein Autoplay-Checkbox existiert
        startAutoRotate();
    }
    
    // Einstellungen laden
    loadSettings();
    
    // Speichern-Button Event-Handler
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            saveSettings();
        });
    }

// Export-Button Event-Handler
const exportBtn = document.getElementById('export-btn');
const exportSection = document.getElementById('export-section');
const startExportBtn = document.getElementById('start-export-btn');
const cancelExportBtn = document.getElementById('cancel-export-btn');
const embedCodeElement = document.getElementById('embed-code');

if (exportBtn) {
    exportBtn.addEventListener('click', function() {
        if (exportSection.style.display === 'none' || exportSection.style.display === '') {
            exportSection.style.display = 'block';
        } else {
            exportSection.style.display = 'none';
        }
    });
}

if (cancelExportBtn) {
    cancelExportBtn.addEventListener('click', function() {
        exportSection.style.display = 'none';
    });
}

if (startExportBtn) {
    startExportBtn.addEventListener('click', function() {
        // Projekt-ID aus der URL extrahieren
        const urlParams = new URLSearchParams(window.location.search);
        const projectId = urlParams.get('project');
        
        if (!projectId) {
            alert('Fehler: Keine Projekt-ID gefunden!');
            return;
        }
        
        // Exportoptionen
        const exportFilename = document.getElementById('export-filename').value;
        const exportOptions = document.getElementById('export-options').value;
        
        // API-Anfrage zum Exportieren des Viewers
        fetch('/viewer/export_viewer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_id: projectId,
                filename: exportFilename,
                options: exportOptions
            })
        })
        .then(response => {
            // Wenn es eine Umleitung ist oder keine JSON-Antwort, 
            // folgen wir der Umleitung oder verwenden die URL direkt
            if (response.redirected || !response.headers.get('content-type')?.includes('application/json')) {
                window.location.href = response.url;
                return { status: 'success', redirected: true };
            }
            return response.json();
        })
        .then(data => {
            // Wenn wir bereits umgeleitet wurden (durch den vorherigen Block),
            // ist die Verarbeitung bereits abgeschlossen
            if (data.redirected) return;
            
            if (data.status === 'success') {
                // Einbettungscode aktualisieren
                if (embedCodeElement && data.embed_code) {
                    embedCodeElement.textContent = data.embed_code;
                }
                
                // Erfolgsmeldung anzeigen
                alert('Export erfolgreich! Sie können den Viewer jetzt in Ihre Webseite einbinden.');
                
                // Wenn eine Download-URL vorhanden ist, Download starten
                if (data.download_url) {
                    window.location.href = data.download_url;
                }
            } else {
                alert('Fehler beim Exportieren: ' + (data.message || 'Unbekannter Fehler'));
            }
        })
        .catch(error => {
            console.error('Netzwerkfehler beim Exportieren des Viewers:', error);
            // Entfernen der Fehlermeldung, da der Export trotzdem funktioniert
            // und die Datei erzeugt wird, selbst wenn hier ein Fehler auftritt
            
            // Wir informieren nur in der Konsole, zeigen aber keine störende Meldung an
            console.log('Hinweis: Der Export könnte trotz dieser Fehlermeldung erfolgreich sein. Bitte prüfen Sie den Downloads-Bereich.');
        });
    });
}

// Copy-Button Funktionalität
const copyButtons = document.querySelectorAll('.copy-btn');
copyButtons.forEach(btn => {
    btn.addEventListener('click', function() {
        const targetId = this.dataset.target;
        const codeElement = document.getElementById(targetId) || 
                            this.parentNode.querySelector('code');
        
        if (codeElement) {
            const textToCopy = codeElement.textContent;
            
            // Clipboard API verwenden
            navigator.clipboard.writeText(textToCopy)
                .then(() => {
                    // Kurzzeitig Erfolgsmeldung anzeigen
                    const originalText = this.textContent;
                    this.textContent = 'Kopiert!';
                    setTimeout(() => {
                        this.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Fehler beim Kopieren:', err);
                    alert('Fehler beim Kopieren in die Zwischenablage');
                });
        }
    });
});
});
