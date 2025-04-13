/*
 * Hall-Sensor Arduino Sketch
 * 
 * Liest den analogen Wert des KY-003 Hall-Sensors an Pin A0 und
 * sendet die Werte über die serielle Schnittstelle.
 * 
 * Der Hall-Sensor gibt niedrige Werte zurück, wenn ein Magnet erkannt wird,
 * und hohe Werte, wenn kein Magnet in der Nähe ist.
 * 
 * Verbindung wie im Schaltplan angegeben:
 * - KY-003 S -> Arduino A0 (blauer Draht)
 * - KY-003 mittlerer Pin -> Arduino 5V (roter Draht)
 * - KY-003 - Pin -> Arduino GND (schwarzer Draht)
 */

// Pin-Definition
const int HALL_SENSOR_PIN = A0;  // Hall-Sensor an A0
const int LED_PIN = LED_BUILTIN; // Eingebaute LED

// Variablen
uint16_t sensorValue = 0;
const int THRESHOLD = 30;        // Schwellwert für Magneterkennung

void setup() {
  // Serielle Kommunikation initialisieren
  Serial.begin(9600);
  
  // LED-Pin als Ausgang konfigurieren
  pinMode(LED_PIN, OUTPUT);
  
  // Begrüßungsnachricht
  Serial.println("Hall-Sensor-Modul gestartet");
  Serial.println("Format der Ausgabe: 'Hall sensor value: <wert>'");
}

void loop() {
  // Hall-Sensor auslesen (analoger Wert 0-1023)
  sensorValue = analogRead(HALL_SENSOR_PIN);
  
  // Sensorwert über serielle Schnittstelle senden
  Serial.print("Hall sensor value: ");
  Serial.println(sensorValue);
  
  // LED entsprechend des Sensorwerts schalten
  // Niedrige Werte (<30) bedeuten, dass ein Magnet erkannt wurde
  if (sensorValue < THRESHOLD) {
    digitalWrite(LED_PIN, LOW);  // LED einschalten bei erkanntem Magnet
  } else {
    digitalWrite(LED_PIN, HIGH); // LED ausschalten, wenn kein Magnet erkannt wird
  }
  
  // Keine Verzögerung mehr, um sofortige Messungen zu ermöglichen
  // Minimale Pause für CPU-Entlastung
  delayMicroseconds(500);
}
