#define S1      2
#define S0      3
#define S3      4
#define S2      5
#define OUT     6
#define RELAY   8

uint16_t frequency = 0;
uint16_t pause = 170; // Dieser Wert ist die Schwelle zwischen Schwarz und weiss

void stop_all() {
  digitalWrite(S0, LOW);
  digitalWrite(S1, LOW);
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
}

void read_20() { // Setting frequency-scaling to 20%
  digitalWrite(S0, HIGH);
  digitalWrite(S1, LOW);
}

void setup() {
  Serial.begin(9600);
  pinMode(S0, OUTPUT);
  pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT);
  pinMode(S3, OUTPUT);
  pinMode(OUT, INPUT);
  pinMode(RELAY, OUTPUT);  // Relais als Ausgang definieren
  digitalWrite(RELAY, LOW); // Relais initial ausschalten
  
  read_20();
}

void loop() {
  bool relayActivated = false;  // Variable zum Verfolgen des Relais-Status
  
  read_20();
 // delay(100);
  
  // Setting Roter filters
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
  
  frequency = pulseIn(OUT, LOW);
  Serial.print("Roter = ");
  Serial.print(frequency);
  Serial.print("\t");
  
  // Prüfen, ob Rotwert > 200
  if (frequency > pause) {
    relayActivated = true;
  }
  
  //delay(200);
  
  // Setting Grüner filters
  digitalWrite(S2, HIGH);
  digitalWrite(S3, HIGH);
  
  frequency = pulseIn(OUT, LOW);
  Serial.print("Grüner = ");
  Serial.print(frequency);
  Serial.print("\t");
  
  // Prüfen, ob Grünwert > 200
  if (frequency > pause) {
    relayActivated = true;
  }
  
 // delay(200);
  
  // Setting Blauer filters
  digitalWrite(S2, LOW);
  digitalWrite(S3, HIGH);
  
  frequency = pulseIn(OUT, LOW);
  Serial.print("Blauer = ");
  Serial.println(frequency);
  
  // Prüfen, ob Blauwert > 200
  if (frequency > pause) {
    relayActivated = true;
  }
  
  //delay(200);
  
  // Relais entsprechend steuern
  if (relayActivated) {
    digitalWrite(RELAY, HIGH);  // Relais einschalten
    Serial.println("Relais EIN");
  } else {
    digitalWrite(RELAY, LOW);   // Relais ausschalten
    Serial.println("Relais AUS");
  }
  
  stop_all();
 // delay(100);
}
