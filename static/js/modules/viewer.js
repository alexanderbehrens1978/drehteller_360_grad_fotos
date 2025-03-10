// viewer.js - Modul für den 360°-Viewer
import api from './api.js';

const viewer = {
    config: {
        currentIndex: 0,
        images: [],
        isPlaying: false,
        isDragging: false,
        startX: 0,
        playInterval: null,
        zoom: 1.0,
        maxZoom: 3.0,
        minZoom: 0.5,
        zoomStep: 0.1
    },
    
    elements: {
        container: null,
        mainImage: null,
        thumbnails: null,
        spinner: null,
        playButton: null,
        projectName: null,
        imageCount: null
    },
    
    // Viewer initialisieren
    init: async function(containerId, projectId) {
        try {
            // Elemente suchen
            this.elements.container = document.getElementById(containerId);
            this.elements.spinner = document.getElementById('spinner');
            this.elements.playButton = document.getElementById('play-btn');
            this.elements.projectName = document.querySelector('#project-name span');
            this.elements.imageCount = document.querySelector('#image-count span');
            
            if (!this.elements.container) {
                throw new Error('Viewer-Container nicht gefunden');
            }
            
            // Projekt laden
            const projectData = await api.getProject(projectId);
            
            // Projektinformationen anzeigen
            this.elements.projectName.textContent = projectData.name || projectId;
            this.elements.imageCount.textContent = projectData.images ? projectData.images.length : 0;
            
            // Bilder verarbeiten
            if (!projectData.images || projectData.images.length === 0) {
                throw new Error('Keine Bilder im Projekt gefunden');
            }
            
            this.config.images = projectData.images.map(img => `/static/projects/${projectId}/${img}`);
            
            // UI erstellen
            this.createViewerUI();
            
            // Events registrieren
            this.setupEvents();
            
            return true;
        } catch (error) {
            console.error('Fehler beim Initialisieren des Viewers:', error);
            this.showError(error.message);
            return false;
        }
    },
    
    // Viewer-UI erstellen
    createViewerUI: function() {
        // Spinner ausblenden
        if (this.elements.spinner) {
            this.elements.spinner.style.display = 'none';
        }
        
        // Container leeren
        this.elements.container.innerHTML = '';
        
        // Hauptbild erstellen
        this.elements.mainImage = document.createElement('img');
        this.elements.mainImage.src = this.config.images[0];
        this.elements.mainImage.alt = 'Hauptbild';
        this.elements.mainImage.className = 'img-fluid main-image';
        this.elements.mainImage.style.maxHeight = '400px';
        this.elements.mainImage.style.margin = '0 auto';
        this.elements.mainImage.style.display = 'block';
        this.elements.mainImage.style.cursor = 'grab';
        
        this.elements.container.appendChild(this.elements.mainImage);
        
        // Thumbnails erstellen
        const thumbnailsContainer = document.createElement('div');
        thumbnailsContainer.className = 'thumbnails-container mt-3 d-flex flex-wrap justify-content-center';
        this.elements.thumbnails = thumbnailsContainer;
        
        this.config.images.forEach((imgSrc, index) => {
            const thumbContainer = document.createElement('div');
            thumbContainer.className = 'thumb-container m-1';
            thumbContainer.style.width = '60px';
            thumbContainer.style.height = '60px';
            thumbContainer.style.overflow = 'hidden';
            thumbContainer.style.border = index === 0 ? '2px solid #0d6efd' : '1px solid #ddd';
            thumbContainer.style.borderRadius = '4px';
            thumbContainer.style.cursor = 'pointer';
            thumbContainer.dataset.index = index;
            
            const thumbImg = document.createElement('img');
            thumbImg.src = imgSrc;
            thumbImg.alt = `Miniaturansicht ${index + 1}`;
            thumbImg.className = 'img-fluid';
            thumbImg.style.width = '100%';
            thumbImg.style.height = '100%';
            thumbImg.style.objectFit = 'cover';
            
            thumbContainer.appendChild(thumbImg);
            thumbnailsContainer.appendChild(thumbContainer);
            
            // Klick-Event für Thumbnail
            thumbContainer.addEventListener('click', () => {
                this.showImage(index);
            });
        });
        
        this.elements.container.appendChild(thumbnailsContainer);
    },
    
    // Events einrichten
    setupEvents: function() {
        // Maus-Events für Hauptbild
        this.elements.mainImage.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Touch-Events für mobile Geräte
        this.elements.mainImage.addEventListener('touchstart', this.handleTouchStart.bind(this));
        document.addEventListener('touchmove', this.handleTouchMove.bind(this));
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));
        
        // Play-Button
        if (this.elements.playButton) {
            this.elements.playButton.addEventListener('click', this.toggleAutoRotation.bind(this));
        }
        
        // Zoom-Buttons
        const zoomInBtn = document.getElementById('zoom-in-btn');
        const zoomOutBtn = document.getElementById('zoom-out-btn');
        
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', this.zoomIn.bind(this));
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', this.zoomOut.bind(this));
        }
        
        // Mausrad-Event für Zoom
        this.elements.mainImage.addEventListener('wheel', this.handleWheel.bind(this));
    },
    
    // Bild anzeigen
    showImage: function(index) {
        if (index < 0 || index >= this.config.images.length) {
            return;
        }
        
        // Aktuellen Index aktualisieren
        this.config.currentIndex = index;
        
        // Hauptbild aktualisieren
        this.elements.mainImage.src = this.config.images[index];
        
        // Thumbnail-Hervorhebung aktualisieren
        const thumbnails = this.elements.thumbnails.querySelectorAll('.thumb-container');
        thumbnails.forEach((thumb, i) => {
            thumb.style.border = i === index ? '2px solid #0d6efd' : '1px solid #ddd';
        });
    },
    
    // Automatische Rotation starten/stoppen
    toggleAutoRotation: function() {
        if (this.config.isPlaying) {
            // Animation stoppen
            clearInterval(this.config.playInterval);
            this.elements.playButton.innerHTML = '<i class="bi bi-play-fill"></i> Auto-Rotation';
            this.config.isPlaying = false;
        } else {
            // Animation starten
            this.config.playInterval = setInterval(() => {
                const nextIndex = (this.config.currentIndex + 1) % this.config.images.length;
                this.showImage(nextIndex);
            }, 300);
            
            this.elements.playButton.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
            this.config.isPlaying = true;
        }
    },
    
    // Maus-Event-Handler
    handleMouseDown: function(e) {
        e.preventDefault();
        this.config.isDragging = true;
        this.config.startX = e.clientX;
        this.elements.mainImage.style.cursor = 'grabbing';
        
        if (this.config.isPlaying) {
            this.toggleAutoRotation();
        }
    },
    
    handleMouseMove: function(e) {
        if (!this.config.isDragging) return;
        
        const deltaX = e.clientX - this.config.startX;
        
        if (Math.abs(deltaX) > 30) {
            const direction = deltaX > 0 ? -1 : 1;
            const newIndex = (this.config.currentIndex + direction + this.config.images.length) % this.config.images.length;
            
            this.showImage(newIndex);
            this.config.startX = e.clientX;
        }
    },
    
    handleMouseUp: function() {
        this.config.isDragging = false;
        if (this.elements.mainImage) {
            this.elements.mainImage.style.cursor = 'grab';
        }
    },
    
    // Touch-Event-Handler
    handleTouchStart: function(e) {
        e.preventDefault();
        this.config.isDragging = true;
        this.config.startX = e.touches[0].clientX;
        
        if (this.config.isPlaying) {
            this.toggleAutoRotation();
        }
    },
    
    handleTouchMove: function(e) {
        if (!this.config.isDragging) return;
        
        const deltaX = e.touches[0].clientX - this.config.startX;
        
        if (Math.abs(deltaX) > 30) {
            const direction = deltaX > 0 ? -1 : 1;
            const newIndex = (this.config.currentIndex + direction + this.config.images.length) % this.config.images.length;
            
            this.showImage(newIndex);
            this.config.startX = e.touches[0].clientX;
        }
    },
    
    handleTouchEnd: function() {
        this.config.isDragging = false;
    },
    
    // Zoom-Funktionen
    zoomIn: function() {
        if (this.config.zoom < this.config.maxZoom) {
            this.config.zoom += this.config.zoomStep;
            this.applyZoom();
        }
    },
    
    zoomOut: function() {
        if (this.config.zoom > this.config.minZoom) {
            this.config.zoom -= this.config.zoomStep;
            this.applyZoom();
        }
    },
    
    applyZoom: function() {
        this.elements.mainImage.style.transform = `scale(${this.config.zoom})`;
    },
    
    handleWheel: function(e) {
        e.preventDefault();
        
        if (e.deltaY < 0) {
            this.zoomIn();
        } else {
            this.zoomOut();
        }
    },
    
    // Fehler anzeigen
    showError: function(message) {
        if (this.elements.spinner) {
            this.elements.spinner.style.display = 'none';
        }
        
        this.elements.container.innerHTML = `
            <div class="alert alert-danger m-3">
                <i class="bi bi-exclamation-triangle me-2"></i>
                ${message || 'Ein Fehler ist aufgetreten'}
            </div>
        `;
    }
};

export default viewer;
