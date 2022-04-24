#!/usr/bin/env python3

# Implementation of a daemon class
# Taken from: http://web.archive.org/web/20131017130434/http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/

# This class handles creating a process and daemonizing itself
# To use it you simply subclass it and implement the run method

import atexit, logging, os, sys, time
from signal import SIGTERM

class Daemon:
    def __init__(self, pidfile):
        self.pidfile = pidfile


    def daemonize(self):
        # UNIX double fork mechanism
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as err:
            logging.critical('Fork #1 failed: {0}\n'.format(err))
            sys.exit(1)

        # Decouple from parent environment
        # NOTE: we do not change the working directory (current working directory is not at risk of being unmounted)
        os.setsid()
        os.umask(0)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit second parent
                sys.exit(0)
        except OSError as err:
            logging.critical('Fork #2 failed: {0}\n'.format(err))
            sys.exit(1)

        # Redirect standard file descriptors into /dev/null
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a')
        se = open(os.devnull, 'a')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # Write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, 'w+') as f:
            f.write(pid + '\n')


    def delpid(self):
        os.remove(self.pidfile)


    def start(self):
        # Check for a pidfile to see if daemon is already running
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile {0} already exists."
            logging.error(message.format(self.pidfile))
            sys.exit(1)
        
        # Start the daemon
        self.daemonize()
        self.run()


    def stop(self):
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile {0} does not exist."
            logging.warn(message.format(self.pidfile))
            return # this is not a fatal error if the daemon is restarting (do not exit program)

        # Try to kill the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            e = str(err.args)
            if e.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                logging.error(e)
                sys.exit(1)


    def restart(self):
        # Restart the daemon
        self.stop()
        self.start()


    def run(self):
        # Should be overwritten when Daemon is subclassed
        # Is called when the daemon finishes start() or restart()
        pass
