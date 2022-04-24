import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# BLE Channel 38
Fs = 2e6      # Sample rate
Fc = 2480e6   # Center frequency

N  = 2**15

# Standard Pluto setup
sdr = adi.Pluto("ip:192.168.2.1")
sdr.sample_rate = int(Fs)
sdr.rx_rf_bandwidth = int(Fs)
sdr.rx_lo = int(Fc)
sdr.rx_buffer_size = N

# Take numFFT sets of samples and append to array S
samps = sdr.rx()

# Call scipy spectrogram function
f, t, Sxx = signal.spectrogram(samps, Fs, return_onesided=False)

f = np.fft.fftshift(f)+Fc
Sxx = np.fft.fftshift(Sxx, axes=0)

# FFT shift to ensure Fc is in the center (for non-onesided)
# (see bottom https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.spectrogram.html)
plt.pcolormesh(t, f, Sxx, shading='gouraud')
plt.ylabel('Freq [Hz]')
plt.xlabel('Time [sec]')
plt.show()
