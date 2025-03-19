# Datei: utils/background_remover.py
# Modul für KI-basierte Hintergrundentfernung mit NVIDIA-Unterstützung

import os
import logging
import numpy as np
import cv2
import torch
from pathlib import Path


class BackgroundRemover:
    """Klasse zur KI-basierten Entfernung des Hintergrunds von Bildern"""

    def __init__(self):
        """Initialisiert den BackgroundRemover"""
        self.logger = logging.getLogger(__name__)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = None
        self.initialized = False

        # Wenn CUDA verfügbar ist, sofort initialisieren
        if self.device == 'cuda':
            self.logger.info("NVIDIA GPU erkannt, verwende CUDA für KI-Verarbeitung")
            self._initialize_model()
        else:
            self.logger.warning("Keine NVIDIA GPU erkannt, KI-Funktionen werden CPU verwenden (langsamer)")

    def _initialize_model(self):
        """Initialisiert das KI-Modell für Segmentierung"""
        try:
            # Versuchen wir, U^2-Net zu laden (wenn installiert)
            import u2net
            self.model_type = 'u2net'
            self.model = u2net.load_model(self.device)
            self.initialized = True
            self.logger.info("U^2-Net Segmentierungsmodell geladen")
            return
        except ImportError:
            self.logger.info("U^2-Net nicht verfügbar, versuche Alternativen...")

        try:
            # Alternativ: Verwenden wir torchvision DeepLabV3
            import torchvision
            from torchvision.models.segmentation import deeplabv3_resnet101

            self.model_type = 'deeplabv3'
            self.model = deeplabv3_resnet101(pretrained=True)
            self.model.to(self.device)
            self.model.eval()
            self.initialized = True
            self.logger.info("DeepLabV3 Segmentierungsmodell geladen")
            return
        except ImportError:
            self.logger.warning("DeepLabV3 konnte nicht geladen werden")

        # Alternativ: Versuche OpenCV DNN mit einem vortrainierten Modell
        try:
            # Prüfen, ob das Modell heruntergeladen werden muss
            model_path = os.path.join(os.path.dirname(__file__), 'models')
            os.makedirs(model_path, exist_ok=True)

            self.model_type = 'opencv_dnn'
            self.initialized = True
            self.logger.info("OpenCV DNN wird für die Segmentierung verwendet")
            return
        except Exception as e:
            self.logger.error(f"Konnte kein Segmentierungsmodell laden: {str(e)}")

        self.logger.error("Keines der Segmentierungsmodelle konnte initialisiert werden")

    def is_available(self):
        """Prüft, ob die Hintergrundentfernung verfügbar ist"""
        if not self.initialized and self.device == 'cuda':
            self._initialize_model()
        return self.initialized

    def remove_background_with_reference(self, image_path, reference_path, output_path):
        """Entfernt den Hintergrund mit einem Referenzbild (Hintergrund ohne Objekt)"""
        try:
            # Bilder laden
            image = cv2.imread(image_path)
            reference = cv2.imread(reference_path)

            if image is None or reference is None:
                self.logger.error(f"Konnte Bilder nicht laden: {image_path} oder {reference_path}")
                return False

            # Stellen Sie sicher, dass die Bilder die gleiche Größe haben
            if image.shape != reference.shape:
                reference = cv2.resize(reference, (image.shape[1], image.shape[0]))

            # Differenzbild berechnen
            diff = cv2.absdiff(image, reference)

            # Schwellenwertbildung für die Maske
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)

            # Rauschen aus der Maske entfernen
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((10, 10), np.uint8))

            # Maske erweitern
            mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)

            # Maske als 3-Kanal-Bild für die Verwendung mit transparentem Hintergrund
            rgba_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGRA)
            rgba_mask[:, :, 3] = mask

            # Bild mit transparentem Hintergrund
            rgba_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            rgba_image[:, :, 3] = mask

            # Ergebnis speichern
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            cv2.imwrite(output_path, rgba_image)

            self.logger.info(f"Hintergrund mit Referenzbild entfernt und gespeichert: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Fehler bei der Hintergrundentfernung mit Referenz: {str(e)}")
            return False

    def remove_background_with_ai(self, image_path, output_path):
        """Entfernt den Hintergrund mit KI-basierter Segmentierung"""
        if not self.is_available():
            self.logger.warning("KI-Segmentierung nicht verfügbar, bitte installieren Sie die erforderlichen Pakete")
            return False

        try:
            # Bild laden
            image = cv2.imread(image_path)

            if image is None:
                self.logger.error(f"Konnte Bild nicht laden: {image_path}")
                return False

            # KI-Segmentierung basierend auf dem geladenen Modell
            if self.model_type == 'u2net':
                # U^2-Net-spezifischer Code
                mask = self._segment_with_u2net(image)
            elif self.model_type == 'deeplabv3':
                # DeepLabV3-spezifischer Code
                mask = self._segment_with_deeplabv3(image)
            elif self.model_type == 'opencv_dnn':
                # OpenCV DNN-spezifischer Code
                mask = self._segment_with_opencv(image)
            else:
                self.logger.error("Kein unterstütztes Segmentierungsmodell verfügbar")
                return False

            # Maske nachbearbeiten
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

            # Bild mit transparentem Hintergrund
            rgba_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
            rgba_image[:, :, 3] = mask

            # Ergebnis speichern
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)

            cv2.imwrite(output_path, rgba_image)

            self.logger.info(f"Hintergrund mit KI entfernt und gespeichert: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Fehler bei der KI-basierten Hintergrundentfernung: {str(e)}")
            return False

    def _segment_with_u2net(self, image):
        """Segmentierung mit U^2-Net"""
        # Hier wäre der spezifische Code für U^2-Net
        # Da dies die tatsächliche Implementierung des Pakets erfordert, hier ein Platzhalter
        self.logger.error("U^2-Net-Segmentierung nicht implementiert")
        return np.zeros(image.shape[:2], dtype=np.uint8)

    def _segment_with_deeplabv3(self, image):
        """Segmentierung mit DeepLabV3"""
        # Bild für das Modell vorbereiten
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((520, 520)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        input_tensor = transform(image)
        input_batch = input_tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            output = self.model(input_batch)['out'][0]

        output_predictions = output.argmax(0).byte().cpu().numpy()

        # Größe wieder auf das Originalbild anpassen
        mask = cv2.resize(output_predictions, (image.shape[1], image.shape[0]))

        # Person/Vordergrund ist typischerweise Klasse 15
        mask = np.where(mask == 15, 255, 0).astype(np.uint8)

        return mask

    def _segment_with_opencv(self, image):
        """Segmentierung mit OpenCV DNN"""
        # Platzhalter für die OpenCV-DNN-Implementierung
        # Hier würde eine einfache Hintergrundentfernung mit GrabCut stattfinden

        # Initialisiere Masken
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        bgd_model = np.zeros((1, 65), dtype=np.float64)
        fgd_model = np.zeros((1, 65), dtype=np.float64)

        # Rechteck, das das Objekt umgibt (hier vereinfacht als zentrales Rechteck)
        rect = (image.shape[1] // 4, image.shape[0] // 4,
                image.shape[1] // 2, image.shape[0] // 2)

        # GrabCut-Algorithmus anwenden
        cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

        # Maske erstellen, wo sicher oder wahrscheinlich Vordergrund ist
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')

        return mask2

    def process_project_images(self, project, session, reference_image=None, use_ai=True):
        """Verarbeitet alle Bilder einer Projekt-Session für transparenten Hintergrund"""
        if not project or not session:
            self.logger.error("Ungültiges Projekt oder Session für die Bildverarbeitung")
            return False

        # Verzeichnis für transparente Bilder erstellen
        transparent_dir = os.path.join(project.path, "sessions", session.id, "transparent")
        os.makedirs(transparent_dir, exist_ok=True)

        success_count = 0
        total_count = len(session.photos)

        for angle, photo_path in session.photos.items():
            output_path = os.path.join(transparent_dir, f"angle_{int(angle):03d}.png")

            if reference_image and os.path.exists(reference_image):
                # Mit Referenzbild
                success = self.remove_background_with_reference(photo_path, reference_image, output_path)
            elif use_ai and self.is_available():
                # Mit KI
                success = self.remove_background_with_ai(photo_path, output_path)
            else:
                # Fehlschlag, keine geeignete Methode verfügbar
                self.logger.warning(f"Keine geeignete Methode zur Hintergrundentfernung für {photo_path}")
                success = False

            if success:
                success_count += 1

        result = {
            'success': success_count > 0,
            'total': total_count,
            'processed': success_count,
            'directory': transparent_dir
        }

        self.logger.info(f"Hintergrundentfernung abgeschlossen: {success_count}/{total_count} Bilder verarbeitet")
        return result