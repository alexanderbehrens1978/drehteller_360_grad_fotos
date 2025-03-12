/**
 * project_create.js
 * JavaScript für die Projekterstellung
 */

document.addEventListener('DOMContentLoaded', function() {
    const projectForm = document.getElementById('projectForm');
    
    if (projectForm) {
        projectForm.addEventListener('submit', function(e) {
            const nameInput = document.getElementById('name');
            const angleStepInput = document.getElementById('angle_step');
            
            // Name validieren
            if (!nameInput.value.trim()) {
                e.preventDefault();
                alert('Bitte geben Sie einen Projektnamen ein.');
                nameInput.focus();
                return false;
            }
            
            // Winkelschritt validieren
            const angleStep = parseInt(angleStepInput.value);
            if (isNaN(angleStep) || angleStep <= 0 || angleStep > 90) {
                e.preventDefault();
                alert('Bitte geben Sie einen gültigen Winkelschritt zwischen 1 und 90 ein.');
                angleStepInput.focus();
                return false;
            }
            
            // Formular absenden
            return true;
        });
    }
});
