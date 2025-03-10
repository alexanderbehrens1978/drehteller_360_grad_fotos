class Viewer360 {
    constructor(containerId, imagesUrls, options = {}) {
        this.container = document.getElementById(containerId);
        this.images = [];
        this.imagesUrls = imagesUrls;
        this.currentIndex = 0;
        this.isPlaying = false;
        this.playInterval = null;
        this.options = {
            autoplay: true,
            autoplaySpeed: 100,
            dragSensitivity: 5,
            ...options
        };

        // Maus-/Touch-Positions-Tracking
        this.dragStartX = 0;
        this.isDragging = false;

        this.init();
    }

    async init() {
        if (!this.container) {
            console.error('Container nicht gefunden!');
            return;
        }

        // UI-Elemente erstellen
        this.container.innerHTML = `
            <div class="viewer360-container">
                <div class="viewer360-image-container">
                    <img class="viewer360-image" src="" alt="360° Ansicht">
                </div>
                <div class="viewer360-controls">
                    <button class="viewer360-play-btn">
                        <i class="bi bi-play-fill"></i>
                    </button>
                    <input type="range" class="viewer360-slider" min="0" max="100" value="0">
                </div>
            </div>
        `;

        // Elemente referenzieren
        this.imageElement = this.container.querySelector('.viewer360-image');
        this.playButton = this.container.querySelector('.viewer360-play-btn');
        this.slider = this.container.querySelector('.viewer360-slider');

        // Event-Listener
        this.playButton.addEventListener('click', () => this.togglePlayPause());
        this.slider.addEventListener('input', (e) => {
            const sliderPercentage = e.target.value / 100;
            const imageIndex = Math.floor(sliderPercentage * (this.imagesUrls.length - 1));
            this.showImage(imageIndex);
        });

        // Dragging-Funktionalität
        this.container.addEventListener('mousedown', (e) => this.onDragStart(e));
        this.container.addEventListener('touchstart', (e) => this.onDragStart(e.touches[0]), { passive: true });

        window.addEventListener('mousemove', (e) => this.onDragMove(e));
        window.addEventListener('touchmove', (e) => this.onDragMove(e.touches[0]));

        window.addEventListener('mouseup', () => this.onDragEnd());
        window.addEventListener('touchend', () => this.onDragEnd());

        // Bilder laden
        await this.loadImages();

        // Slider aktualisieren
        this.slider.max = this.imagesUrls.length - 1;

        // Erstes Bild anzeigen
        this.showImage(0);

        // Autoplay starten, wenn aktiviert
        if (this.options.autoplay) {
            this.play();
        }
    }

    async loadImages() {
        // Bilder vorladen für flüssigere Anzeige
        const loadPromises = this.imagesUrls.map(url => {
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = reject;
                img.src = url;
                this.images.push(img);
            });
        });

        try {
            await Promise.all(loadPromises);
            console.log(`${this.images.length} Bilder erfolgreich geladen.`);
        } catch (error) {
            console.error('Fehler beim Laden der Bilder:', error);
        }
    }

    showImage(index) {
        if (index < 0) index = this.imagesUrls.length - 1;
        if (index >= this.imagesUrls.length) index = 0;

        this.currentIndex = index;
        this.imageElement.src = this.imagesUrls[index];
        this.slider.value = index;
    }

    play() {
        if (this.isPlaying) return;

        this.isPlaying = true;
        this.playButton.innerHTML = '<i class="bi bi-pause-fill"></i>';

        this.playInterval = setInterval(() => {
            this.showImage((this.currentIndex + 1) % this.imagesUrls.length);
        }, this.options.autoplaySpeed);
    }

    pause() {
        if (!this.isPlaying) return;

        this.isPlaying = false;
        clearInterval(this.playInterval);
        this.playButton.innerHTML = '<i class="bi bi-play-fill"></i>';
    }

    togglePlayPause() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    onDragStart(event) {
        this.isDragging = true;
        this.dragStartX = event.clientX;

        // Autoplay bei Interaktion pausieren
        this.pause();
    }

    onDragMove(event) {
        if (!this.isDragging) return;

        const dragDelta = event.clientX - this.dragStartX;

        // Wenn genug bewegt wurde, ändern wir das Bild
        if (Math.abs(dragDelta) > this.options.dragSensitivity) {
            // Nach rechts ziehen zeigt vorheriges Bild (Drehung gegen den Uhrzeigersinn)
            // Nach links ziehen zeigt nächstes Bild (Drehung im Uhrzeigersinn)
            const direction = dragDelta > 0 ? -1 : 1;
            this.showImage((this.currentIndex + direction + this.imagesUrls.length) % this.imagesUrls.length);

            this.dragStartX = event.clientX;
        }
    }

    onDragEnd() {
        this.isDragging = false;
    }
}

// Beispiel für die Verwendung:
// const viewer = new Viewer360('viewer-container', ['/static/photos/image1.jpg', '/static/photos/image2.jpg']);