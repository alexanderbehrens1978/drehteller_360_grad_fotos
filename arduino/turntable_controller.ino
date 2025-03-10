/*
 * Datei: arduino/turntable_controller.ino
 * Arduino-Sketch zur Steuerung des Drehtellers
 *
 * Steuert ein Relais an Pin 9 zur Steuerung eines Drehtellers.
 * Kommuniziert über die serielle Schnittstelle mit dem Hauptprogramm.
 */

// Pin-Definitionen
#define RELAY_PIN 9

// Zustände
bool motorRunning = false;

void setup() {
  // Serielle Verbindung initialisieren
  Serial.begin(9600);

  // Relais-Pin als Ausgang konfigurieren
  pinMode(RELAY_PIN, OUTPUT);

  // Relais initial ausschalten (LOW = Relais aus = Motor aus)
  digitalWrite(RELAY_PIN, LOW);

  // Status ausgeben
  Serial.println("Drehteller-Controller bereit");
}

void loop() {
  // Auf serielle Befehle warten
  if (Serial.available() > 0) {
    // Befehl einlesen
    char command = Serial.read();

    // Befehl verarbeiten
    switch (command) {
      case '0':
        // Motor ausschalten
        stopMotor();
        break;

      case '1':
        // Motor einschalten
        startMotor();
        break;

      case 'S':
        // Status abfragen
        sendStatus();
        break;

      default:
        // Unbekannter Befehl
        Serial.println("ERROR: Unknown command");
        break;
    }

    // Restlichen Puffer leeren
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}

void startMotor() {
  // Motor einschalten (HIGH = Relais an = Motor an)
  digitalWrite(RELAY_PIN, HIGH);
  motorRunning = true;

  // Bestätigung senden
  Serial.println("OK");
}

void stopMotor() {
  // Motor ausschalten (LOW = Relais aus = Motor aus)
  digitalWrite(RELAY_PIN, LOW);
  motorRunning = false;

  // Bestätigung senden
  Serial.println("OK");
}

void sendStatus() {
  // Aktuellen Status senden
  if (motorRunning) {
    Serial.println("STATUS: RUNNING");
  } else {
    Serial.println("STATUS: STOPPED");
  }
}