// projectManager.js - Modul für Projektverwaltung
import api from './api.js';

const projectManager = {
    // Projekte laden und sortieren
    loadProjects: async function() {
        try {
            const projects = await api.getProjects();
            
            // Projekte nach Erstellungsdatum sortieren (neueste zuerst)
            return projects.sort((a, b) => b.created - a.created);
        } catch (error) {
            console.error('Fehler beim Laden der Projekte:', error);
            throw error;
        }
    },
    
    // Projekt löschen
    deleteProject: async function(projectId) {
        try {
            await api.deleteProject(projectId);
            return true;
        } catch (error) {
            console.error('Fehler beim Löschen des Projekts:', error);
            throw error;
        }
    },
    
    // Projekt-Element für die Anzeige erstellen
    createProjectElement: function(project, onDeleteClick) {
        // Projekt-Template klonen
        const template = document.getElementById('project-template');
        const projectElement = template.content.cloneNode(true);
        
        // Hauptelement für das Projekt
        const projectCard = projectElement.querySelector('.project-card');
        projectCard.dataset.projectId = project.id;
        
        // Elemente für Projektdaten
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
        
        // Lösch-Button-Event
        if (deleteButton && typeof onDeleteClick === 'function') {
            deleteButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                onDeleteClick(project);
            });
        }
        
        return projectElement.firstElementChild;
    }
};

export default projectManager;
