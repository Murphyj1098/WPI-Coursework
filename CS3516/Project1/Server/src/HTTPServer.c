// Joseph Murphy (jrmurphy)
// CS3516 Project 1 - Socket Programming

#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#include "HTTPServer.h"

int main(int argc, char** argv)
{

    int socketID, clientID;
    socklen_t addressSize;

    char c;
    char inMessage[4096];
    char *OK, *notFound; // HTTP responses

    struct addrinfo hints;
    struct addrinfo *serverAddress;
    struct sockaddr_storage clientAddress;

    FILE *outFile;
    FILE *outStream;

    if(argc != 2)
    {
        usage();
        exit(1);
    }

    // hints struct
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags = AI_PASSIVE;

    // get address info
    if(getaddrinfo(NULL, argv[1], &hints, &serverAddress) < 0)
    {
        printf("Failed to get address info\n");
        exit(1);
    }

    // create socket
    if((socketID = socket(serverAddress->ai_family, serverAddress->ai_socktype, serverAddress->ai_protocol)) < 0)
    {
        printf("Failed to create socket\n");
        exit(1);
    }

    // bind socket to server address
    if(bind(socketID, serverAddress->ai_addr, serverAddress->ai_addrlen) < 0)
    {
        printf("Failed to bind socket\n");
        close(socketID);
        exit(1);
    }

    // Convert unconnected socket into passive socket and allow connections to queue
    if(listen(socketID, 10) != 0)
    {
        printf("Listen call error\n");
        close(socketID);
        exit(1);
    }

    printf("Waiting for client to connect\n");

    while(1)
    {
        addressSize = sizeof clientAddress;
        if((clientID = accept(socketID, (struct sockaddr *)&clientAddress, &addressSize)) < 0)
        {
            printf("Error accepting client");
            continue;
        }

        // Take in request
        recv(clientID, inMessage, sizeof(inMessage), 0);

        // Parse request (is requested file /TMDG.html or /index.html)
        if(strstr(inMessage, "/TMDG.html") != NULL || strstr(inMessage, "/index.html") != NULL)
        {
            // Send HTTP Header and TMDG.html
            outStream = fdopen(clientID, "r+");
            outFile = fopen("TMDG.html", "r");

            OK = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: Closed\r\n\r\n";
            fprintf(outStream, "%s", OK);

            while((c = fgetc(outFile)) != EOF)
            {
                fputc(c, outStream);
            }

            fclose(outStream);
            fclose(outFile);
            close(clientID);
        }
        else
        {
            notFound = "HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\nConnection: Closed\r\n\r\n";
            send(clientID, notFound, strlen(notFound), 0);
            close(clientID);
        }
    }

    return 0;
}

// print out program usage to console
void usage() 
{
    printf("usage: ./HTTPServer <port number>\n");
    printf("Port number should be above 5000\n");
}