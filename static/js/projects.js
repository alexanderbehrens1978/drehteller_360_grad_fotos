// projects.js - Hauptskript für die Projektseite
document.addEventListener('DOMContentLoaded', () => {
    // DOM-Elemente
    const projectsContainer = document.getElementById('projects-container');
    const loadingElement = document.getElementById('loading');
    const noProjectsElement = document.getElementById('no-projects');
    
    // Lösch-Dialog
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    const deleteProjectNameElement = document.getElementById('delete-project-name');
    const confirmDeleteButton = document.getElementById('confirm-delete');
    
    // Aktuell zu löschendes Projekt
    let projectToDelete = null;
    
    // Projekte laden
    async function loadProjects() {
        try {
            const response = await fetch('/api/projects');
            const projects = await response.json();
            
            // Loading-Element entfernen
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // Prüfen, ob Projekte vorhanden sind
            if (projects.length === 0) {
                if (noProjectsElement) {
                    noProjectsElement.classList.remove('d-none');
                }
                return;
            }
            
            // Projekte sortieren (neueste zuerst)
            projects.sort((a, b) => b.created - a.created);
            
            // Projekte anzeigen
            projects.forEach(project => {
                const projectElement = createProjectElement(project);
                projectsContainer.appendChild(projectElement);
            });
        } catch (error) {
            console.error('Fehler beim Laden der Projekte:', error);
            
            if (loadingElement) {
                loadingElement.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i> Fehler beim Laden der Projekte: ${error.message}
                    </div>
                `;
            }
        }
    }
    
    // Projekt-Element erstellen
    function createProjectElement(project) {
        const template = document.getElementById('project-template');
        const projectElement = template.content.cloneNode(true);
        
        // Wichtig: Projekt-ID als data-Attribut speichern
        const projectCard = projectElement.querySelector('.project-card');
        projectCard.dataset.projectId = project.id;
        
        console.log('Erstelle Projektelement für Projekt-ID:', project.id);
        
        // Projektdaten einfügen
        const thumbnailElement = projectElement.querySelector('.project-thumbnail');
        const nameElement = projectElement.querySelector('.project-name');
        const dateElement = projectElement.querySelector('.project-date');
        const imageCountElement = projectElement.querySelector('.project-image-count');
        const viewButton = projectElement.querySelector('.view-btn');
        const deleteButton = projectElement.querySelector('.delete-btn');
        
        // Thumbnail setzen (erstes Bild im Projekt)
        if (project.images && project.images.length > 0) {
            thumbnailElement.style.backgroundImage = `url('/static/projects/${project.id}/${project.images[0]}')`;
        }
        
        // Projektname setzen
        nameElement.textContent = project.name || project.id;
        
        // Datum formatieren
        const date = new Date(project.created * 1000);
        dateElement.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        // Bildanzahl
        const imageCount = project.image_count || (project.images ? project.images.length : 0);
        imageCountElement.textContent = `${imageCount} Bilder`;
        
        // Link zum Viewer
        viewButton.href = `/viewer?project=${project.id}`;
        
        // Lösch-Button
        if (deleteButton) {
            deleteButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Löschen von Projekt mit ID:', project.id);
                deleteProjectNameElement.textContent = project.name || project.id;
                projectToDelete = project.id;
                deleteModal.show();
            });
        }
        
        return projectElement.firstElementChild;
    }
    
    // Projekt löschen
    async function deleteProject(projectId) {
        console.log('Starte Löschvorgang für Projekt:', projectId);
        
        try {
            const response = await fetch(`/api/project/${projectId}`, {
                method: 'DELETE'
            });
            
            console.log('Löschanfrage-Status:', response.status);
            
            if (response.ok) {
                console.log('Projekt erfolgreich gelöscht, lade Seite neu');
                window.location.reload();
            } else {
                const errorData = await response.json();
                console.error('Server-Fehler beim Löschen:', errorData);
                throw new Error(errorData.error || 'Unbekannter Fehler beim Löschen');
            }
        } catch (error) {
            console.error('Fehler beim Löschen des Projekts:', error);
            alert(`Fehler beim Löschen: ${error.message}`);
        }
    }
    
    // Event-Listener für den Bestätigungs-Button
    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', () => {
            if (projectToDelete) {
                console.log('Bestätigung zum Löschen von Projekt:', projectToDelete);
                deleteProject(projectToDelete);
                deleteModal.hide();
            }
        });
    }
    
    // Projekte laden
    loadProjects();
});
