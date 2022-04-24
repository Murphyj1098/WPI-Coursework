#!/usr/bin/python3

# Imports
import base64   # Encoding binary data
import json     # Creating json
import os       # File path manipluation
import requests # Making HTTP requests
import sys      # Reading program arguments
import time     # Program sleep

# Constants
HOST = 'http://ptsv2.com/t/aubib-1606831780/post'  # host of webserver (spectrumobservatory.wpi.edu)

BINNAME  = "sample.dat"     # name of the input file  TODO: standardize
JSONNAME = "sample.json"    # name of file being sent TODO: standardize

HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# This will be called if the program recieves a SIGTERM signal
# This closes the websocket and handles anyother necessary cleanup
def term():
    return None


# Main parent function
def main():

    rx_time     = 1
    sampleRate  = 10000
    radio       = 1

    ## Main loop: 
    # 1. Read GNURadio output file
    # 2. Parse header info
    # 3. Encode payload
    # 4. Create JSON
    # 5. Send JSON
    # 6. Wait and repeat
    while(rx_time < 10):
        ## Read in bin file (in demo the headers will be prompted for user input)
        # TODO: replace this with proper header parsing from bin file

        ## Encode data payload from bin file into base64 ascii characters
        # TODO: is this as simple as opening a file and reading? (Earlier parsing can split the headers into a seperate file?)
        inputFile   = open(BINNAME, "rb")
        inputBinary = inputFile.read()
        encodedData = (base64.b64encode(inputBinary)).decode('ascii')

        ## Create JSON file using encoded payload and header metadata
        jsonFormat = {"metadata":[{"rx_time" : rx_time, "rx_sample" : sampleRate, "radio_num" : radio}], "payload" : encodedData}
        jsonFile = json.dumps(jsonFormat, indent=4)

        r = requests.post(url=HOST, data=jsonFile, headers=HEADERS)
        print(r)
        ## Wait and repeat process
        rx_time = rx_time + 5   # temporary time increment (the header parsing will update this)
        # os.remove(JSONNAME)     # remove the transmitted json file

        # Wait to send next file (TODO: does this program need to do anything else in the meanwhile?)
        print(f"[+] Sleeping for 5 seconds")
        time.sleep(5) # TODO: this sleep amount will change based on GNURadio file creation timing
        
    # TODO: add some sort of handling for signal interupts? (Safely terminate while process is running in background)

if __name__ == '__main__':
    main()
