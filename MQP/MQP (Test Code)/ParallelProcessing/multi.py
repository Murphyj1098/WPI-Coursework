import multiprocessing
import subprocess
import time

def radios1():
    subprocess.run(["uhd_fft", "-f 700"])
    print("Ran1")


def radios2():
    subprocess.run(["uhd_fft", "-f 800"])
    print("Ran2")


def main():
    p1 = multiprocessing.Process(target=radios1)
    p2 = multiprocessing.Process(target=radios2)

    p1.start()
    p2.start()

    p1.join()
    p2.join()

    print("Done")

if __name__ == '__main__':
    main()
