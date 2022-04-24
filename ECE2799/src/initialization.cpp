#include <Arduino.h>

#include "initialization.h"
#include "serverHandlers.h"

ESP8266WebServer server(255);    // Webserver object that listens for HTTP request on port 255
bool stoveState = false;

// initialize GPIO
void gpioInit(void)
{
    pinMode(SWITCH, INPUT);
    pinMode(MOTOR, OUTPUT);

    // when switch changes (value of GPIO0 changes), run switch_ISR
    attachInterrupt(digitalPinToInterrupt(SWITCH), switch_ISR, CHANGE);
}

// initialize WiFi using WiFiManager
void wifiInit(void)
{
    WiFiManager wifiManager;

    #ifdef ESP01
    IPAddress _ip = IPAddress(*);         // device's ip
    #endif

    #ifdef NODEMCU
    IPAddress _ip = IPAddress(*);         // device's ip
    #endif

    IPAddress _gw = IPAddress(*);          // router ip
    IPAddress _sn = IPAddress(*);        // subnet mask

    wifiManager.setSTAStaticIPConfig(_ip, _gw, _sn);    // set static ip, router ip, and subnet mask

    wifiManager.autoConnect();

    Serial.println('\n');
    Serial.print("Connected to ");
    Serial.println(WiFi.SSID());                        // Print SSID
    Serial.print("IP address:\t");
    Serial.println(WiFi.localIP());                     // Print IP Address of ESP8266
}

// initialize and start web server
void serverInit(void)
{
    server.on("/", HTTP_GET, handleRoot);                   // Handle root page
    server.on("/StoveState", HTTP_GET, handleState);        // Handle status GET
    server.on("/StoveMotor", HTTP_POST, handleMotor);       // Handle motor POST

    server.onNotFound([](){                                 // Handle unknown URIs
      server.send(404, "text/plain", "404: Not found");
      });

    server.begin();                                         // Start the server

    Serial.println("HTTP server started");
}

// called when switch changes state - updates state and turns off motor if its on
ICACHE_RAM_ATTR void switch_ISR(void)
{
    stoveState = digitalRead(SWITCH);                       // Set stove state on switch state change          
    if(!digitalRead(SWITCH))                                // if switch reads off (switch changed from off to on)
        analogWrite(MOTOR, 0);                              // turn off motor
}
