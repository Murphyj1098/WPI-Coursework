#ifndef INITIALIZATION_H
#define INITIALIZATION_H

/* libraries */
#include "ESP8266WebServer.h"
#include "WiFiManager.h"

/*constants*/

#define NODEMCU
// #define ESP01

#ifdef ESP01
#define MOTOR  3    // GPIO0 pin -> Stove PWM
#define SWITCH 5    // GPIO2 pin -> Switch State
#endif

#ifdef NODEMCU
#define MOTOR  D1    // GPIO pin -> Stove PWM
#define SWITCH D5    // GPIO pin -> Switch State
#endif

/*shared global variables*/
extern ESP8266WebServer server;     // Webserver object that listens for HTTP request on port 255
extern bool stoveState;             // Stove state

/*function prototypes*/
// initialize GPIO
void gpioInit(void);

// initialize WiFi using WiFiManager
void wifiInit(void);

// initialize and start web server
void serverInit(void);

// called when switch changes state - updates state and turns off motor if on
ICACHE_RAM_ATTR void switch_ISR(void);

#endif