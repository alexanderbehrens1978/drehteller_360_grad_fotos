// relais_test.ino
void setup() {
  Serial.begin(9600);
  pinMode(8, OUTPUT);

  Serial.println("Relais-Test startet");
  digitalWrite(8, HIGH);  // Dauerhaft einschalten
  Serial.println("Relais sollte jetzt eingeschaltet sein");
}

void loop() {
  // Nichts hier, Relais bleibt eingeschaltet
}