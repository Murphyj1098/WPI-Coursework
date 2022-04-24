import daemon
import daemon.pidfile
import os
import signal


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    out = open('loga.log', 'w+')

    context = daemon.DaemonContext(
        working_directory=here,
        stdout=out,
        pidfile=daemon.pidfile.PIDLockFile('/home/jrmurphy/lock.pid')
    )

    with context:
        j = 0
        while(j < 1000000000):
            print('Counting ... %s' % j)
            j += 1
