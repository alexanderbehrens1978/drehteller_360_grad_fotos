// Datei: static/js/main.js - Haupt-JavaScript für die Anwendung

document.addEventListener('DOMContentLoaded', function() {
    // Datum-Formatierung für Flask-Jinja-Filter
    if (typeof window.formatDate !== 'function') {
        window.formatDate = function(timestamp, format = 'full') {
            const date = new Date(timestamp * 1000);

            if (format === 'short') {
                return date.toLocaleDateString();
            } else if (format === 'time') {
                return date.toLocaleTimeString();
            } else {
                return date.toLocaleString();
            }
        };
    }

    // Globale Funktionen für Ajax-Anfragen
    window.api = {
        // GET-Anfrage
        get: async function(url) {
            try {
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error("API GET error:", error);
                return { error: error.message };
            }
        },

        // POST-Anfrage
        post: async function(url, data) {
            try {
                const formData = new FormData();

                // FormData füllen
                for (const key in data) {
                    formData.append(key, data[key]);
                }

                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                console.error("API POST error:", error);
                return { error: error.message };
            }
        }
    };
});

// Datei: static/js/settings.js - JavaScript für die Einstellungsseite

document.addEventListener('DOMContentLoaded', function() {
    // Kameratyp-Toggle
    const cameraTypeSelect = document.getElementById('camera_type');
    const webcamOptions = document.querySelectorAll('.webcam-option');
    const gphotoOptions = document.querySelectorAll('.gphoto-option');

    if (cameraTypeSelect) {
        cameraTypeSelect.addEventListener('change', function() {
            if (this.value === 'webcam') {
                webcamOptions.forEach(el => el.style.display = 'block');
                gphotoOptions.forEach(el => el.style.display = 'none');
            } else if (this.value === 'gphoto2') {
                webcamOptions.forEach(el => el.style.display = 'none');
                gphotoOptions.forEach(el => el.style.display = 'block');
            }
        });
    }

    // Arduino testen
    const testArduinoBtn = document.getElementById('test-arduino-btn');

    if (testArduinoBtn) {
        testArduinoBtn.addEventListener('click', async function() {
            const arduinoPort = document.getElementById('arduino_port').value;
            const arduinoBaudrate = document.getElementById('arduino_baudrate').value;

            this.disabled = true;
            this.textContent = 'Teste Arduino...';

            try {
                const response = await window.api.post('/api/test/arduino', {
                    port: arduinoPort,
                    baudrate: arduinoBaudrate
                });

                if (response.success) {
                    alert('Arduino erfolgreich getestet!');
                } else {
                    alert('Arduino-Test fehlgeschlagen: ' + (response.error || 'Unbekannter Fehler'));
                }
            } catch (error) {
                alert('Arduino-Test fehlgeschlagen: ' + error.message);
            } finally {
                this.disabled = false;
                this.textContent = 'Arduino testen';
            }
        });
    }

    // Kamera testen
    const testCameraBtn = document.getElementById('test-camera-btn');

    if (testCameraBtn) {
        testCameraBtn.addEventListener('click', async function() {
            const cameraType = document.getElementById('camera_type').value;
            const cameraDevice = cameraType === 'webcam'
                ? document.getElementById('webcam_device').value
                : document.getElementById('gphoto_device').value;
            const cameraResolution = document.getElementById('camera_resolution').value;

            this.disabled = true;
            this.textContent = 'Teste Kamera...';

            try {
                const response = await window.api.post('/api/test/camera', {
                    type: cameraType,
                    device: cameraDevice,
                    resolution: cameraResolution
                });

                if (response.success) {
                    alert('Kamera erfolgreich getestet!');

                    // Zeige Testbild, falls vorhanden
                    if (response.image_url) {
                        window.open(response.image_url, '_blank');
                    }
                } else {
                    alert('Kamera-Test fehlgeschlagen: ' + (response.error || 'Unbekannter Fehler'));
                }
            } catch (error) {
                alert('Kamera-Test fehlgeschlagen: ' + error.message);
            } finally {
                this.disabled = false;
                this.textContent = 'Kamera testen';
            }
        });
    }
});

// Datei: static/js/capture.js - JavaScript für die Aufnahmeseite

document.addEventListener('DOMContentLoaded', function() {
    // Hardware-Status prüfen
    const checkStatusBtn = document.getElementById('check-status-btn');
    const arduinoStatus = document.getElementById('arduino-status').querySelector('.status-value');
    const cameraStatus = document.getElementById('camera-status').querySelector('.status-value');

    async function checkHardwareStatus() {
        // Arduino-Status prüfen
        arduinoStatus.textContent = 'Wird geprüft...';
        arduinoStatus.className = 'status-value loading';

        try {
            const arduinoResponse = await window.api.get('/api/status/arduino');

            if (arduinoResponse.connected) {
                arduinoStatus.textContent = 'Verbunden';
                arduinoStatus.className = 'status-value ok';
            } else {
                arduinoStatus.textContent = 'Nicht verbunden';
                arduinoStatus.className = 'status-value error';
            }
        } catch (error) {
            arduinoStatus.textContent = 'Fehler: ' + error.message;
            arduinoStatus.className = 'status-value error';
        }

        // Kamera-Status prüfen
        cameraStatus.textContent = 'Wird geprüft...';
        cameraStatus.className = 'status-value loading';

        try {
            const cameraResponse = await window.api.get('/api/status/camera');

            if (cameraResponse.available) {
                cameraStatus.textContent = 'Verfügbar';
                cameraStatus.className = 'status-value ok';
            } else {
                cameraStatus.textContent = 'Nicht verfügbar';
                cameraStatus.className = 'status-value error';
            }
        } catch (error) {
            cameraStatus.textContent = 'Fehler: ' + error.message;
            cameraStatus.className = 'status-value error';
        }
    }

    if (checkStatusBtn) {
        // Initialer Check
        checkHardwareStatus();

        // Button-Event
        checkStatusBtn.addEventListener('click', checkHardwareStatus);
    }
});

// Datei: static/js/viewer.js - JavaScript für den 360° Viewer

document.addEventListener('DOMContentLoaded', function() {
    // Prüfen, ob die Viewer-Seite aktiv ist
    const viewer = document.getElementById('viewer360');
    if (!viewer) return;

    // Prüfen, ob sessionData verfügbar ist
    if (typeof sessionData === 'undefined') {
        console.error('Keine Session-Daten für den Viewer verfügbar');
        return;
    }

    // Elemente
    const currentImage = document.getElementById('currentImage');
    const rotationSlider = document.getElementById('rotationSlider');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const downloadBtn = document.getElementById('download-btn');

    // Variablen
    let currentFrame = 0;
    let isPlaying = true;
    let animationId = null;
    let lastDragX = 0;
    let isDragging = false;
    let autoRotationSpeed = 0.2; // Frames pro Animation

    // Photos sortieren und aufbereiten
    const photos = [...sessionData.photos].sort((a, b) => a.angle - b.angle);

    // Slider konfigurieren
    rotationSlider.min = 0;
    rotationSlider.max = photos.length - 1;
    rotationSlider.value = 0;

    // Bild laden
    function loadFrame(frameIndex) {
        currentFrame = frameIndex;
        rotationSlider.value = frameIndex;
        currentImage.src = photos[frameIndex].path;
    }

    // Animation starten/stoppen
    function togglePlayPause() {
        isPlaying = !isPlaying;
        playPauseBtn.textContent = isPlaying ? 'Pause' : 'Play';

        if (isPlaying) {
            startAnimation();
        } else {
            stopAnimation();
        }
    }

    // Animation starten
    function startAnimation() {
        if (animationId) return;

        function animate() {
            currentFrame = (currentFrame + autoRotationSpeed) % photos.length;
            loadFrame(Math.floor(currentFrame));
            animationId = requestAnimationFrame(animate);
        }

        animationId = requestAnimationFrame(animate);
    }

    // Animation stoppen
    function stopAnimation() {
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }
    }

    // Export-Funktion
    async function exportViewer() {
        try {
            const response = await window.api.post('/api/export/360', {
                project_id: sessionData.project_id,
                session_id: sessionData.session_id
            });

            if (response.success && response.export_url) {
                window.open(response.export_url, '_blank');
            } else {
                alert('Export fehlgeschlagen: ' + (response.error || 'Unbekannter Fehler'));
            }
        } catch (error) {
            alert('Export fehlgeschlagen: ' + error.message);
        }
    }

    // Event-Listener
    playPauseBtn.addEventListener('click', togglePlayPause);

    rotationSlider.addEventListener('input', function() {
        stopAnimation();
        isPlaying = false;
        playPauseBtn.textContent = 'Play';
        loadFrame(parseInt(this.value));
    });

    if (downloadBtn) {
        downloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            exportViewer();
        });
    }

    // Touch/Maus-Steuerung
    viewer.addEventListener('mousedown', handleDragStart);
    viewer.addEventListener('touchstart', handleDragStart);

    window.addEventListener('mousemove', handleDragMove);
    window.addEventListener('touchmove', handleDragMove);

    window.addEventListener('mouseup', handleDragEnd);
    window.addEventListener('touchend', handleDragEnd);

    function handleDragStart(event) {
        event.preventDefault();
        stopAnimation();
        isPlaying = false;
        playPauseBtn.textContent = 'Play';
        isDragging = true;
        lastDragX = event.clientX || event.touches[0].clientX;
    }

    function handleDragMove(event) {
        if (!isDragging) return;
        event.preventDefault();

        const clientX = event.clientX || event.touches[0].clientX;
        const deltaX = clientX - lastDragX;
        lastDragX = clientX;

        // Berechne die Anzahl der zu verschiebenden Frames
        const framesToMove = -Math.sign(deltaX) * Math.ceil(Math.abs(deltaX) / 10);
        const newFrame = Math.floor((currentFrame + framesToMove + photos.length) % photos.length);

        loadFrame(newFrame);
    }

    function handleDragEnd() {
        if (!isDragging) return;
        isDragging = false;

        // Automatische Rotation nach Mausinteraktion fortsetzen
        if (!isPlaying) {
            isPlaying = true;
            playPauseBtn.textContent = 'Pause';
            startAnimation();
        }
    }

    // Initialisierung
    loadFrame(0);
    startAnimation();
});