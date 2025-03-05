// static/js/index.js
// DOM Elements
const startButton = document.getElementById('start-360-rotation');
const stopButton = document.getElementById('stop-rotation');
const rotationIntervalInput = document.getElementById('rotation-interval');
const rotationDegreesInput = document.getElementById('rotation-degrees');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('rotation-progress');
const rotationStatus = document.getElementById('rotation-status');
const capturedImage = document.getElementById('captured-image');
const manualRotationForm = document.getElementById('manual-rotation-form');

// Rotation state
let isRotating = false;
let rotationAborted = false;

// 360° Rotation Function
async function start360Rotation() {
    const interval = parseInt(rotationIntervalInput.value);
    const stepDegrees = parseInt(rotationDegreesInput.value);
    const totalRotations = Math.floor(360 / stepDegrees);

    // Disable start button, show stop button
    startButton.disabled = true;
    stopButton.classList.remove('d-none');
    progressContainer.style.display = 'block';
    rotationStatus.textContent = 'Rotation gestartet...';
    isRotating = true;
    rotationAborted = false;

    // Reset progress
    progressBar.style.width = '0%';
    progressBar.classList.add('progress-bar-animated');

    try {
        for (let i = 0; i < totalRotations; i++) {
            // Check if rotation was aborted
            if (rotationAborted) {
                break;
            }

            // Update progress
            const progress = ((i + 1) / totalRotations) * 100;
            progressBar.style.width = `${progress}%`;
            rotationStatus.textContent = `Foto ${i + 1} von ${totalRotations}`;

            // Send rotation and photo capture request
            const response = await fetch('/rotate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `degrees=${stepDegrees}&interval=${interval}`
            });

            // Check if request was successful
            if (!response.ok) {
                throw new Error('Rotation fehlgeschlagen');
            }

            // Update image source with the latest photo
            const result = await response.text();
            capturedImage.src = result; // Assuming the response contains the photo path

            // Wait for the specified interval
            await new Promise(resolve => setTimeout(resolve, interval * 1000));
        }

        // Rotation complete
        if (!rotationAborted) {
            rotationStatus.textContent = 'Rotation abgeschlossen!';
            progressBar.classList.remove('progress-bar-animated');
        } else {
            rotationStatus.textContent = 'Rotation abgebrochen!';
            progressBar.classList.add('bg-warning');
        }
    } catch (error) {
        // Handle errors
        rotationStatus.textContent = `Fehler: ${error.message}`;
        progressBar.classList.add('bg-danger');
    } finally {
        // Re-enable start button, hide stop button
        startButton.disabled = false;
        stopButton.classList.add('d-none');
        isRotating = false;
    }
}

// Stop Rotation Function
function stopRotation() {
    if (isRotating) {
        rotationAborted = true;
        rotationStatus.textContent = 'Rotation wird gestoppt...';
    }
}

// Manual Rotation
manualRotationForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const degrees = document.getElementById('manual-degrees').value;

    try {
        const response = await fetch('/rotate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `degrees=${degrees}`
        });

        const result = await response.text();
        capturedImage.src = result; // Update image with latest photo
    } catch (error) {
        console.error('Rotation error:', error);
    }
});

// Event Listeners
startButton.addEventListener('click', start360Rotation);
stopButton.addEventListener('click', stopRotation);