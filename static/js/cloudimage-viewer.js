/**
 * CloudImage 360-Grad Viewer JavaScript
 * Steuert die Anzeige und Interaktion mit dem 360-Grad Viewer
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM geladen, initialisiere Viewer...');
    const viewerContainer = document.getElementById('viewer-container');
    const viewer = document.getElementById('viewer');
    
    if (!viewerContainer || !viewer) {
        console.error('Viewer-Container oder Viewer nicht gefunden!', {
            viewerContainer: !!viewerContainer,
            viewer: !!viewer
        });
        return;
    }
    
    // Bereits vorhandene Bilder zuerst prüfen
    let images = Array.from(viewer.querySelectorAll('.product-image'));
    
    // Wenn Bilder bereits im HTML vorhanden sind, verwende diese
    if (images.length > 0) {
        console.log(`${images.length} Bilder bereits im HTML gefunden, verwende diese direkt`);
        initializeViewer(images);
        return;
    }
    
    // Ansonsten lade dynamisch
    // Lade die Parameter aus dem Viewer-Element
    const folderPath = viewer.getAttribute('data-folder');
    const filenamePattern = viewer.getAttribute('data-filename-pattern');
    const imageCount = parseInt(viewer.getAttribute('data-amount'));
    
    // Überprüfe, ob alle erforderlichen Attribute vorhanden sind
    if (!folderPath || !filenamePattern || isNaN(imageCount)) {
        console.error('Erforderliche Attribute fehlen oder sind ungültig!', { folderPath, filenamePattern, imageCount });
        return;
    }
    
    console.log('Lade 360° Viewer mit:', { folderPath, filenamePattern, imageCount });
    
    // Bildcontainer erstellen, falls er nicht bereits existiert
    let imageContainer = viewer.querySelector('.image-container');
    if (!imageContainer) {
        imageContainer = document.createElement('div');
        imageContainer.className = 'image-container';
        viewer.appendChild(imageContainer);
    } else {
        // Bestehenden Container leeren
        imageContainer.innerHTML = '';
    }
    
    // Ladestatus anzeigen
    const loaderElement = document.createElement('div');
    loaderElement.className = 'loader';
    loaderElement.textContent = 'Bilder werden geladen...';
    imageContainer.appendChild(loaderElement);
    
    // Bilder laden
    const dynamicImages = [];
    let loadedCount = 0;
    
    // Starte das Laden der Bilder
    for (let i = 0; i < imageCount; i++) {
        const img = document.createElement('img');
        img.className = 'product-image';
        img.alt = `Bild ${i+1} von ${imageCount}`;
        
        // Pfad zum Bild erstellen
        const index = i + 1;
        let imgFilename = filenamePattern
            .replace('{index}', index)
            .replace('{index:00}', index.toString().padStart(2, '0'))
            .replace('{index:000}', index.toString().padStart(3, '0'));
        
        // Achten Sie darauf, dass der Pfad korrekt ist
        const imgSrc = folderPath + imgFilename;
        console.log(`Lade Bild ${index}/${imageCount}: ${imgSrc}`);
        
        // Event-Listener für Laden und Fehler
        img.onload = function() {
            console.log(`Bild erfolgreich geladen: ${img.src}`);
            loadedCount++;
            
            if (loadedCount === 1) {
                // Das erste geladene Bild sofort anzeigen
                img.classList.add('active');
                console.log('Erstes Bild aktiviert');
            }
            
            if (loadedCount === imageCount) {
                // Alle Bilder geladen
                loaderElement.remove();
                console.log('Alle Bilder geladen!');
                initializeViewer(dynamicImages);
            }
        };
        
        img.onerror = function() {
            console.error(`Fehler beim Laden des Bildes: ${img.src}`);
            loadedCount++;
            if (loadedCount === imageCount) {
                loaderElement.remove();
                if (dynamicImages.length > 0) {
                    initializeViewer(dynamicImages);
                }
            }
        };
        
        // Füge das Bild dem Container hinzu und speichere es im Array
        imageContainer.appendChild(img);
        dynamicImages.push(img);
        
        // Starte das Laden des Bildes
        img.src = imgSrc;
    }
    
    function initializeViewer(imageElements) {
        // Ersten Frame anzeigen, wenn kein Bild im Ladevorgang aktiviert wurde
        if (!document.querySelector('.product-image.active') && imageElements.length > 0) {
            imageElements[0].classList.add('active');
            console.log('Erstes Bild per Timeout aktiviert');
        }
        
        // CircleIndicator erstellen oder vorhandenen finden
        let circleIndicator = document.querySelector('.circle-indicator');
        if (!circleIndicator) {
            circleIndicator = document.createElement('div');
            circleIndicator.className = 'circle-indicator';
            circleIndicator.id = 'circle-indicator';
            const bottomCircle = viewerContainer.querySelector('.bottom-circle');
            if (bottomCircle) {
                bottomCircle.appendChild(circleIndicator);
            } else {
                viewerContainer.appendChild(circleIndicator);
            }
        }
        
        // Buttons und andere UI-Elemente
        const playBtn = document.getElementById('play-btn');
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        const magnifierBtn = document.getElementById('magnifier-btn');
        const exportBtn = document.getElementById('export-btn');
        const settingsBtn = document.getElementById('settings-btn');
        const playIcon = document.getElementById('play-icon');
        
        console.log('UI-Elemente gefunden:', {
            playBtn: !!playBtn,
            fullscreenBtn: !!fullscreenBtn,
            magnifierBtn: !!magnifierBtn,
            exportBtn: !!exportBtn,
            settingsBtn: !!settingsBtn,
            playIcon: !!playIcon
        });
        
        // Status und Konfiguration
        let currentIndex = 0;
        let isPlaying = false;
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
            // Sicherstellen, dass der Index gültig ist
            if (index < 0) index = imageElements.length - 1;
            if (index >= imageElements.length) index = 0;
            
            // Aktuelles Bild ausblenden
            const currentImg = document.querySelector('.product-image.active');
            if (currentImg) {
                currentImg.classList.remove('active');
            }
            
            // Neues Bild anzeigen
            currentIndex = index;
            if (imageElements[currentIndex]) {
                imageElements[currentIndex].classList.add('active');
                console.log(`Bild ${currentIndex + 1} angezeigt`);
                
                // Bottom Circle Indicator aktualisieren
                if (circleIndicator) {
                    const progress = (currentIndex / (imageElements.length - 1)) * 100;
                    circleIndicator.style.width = progress + '%';
                }
            } else {
                console.error(`Bild mit Index ${index} nicht gefunden!`);
            }
        }
        
        /**
         * Startet die Auto-Rotation des Viewers
         */
        function startAutoRotate() {
            // Wenn bereits läuft, zuerst stoppen
            stopAutoRotate();
            
            // Geschwindigkeit aus den Einstellungen holen oder Standard verwenden
            const speed = autoPlaySpeed ? parseInt(autoPlaySpeed.value) : 100;
            
            // Auto-Rotation starten
            autoRotateTimer = setInterval(function() {
                // Je nach Richtung nächstes oder vorheriges Bild anzeigen
                const reverse = autoPlayReverse && autoPlayReverse.checked;
                
                if (reverse) {
                    showImage(currentIndex - 1);
                } else {
                    showImage(currentIndex + 1);
                }
                
                // Bei einmaligem Abspielen prüfen, ob wir am Ende sind
                if (autoPlayOnce && autoPlayOnce.checked) {
                    if ((reverse && currentIndex === 0) || (!reverse && currentIndex === imageElements.length - 1)) {
                        stopAutoRotate();
                    }
                }
            }, speed);
            
            if (playIcon) {
                playIcon.textContent = '⏸';
            }
            isPlaying = true;
        }
        
        /**
         * Stoppt die Auto-Rotation des Viewers
         */
        function stopAutoRotate() {
            // Timer zurücksetzen, falls vorhanden
            if (autoRotateTimer) {
                clearInterval(autoRotateTimer);
                autoRotateTimer = null;
            }
            
            if (playIcon) {
                playIcon.textContent = '▶';
            }
            isPlaying = false;
        }
        
        // Event-Listener einrichten
        
        // Play/Pause-Button
        if (playBtn) {
            playBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Play/Pause Button geklickt');
                
                if (isPlaying) {
                    stopAutoRotate();
                } else {
                    startAutoRotate();
                }
            });
        }
        
        // Vollbild-Button
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Vollbild Button geklickt');
                
                // Finde das Element, das in den Vollbildmodus gehen soll
                const elem = viewerContainer;
                
                // Vollbildmodus umschalten
                if (!document.fullscreenElement) {
                    // In Vollbild gehen
                    if (elem.requestFullscreen) {
                        elem.requestFullscreen();
                    } else if (elem.mozRequestFullScreen) { /* Firefox */
                        elem.mozRequestFullScreen();
                    } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
                        elem.webkitRequestFullscreen();
                    } else if (elem.msRequestFullscreen) { /* IE/Edge */
                        elem.msRequestFullscreen();
                    }
                } else {
                    // Vollbild beenden
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    } else if (document.mozCancelFullScreen) { /* Firefox */
                        document.mozCancelFullScreen();
                    } else if (document.webkitExitFullscreen) { /* Chrome, Safari & Opera */
                        document.webkitExitFullscreen();
                    } else if (document.msExitFullscreen) { /* IE/Edge */
                        document.msExitFullscreen();
                    }
                }
            });
        }
        
        // Export-Button
        if (exportBtn) {
            exportBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Export Button geklickt');
                
                // Projekt-ID aus dem globalen Kontext holen
                const projectId = window.projectId || document.querySelector('meta[name="project-id"]')?.content;
                
                if (projectId) {
                    // Zur Export-Optionen-Seite navigieren
                    window.location.href = `/export/options/${projectId}`;
                } else {
                    console.error('Projekt-ID nicht gefunden!');
                    alert('Fehler: Projekt-ID konnte nicht ermittelt werden.');
                }
            });
        }
        
        // Schließen-Button für Modal
        const closeBtn = document.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                const exportModal = document.getElementById('export-modal');
                if (exportModal) {
                    exportModal.style.display = 'none';
                }
            });
        }
        
        // Settings-Button
        if (settingsBtn) {
            settingsBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('Settings Button geklickt');
                
                // Toggle der Einstellungen
                const settingsSection = document.querySelector('.viewer-settings');
                if (settingsSection) {
                    settingsSection.classList.toggle('visible');
                }
            });
        }
        
        // Setting-Elemente
        const autoPlayBehavior = document.getElementById('auto-play-behavior');
        const autoPlaySpeed = document.getElementById('auto-play-speed');
        const dragSpeed = document.getElementById('drag-speed');
        const autoPlay = document.getElementById('auto-play');
        const autoPlayOnce = document.getElementById('auto-play-once');
        const autoPlayReverse = document.getElementById('auto-play-reverse');
        
        // Auto-Play bei Laden, wenn aktiviert
        if (autoPlay && autoPlay.checked) {
            startAutoRotate();
        }
    }
});
