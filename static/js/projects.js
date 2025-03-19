/**
 * projects.js
 * JavaScript für die Projektverwaltungsseite
 */

document.addEventListener('DOMContentLoaded', function() {
    // Projekte laden
    loadProjects();
    
    // Event-Listener für das Löschen von Projekten
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-project-btn')) {
            e.preventDefault();
            deleteProject(e.target.dataset.projectId, e.target.dataset.projectName);
        }
    });
});

// Projekte laden
function loadProjects() {
    const projectsList = document.getElementById('projectsList');
    if (!projectsList) return;
    
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.textContent = 'Projekte werden geladen...';
    projectsList.appendChild(loadingIndicator);
    
    fetch('/api/projects')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP-Fehler: ${response.status}`);
            }
            return response.json();
        })
        .then(projects => {
            projectsList.innerHTML = '';
            
            if (!projects || projects.error) {
                throw new Error(projects.error || 'Unbekannter Fehler');
            }
            
            if (projects.length === 0) {
                const noProjects = document.createElement('div');
                noProjects.className = 'no-projects';
                noProjects.textContent = 'Keine Projekte vorhanden. Erstellen Sie ein neues Projekt, um zu beginnen.';
                projectsList.appendChild(noProjects);
                return;
            }
            
            // Projekte anzeigen
            projects.forEach(project => {
                // Sicherstellen, dass project definiert ist
                if (!project) {
                    console.error('Ungültiges Projekt in der Projektliste');
                    return;
                }
                
                const card = createProjectCard(project);
                projectsList.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Fehler beim Laden der Projekte:', error);
            projectsList.innerHTML = `<div class="error">Fehler beim Laden der Projekte: ${error.message}</div>`;
        });
}

// Projektkarte erstellen
function createProjectCard(project) {
    // Defensive Programmierung: Prüfe, ob das Projekt gültig ist
    if (!project || typeof project !== 'object') {
        console.error('Ungültiges Projektformat:', project);
        return document.createElement('div'); // Leeres Element zurückgeben
    }
    
    const card = document.createElement('div');
    card.className = 'project-card';
    
    const title = document.createElement('h3');
    title.textContent = project.name || `Projekt ${project.id || 'Unbekannt'}`;
    
    const meta = document.createElement('div');
    meta.className = 'project-meta';
    
    if (project.description) {
        const desc = document.createElement('p');
        desc.textContent = project.description;
        meta.appendChild(desc);
    } else {
        const noDesc = document.createElement('p');
        noDesc.className = 'no-description';
        noDesc.textContent = 'Keine Beschreibung';
        meta.appendChild(noDesc);
    }
    
    const date = document.createElement('p');
    date.className = 'created-date';
    const createdDate = new Date(project.created_at * 1000);
    date.textContent = `Erstellt: ${createdDate.toLocaleDateString()} ${createdDate.toLocaleTimeString()}`;
    meta.appendChild(date);
    
    const imageCount = document.createElement('p');
    imageCount.className = 'image-count';
    imageCount.textContent = `Bilder: ${project.images ? project.images.length : 0}`;
    meta.appendChild(imageCount);
    
    const actions = document.createElement('div');
    actions.className = 'project-actions';
    
    const viewLink = document.createElement('a');
    viewLink.href = `/projects/${project.id}`;
    viewLink.className = 'btn btn-secondary';
    viewLink.textContent = 'Anzeigen';
    actions.appendChild(viewLink);
    
    const captureLink = document.createElement('a');
    captureLink.href = `/?project_id=${project.id}`;
    captureLink.className = 'btn btn-primary';
    captureLink.textContent = 'Bilder aufnehmen';
    actions.appendChild(captureLink);
    
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-danger delete-project-btn';
    deleteBtn.textContent = 'Löschen';
    deleteBtn.dataset.projectId = project.id;
    deleteBtn.dataset.projectName = project.name;
    actions.appendChild(deleteBtn);
    
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(actions);
    
    return card;
}

// Projekt löschen
function deleteProject(projectId, projectName) {
    if (!confirm(`Möchten Sie das Projekt "${projectName}" wirklich löschen?`)) {
        return;
    }
    
    fetch(`/projects/delete/${projectId}`, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            // Projekt erfolgreich gelöscht, Seite neu laden
            window.location.reload();
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && data.error) {
            alert(`Fehler beim Löschen des Projekts: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Fehler beim Löschen des Projekts:', error);
        alert('Fehler beim Löschen des Projekts');
    });
}
