import React, { useState, useEffect, useRef } from 'react';

const Viewer360 = () => {
  const [isViewerOpen, setIsViewerOpen] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [images, setImages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const viewerRef = useRef(null);

  // Simuliere das Laden von Bildern (in der Praxis würden diese von deinem Server kommen)
  useEffect(() => {
    // In einer realen Implementierung würdest du hier deine Bilder vom Server laden
    const loadImages = async () => {
      setIsLoading(true);

      // Hier würden normalerweise deine tatsächlichen Bilder geladen werden
      // Für die Demo erstellen wir 36 Bildpfade (alle 10 Grad eine Aufnahme)
      const demoImages = Array.from({ length: 36 }, (_, i) =>
        `/static/sample_images/sample_image_${i % 10}.jpg`
      );

      setImages(demoImages);
      setIsLoading(false);
    };

    loadImages();
  }, []);

  // Öffne den Viewer
  const openViewer = () => {
    setIsViewerOpen(true);
    document.body.style.overflow = 'hidden'; // Verhindere Scrollen im Hintergrund
  };

  // Schließe den Viewer
  const closeViewer = () => {
    setIsViewerOpen(false);
    document.body.style.overflow = 'auto'; // Erlaube Scrollen wieder
  };

  // Mauszieh-Ereignisse für die Rotation
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setStartX(e.clientX);
  };

  const handleTouchStart = (e) => {
    setIsDragging(true);
    setStartX(e.touches[0].clientX);
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const deltaX = e.clientX - startX;

    if (Math.abs(deltaX) > 5) { // Kleine Bewegungen ignorieren
      // Berechne den Index basierend auf der Bewegungsrichtung
      const direction = deltaX > 0 ? -1 : 1; // Nach rechts ziehen = nach links rotieren

      // Berechne neuen Index und stelle sicher, dass er im gültigen Bereich liegt
      const newIndex = (currentImageIndex + direction + images.length) % images.length;

      setCurrentImageIndex(newIndex);
      setStartX(e.clientX);
    }
  };

  const handleTouchMove = (e) => {
    if (!isDragging) return;

    const deltaX = e.touches[0].clientX - startX;

    if (Math.abs(deltaX) > 5) {
      const direction = deltaX > 0 ? -1 : 1;
      const newIndex = (currentImageIndex + direction + images.length) % images.length;

      setCurrentImageIndex(newIndex);
      setStartX(e.touches[0].clientX);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleTouchEnd = () => {
    setIsDragging(false);
  };

  // Event-Listener für globale Maus- und Touch-Ereignisse hinzufügen/entfernen
  useEffect(() => {
    if (isViewerOpen) {
      window.addEventListener('mouseup', handleMouseUp);
      window.addEventListener('touchend', handleTouchEnd);

      return () => {
        window.removeEventListener('mouseup', handleMouseUp);
        window.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isViewerOpen, isDragging]);

  return (
    <div className="w-full">
      {!isViewerOpen ? (
        // Logo/Vorschau, die den Viewer öffnet
        <div
          className="cursor-pointer mx-auto text-center"
          onClick={openViewer}
        >
          <div className="bg-blue-600 text-white rounded-lg p-4 shadow-lg inline-block">
            <div className="text-4xl mb-2">360°</div>
            <div className="text-sm">Klicken für 360° Ansicht</div>
          </div>
        </div>
      ) : (
        // Vollbild-Viewer
        <div className="fixed inset-0 z-50 bg-black flex flex-col">
          {/* Schließen-Button */}
          <button
            className="absolute top-4 right-4 z-10 text-white bg-red-600 rounded-full w-10 h-10 flex items-center justify-center"
            onClick={closeViewer}
          >
            ✕
          </button>

          {/* Viewer Container */}
          <div
            ref={viewerRef}
            className="flex-1 flex items-center justify-center cursor-grab active:cursor-grabbing"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
          >
            {isLoading ? (
              <div className="text-white text-xl">Lade Bilder...</div>
            ) : (
              <img
                src={images[currentImageIndex]}
                alt={`360-Grad Ansicht ${currentImageIndex}`}
                className="max-h-full max-w-full object-contain select-none"
                draggable="false"
              />
            )}
          </div>

          {/* Hinweistext */}
          <div className="text-white text-center p-2 bg-black bg-opacity-50">
            Mit der Maus klicken und ziehen, um zu drehen
          </div>
        </div>
      )}
    </div>
  );
};

export default Viewer360;