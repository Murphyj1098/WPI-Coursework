#!/usr/bin/env python3

## Imports
import argparse         # Parse commandline args (to set number of radios)
import logging          # Logging library
import multiprocessing  # Seperate child process for each Radio Instance
import signal           # Kernel signal handling
import sys              # Exit program
import threading        # Seperate thread for GNU Radio and EncodeTransfer
import time             # Program sleep

from top_block import (
    top_block
) # GNU Radio top block class

from transfer import (
    Transfer
) # Transfer class

from daemon import (
    Daemon
) # Daemon class


## Daemon subclass
class RadioDaemon(Daemon):

    # Override init to have args attribute
    def __init__(self, pidfile, args):
        Daemon.__init__(self, pidfile) # Run parent constructor

        self.args = args

    # Override run with main process code
    def run(self):

        # Set up signal handler
        signal.signal(signal.SIGTERM, signalHandler)

        # Set up child processes
        p1 = RadioChild(1)
        if self.args.n == 2: 
            p2 = RadioChild(2)

        # Start the child processes
        logging.info("Start Radio Process 1")
        p1.start()

        if self.args.n == 2:
            logging.info("Start Radio Process 2")
            p2.start()

        try:        
            while True:
                time.sleep(0.5)

        except ServiceExit:
            # Terminate the running threads.
            # Signal the GNU Radio thread to stop
            p1.shutdown_flag.set()
            if self.args.n == 2:
                p2.shutdown_flag.set()

            # Wait for the processes to close...
            p1.join()
            if self.args.n == 2:
                p2.join()
 
            logging.info('Exiting main program')


## Radio child-process sublass
class RadioChild(multiprocessing.Process):

    # Override init to have radioNum attribute
    def __init__(self, radioNum):
        multiprocessing.Process.__init__(self) # Run parent constructor

        self.radioNum = radioNum
        self.shutdown_flag = multiprocessing.Event()

    def run(self):
        # Startup code
        g = GNURadioJob(self.radioNum)
        t = EncodeTransferJob(self.radioNum)

        logging.info(f"[Process: {self.radioNum}] Starting GNU Radio Thread")
        g.start()
        time.sleep(5)
        logging.info(f"[Process: {self.radioNum}] Starting Upload Thread")
        t.start()

        # Spin until shutdown is signaled
        while not self.shutdown_flag.is_set():
            time.sleep(0.5)

        # Shutdown code
        g.shutdown_flag.set()
        t.shutdown_flag.set()


## GNU Radio thread subclass
class GNURadioJob(threading.Thread):

    # Override init to have radioNum attribute
    def __init__(self, radioNum):
        threading.Thread.__init__(self) # Run parent constructor

        self.radioNum = radioNum
        self.shutdown_flag = threading.Event()

    def run(self):
        # Startup Code
        tb = top_block(self.radioNum)
        tb.start()
        tb.startThread()

        # Spin until shutdown is signaled
        while not self.shutdown_flag.is_set():
            time.sleep(0.5)

        # Shutdown Code
        tb.stop()
        tb.wait()
        logging.info(f"[Process: {self.radioNum}] GNU Radio Shutdown")


## Encode and Transfer Script thread subclass
class EncodeTransferJob(threading.Thread):

    # Override init to have radioNum attribute
    def __init__(self, radioNum):
        threading.Thread.__init__(self) # Run parent constructor

        self.radioNum = radioNum
        self.shutdown_flag = threading.Event()

    def run(self):
        # Startup Code
        tx = Transfer(self.radioNum)
        tx.run()

        # Spin until shutdown is signaled
        while not self.shutdown_flag.is_set():
            time.sleep(0.5)

        # Shutdown Code
            # Transfer class handles its own shutdown

## Custom exception for termination
class ServiceExit(Exception):
    pass

def signalHandler(signum, frame):
    raise ServiceExit

## Setup daemon and start
def main():

    # Argument parsing (sets number of radios in use and daemon commands)
    parser = argparse.ArgumentParser(description="Daemon controlling radios and data upload")
    parser.add_argument("n", type=int, help="Number of radios in use")
    parser.add_argument("d", type=str, help="Command for daemon (start, stop, restart)")

    args = parser.parse_args()

    # Check if args are invalid
    if args.n < 1 or args.n > 2:
        parser.error("Number of radios must be 1 or 2")
    if args.d != "start" and args.d != "stop" and args.d != "restart":
        parser.error("Daemon command must be start, stop, or restart")

    # Create instance of daemon
    daemon = RadioDaemon('./RadioDaemon.pid', args)

    # Daemon command handling
    if "start" == args.d:

        # Setup logger
        logging.basicConfig(filename="RadioDaemon.log",
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        filemode='w')

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        daemon.start()

    elif "stop" == args.d:
        daemon.stop()

    elif "restart" == args.d:
        daemon.restart()

    sys.exit(0)


if __name__ == "__main__":
    main()