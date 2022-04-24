import adi
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal

from funcs import bitList2Binary


## PHY Variables
Fc = 2480e6   # Ideally at 2.480 GHz (BLE Channel 39)
Fs = 2e6      # BLE channels are 2 MHz wide
SymRate = 1e6 # Symbol rate of BLE is 1MSym/s

N = 2**15 # Number of samples

## Pluto Setup
sdr = adi.Pluto("ip:192.168.2.1")
sdr.sample_rate = int(Fs)
sdr.rx_rf_bandwidth = int(Fs)
sdr.rx_lo = int(Fc)
sdr.rx_buffer_size = N


## Data Collection / Packet Selection
frameStart = 0
frameEnd = 0
attempts = 0

while(1):
    # Collect BLE Data
    attempts += 1
    frameData = []
    frameFound = False
    data = sdr.rx()

    # Determine the start and end points of a frame
    threshold = 0.5*max(data)
    frameFlag = False
    nextSamples = np.zeros(400, dtype=np.complex64) 
    rollingAvg = np.zeros(50, dtype=np.complex64)

    for i in range(len(data)):
        rollingAvg[i % 50] = data[i]
        if(frameFound):
            i = len(data)
        elif(np.max(rollingAvg) >= threshold): # We are most likely getting a frame right now
            for n in range(nextSamples.size):
                nextSamples[n] = data[i+n]
            if((not frameFlag) & (max(nextSamples < 1900))):  # Making sure this packet isn't at max magnitude
                frameFlag = True
                frameStart = i-50
        elif(frameFlag):
            frameEnd = i-25
            frameFound = True

    if(frameFound):
        frameDuration = frameEnd - frameStart
        selFrameData = np.zeros(frameDuration, dtype=np.complex64)
        selFrameData = data[frameStart:frameEnd]
        if((max(abs(selFrameData)) < 2000) and (frameDuration > 600)):
            break

print("Found valid frame in %d tries" % attempts)

avgReal = np.average(np.abs(np.real(selFrameData)))
avgImag = np.average(np.abs(np.imag(selFrameData)))

# Starts from beginning of sample array and moves out
# Check if next 3 samples are all above threshold
# Once 3 sequential samples are, we can assume the start of a packet
for index in range(selFrameData.size):
    if(np.abs(np.real(selFrameData[index])) > avgReal/8 or np.abs(np.imag(selFrameData[index])) > avgImag/8): # Current Index
        if (np.abs(np.real(selFrameData[index+1])) > avgReal / 8 or np.abs(np.imag(selFrameData[index+1])) > avgImag / 8):  # Next Index
            if (np.abs(np.real(selFrameData[index+2])) > avgReal / 8 or np.abs(np.imag(selFrameData[index+2])) > avgImag / 8):  # Index + 2
                endOfNoise = index
                break

# Starts from end of sample array and moves in
# Check if next 3 samples are all above threshold
# Once 3 sequential samples are, we can assume the end of a packet
for index in range(selFrameData.size-1, -1, -1):
    if(np.abs(np.real(selFrameData[index])) > avgReal/8 or np.abs(np.imag(selFrameData[index])) > avgImag/8): # Current Index
        if (np.abs(np.real(selFrameData[index-1])) > avgReal / 8 or np.abs(np.imag(selFrameData[index-1])) > avgImag / 8):  # Next Index
            if (np.abs(np.real(selFrameData[index-2])) > avgReal / 8 or np.abs(np.imag(selFrameData[index-2])) > avgImag / 8):  # Index + 2
                startOfNoise = index
                break

frameData = selFrameData[endOfNoise:startOfNoise]

# Take FFT
frameFFT = np.fft.fftshift(np.fft.fft(frameData))
dataFFT = np.fft.fftshift(np.fft.fft(data))

# Plot Time Domain of Full Samples
timeSpace = np.linspace(0.0,(N-1)/(float(Fs)),N)
plt.figure(0)
plt.title("Time Domain of Total Sample")
plt.plot(timeSpace, np.real(data))
plt.xlabel('Time [sec]')

# Plot Time Domain of Selected Frame
timeSpaceFrame = timeSpace[frameStart+endOfNoise:frameStart+startOfNoise]
plt.figure(1)
plt.title("Time Domain of Selected Frame")
plt.plot(timeSpaceFrame, np.real(frameData))
plt.xlabel('Time [sec]')

# Plot Frequency Domain of Selected Frame
f = np.linspace(-Fs/2 + Fc, Fs/2 + Fc, num=frameData.size)
plt.figure(2)
plt.title("Freq Domain of Selected Frame")
plt.plot(f, abs(frameFFT))
plt.xlabel('Freq [Hz]')

# Plot IQ of Selected Frame
plt.figure(3)
plt.title("IQ Plot of Selected Frame")
plt.scatter(np.real(frameData),np.imag(frameData))
plt.xlabel('Inphase')
plt.ylabel('Quadrature')

plt.show()


## Coarse Frequency Correction
# Integrate total channel, progressively integrate until halfway point
binWidth = Fs / frameFFT.size # Width of each FFT bin

freqSum = sum(abs(frameFFT)) # Total integral
halfIntegral = freqSum / 2 # Halfway point of total energy (target point)

currSum = 0
numBins = 0

# Progressively integrate, including each bin until the halfway point is reached
for j in range(frameFFT.size):
    currSum += abs(frameFFT[j])
    
    if currSum >= halfIntegral:
        numBins = j
        break
    else:
        continue

centerLocation = binWidth * numBins # Correlate center bin with frequency value
fOffset = centerLocation - (Fs/2)   # Determine if the offset is above or below original Fc
newFc = Fc + fOffset                # Find proper center frequency

print("Found frequency offset from original Fc: %fHz" % fOffset)
print("New center frequency: %fHz" % newFc)


## DPLL
PhaseOffset = 0.0 # Unexpected phase offset
FreqOffset = 0.0  # Unexpected frequency offset
t = np.arange(0.0, frameData.size/Fs, 1/Fs) # Linear time space for ideal signals

# Low pass output to remove double freq term, preserving low freq component containing the error
A = [1, 1, 0, 0]
w = [0, 550e3, 650e3, 1000e3]

tapNum = 41
maxTap = tapNum-1
coeffs = scipy.signal.firls(numtaps=tapNum, bands=w, desired=A, fs=Fs)
loopFilterMemory = np.zeros(tapNum, dtype=np.complex64)
out = np.zeros(frameData.size)

for k in range(frameData.size):
    IdealI = np.cos(2.0*np.pi*(newFc+FreqOffset)*t[k]+PhaseOffset)
    IdealQ = -np.sin(2.0*np.pi*(newFc+FreqOffset)*t[k]+PhaseOffset)
    IdealSignal = complex(IdealI, IdealQ)
    loopFilterMemory[0] = IdealSignal * frameData[k]

    # Filter
    filterOutput = scipy.signal.lfilter(a=coeffs, b=[1.0], x=loopFilterMemory)
    PhaseOffset = np.angle(filterOutput[-1])
    out[k] = PhaseOffset

    #refresh memory
    for i in range(maxTap):
        loopFilterMemory[maxTap-i] = loopFilterMemory[maxTap-1-i]

xout = np.linspace(0,len(out),len(out))
plt.scatter(xout,out)
plt.title("phase diff")
plt.ylabel("Amplitude")
plt.xlabel("Sample")
plt.show()

## Binary Conversion

# Sample test data
binaryList = [0,0,1,1,1,                                                                                        # Junk bits before packet
              1,0,1,0,1,0,1,0,                                                                                  # Preamble (According to spec)
              1,0,0,1,1,1,1,0,0,1,0,1,1,1,0,0,0,0,1,0,0,1,0,1,0,0,1,0,1,1,1,0,                                  # Access Address (random binary)
              0,0,1,0,1,1,0,0,0,0,0,0,1,1,0,1,                                                                  # PDU Header (all but last octet random)
              1,1,1,0,1,1,0,0,0,1,0,0,1,0,0,0,0,1,1,1,0,1,1,0,0,1,1,0,0,0,0,0,1,0,1,1,1,0,1,1,0,1,0,1,1,0,0,0,  # AdvA Payload (random binary)
              0,1,0,1,0,0,1,1,0,1,1,1,0,0,0,0,0,1,1,0,0,1,0,1,0,1,1,0,0,0,0,1,                                  # AdvData Payload (ASCII for "Speaker")
              0,1,1,0,1,0,1,1,0,1,1,0,0,1,0,1,0,1,1,1,0,0,1,0]

# Dewhitening
# Code from Galahad?

## Packet Sync and Decode
preamble0 = [0,1,0,1,0,1,0,1] # 1 Octet for 1 MSps packet
preamble1 = [1,0,1,0,1,0,1,0] # Order of preamble bits is dependent on access address
packetStart = None

# Iterate through until preamble is found
# Preamble has additional condition of first bit of access address matching first bit of preamble
for p in range(len(binaryList)):
    if(preamble0 == binaryList[p:p+8] and preamble0[0] == binaryList[p+8]):
        packetStart = p
        break
    elif(preamble1 == binaryList[p:p+8] and preamble1[0] == binaryList[p+8]):
        packetStart = p
        break

if(packetStart == None):
    print("Valid packet not found")
    quit()

accessAddressStart = packetStart + 8
pduStart = packetStart + 40
payloadStart = packetStart + 56

# Access address is 4 octets long (32 bits)
accessAddressBinary = binaryList[accessAddressStart:accessAddressStart+32]

# PDU
# PDU Header is 16 bits long (last 8 bits are payload length)
pduHeaderBinary = binaryList[pduStart:pduStart+16]
payloadLengthBinary = pduHeaderBinary[8:16]
payloadLength = bitList2Binary(payloadLengthBinary) # Number of octets in payload

payloadEnd = payloadStart + (payloadLength*8)

payloadBinary = binaryList[payloadStart:payloadEnd]

advBinary = payloadBinary[48:]
advData = bitList2Binary(advBinary)

byteNumber = advData.bit_length() + 7 // 8
binArray = advData.to_bytes(byteNumber, "big")
payloadText = binArray.decode()

print("Payload data:", payloadText)
