import adi
import matplotlib.pyplot as plt
import numpy as np
# import scipy.signal

from funcs import bitList2Binary, dewhiten_bits, gapMap, pduMap


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

    # # Save working data to file
    # data = np.fromfile('sampleData.iq', np.complex64)

    # # Load working data from file
    # data = data.astype(np.complex64)
    # data.tofile('sampleData.iq')

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
            if((not frameFlag) & (max(nextSamples < 1900))):  # Making sure this packet isn't clipping
                frameFlag = True
                frameStart = i-50
        elif(frameFlag):
            frameEnd = i-25
            frameFound = True

    if(frameFound):
        frameDuration = frameEnd - frameStart
        selFrameData = data[frameStart:frameEnd]
        if((max(abs(selFrameData)) < 2000) and (frameDuration > 600)):
            break

print("\n~~~ Possible Packet Selection ~~~")
print("Found a possible packet in %d tries" % attempts)

# Find the absolute value of the average I and Q value to compare noise against
avgReal = np.average(np.abs(np.real(selFrameData)))
avgImag = np.average(np.abs(np.imag(selFrameData)))

# Starts from beginning of sample array and moves out
# Check if next 3 samples are all above threshold
# Once 3 sequential samples are, we can assume the start of a packet
for index in range(selFrameData.size):
    if(np.abs(np.real(selFrameData[index])) > avgReal/8 or np.abs(np.imag(selFrameData[index])) > avgImag/8): # Current Index
        if (np.abs(np.real(selFrameData[index+1])) > avgReal/8 or np.abs(np.imag(selFrameData[index+1])) > avgImag/8):  # Next Index
            if (np.abs(np.real(selFrameData[index+2])) > avgReal/8 or np.abs(np.imag(selFrameData[index+2])) > avgImag/8):  # Index + 2
                endOfNoise = index
                break

# Starts from end of sample array and moves in
# Check if next 3 samples are all above threshold
# Once 3 sequential samples are, we can assume the end of a packet
for index in range(selFrameData.size-1, -1, -1):
    if(np.abs(np.real(selFrameData[index])) > avgReal/8 or np.abs(np.imag(selFrameData[index])) > avgImag/8): # Current Index
        if (np.abs(np.real(selFrameData[index-1])) > avgReal/8 or np.abs(np.imag(selFrameData[index-1])) > avgImag/8):  # Next Index
            if (np.abs(np.real(selFrameData[index-2])) > avgReal/8 or np.abs(np.imag(selFrameData[index-2])) > avgImag/8):  # Index + 2
                startOfNoise = index
                break

frameData = selFrameData[endOfNoise:startOfNoise]

print("Removed %d samples classified as noise" % (len(selFrameData) - len(frameData)))

# Take FFT
frameFFT = np.fft.fftshift(np.fft.fft(frameData))

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

print("\n~~~ Coarse Frequency Correction ~~~")
print("Found frequency offset from original Fc: %.2f Hz" % fOffset)
print("New center frequency: %.2f Hz" % newFc)


## Defunct DPLL Attempt Code
# *******************************************************************************************
# PhaseOffset = 0.0 # Unexpected phase offset
# FreqOffset = 0.0  # Unexpected frequency offset
# t = np.arange(0.0, frameData.size/Fs, 1/Fs) # Linear time space for ideal signals

# # Low pass output to remove double freq term, preserving low freq component containing the error
# A = [1, 1, 0, 0]
# w = [0, 550e3, 650e3, 1000e3]

# tapNum = 41
# maxTap = tapNum-1
# coeffs = scipy.signal.firls(numtaps=tapNum, bands=w, desired=A, fs=Fs)
# loopFilterMemory = np.zeros(tapNum, dtype=np.complex64)
# out = np.zeros(frameData.size)

# for k in range(frameData.size):
#     IdealI = np.cos(2.0*np.pi*(newFc+FreqOffset)*t[k]+PhaseOffset)
#     IdealQ = -np.sin(2.0*np.pi*(newFc+FreqOffset)*t[k]+PhaseOffset)
#     IdealSignal = complex(IdealI, IdealQ)
#     loopFilterMemory[0] = IdealSignal * frameData[k]

#     # Filter
#     filterOutput = scipy.signal.lfilter(a=coeffs, b=[1.0], x=loopFilterMemory)
#     PhaseOffset = np.angle(filterOutput[-1])
#     out[k] = PhaseOffset

#     #refresh memory
#     for i in range(maxTap):
#         loopFilterMemory[maxTap-i] = loopFilterMemory[maxTap-1-i]

# xout = np.linspace(0,len(out),len(out))
# plt.figure(4)
# plt.scatter(xout,out)
# plt.title("phase diff")
# plt.ylabel("Amplitude")
# plt.xlabel("Sample")
# *******************************************************************************************


## Binary Conversion
phaseDiff = []

# Find the phase difference between current and previous sample
for i in range(frameData.size-1):
    angleDiff = np.angle(frameData[i+1])-np.angle(frameData[i])

    # Modify phase to account for wrap around from 2pi (This block is the same as calling np.unwrap() on phaseDiff)
    if(angleDiff > np.pi):
        angleDiff -= 2*np.pi
    elif(angleDiff < -np.pi):
        angleDiff += 2*np.pi
    
    # Drop every other sample since sampling rate is twice symbol rate
    if i % 2:
        phaseDiff.append(angleDiff)

# Plot Phase differences
xphase = np.linspace(0,len(phaseDiff),len(phaseDiff))
plt.figure(5)
plt.scatter(xphase,phaseDiff)
plt.title("Phase Differences")
plt.xlabel("Sample Number")
plt.ylabel("Phase Difference (Rads)")

# Translate phasediff into bits
bits = []
errorBits = 0
for i in range(len(phaseDiff)):
    if phaseDiff[i] > 0:
        bits.append(1)
    elif phaseDiff[i] < 0:
        bits.append(0)
    else:
        errorBits += 1

print("\n~~~ Binary Conversion ~~~")
print("Percent of \"1\" bits = %2.2f%%" % ((sum(bits)/len(bits))*100.0))

plt.show()


## Packet Sync and Decode

print("\n~~~ Packet Decode Information ~~~")

preamble = [0,1,0,1,0,1,0,1] # Order of preamble bits is dependent on access address
accessAddress = [0,1,1,0,1,0,1,1,0,1,1,1,1,1,0,1,1,0,0,1,0,0,0,1,0,1,1,1,0,0,0,1]
packetStart = None

# Iterate through until preamble is found
# Check if preamble is followed by known access address
for p in range(len(bits)):
    if(preamble == bits[p:p+8] and accessAddress == bits[p+8:p+40]):
        packetStart = p
        break

if(packetStart is None):
    print("Valid packet not found")
    quit()

print("Packet starts at bit", packetStart)

# Dewhitening code
pduStart = packetStart + 40
deWhitenedBits = dewhiten_bits(bits[pduStart:], 39)

# PDU
# PDU Header is 16 bits long (last 8 bits are payload length)
pduHeaderBinary = deWhitenedBits[0:16]

# PDU Type
pduType = pduHeaderBinary[0:4]
pduType.reverse()
pduTypeDec = bitList2Binary(pduType)
print("PDU Type:", pduMap(pduTypeDec))

# Payload Length
payloadLengthBinary = pduHeaderBinary[8:16]
payloadLengthBinary.reverse() # Transmitted LSB first
payloadLength = bitList2Binary(payloadLengthBinary) # Number of octets in payload
print("Payload is %d bytes long" % payloadLength)
payloadEnd = (payloadLength*8) + 16

# Detwhiten Payload
payloadBinary = deWhitenedBits[16:payloadEnd]

# Adv Address
advAddr = payloadBinary[:48]
advAddr.reverse()
advAddrHex = hex(bitList2Binary(advAddr))
advBinary = payloadBinary[48:]

if(pduHeaderBinary[6]):
    print("Advertiser's Address (Random):", advAddrHex)
elif(not pduHeaderBinary[6]):
    print("Advertiser's Address (Public):", advAddrHex)

# Payload Sections
remainingLength = payloadLength - 6
sectionNum = 1
binaryIndex = 0

while(remainingLength > 0):
    print("\nPayload Section %d" % sectionNum)
    sectionLengthBinary = advBinary[binaryIndex:binaryIndex+8]
    sectionLengthBinary.reverse()
    sectionLength = bitList2Binary(sectionLengthBinary)
    print("Section is %d bytes long (not including length byte)" % sectionLength)
    remainingLength = remainingLength - (sectionLength + 1)

    sectionTypeBinary = advBinary[binaryIndex+8:binaryIndex+16]
    sectionTypeBinary.reverse()
    sectionType = bitList2Binary(sectionTypeBinary)
    print("Payload Section Type:", gapMap(sectionType))

    sectionNum += 1
    binaryIndex += (sectionLength * 8) + 8
