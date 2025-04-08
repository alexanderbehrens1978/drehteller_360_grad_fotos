/*
 * Arduino-Sketch für einen Näherungssensor (LJ12A3-4-Z/BX) an Pin 2
 * Die eingebaute LED auf dem Arduino Uno R3 (Pin 13) wird entsprechend dem Schaltzustand ein- und ausgeschaltet
 */

// Konstanten definieren
const int SENSOR_PIN = 2;      // Der Näherungssensor ist an Pin 2 angeschlossen
// Braun = 5V
// Blau = GND
const int LED_PIN = 13;        // Die eingebaute LED des Arduino ist an Pin 13 angeschlossen

// Variablen
int sensorStatus = 0;          // Variable zum Speichern des Sensorstatus

void setup() {
  // Serial-Kommunikation initialisieren (für Debugging)
  Serial.begin(9600);
  
  // Warten bis die serielle Verbindung aufgebaut ist
  while (!Serial) {
    ; // Warten auf Verbindung
  }
  
  // Pin-Modi festlegen
  pinMode(SENSOR_PIN, INPUT);  // Sensorpin als Eingang konfigurieren
  pinMode(LED_PIN, OUTPUT);    // LED-Pin als Ausgang konfigurieren
  
  delay(1000); // Kurze Pause zum Stabilisieren
  Serial.println("Naherungssensor-Sketch gestartet");
}

void loop() {
  // Sensorstatus digital auslesen
  sensorStatus = digitalRead(SENSOR_PIN);
  
  // Zusätzlich analog auslesen (falls der Sensor auch analoge Werte liefert)
  int analogValue = analogRead(A0);  // Vorausgesetzt, Sie haben den Sensor auch an A0 angeschlossen
  
  // Sensorstatus im seriellen Monitor ausgeben
  Serial.print("Digitaler Status: ");
  Serial.print(sensorStatus);
  Serial.print("  |  Analoger Wert: ");
  Serial.println(analogValue);
  
  // LED entsprechend dem Sensorstatus schalten
  if (sensorStatus == HIGH) {
    digitalWrite(LED_PIN, HIGH);  // LED einschalten wenn Sensor aktiviert ist
    Serial.println("LED: EIN");
  } else {
    digitalWrite(LED_PIN, LOW);   // LED ausschalten wenn Sensor nicht aktiviert ist
    Serial.println("LED: AUS");
  }
  
  // Kurze Pause, um die Serielle Ausgabe lesbar zu halten
  delay(1000);
}