// Ein vereinfachter 360° Viewer
document.addEventListener('DOMContentLoaded', function() {
    // Prüfen, ob wir auf der Viewer-Seite sind
    const urlParams = new URLSearchParams(window.location.search);
    const projectId = urlParams.get('project');
    
    if (!projectId) {
        console.error('Keine Projekt-ID in der URL gefunden');
        return;
    }
    
    console.log('Lade Projekt mit ID:', projectId);
    
    // Viewer-Container
    const viewerContainer = document.getElementById('product-viewer');
    if (!viewerContainer) {
        console.error('Viewer-Container nicht gefunden');
        return;
    }
    
    // Spinner anzeigen
    const spinner = document.getElementById('spinner');
    
    // Lade Projektdaten
    fetch(`/api/project/${projectId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Projekt konnte nicht geladen werden (Status: ${response.status})`);
            }
            return response.json();
        })
        .then(projectData => {
            console.log('Projektdaten geladen:', projectData);
            
            // Projektinformationen anzeigen
            document.querySelector('#project-name span').textContent = projectData.name || projectId;
            document.querySelector('#image-count span').textContent = projectData.images.length;
            
            // Bilder laden
            if (!projectData.images || projectData.images.length === 0) {
                throw new Error('Keine Bilder im Projekt gefunden');
            }
            
            // Spinner ausblenden
            spinner.style.display = 'none';
            
            // Bilder in den Viewer laden
            const images = projectData.images.map(img => `/static/projects/${projectId}/${img}`);
            console.log('Bildpfade:', images);
            
            // Erstelle Bilder-Container
            viewerContainer.innerHTML = '';
            
            // Erstes Bild anzeigen
            const mainImage = document.createElement('img');
            mainImage.src = images[0];
            mainImage.alt = 'Projekbild';
            mainImage.className = 'img-fluid main-image';
            mainImage.style.maxHeight = '400px';
            mainImage.style.margin = '0 auto';
            mainImage.style.display = 'block';
            
            viewerContainer.appendChild(mainImage);
            
            // Bilder-Auswahl erstellen
            const imageSelector = document.createElement('div');
            imageSelector.className = 'image-selector mt-3 d-flex flex-wrap justify-content-center';
            
            images.forEach((img, index) => {
                const thumbContainer = document.createElement('div');
                thumbContainer.className = 'thumb-container m-1';
                thumbContainer.style.width = '60px';
                thumbContainer.style.height = '60px';
                thumbContainer.style.overflow = 'hidden';
                thumbContainer.style.border = '1px solid #ddd';
                thumbContainer.style.borderRadius = '4px';
                thumbContainer.style.cursor = 'pointer';
                
                const thumbImg = document.createElement('img');
                thumbImg.src = img;
                thumbImg.alt = `Ansicht ${index + 1}`;
                thumbImg.className = 'img-fluid';
                thumbImg.style.width = '100%';
                thumbImg.style.height = '100%';
                thumbImg.style.objectFit = 'cover';
                
                thumbContainer.appendChild(thumbImg);
                
                // Beim Klick großes Bild wechseln
                thumbContainer.addEventListener('click', () => {
                    mainImage.src = img;
                });
                
                imageSelector.appendChild(thumbContainer);
            });
            
            viewerContainer.appendChild(imageSelector);
            
            // Mausrad-Navigation für das Hauptbild
            let currentIndex = 0;
            mainImage.addEventListener('wheel', (event) => {
                event.preventDefault();
                if (event.deltaY > 0) {
                    // Nach unten = nächstes Bild
                    currentIndex = (currentIndex + 1) % images.length;
                } else {
                    // Nach oben = vorheriges Bild
                    currentIndex = (currentIndex - 1 + images.length) % images.length;
                }
                mainImage.src = images[currentIndex];
            });
            
            // Maus-Drag-Navigation
            let isDragging = false;
            let startX = 0;
            
            mainImage.addEventListener('mousedown', (event) => {
                isDragging = true;
                startX = event.clientX;
                mainImage.style.cursor = 'grabbing';
            });
            
            document.addEventListener('mousemove', (event) => {
                if (!isDragging) return;
                
                const deltaX = event.clientX - startX;
                
                if (Math.abs(deltaX) > 30) {
                    // Genug Bewegung für Bildwechsel
                    if (deltaX > 0) {
                        // Nach rechts = vorheriges Bild
                        currentIndex = (currentIndex - 1 + images.length) % images.length;
                    } else {
                        // Nach links = nächstes Bild
                        currentIndex = (currentIndex + 1) % images.length;
                    }
                    mainImage.src = images[currentIndex];
                    startX = event.clientX;
                }
            });
            
            document.addEventListener('mouseup', () => {
                isDragging = false;
                mainImage.style.cursor = 'grab';
            });
            
            // Touch-Events für mobile Geräte
            mainImage.addEventListener('touchstart', (event) => {
                isDragging = true;
                startX = event.touches[0].clientX;
            });
            
            document.addEventListener('touchmove', (event) => {
                if (!isDragging) return;
                
                const deltaX = event.touches[0].clientX - startX;
                
                if (Math.abs(deltaX) > 30) {
                    if (deltaX > 0) {
                        currentIndex = (currentIndex - 1 + images.length) % images.length;
                    } else {
                        currentIndex = (currentIndex + 1) % images.length;
                    }
                    mainImage.src = images[currentIndex];
                    startX = event.touches[0].clientX;
                }
            });
            
            document.addEventListener('touchend', () => {
                isDragging = false;
            });
        })
        .catch(error => {
            console.error('Fehler beim Laden des Projekts:', error);
            spinner.style.display = 'none';
            
            // Fehlermeldung anzeigen
            viewerContainer.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    ${error.message || 'Fehler beim Laden des Projekts'}
                </div>
            `;
        });
    
    // Play-Button-Funktionalität
    const playBtn = document.getElementById('play-btn');
    if (playBtn) {
        let isPlaying = false;
        let playInterval = null;
        
        playBtn.addEventListener('click', () => {
            if (isPlaying) {
                // Animation stoppen
                clearInterval(playInterval);
                playBtn.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
                isPlaying = false;
            } else {
                // Animation starten
                let currentIndex = 0;
                const mainImage = document.querySelector('.main-image');
                if (!mainImage) return;
                
                playInterval = setInterval(() => {
                    fetch(`/api/project/${projectId}`)
                        .then(response => response.json())
                        .then(projectData => {
                            const images = projectData.images.map(img => `/static/projects/${projectId}/${img}`);
                            currentIndex = (currentIndex + 1) % images.length;
                            mainImage.src = images[currentIndex];
                        });
                }, 500);
                
                playBtn.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
                isPlaying = true;
            }
        });
    }
});
