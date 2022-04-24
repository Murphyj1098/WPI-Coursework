def bitList2Binary(inList):

    s = [str(i) for i in inList]
    outList = int(''.join(s), 2)

    return outList


#****************************************************************************************
# Dewhitening code provided by Galahad

def bit_xor(a,b): # returns a list of bits
    return list(map(lambda x: x[0] ^ x[1], zip(a,b)))


def dewhiten_bits(bits, channel_num):
    front_half = [1,1,0,0]
    back_half = [1,1,0]
    if channel_num == 37:
        back_half = [1,0,1]
    elif channel_num == 38:
        back_half = [1,1,0]
    elif channel_num == 39:
        back_half = [1,1,1]
    else:
        print("you didn't call this correctly")
        quit()
    # LSB on left, initialize to [1, channel in binary]
    current_state = [front_half,back_half] # output of lfsr on right
    lfsr_out_bit = []
    for i in range(len(bits)):
        out_bit = current_state[1][-1]
        lfsr_out_bit.append(out_bit)
        current_state[1] = [current_state[0][-1] ^ out_bit] + current_state[1][:-1]
        current_state[0] = [out_bit] + current_state[0][:-1]
    return bit_xor(bits, lfsr_out_bit)

#****************************************************************************************


def pduMap(argument):
    lookup = {
        0: "ADV_IND",
        1: "ADV_DIRECT_IND",
        2: "ADV_NONCONN_IND",
        3: "SCAN_REQ",
        4: "SCAN_RSP",
        5: "CONNECT_REQ",
        6: "ADV_SCAN_IND"
    }

    return(lookup.get(argument, "Invalid PDU Type"))

# Data on GAP codes provided by Galahad (not present in the Core Spec document)
def gapMap(argument):
    lookup = {
        1:  "Flags",
        2:  "Incomplete List of 16-bit Service Class UUIDs",
        3:  "Complete list of 16-bit Service Class UUIDs",
        4:  "Incomplete list of 32-bit Service Class UUIDs",
        5:  "Complete list of 32-bit Service Class UUIDs",
        6:  "Incomplete list of 128-bit Service Class UUIDs",
        7:  "Incomplete list of 128-bit Service Class UUIDs",
        8:  "Shortened Local Name",
        9:  "Complete Local Name",
        10: "Tx Power Level",
        13: "Class of Device",
        14: "Simple Pairing Hash C(-192)",
        15: "Simple Pairing Randomizer R(-192)",
        16: "Device ID (or Security Manager TK Value)",
        17: "Security Manager Out of Band Flags",
        18: "Slave Connection Interval Range",
        20: "List of 16-bit Service Solicitation UUIDs",
        21: "List of 128-bit Service Solicitation UUIDs",
        22: "Service Data (- 16-bit UUID)",
        23: "Public Target Address",
        24: "Random Target Address",
        25: "Appearance",
        26: "Advertising Interval",
        27: "LE Bluetooth Device Address",
        28: "LE Role",
        29: "Simple Pairing Hash C-256",
        30: "Simple Pairing Randomizer R-256",
        31: "List of 32-bit Service Solicitation UUIDs",
        32: "Service Data - 32-bit UUID",
        33: "Service Data - 128-bit UUID",
        34: "LE Secure Connections Confirmation Value",
        35: "LE Secure Connections Random Value",
        36: "URI",
        37: "Indoor Positioning",
        38: "Transport Discovery Data",
        39: "LE Supported Features",
        40: "Channel Map Update Indicator",
        41: "PB-ADV",
        42: "Mesh Message",
        43: "Mesh Beacon",
        44: "BIGInfo",
        45: "Broadcast_Code",
        61: "3D Information Data",
        255: "Manufacturer Specific Data"
    }
    
    return (lookup.get(argument, "Unknown GAP Code"))
