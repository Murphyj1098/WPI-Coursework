#ifndef SERVERHANDLERS_H
#define SERVERHANDLERS_H

/* libraries */


/*constants*/


/*shared global variables*/


/*function prototypes*/
// reponds to GET request to root page
void handleRoot(void);

// reponds to GET request with state of stove (GPIO0)
void handleState(void);

// on POST turns off the stove with motor (GPIO2)
void handleMotor(void);

#endif