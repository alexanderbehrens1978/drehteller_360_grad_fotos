/*
 * Drehteller-Controller für 360-Grad-Fotografie
 * 
 * Dieser Sketch steuert ein Relais, welches einen Motor für einen Drehteller antreibt.
 * Kommunikation erfolgt über serielle Schnittstelle.
 * 
 * Befehle:
 * - "ON": Schaltet das Relais ein (Motor läuft)
 * - "OFF": Schaltet das Relais aus (Motor stoppt)
 * 
 * Bei jedem erfolgreichen Befehl antwortet der Arduino mit "OK"
 */

// Pin-Konfiguration
const int RELAY_PIN = 8;  // Das Relais ist an Pin 3 angeschlossen

// Status-Variablen
bool motorRunning = false;

void setup() {
  // Serielle Verbindung initialisieren
  Serial.begin(9600);
  
  // Pin-Konfiguration
  pinMode(RELAY_PIN, OUTPUT);
  
  // Relais zu Beginn ausschalten
  digitalWrite(RELAY_PIN, LOW);
  
  // Status ausgeben
  Serial.println("Drehteller-Controller bereit");
}

void loop() {
  // Auf Befehle über serielle Schnittstelle prüfen
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();  // Entfernt Leerzeichen und Zeilenumbrüche
    
    // Befehl verarbeiten
    if (command == "ON") {
      // Relais einschalten (Motor starten)
      digitalWrite(RELAY_PIN, HIGH);
      motorRunning = true;
      Serial.println("OK");
    } 
    else if (command == "OFF") {
      // Relais ausschalten (Motor stoppen)
      digitalWrite(RELAY_PIN, LOW);
      motorRunning = false;
      Serial.println("OK");
    }
    else {
      // Unbekannter Befehl
      Serial.println("ERROR: Unbekannter Befehl. Verwende 'ON' zum Einschalten und 'OFF' zum Ausschalten.");
    }
  }
  
  // Kurze Pause zur Vermeidung von CPU-Last
//  delay(50);
}
