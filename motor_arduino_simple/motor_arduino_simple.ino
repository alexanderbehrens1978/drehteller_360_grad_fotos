/*
 * Einfache Motor Steuerung für Arduino
 * 
 * Dieses Sketch empfängt Befehle über die serielle Schnittstelle:
 * - "1\n": Schaltet den Motor ein
 * - "0\n": Schaltet den Motor aus
 * 
 * Pin-Konfiguration:
 * - Pin 8: Digitaler Ausgang für Motor (HIGH = ein, LOW = aus)
 */

// Motor-Pin definieren
const int MOTOR_PIN = 8;  // Digitaler Pin für Motor

// Status-Variablen
boolean motorRunning = false;

// Buffer für serielle Kommunikation
String inputBuffer = "";
boolean commandComplete = false;

void setup() {
  // Serielle Kommunikation initialisieren
  Serial.begin(9600);
  
  // Motor-Pin konfigurieren
  pinMode(MOTOR_PIN, OUTPUT);
  
  // Initialen Zustand setzen
  digitalWrite(MOTOR_PIN, LOW);  // Motor aus
  
  // Willkommensnachricht
  Serial.println("Motor Controller bereit");
}

void loop() {
  // Auf serielle Befehle prüfen
  readSerialCommand();
  
  // Befehl verarbeiten, wenn vollständig
  if (commandComplete) {
    processCommand();
    
    // Buffer zurücksetzen
    inputBuffer = "";
    commandComplete = false;
  }
}

void readSerialCommand() {
  // Prüfen, ob Daten verfügbar sind
  while (Serial.available() > 0) {
    char inChar = (char)Serial.read();
    
    // Wenn Zeilenende erkannt, Befehl als vollständig markieren
    if (inChar == '\n') {
      commandComplete = true;
      break;
    } else {
      // Sonst zum Buffer hinzufügen
      inputBuffer += inChar;
    }
  }
}

void processCommand() {
  // Buffer trimmen
  inputBuffer.trim();
  
  // Befehl interpretieren
  if (inputBuffer.length() > 0) {
    if (inputBuffer == "1") {
      // Motor einschalten
      digitalWrite(MOTOR_PIN, HIGH);
      motorRunning = true;
      Serial.println("Motor EIN");
    } 
    else if (inputBuffer == "0") {
      // Motor ausschalten
      digitalWrite(MOTOR_PIN, LOW);
      motorRunning = false;
      Serial.println("Motor AUS");
    } 
    else {
      // Unbekannter Befehl
      Serial.print("Unbekannter Befehl: ");
      Serial.println(inputBuffer);
    }
  }
}
