import os
import collections
import numpy as np
import math
import matplotlib.pyplot as plt
import time
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

__all__ = [
    "read_pcap"
]
from trial1.Frame.pcap import PcapFrame
# Indexes of Null and Pilot OFDM subcarriers
# https://www.oreilly.com/library/view/80211ac-a-survival/9781449357702/ch02.html
from plotters.plotter2 import Plotter

nulls = {
    20: [x+32 for x in [
        -32, -31, -30, -29,
              31,  30,  29,  0
    ]],

    40: [x+64 for x in [
        -64, -63, -62, -61, -60, -59, -1,
              63,  62,  61,  60,  59,  1,  0
    ]],

    80: [x+128 for x in [
        -128, -127, -126, -125, -124, -123, -1,
               127,  126,  125,  124,  123,  1,  0
    ]],

    160: [x+256 for x in [
        -256, -255, -254, -253, -252, -251, -129, -128, -127, -5, -4, -3, -2, -1,
               255,  254,  253,  252,  251,  129,  128,  127,  5,  4,  3,  3,  1,  0
    ]]
}

pilots = {
    20: [x+32 for x in [
        -21, -7,
         21,  7
    ]],

    40: [x+64 for x in [
        -53, -25, -11,
         53,  25,  11
    ]],

    80: [x+128 for x in [
        -103, -75, -39, -11,
         103,  75,  39,  11
    ]],

    160: [x+256 for x in [
        -231, -203, -167, -139, -117, -89, -53, -25,
         231,  203,  167,  139,  117,  89,  53,  25
    ]]
}
remove_null_subcarriers = True
remove_pilot_subcarriers = True
apply_hampel = True
apply_smoothing = False
_amplitude = True
_fase = False

windowSize = 200
updates= 10

bandwidth = 80

class Pcap:
    PCAP_HEADER_DTYPE = np.dtype([
        ("magic_number", np.uint32),
        ("version_major", np.uint16),
        ("version_minor", np.uint16),
        ("thiszone", np.int32),
        ("sigfigs", np.uint32),
        ("snaplen", np.uint32),
        ("network", np.uint32)
    ])

    def __init__(self, fname: str):
        self.data = open(fname, 'rb')
        self.header = self.data.read(self.PCAP_HEADER_DTYPE.itemsize)
        self.frames = []
        self.skipped_frames = 0
        self.bandwidth = 0
        self.expected_size = None

    def read(self):
        while True:
            try:
                next_frame = PcapFrame(self.data)
                if self.calculate_size(next_frame):
                    self.frames.append(next_frame)
            except BufferError:
                break
        self.data.close()


    def calculate_size(self, frame):
        if frame is None or frame.packet_header is None or frame.payload is None or frame.payload_header is None:
            # print("Incomplete pcap frame header found. Cannot parse any further frames.")
            # self.skipped_frames += 1
            return False

        given_size = frame.packet_header["orig_len"][0]-(16-1)*4

        # Checking if the frame size is valid for ANY bandwidth.
        if given_size != 80*3.2*4 or frame.payload is None:
            #print("Skipped frame with incorrect size.")
            self.skipped_frames += 1
            return False

        # Establishing the bandwidth (and so, expected size) using the first frame.
        if self.expected_size is None:
            self.bandwidth = 80
            self.expected_size = given_size

        # Checking if the frame size matches the expected size for the established bandwidth.
        if self.expected_size != given_size:
            print("Change in bandwidth observed in adjacent CSI frames, skipping...")
            self.skipped_frames += 1
            return False

        return True

    # frames[0] for frame, maybe put user index here
    def print(self, frameIndex):
        frame = self.frames[frameIndex]
        # Mac ID
        mac = frame.payload_header["mac"]
        # Sequence control
        seq = frame.payload_header["seq"]
        # Core and Spatial Stream
        core = frame.payload_header["core"]
        spatial_stream = frame.payload_header["spatial_stream"]

        rssi = frame.payload_header["rssi"]
        fctl = frame.payload_header["fctl"]
        #
        print(
                f'''
                Frame #{frameIndex}
                ---------------
                Source Mac ID: {mac}
                Sequence: {seq}
                Core: {core}
                Spatial Stream: {spatial_stream}
                RSSI: {rssi}    
                FCTL: {fctl}
                '''
        )

    def format_csi(self):
        nsamples_max = len(self.frames)
        nsub = int(self.bandwidth * 3.2)
        csi = bytearray(nsamples_max * nsub * 4)

        for i in range(nsamples_max):
            x = self.frames[i].payload_header
            csi[i * (nsub * 4): (i + 1) * (nsub * 4)] = x["csi"]
        csi_np = np.frombuffer(
            csi,
            dtype=np.int16,
            count=nsub * 2 * nsamples_max
        )
        csi_np = csi_np.reshape((nsamples_max, nsub * 2))
        csi_cmplx = np.fft.fftshift(
            csi_np[:nsamples_max, ::2] + 1.j * csi_np[:nsamples_max, 1::2], axes=(1,)
        )
        return csi_cmplx

    def get_csi(self, index, rm_nulls=False, rm_pilots=False):
        x = self.format_csi()
        csi = x[index].copy()
        if rm_nulls:
            csi[nulls[self.bandwidth]] = 0
        if rm_pilots:
            csi[pilots[self.bandwidth]] = 0

        return csi


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
                12 + 46 + 18 + (nsub * 4)
        )
    )

    return nsamples_max

def string_is_int(s):
    '''
    Check if a string is an integer
    '''
    try:
        int(s)
        return True
    except ValueError:
        return False

    # already read so no need to call pcap again

def read_pcap(pcap_filepath, bandwidth=0, nsamples_max=0):
    '''
        Reads CSI samples from
        a pcap file. A SampleSet
        object is returned.
        Bandwidth and maximum samples
        are inferred from the pcap file by
        default, but you can also set them explicitly.
    '''
    pcap = Pcap(pcap_filepath)
    pcap.read()

    # test for printing out a specific packet
    # pcap.print(1)

    plotter = Plotter(80, apply_hampel=apply_hampel, apply_smoothing=apply_smoothing,
                      plot_phase=_fase, plot_amp=_amplitude, window_size=windowSize,
                      packets_refresh=updates)

    while True:
        pcap = Pcap(pcap_filepath)
        pcap.read()
        for x in range(len(pcap.frames)):
            pcap.print(x)
            csi = pcap.get_csi(
                x,
                True,
                True
            )

            # signal interpolation
            # time_interval = 1/10
            # num_frames = len(pcap.frames)
            # time_vector = np.arange(0, num_frames*time_interval, time_interval)
            # original_time_interval = time_vector[1] - time_vector[0]
            # new_time_vector = np.arange(time_vector[0], time_vector[-1] + time_interval,
            #                             time_interval)
            # interpolation_function = interp1d(time_vector, pcap, axis=0, kind='linear')
            # new_csi_data = interpolation_function(new_time_vector)


            # PCA
            # scaler = StandardScaler()

            # standardized_data = scaler.fit_transform(new_csi_data)
            num_components = 2
            # pca = PCA()
            # pca.fit(new_csi_data)
            # expVariance = pca.explained_variance_ratio_
            # cumulative_variances = np.cumsum(expVariance)
            # pca_scores = pca.fit_transform(new_csi_data)

            plotter.update(csi, x)
if __name__ == "__main__":
    while True:
        samples = read_pcap("../listener/example.pcap")
