// Dateipfad: static/js/settings.js
// Funktionen für die Einstellungsseite

document.addEventListener('DOMContentLoaded', function() {
    // Überprüfen, ob jQuery verfügbar ist
    if (typeof jQuery === 'undefined') {
        console.error('jQuery ist nicht geladen. Bitte fügen Sie jQuery-Bibliothek hinzu.');
        return;
    }

    // Einstellungen laden
    $.getJSON('/settings/get_config', function(config) {
        console.log('Konfiguration geladen:', config);
        
        // Kamera-Einstellungen
        $('#camera-type').val(config.camera.type);
        $('#camera-device').val(config.camera.device_path);
        $('#camera-width').val(config.camera.resolution.width);
        $('#camera-height').val(config.camera.resolution.height);

        // Arduino-Einstellungen
        $('#arduino-port').val(config.arduino.port);
        $('#arduino-baudrate').val(config.arduino.baudrate);

        // Drehteller-Einstellungen
        $('#default-angle').val(config.rotation.default_degrees);
        $('#default-interval').val(config.rotation.default_interval);
        
        // Prüfen, ob default_duration existiert
        if (config.rotation.default_duration !== undefined) {
            $('#default-duration').val(config.rotation.default_duration);
        }
        
        // Rotationsmodus einstellen, wenn verfügbar
        if (config.rotation.mode === 'time') {
            $('#time-mode').prop('checked', true);
        } else {
            $('#angle-mode').prop('checked', true);
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error('Fehler beim Laden der Einstellungen:', textStatus, errorThrown);
        alert('Fehler beim Laden der Einstellungen: ' + textStatus);
    });

    // Einstellungen speichern
    $('#settings-form').on('submit', function(e) {
        e.preventDefault();
        console.log('Formular wird übermittelt');

        // Neue Konfiguration erstellen
        const newConfig = {
            camera: {
                type: $('#camera-type').val(),
                device_path: $('#camera-device').val(),
                resolution: {
                    width: parseInt($('#camera-width').val()) || 1920,
                    height: parseInt($('#camera-height').val()) || 1080
                }
            },
            arduino: {
                port: $('#arduino-port').val(),
                baudrate: parseInt($('#arduino-baudrate').val()) || 9600
            },
            rotation: {
                mode: $('input[name="rotation-mode"]:checked').val() || 'angle',
                default_degrees: parseInt($('#default-angle').val()) || 15,
                default_interval: parseInt($('#default-interval').val()) || 5,
                default_duration: parseInt($('#default-duration').val()) || 2
            }
        };

        console.log('Neue Konfiguration zum Speichern:', newConfig);

        // Konfiguration an den Server senden
        $.ajax({
            url: '/settings/save_config',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newConfig),
            success: function(response) {
                console.log('Server-Antwort:', response);
                if (response.status === 'success') {
                    alert('Einstellungen wurden erfolgreich gespeichert.');
                } else {
                    alert('Fehler beim Speichern der Einstellungen: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('AJAX-Fehler:', xhr.responseText, status, error);
                alert('Fehler beim Speichern der Einstellungen: ' + error);
            }
        });
    });
});
