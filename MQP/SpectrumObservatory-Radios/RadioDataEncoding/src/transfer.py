#!/usr/bin/env python3

## Imports
import base64   # Encoding binary data
import json     # Creating JSON file
import logging  # Logging library
import os       # File path manipluation
import pmt      # GNU Radio header parsing
import requests # Creating HTTP requests
import sys      # Reading program arguments
import time     # Program sleep

from gnuradio.blocks import parse_file_metadata # GNU Radio header parsing

class Transfer:
    def __init__(self, radioNum):
        self.radioNum = radioNum
        self.HOST = "http://spectrumobservatory.wpi.edu/data"                       # host of webserver
        self.BINNAME = "sample.dat"                                                 # name of the input file (gets overriden on init)
        self.HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'} # Headers for POST request
        self.NITEMS = 300000

        self.inFile = None


    ## Called to update the data file name based on assigned radio number
    def setBINNAME(self):
        self.BINNAME = f'sample{self.radioNum}.dat'


    ## Called when the transfer program is terminated
    # Cleans up open files, removes temporary files and exits (termianting the thread)
    def stop(self):
        logging.info(f"[Process: {self.radioNum}] Program termination\n")
        self.inFile.close()
        os.remove(self.BINNAME)
        sys.exit(0)


    ## This will be called to parse header data out of the dat file
    # Takes in an open file descriptor and returns a python dictionary
    # NOTE: This function is built on the gr_read_file_metadata program from GNU Radio
    def parseHeaders(self):
        
        # read out header bytes into a string
        header_str = self.inFile.read(parse_file_metadata.HEADER_LENGTH)

        # Convert from created string to PMT dict
        try:
            header = pmt.deserialize_str(header_str)
        except RuntimeError:
            logging.info(f"[Process: {self.radioNum}] Could not deserialize header\n")
            self.stop()

        # Convert from PMT dict to Python dict
        info = parse_file_metadata.parse_header(header)

        if(info["extra_len"] > 0):
            extra_str = self.inFile.read(info["extra_len"])

        # Extra header info
        try:
            extra = pmt.deserialize_str(extra_str)
        except RuntimeError:
            logging.info(f"[Process: {self.radioNum}] Could not deserialize extra headers\n")
            self.stop()

        info = parse_file_metadata.parse_extra_dict(extra, info)

        return info


    ## Main running function
    def run(self):

        ## Set the data file name (changes based on radio instance)
        self.setBINNAME()

        ## Open the binary data file
        self.inFile = open(self.BINNAME, "rb")

        headerNum = 0 # Number of headers read

        ## Main loop: 
        # 1. Read GNU Radio output file
        # 2. Parse header info
        # 3. Check if final segment
        # 4. Encode payload
        # 5. Create JSON
        # 6. Send JSON with HTTP POST
        while(True):

            # Read in bin file to parse header metadata
            headerData = self.parseHeaders()
            headerNum += 1
            logging.info(f"[Process: {self.radioNum}] Header Number: {headerNum}")

            # Size of each data segment
            ITEM_SIZE = headerData["nitems"]
            SEG_SIZE  = headerData["nbytes"]

            # Check if sample is too small
            # GET request interrupts GNU Radio's loop causing it to prematurely reinsert a header
            if ITEM_SIZE < self.NITEMS:
                self.inFile.read(SEG_SIZE)
                logging.info(f"[Process: {self.radioNum}] Segment too small, skipping\n")
                continue

            # Pull out relevant header info
            rx_time     = headerData["rx_time"]
            rx_rate     = headerData["rx_rate"]
            rx_freq     = pmt.to_python(headerData["rx_freq"])
            radio       = pmt.to_python(headerData["radio_num"])

            # Encode data payload from bin file into base64 ascii characters
            inputBinary = self.inFile.read(SEG_SIZE)
            encodedData = (base64.b64encode(inputBinary)).decode('ascii')

            # Create JSON file using encoded payload and header metadata
            jsonFormat = {"metadata":{"rx_time" : rx_time, "rx_sample" : rx_rate, "rx_freq" : rx_freq, "radio_num" : radio}, "payload" : encodedData}
            jsonFile = json.dumps(jsonFormat, indent=4)

            # Send this JSON file to the WebServer with an HTTP POST
            r = requests.post(url=self.HOST, data=jsonFile, headers=self.HEADERS)
            logging.info(f"[Process: {self.radioNum}] Response from server: %s\n" %r)
        
            # Wait to send next segment (segments are generated at a rate of 1 per second)
            time.sleep(1)