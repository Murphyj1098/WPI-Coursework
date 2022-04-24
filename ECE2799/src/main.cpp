#include <Arduino.h>

#include "initialization.h"
#include "serverHandlers.h"

void setup()
{
    Serial.begin(115200);       // Start the Serial communication buad rate 115200
    delay(10);
    Serial.println('\n');

    gpioInit();                 // initialize
    wifiInit();
    serverInit();
}

void loop()
{
  server.handleClient();        // handle web server requests
}
