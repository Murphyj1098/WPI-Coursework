To Compile and Run the Client

    In the Client directory, run "make" to complile the project into the file HTTPClient

    "make clean" will remove this file 

    To run the client use the command ./HTTPClient <-p> <domain> <port number>
        <-p> is optional to print out the RTT
        <domain> is the website to connect to e.g, www.wpi.edu or www.mit.edu
        <port number> is the port to use e.g, 80

    The client will download the html file into index.html in the Client directory



To Compile and Run the Server

    In the Server directory, run "make" to complile the project into the file HTTPServer

    "make clean" will remove this file 

    To run the server use the command ./HTTPServer <port number>
        <port number> is the port to listen to e.g, 80



To Use Both the Server and Client
    
    Make both as explained above

    Use ./HTTPClient <-p> <domain>/index.html <port number>
    Use ./HTTPServer <port number>

    The extension for the domain can be either /index.html or /TMDG.html