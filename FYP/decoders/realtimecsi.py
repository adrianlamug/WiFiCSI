"""
Interleaved
===========
Fast and efficient methods to extract
Interleaved CSI frame_info in PCAP files.
~230k frame_info per second.
Suitable for bcm43455c0 and bcm4339 chips.
Requires Numpy.
Usage
-----
import decoders.interleaved as decoder
frame_info = decoder.read_pcap('path_to_pcap_file')
Bandwidth is inferred from the pcap file, but
can also be explicitly set:
frame_info = decoder.read_pcap('path_to_pcap_file', bandwidth=40)
"""

__all__ = [
    'read_frame',
    'hampel_filter',
    'moving_average',
    'searchVariance'
]
import os
import numpy as np
# from numba import jit
from statistics import variance

np.seterr(all="ignore")

# Indexes of Null and Pilot OFDM subcarriers
# https://www.oreilly.com/library/view/80211ac-a-survival/9781449357702/ch02.html
nulls = {
    20: [x + 32 for x in [
        -32, -31, -30, -29,
        31, 30, 29, 0
    ]],

    40: [x + 64 for x in [
        -64, -63, -62, -61, -60, -59, -1,
        63, 62, 61, 60, 59, 1, 0
    ]],

    80: [x + 128 for x in [
        -128, -127, -126, -125, -124, -123, -1,
        127, 126, 125, 124, 123, 1, 0
    ]],

    160: [x + 256 for x in [
        -256, -255, -254, -253, -252, -251, -129, -128, -127, -5, -4, -3, -2, -1,
        255, 254, 253, 252, 251, 129, 128, 127, 5, 4, 3, 3, 1, 0
    ]]
}

pilots = {
    20: [x + 32 for x in [
        -21, -7,
        21, 7
    ]],

    40: [x + 64 for x in [
        -53, -25, -11,
        53, 25, 11
    ]],

    80: [x + 128 for x in [
        -103, -75, -39, -11,
        103, 75, 39, 11
    ]],

    160: [x + 256 for x in [
        -231, -203, -167, -139, -117, -89, -53, -25,
        231, 203, 167, 139, 117, 89, 53, 25
    ]]
}


class SampleSet(object):
    """
        A helper class to contain data read
        from pcap files.
    """

    def __init__(self, sampless, bandwidth):
        self.mac, self.seq, self.css, self.csi = sampless

        self.nsamples = self.csi.shape[0]
        self.bandwidth = bandwidth

    def get_mac(self, index):
        return self.mac[index * 6: (index + 1) * 6]

    def get_seq(self, index):
        sc = int.from_bytes(  # uint16: SC
            self.seq[index * 2: (index + 1) * 2],
            byteorder='little',
            signed=False
        )
        fn = sc % 16  # Fragment Number
        sc = int((sc - fn) / 16)  # Sequence Number

        return sc, fn

    def get_css(self, index):
        return self.css[index * 2: (index + 1) * 2]

    def get_csi(self, index, rm_nulls=False, rm_pilots=False):
        csi = self.csi[index].copy()
        if rm_nulls:
            csi[nulls[self.bandwidth]] = 0
        if rm_pilots:
            csi[pilots[self.bandwidth]] = 0

        return csi

    def print(self, index, n_frame):
        # Mac ID
        macid = self.get_mac(index).hex()
        macid = ':'.join([macid[i:i + 2] for i in range(0, len(macid), 2)])

        # Sequence control
        sc, fn = self.get_seq(index)

        # Core and Spatial Stream
        css = self.get_css(index).hex()

        print(
            f'''
Sample #{n_frame}
---------------
Source Mac ID: {macid}
Sequence: {sc}.{fn}
Core and Spatial Stream: 0x{css}
            '''
        )


def __find_bandwidth(incl_len):  # incl_len é o tamanho do pacote
    """
        Determines bandwidth
        from length of packets.
        incl_len is the 4 bytes
        indicating the length of the
        packet in packet header
        https://wiki.wireshark.org/Development/LibpcapFileFormat/
        This function is immune to small
        changes in packet lengths.
    """

    pkt_len = incl_len

    # The number of bytes before we
    # have CSI data is 60. By adding
    # 128-60 to frame_len, bandwidth
    # will be calculated correctly even
    # if frame_len changes +/- 128
    # Some packets have zero padding.
    # 128 = 20 * 3.2 * 4
    nbytes_before_csi = 0
    pkt_len += (128 - nbytes_before_csi)

    bandwidth = 20 * int(
        pkt_len // (20 * 3.2 * 4)
    )

    return bandwidth

def read_pcap(pcap_filepath, bandwidth = 0, nsamples_max=0):
    pcap_filesize = os.stat(pcap_filepath).st_size
    with open(pcap_filepath, 'rb') as pcapfile:
        fc = pcapfile.read()
    if bandwidth == 0:
        bandwidth = __find_bandwidth(
            # 32-36 is where the incl_len
            # bytes for the first frame are
            # located.
            # https://wiki.wireshark.org/Development/LibpcapFileFormat/
            fc[32:36]
        )
    nsub = int(bandwidth * 3.2)
    if nsamples_max == 0:
        nsamples_max = __find_nsamples_max(pcap_filesize, nsub)
    rssi = bytearray(nsamples_max * 1)
    fctl = bytearray(nsamples_max * 1)
    mac = bytearray(nsamples_max * 6)
    seq = bytearray(nsamples_max * 2)
    css = bytearray(nsamples_max * 2)
    csi = bytearray(nsamples_max * nsub * 4)

def __find_nsamples_max(pcap_filesize, nsub):
    '''
        Returns an estimate for the maximum possible number
        of samples in the pcap file.
        The size of the pcap file is divided by the size of
        a packet to calculate the number of samples. However,
        some packets have a padding of a few bytes, so the value
        returned is slightly higher than the actual number of
        samples in the pcap file.
    '''

    # PCAP global header is 24 bytes
    # PCAP packet header is 12 bytes
    # Ethernet + IP + UDP headers are 46 bytes
    # Nexmon metadata is 18 bytes
    # CSI is nsub*4 bytes long
    #
    # So each packet is 12 + 46 + 18 + nsub*4 bytes long
    nsamples_max = int(
        (pcap_filesize - 24) / (
            12 + 46 + 18 + (nsub*4)
        )
    )

    return nsamples_max


def read_frame(frame, bandwidth=0, nsamples_max=1):
    """
        Reads CSI frame_info from
        a pcap file. A SampleSet
        object is returned.
        Bandwidth and maximum frame_info
        are inferred from the pcap file by
        default, but you can also set them explicitly.
    """

    # Number of OFDM sub-carriers
    nsub = int(bandwidth * 3.2)
    fc = frame[:18 + nsub * 4]

    # Preallocating memory
    # rssi = bytearray(nsamples_max * 1)
    # fctl = bytearray(nsamples_max * 1)
    mac = bytearray(nsamples_max * 6)
    seq = bytearray(nsamples_max * 2)
    css = bytearray(nsamples_max * 2)
    csi = bytearray(nsamples_max * nsub * 4)

    # Pointer to current location in file.
    # This is faster than using file.tell()
    # =24 to skip pcap global header
    ptr = 0  # packet header + nexmon metadata

    nsamples = 0

    # could do this using a pointer
    # 2 bytes: Magic Bytes               @ 0 - 1
    # 1 byte: RSSI                       @ 2 - 2
    # 1 bytes: FCTL                      @ 3 - 3
    # 6 bytes: Source Mac ID             @ 4 - 10
    # 2 bytes: Sequence Number           @ 10 - 12
    # 2 bytes: Core and Spatial Stream   @ 12 - 14
    # 2 bytes: ChanSpec                  @ 14 - 16
    # 2 bytes: Chip Version              @ 16 - 18
    # nsub*4 bytes: CSI Data             @ 18 - 18 + nsub*4

    # rssi[nsamples * 1: (nsamples + 1) * 1] = fc[ptr + 2]
    # fctl[nsamples * 1: (nsamples + 1) * 1] = fc[ptr + 3]
    mac[nsamples * 6: (nsamples + 1) * 6] = fc[ptr + 4: ptr + 10]
    seq[nsamples * 2: (nsamples + 1) * 2] = fc[ptr + 10: ptr + 12]
    css[nsamples * 2: (nsamples + 1) * 2] = fc[ptr + 12: ptr + 14]
    csi[nsamples * (nsub * 4): (nsamples + 1) * (nsub * 4)] = fc[ptr + 18: ptr + 18 + nsub * 4]

    # ptr += (frame_len - 42)
    nsamples += 1

    # Convert CSI bytes to numpy array
    try:
        csi_np = np.frombuffer(
            csi,
            dtype=np.int16,
            count=nsub * 2 * nsamples
        )
    except:
        print("Received buffer is smaller")
        return -1

    # Cast numpy 1-d array to matrix
    csi_np = csi_np.reshape((nsamples, nsub * 2))

    # Convert csi into complex numbers
    csi_cmplx = np.fft.fftshift(
        csi_np[:nsamples, ::2] + 1.j * csi_np[:nsamples, 1::2], axes=(1,)
    )

    return SampleSet(
        (mac,
         seq,
         css,
         csi_cmplx),
        bandwidth
    )


# Signal processing and filtering functions


# reference: https://towardsdatascience.com/outlier-detection-with-hampel-filter-85ddf523c73d
def hampel_filter(input_series, window_size, n_subcarriers, n_sigmas=3):
    new_series = input_series.copy()
    k = 1.4826  # scale factor for Gaussian distribution
    n = len(new_series[0, :])
    for s in range(n_subcarriers):
        amplitudeOfSubcarrier = new_series[s, :].copy()

        for i in range(window_size, n - window_size + 1):
            x0 = np.nanmedian(amplitudeOfSubcarrier[i - window_size:i + window_size])
            S0 = k * np.nanmedian(np.abs(amplitudeOfSubcarrier[i - window_size:i + window_size] - x0))

            if i - window_size == 0:  # if first and last values not available
                for j in range(window_size + 1):
                    if np.abs(amplitudeOfSubcarrier[j] - x0) > n_sigmas * S0:
                        new_series[s, j] = x0
            elif i + window_size == n - 1:
                for j in range(n - window_size, n):
                    if np.abs(amplitudeOfSubcarrier[j] - x0) > n_sigmas * S0:
                        new_series[s, j] = x0
            else:
                if np.abs(amplitudeOfSubcarrier[i] - x0) > n_sigmas * S0:
                    new_series[s, i] = x0

    return new_series


# Inspired by https://towardsdatascience.com/moving-averages-in-python-16170e20f6c
def moving_average(input_series, window_size, n_subcarrier):
    mean_series = input_series.copy()
    n = len(mean_series[0, :])
    for subcarrier in range(n_subcarrier):
        amplitudeOfSubcarrier = mean_series[subcarrier, :].copy()

        for idx in range(n):
            if idx - window_size >= 0:
                mean = amplitudeOfSubcarrier[idx - window_size:idx].sum() / window_size
            else:
                mean = amplitudeOfSubcarrier[:idx + 1].sum() / (idx + 1)

            mean_series[subcarrier, idx] = mean

    return mean_series


def searchVariance(input_series, n_subport, k=12):
    # returns the amplitudes with the most variance and their appropriate subcarriers
    varianciesPerSubcarrier = {}

    for subcarrrier in range(n_subport):
        amplitudeOfSubcarrier = input_series[subcarrrier, :]
        v = variance(amplitudeOfSubcarrier)
        varianciesPerSubcarrier[v] = subcarrrier

    variancies = list(varianciesPerSubcarrier.keys())
    variancies = sorted(variancies, reverse=True)
    return [varianciesPerSubcarrier[x] for x in variancies[:k]]


if __name__ == "__main__":
    samples = read_frame('output-40.pcap')