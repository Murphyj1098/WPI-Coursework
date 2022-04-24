#include <Arduino.h>
#include <Server.h>

#include "initialization.h"
#include "serverHandlers.h"

// reponds to GET request to root page
void handleRoot(void)
{
    server.send(200, "plain/text", "Hello");
}

// reponds to GET request with state of stove (GPIO0)
void handleState(void)
{
    String state;
    if(stoveState)              // if stove is on
        state = "on";           // send on
    else if(!stoveState)        // if stove is off
        state = "off";          // send off

    server.send(200, "text/plain", state);
}

// on POST turns off the stove with motor (GPIO2)
void handleMotor(void)
{
    server.send(200, "plain/text", "\0");   // blank response

    if(stoveState) // if stove is on
    {                          
        analogWriteFreq(50);
        analogWrite(MOTOR, 51);            // start motor
    }
}