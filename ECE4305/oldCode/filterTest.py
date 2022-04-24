import adi
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal

signal = np.zeros(200)
timeSamples = np.linspace(0,200,200)
for i in range(4):
    #signal[i] = np.cos(500*timeSamples[i]) + np.cos(750*timeSamples[i])
    signal[50* i] = 1
signalFFT = np.fft.fft(signal)

A = [1,1,0,0]
w = [0, 550, 650, 1000]
Fs = 2000
coeffs = scipy.signal.firls(numtaps=41, bands=w, desired=A, fs=Fs)

filtOut = filt = np.zeros(200)
memTap = np.zeros(41)
for i in range(200):
    memTap[0] = signal[i]
    filt = scipy.signal.lfilter(a=[1.0], b=coeffs, x=[memTap])
    filtOut[i] = filt[0,40]
    for k in range(40):
        memTap[40-k] = memTap[39-k]
filtFFT = np.fft.fft(filtOut)

plt.figure(0)
plt.title("pre filtering fft")
plt.plot(signalFFT[0:99])
plt.figure(1)
plt.title("pre filtering time domain")
plt.plot(signal)
plt.figure(2)
plt.title("post filtering fft")
plt.plot(filtFFT[0:99])
plt.figure(3)
plt.title("post filtering time domain")
plt.plot(filtOut)
plt.show()
