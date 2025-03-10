// api.js - Modul für API-Kommunikation
const api = {
    // Projekte abrufen
    getProjects: async function() {
        try {
            const response = await fetch('/api/projects');
            if (!response.ok) {
                throw new Error(`HTTP-Fehler: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API-Fehler beim Abrufen der Projekte:', error);
            throw error;
        }
    },
    
    // Einzelnes Projekt abrufen
    getProject: async function(projectId) {
        try {
            const response = await fetch(`/api/project/${projectId}`);
            if (!response.ok) {
                throw new Error(`HTTP-Fehler: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API-Fehler beim Abrufen des Projekts ${projectId}:`, error);
            throw error;
        }
    },
    
    // Projekt löschen
    deleteProject: async function(projectId) {
        try {
            const response = await fetch(`/api/project/${projectId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Fehler beim Löschen: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API-Fehler beim Löschen des Projekts ${projectId}:`, error);
            throw error;
        }
    },
    
    // Geräte abrufen
    getDevices: async function() {
        try {
            const response = await fetch('/api/devices');
            if (!response.ok) {
                throw new Error(`HTTP-Fehler: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API-Fehler beim Abrufen der Geräte:', error);
            throw error;
        }
    },
    
    // Konfiguration abrufen
    getConfig: async function() {
        try {
            const response = await fetch('/get_config');
            if (!response.ok) {
                throw new Error(`HTTP-Fehler: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API-Fehler beim Abrufen der Konfiguration:', error);
            throw error;
        }
    },
    
    // Konfiguration speichern
    saveConfig: async function(config) {
        try {
            const response = await fetch('/save_config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `Fehler beim Speichern: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API-Fehler beim Speichern der Konfiguration:', error);
            throw error;
        }
    }
};

export default api;
