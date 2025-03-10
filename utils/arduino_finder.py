# Datei: utils/arduino_finder.py
# Modul zur Erkennung von Arduino-Geräten

import logging
import serial.tools.list_ports
import platform
import subprocess
import re


class ArduinoFinder:
    """Klasse zur Erkennung von Arduino-Geräten"""

    def __init__(self):
        """Initialisiert den Arduino-Finder"""
        self.logger = logging.getLogger(__name__)

    def find_arduino_ports(self):
        """Sucht nach angeschlossenen Arduino-Geräten und gibt eine Liste der Ports zurück"""
        arduino_ports = []

        try:
            # Alle seriellen Ports auflisten
            all_ports = list(serial.tools.list_ports.comports())

            for port in all_ports:
                port_info = {
                    'device': port.device,
                    'description': port.description,
                    'hwid': port.hwid,
                    'is_arduino': False
                }

                # Prüfen, ob es sich um einen Arduino handelt
                if self._is_arduino(port):
                    port_info['is_arduino'] = True
                    arduino_ports.append(port_info)
                else:
                    # Auch nicht-Arduino-Ports hinzufügen, aber als nicht-Arduino markieren
                    arduino_ports.append(port_info)

            self.logger.info(f"Gefundene Arduino-Ports: {len([p for p in arduino_ports if p['is_arduino']])}")
        except Exception as e:
            self.logger.error(f"Fehler bei der Arduino-Suche: {str(e)}")

        return arduino_ports

    def _is_arduino(self, port):
        """Prüft, ob ein serieller Port zu einem Arduino gehört"""
        # Arduino-Geräte haben oft bestimmte Hersteller-IDs oder Beschreibungen
        # VID:PID=2341:0043 ist z.B. ein Arduino Uno
        # VID:PID=2341:0001 ist z.B. ein Arduino Mega
        # VID:PID=2341:0010 ist z.B. ein Arduino Mega 2560
        # VID:PID=2341:0042 ist z.B. ein Arduino Mega 2560 R3
        arduino_identifiers = [
            "2341:",  # Arduino
            "1A86:",  # China-Clone CH340
            "2A03:",  # Arduino.org
            "FTDI",  # FTDI-basierte Boards
        ]

        common_names = [
            "arduino",
            "uno",
            "mega",
            "leonardo",
            "nano",
            "micro",
            "due",
        ]

        if any(identifier in port.hwid for identifier in arduino_identifiers):
            return True

        if any(name in port.description.lower() for name in common_names):
            return True

        return False

    def get_detailed_port_info(self):
        """Gibt detaillierte Informationen über alle seriellen Ports zurück"""
        port_info = []

        try:
            # Betriebssystemspezifische Informationen sammeln
            if platform.system() == 'Linux':
                # Auf Linux können wir zusätzliche Informationen mit lsusb sammeln
                self._add_linux_port_info(port_info)
            elif platform.system() == 'Windows':
                # Auf Windows müssen wir uns auf die pyserial-Informationen verlassen
                self._add_windows_port_info(port_info)
            elif platform.system() == 'Darwin':  # macOS
                # Auf macOS können wir zusätzliche Informationen mit system_profiler sammeln
                self._add_macos_port_info(port_info)
            else:
                # Auf anderen Systemen nur Standardinformationen
                for port in serial.tools.list_ports.comports():
                    port_info.append({
                        'device': port.device,
                        'description': port.description,
                        'hwid': port.hwid,
                        'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unbekannt',
                        'is_arduino': self._is_arduino(port)
                    })

        except Exception as e:
            self.logger.error(f"Fehler beim Sammeln detaillierter Port-Informationen: {str(e)}")

        return port_info

    def _add_linux_port_info(self, port_info):
        """Sammelt detaillierte Informationen über serielle Ports unter Linux"""
        # Standardinformationen sammeln
        for port in serial.tools.list_ports.comports():
            port_data = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unbekannt',
                'is_arduino': self._is_arduino(port)
            }

            # Versuchen, zusätzliche Informationen über lsusb zu bekommen
            if "USB" in port.hwid:
                try:
                    # USB-ID extrahieren (z.B. 2341:0043)
                    match = re.search(r'VID:PID=([0-9a-fA-F]+:[0-9a-fA-F]+)', port.hwid)
                    if match:
                        usb_id = match.group(1)
                        vendor_id, product_id = usb_id.split(':')

                        # lsusb -d vendor_id:product_id -v ausführen
                        cmd = ['lsusb', '-d', usb_id, '-v']
                        result = subprocess.run(cmd, capture_output=True, text=True)

                        if result.returncode == 0:
                            # Wichtige Informationen extrahieren
                            port_data['lsusb_info'] = result.stdout
                except Exception as e:
                    self.logger.debug(f"Fehler bei lsusb für {port.device}: {str(e)}")

            port_info.append(port_data)

    def _add_windows_port_info(self, port_info):
        """Sammelt detaillierte Informationen über serielle Ports unter Windows"""
        for port in serial.tools.list_ports.comports():
            port_info.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unbekannt',
                'is_arduino': self._is_arduino(port)
            })

    def _add_macos_port_info(self, port_info):
        """Sammelt detaillierte Informationen über serielle Ports unter macOS"""
        # Standardinformationen sammeln
        for port in serial.tools.list_ports.comports():
            port_data = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
                'manufacturer': port.manufacturer if hasattr(port, 'manufacturer') else 'Unbekannt',
                'is_arduino': self._is_arduino(port)
            }

            # Versuchen, zusätzliche Informationen über system_profiler zu bekommen
            try:
                cmd = ['system_profiler', 'SPUSBDataType']
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    # Hier könnten wir die Ausgabe parsen, um Informationen zu extrahieren
                    port_data['usb_info'] = "Verfügbar (siehe system_profiler SPUSBDataType)"
            except Exception as e:
                self.logger.debug(f"Fehler bei system_profiler für {port.device}: {str(e)}")

            port_info.append(port_data)