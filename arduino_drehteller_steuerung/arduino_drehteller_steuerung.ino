/*
 * Drehteller-Steuerung über Solid State Relais
 * 
 * Steuert einen Motor mit einem Solid State Relais an.
 * Kommandos über die serielle Schnittstelle:
 * 1 = Motor einschalten (Relais schließen)
 * 0 = Motor ausschalten (Relais öffnen)
 */

const int RELAY_PIN = 8;  // Pin an dem das Relais angeschlossen ist (ggf. anpassen)

void setup() {
  // Initialisierung der seriellen Kommunikation
  Serial.begin(9600);
  
  // Relay-Pin als Ausgang konfigurieren
  pinMode(RELAY_PIN, OUTPUT);
  
  // Relay initial ausschalten
  digitalWrite(RELAY_PIN, LOW);
  
  // Status-Meldung
  Serial.println("Drehteller-Steuerung bereit");
}

void loop() {
  // Auf Befehle von der seriellen Schnittstelle warten
  if (Serial.available() > 0) {
    // Befehl lesen
    String command = Serial.readStringUntil('\n');
    command.trim(); // Leerzeichen und Zeilenumbrüche entfernen
    
    // Befehl verarbeiten
    if (command == "1") {
      // Motor einschalten
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("OK");
    } 
    else if (command == "0") {
      // Motor ausschalten
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("OK");
    }
    else {
      // Unbekannter Befehl
      Serial.println("ERROR: Unknown command");
    }
  }
}
