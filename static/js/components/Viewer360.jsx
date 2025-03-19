/**
 * 360° Produktansicht Viewer mit Vollbild-Modus
 * Interaktiver Viewer für 360-Grad-Produktansichten
 */

class Viewer360 {
    constructor(containerId, projectId = null, options = {}) {
        // Grundkonfiguration
        this.container = document.getElementById(containerId);
        this.projectId = projectId;
        this.options = {
            logoText: "360°",
            logoSubText: "Klicken für 360° Ansicht",
            logoClass: "bg-blue-600 text-white rounded-lg p-4 shadow-lg inline-block",
            imageDirectory: projectId ? `/static/projects/${projectId}/` : '/static/sample_images/',
            autoRotate: false,
            autoRotateSpeed: 100,
            ...options
        };

        // Status-Variablen
        this.images = [];
        this.currentImageIndex = 0;
        this.isViewerOpen = false;
        this.isDragging = false;
        this.startX = 0;
        this.isLoading = true;
        this.autoRotateTimer = null;

        // Initialisierung
        this.init();
    }

    async init() {
        if (!this.container) {
            console.error('Container nicht gefunden!');
            return;
        }

        // UI-Elemente erstellen
        this.render();

        // Bilder laden
        await this.loadImages();
    }

    render() {
        // Logo erstellen, das als Trigger für den Viewer dient
        this.container.innerHTML = `
            <div class="viewer360-logo" style="cursor: pointer; text-align: center;">
                <div style="background-color: #2563eb; color: white; border-radius: 0.5rem; padding: 1rem; display: inline-block; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">${this.options.logoText}</div>
                    <div style="font-size: 0.875rem;">${this.options.logoSubText}</div>
                </div>
            </div>
        `;

        // Logo-Klick-Event hinzufügen
        this.container.querySelector('.viewer360-logo').addEventListener('click', () => this.openViewer());
    }

    async loadImages() {
        try {
            this.isLoading = true;

            // Wenn eine Projekt-ID angegeben ist, versuche die Bilder vom Server zu laden
            if (this.projectId) {
                try {
                    const response = await fetch(`/api/project/${this.projectId}`);

                    if (response.ok) {
                        const projectData = await response.json();

                        if (projectData.images && projectData.images.length > 0) {
                            this.images = projectData.images.map(img =>
                                `${this.options.imageDirectory}${img}`
                            );
                            console.log(`${projectData.images.length} Bilder für Projekt ${this.projectId} geladen`);
                        } else {
                            this.loadDemoImages();
                        }
                    } else {
                        this.loadDemoImages();
                    }
                } catch (error) {
                    console.error('Fehler beim Laden der Projektbilder:', error);
                    this.loadDemoImages();
                }
            } else {
                this.loadDemoImages();
            }

            this.isLoading = false;
        } catch (error) {
            console.error('Fehler beim Laden der Bilder:', error);
            this.isLoading = false;
        }
    }

    loadDemoImages() {
        // Demo-Bilder laden (36 Bilder für 10-Grad-Schritte)
        console.log('Lade Demo-Bilder als Fallback');
        this.images = Array.from({ length: 36 }, (_, i) =>
            `${this.options.imageDirectory}sample_image_${i % 10}.jpg`
        );
    }

    openViewer() {
        if (this.isLoading || this.images.length === 0) {
            console.log('Bilder werden noch geladen oder keine Bilder verfügbar');
            return;
        }

        this.isViewerOpen = true;

        // Scrolling verhindern
        document.body.style.overflow = 'hidden';

        // Vollbild-Viewer-Container erstellen
        const viewerContainer = document.createElement('div');
        viewerContainer.className = 'viewer360-fullscreen';
        viewerContainer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: black;
            z-index: 9999;
            display: flex;
            flex-direction: column;
        `;

        // Schließen-Button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '✕';
        closeButton.style.cssText = `
            position: absolute;
            top: 1rem;
            right: 1rem;
            z-index: 10;
            color: white;
            background-color: #dc2626;
            border: none;
            border-radius: 9999px;
            width: 2.5rem;
            height: 2.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 1rem;
        `;
        closeButton.addEventListener('click', () => this.closeViewer());

        // Bild-Container
        const imageContainer = document.createElement('div');
        imageContainer.className = 'viewer360-image-container';
        imageContainer.style.cssText = `
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
        `;

        // Bild-Element
        const image = document.createElement('img');
        image.src = this.images[this.currentImageIndex];
        image.alt = `360-Grad Ansicht ${this.currentImageIndex}`;
        image.style.cssText = `
            max-height: 100%;
            max-width: 100%;
            object-fit: contain;
            user-select: none;
            -webkit-user-drag: none;
        `;
        image.draggable = false;

        // Hinweistext
        const hintText = document.createElement('div');
        hintText.textContent = 'Mit der Maus klicken und ziehen, um zu drehen';
        hintText.style.cssText = `
            color: white;
            text-align: center;
            padding: 0.5rem;
            background-color: rgba(0, 0, 0, 0.5);
        `;

        // Elemente zusammenfügen
        imageContainer.appendChild(image);
        viewerContainer.appendChild(closeButton);
        viewerContainer.appendChild(imageContainer);
        viewerContainer.appendChild(hintText);
        document.body.appendChild(viewerContainer);

        // Event-Listener für die Rotation
        this.setupRotationEvents(imageContainer, image);

        // Automatische Rotation starten, falls aktiviert
        if (this.options.autoRotate) {
            this.startAutoRotate();
        }
    }

    setupRotationEvents(container, image) {
        // Maus-Events
        container.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.startX = e.clientX;
            container.style.cursor = 'grabbing';

            // Auto-Rotation stoppen, falls aktiv
            this.stopAutoRotate();
        });

        container.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;

            const deltaX = e.clientX - this.startX;

            if (Math.abs(deltaX) > 5) {
                const direction = deltaX > 0 ? -1 : 1;
                this.currentImageIndex = (this.currentImageIndex + direction + this.images.length) % this.images.length;

                image.src = this.images[this.currentImageIndex];
                this.startX = e.clientX;
            }
        });

        // Touch-Events für mobile Geräte
        container.addEventListener('touchstart', (e) => {
            this.isDragging = true;
            this.startX = e.touches[0].clientX;

            // Auto-Rotation stoppen, falls aktiv
            this.stopAutoRotate();
        });

        container.addEventListener('touchmove', (e) => {
            if (!this.isDragging) return;

            const deltaX = e.touches[0].clientX - this.startX;

            if (Math.abs(deltaX) > 5) {
                const direction = deltaX > 0 ? -1 : 1;
                this.currentImageIndex = (this.currentImageIndex + direction + this.images.length) % this.images.length;

                image.src = this.images[this.currentImageIndex];
                this.startX = e.touches[0].clientX;
            }
        });

        // Globale Events für das Ende des Ziehens
        const mouseUpHandler = () => {
            if (this.isDragging) {
                this.isDragging = false;
                container.style.cursor = 'grab';
            }
        };

        document.addEventListener('mouseup', mouseUpHandler);
        document.addEventListener('touchend', mouseUpHandler);

        // Cleanup-Funktion für Event-Listener
        this.cleanupListeners = () => {
            document.removeEventListener('mouseup', mouseUpHandler);
            document.removeEventListener('touchend', mouseUpHandler);
        };
    }

    closeViewer() {
        this.isViewerOpen = false;

        // Scrolling wieder erlauben
        document.body.style.overflow = 'auto';

        // Auto-Rotation stoppen, falls aktiv
        this.stopAutoRotate();

        // Event-Listener bereinigen
        if (this.cleanupListeners) {
            this.cleanupListeners();
        }

        // Viewer-Container entfernen
        const viewerContainer = document.querySelector('.viewer360-fullscreen');
        if (viewerContainer) {
            document.body.removeChild(viewerContainer);
        }
    }

    startAutoRotate() {
        if (this.autoRotateTimer) return;

        this.autoRotateTimer = setInterval(() => {
            if (!this.isDragging) {
                this.currentImageIndex = (this.currentImageIndex + 1) % this.images.length;

                const image = document.querySelector('.viewer360-fullscreen img');
                if (image) {
                    image.src = this.images[this.currentImageIndex];
                }
            }
        }, this.options.autoRotateSpeed);
    }

    stopAutoRotate() {
        if (this.autoRotateTimer) {
            clearInterval(this.autoRotateTimer);
            this.autoRotateTimer = null;
        }
    }
}

// Beim Laden der Seite den Viewer initialisieren
document.addEventListener('DOMContentLoaded', function() {
    // Prüfe, ob ein Viewer-Container existiert
    const container = document.getElementById('viewer360-container');
    if (container) {
        // Optional: Projekt-ID aus Attribut oder URL-Parameter auslesen
        let projectId = container.getAttribute('data-project-id');

        if (!projectId) {
            // Versuche, die Projekt-ID aus URL-Parametern zu extrahieren
            const urlParams = new URLSearchParams(window.location.search);
            projectId = urlParams.get('project');
        }

        // Viewer initialisieren
        window.viewer360 = new Viewer360('viewer360-container', projectId, {
            autoRotate: true, // Automatische Rotation aktivieren
            logoText: "360° Ansicht", // Text im Logo anpassen
            logoSubText: "Klicken zum Vergrößern" // Un