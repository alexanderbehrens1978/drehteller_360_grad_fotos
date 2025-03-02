// arduino_drehteller_steuerung.ino

// Definiere den Pin für das Relais
#define RELAIS_PIN 8

void setup() {
  // Initialisiere die serielle Kommunikation mit 9600 Baud
  Serial.begin(9600);

  // Konfiguriere den Relais-Pin als Ausgang
  pinMode(RELAIS_PIN, OUTPUT);

  // Stelle sicher, dass das Relais zu Beginn ausgeschaltet ist
  digitalWrite(RELAIS_PIN, LOW);

  Serial.println("Arduino Drehteller Steuerung bereit");
}

void loop() {
  // Prüfe, ob Daten verfügbar sind
  if (Serial.available() > 0) {
    // Lese eingehende Daten
    char command = Serial.read();

    // Interpretiere Befehl
    if (command == '1') {
      // Relais einschalten
      digitalWrite(RELAIS_PIN, HIGH);
      Serial.println("Relais eingeschaltet - Drehteller läuft");
    }
    else if (command == '0') {
      // Relais ausschalten
      digitalWrite(RELAIS_PIN, LOW);
      Serial.println("Relais ausgeschaltet - Drehteller gestoppt");
    }
    else {
      // Unbekannter Befehl
      Serial.println("Unbekannter Befehl empfangen. Verwende '1' zum Einschalten und '0' zum Ausschalten.");
    }
  }

  // Kurze Pause, um CPU-Last zu reduzieren
  delay(10);
}