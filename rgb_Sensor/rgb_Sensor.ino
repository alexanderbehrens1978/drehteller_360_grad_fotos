#include <SPI.h>
#include <Ethernet.h>

// Angepasste Pin-Belegung für Kompatibilität mit Ethernet Shield
#define S0      2     // S0 bleibt auf Pin 2
#define S1      3     // S1 bleibt auf Pin 3
#define S2      5     // S2 bleibt auf Pin 5
#define S3      6     // S3 verschoben auf Pin 6 (vorher 4)
#define OUT     7     // OUT verschoben auf Pin 7 (vorher 6)
#define RELAY   8     // Relais bleibt auf Pin 8

// Schwellwert für Schwarz/Weiß-Erkennung
uint16_t THRESHOLD = 120;

// Ethernet-Konfiguration
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 188, 177);
EthernetServer server(80);

// Watchdog-Timer
unsigned long lastConnectionTime = 0;
const unsigned long connectionTimeout = 60000;

// Messwerte
uint16_t redFreq = 0;
uint16_t greenFreq = 0;
uint16_t blueFreq = 0;
uint16_t clearFreq = 0;
uint16_t brightness = 0;
boolean isBlack = false;

void stop_all() {
  digitalWrite(S0, LOW);
  digitalWrite(S1, LOW);
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
}

void read_20() { 
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
  pinMode(RELAY, OUTPUT); 
  
  digitalWrite(RELAY, HIGH);
  delay(10);  
  digitalWrite(RELAY, LOW);
  delay(10);  
  
  Ethernet.begin(mac, ip);
  server.begin();
  
  Serial.print("Server gestartet auf IP: ");
  Serial.println(Ethernet.localIP());
  Serial.println("Warte auf Threshold-Konfiguration vom 360° Drehteller-System...");
  
  read_20();
}

void handleWebClient() {
  EthernetClient client = server.available();
  if (client) {
    lastConnectionTime = millis();
    boolean currentLineIsBlank = true;
    String requestLine = "";
    char buffer[40];
    unsigned long requestStartTime = millis();
    
    while (client.connected()) {
      if (millis() - requestStartTime > 5000) {
        break;
      }
      
      if (client.available()) {
        char c = client.read();
        
        if (requestLine.length() < 40) {
          requestLine += c;
        }
        
        if (c == '\n' && requestLine.length() > 0) {
          if (requestLine.indexOf("threshold=") > 0) {
            int startPos = requestLine.indexOf("threshold=") + 10;
            int endPos = requestLine.indexOf(" ", startPos);
            if (endPos == -1) endPos = requestLine.indexOf("&", startPos);
            if (endPos == -1) endPos = requestLine.length();
              
            if (endPos > startPos && (endPos - startPos) < 4) {
              for (int i = 0; i < (endPos - startPos) && i < 3; i++) {
                buffer[i] = requestLine.charAt(startPos + i);
                buffer[i+1] = '\0';
              }
              THRESHOLD = atoi(buffer);
            }
          }
          
          if (requestLine.indexOf("GET /status") > 0) {
            // Status-API für die Hauptanwendung
          }
          
          requestLine = "";
        }
        
        if (c == '\n' && currentLineIsBlank) {
          client.println("HTTP/1.1 200 OK");
          
          if (requestLine.indexOf("GET /status") > 0) {
            client.println("Content-Type: application/json");
            client.println("Connection: close");
            client.println();
            client.print("{\"isBlack\":");
            client.print(isBlack ? "true" : "false");
            client.print(",\"threshold\":");
            client.print(THRESHOLD);
            client.print(",\"values\":{\"r\":");
            client.print(redFreq);
            client.print(",\"g\":");
            client.print(greenFreq);
            client.print(",\"b\":");
            client.print(blueFreq);
            client.print(",\"c\":");
            client.print(clearFreq);
            client.print(",\"brightness\":");
            client.print(brightness);
            client.println("}}");
          } 
          else {
            client.println("Content-Type: text/html; charset=utf-8");
            client.println("Connection: close");
            client.println();
            
            client.println("<html><head><meta charset=\"utf-8\"></head><body>");
            
            client.print("<p>R: ");
            client.print(redFreq);
            client.print(" G: ");
            client.print(greenFreq);
            client.print(" B: ");
            client.print(blueFreq);
            client.print(" Clear: ");
            client.print(clearFreq);
            client.print(" Helligkeit: ");
            client.print(brightness);
            client.println("</p>");
            
            client.print("<form><input type='number' name='threshold' value='");
            client.print(THRESHOLD);
            client.println("'><input type='submit'></form>");
            
            client.println("</body></html>");
          }
          
          break;
        }
        
        if (c == '\n') {
          currentLineIsBlank = true;
        } 
        else if (c != '\r') {
          currentLineIsBlank = false;
        }
      }
    }
    
    delay(1);
    client.stop();
  }
}

void detectColor() {
  digitalWrite(S2, LOW);
  digitalWrite(S3, LOW);
  delay(2);
  redFreq = pulseIn(OUT, LOW, 2500);
  
  digitalWrite(S2, HIGH);
  digitalWrite(S3, HIGH);
  delay(2);
  greenFreq = pulseIn(OUT, LOW, 2500);
  
  digitalWrite(S2, LOW);
  digitalWrite(S3, HIGH);
  delay(2);
  blueFreq = pulseIn(OUT, LOW, 2500);
  
  digitalWrite(S2, HIGH);
  digitalWrite(S3, LOW);
  delay(2);
  clearFreq = pulseIn(OUT, LOW, 2500);
  
  brightness = (redFreq + greenFreq + blueFreq) / 3;
  
  if (brightness > THRESHOLD) {
    isBlack = true;
    digitalWrite(RELAY, HIGH);
  } else {
    isBlack = false;
    digitalWrite(RELAY, LOW);
  }
}

void checkEthernetStatus() {
  if (millis() - lastConnectionTime > connectionTimeout) {
    Serial.println("Keine Verbindung seit längerer Zeit, Neustart des Ethernet-Shields...");
    
    delay(100);
    
    Ethernet.begin(mac, ip);
    server.begin();
    Serial.print("Server neu gestartet auf IP: ");
    Serial.println(Ethernet.localIP());
    
    lastConnectionTime = millis();
  }
}

void loop() {
  Ethernet.maintain();
  
  static unsigned long lastReadTime = 0;
  if (millis() - lastReadTime > 100) {  
    read_20();
    detectColor();
    stop_all();
    lastReadTime = millis();
  }
  
  handleWebClient();
  
  checkEthernetStatus();
  
  delay(10);
}
