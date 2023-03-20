import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from FYP.trial1.utils.matlab import db
from FYP.trial1.decoders.realtimecsi import hampel_filter, moving_average, searchVariance
from FYP.trial1.decoders.interleaved import read_pcap
from time import time
from scipy import signal
import matplotlib.animation as animation
import os
'''
Amplitude plotter
---------------------------

Plot Amplitude and Phase of CSI frame_info
and update the plots in the same window.

Initiate Plotter with bandwidth, and
call update with CSI value.

'''


class Plotter():
    def __init__(self, pcap_file, window_size, bandwidth):
        self.pcap_file = pcap_file
        self.window_size = window_size

        self.data = read_pcap(self.pcap_file)
        self.bandwidth = self.data.bandwidth
        self.csi = self.data.csi
        self.no_subcarriers = int(3.2 * self.bandwidth)
        self.timestamps = self.data.timestamps

        # self.temp_frames = np.zeros((2, 3.2*self.bandwidth, 200))
    def heatmap(self):
        amplitudes = np.abs(self.csi)
        dBm = db(amplitudes)
        finalData = dBm[:, :, 0]

        # subcarriers * amplitude
        finalData = np.transpose(finalData)
        x_label = "Time (s)"
        x = self.timestamps
        x = [timestamp - x[0] for timestamp in x]
        avg_sample_rate = self.data.nsamples / x[-1]
        xlim = max(x)

        limits = [0, xlim, 1, self.no_subcarriers]

        _, ax = plt.subplots()
        im = ax.imshow(finalData, cmap="jet", extent=limits, aspect="auto")
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Amplitude (dBm)")

        plt.xlabel(x_label)
        plt.ylabel("Subcarrier Index")

        name, ext = os.path.splitext(os.path.basename(self.pcap_file))
        plt.title(os.path.basename(name))
        plt.plot()
        # plt.savefig("../static/images/generated.png")

        plt.show()

    def mean_difference(self):
        mean_corr = 0.9971
        diff_corr = 0.0080
        moving_threshold = 0.15
        notmoving_threshold = 0.05
        containsMovement_threshold = mean_corr-(diff_corr*2)
        prev_frame = None
        sti_values = []
        corr_values = []

        amplitudes = np.abs(self.csi)
        dBm = db(amplitudes)
        finalData = dBm[:, :, 0]

        # subcarriers * amplitude
        finalData = np.transpose(finalData)
        x_label = "Time (s)"
        x = self.timestamps
        x = [timestamp - x[0] for timestamp in x]
        avg_sample_rate = self.data.nsamples / x[-1]

        prev_frame = self.csi[0]
        for x in range(finalData[0] - 1):
            frame = finalData[x+1]

        amplitudes = np.abs(self.csi)
        mean = np.mean(amplitudes)
        differences = amplitudes - mean
        mean_difference = np.mean(differences, axis=1)
        print(mean_difference)


temp_frames = np.zeros((2, 256, 200))
window_size = 1000
# data = pd.read_csv("../listener/data/test-amp.csv")
# data = read_pcap("../data/walking-1677946656.pcap")
# data2 = read_pcap("../data/static-1677946272.pcap")
def heatmap(data):
    csi = np.transpose(data)
    no_frames = window_size
    no_subcarriers = 256

    x_label = "Frame No."
    xlim = no_frames

    limits = [0, xlim, 1, no_subcarriers]

    _,ax = plt.subplots()
    im = ax.imshow(csi, cmap="jet", extent=limits, aspect="auto")
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Amplitude (dBm)")

    plt.xlabel(x_label)
    plt.ylabel("Subcarrier Index")

    plt.title("Test")

    # plt.show()


def heatmap2(data):
    csi = data.csi
    csi_shape = csi[0].shape

    amplitudes = np.abs(csi)
    dBm = db(amplitudes)
    finalData = dBm[:, :, 0]

    # subcarriers * amplitude
    finalData = np.transpose(finalData)
    no_frames = data.nsamples
    no_subcarriers = int(3.2* data.bandwidth)

    x_label = "Time (s)"
    x = data.timestamps
    x = [timestamp - x[0] for timestamp in x]
    avg_sample_rate = no_frames/x[-1]
    xlim = max(x)

    limits = [0, xlim, 1, no_subcarriers]

    _,ax = plt.subplots()
    im = ax.imshow(finalData, cmap="jet", extent=limits, aspect="auto")
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Amplitude (dBm)")

    plt.xlabel(x_label)
    plt.ylabel("Subcarrier Index")

    plt.title("No activity")

    plt.show()


def animate(frame):
    temp_amplitude = data.iloc[frame]
    for i in range(window_size -1, -1, -1):
        copy_amp = np.copy(temp_frames[0, :, i][:])
        temp_frames[0, :, i] = temp_amplitude
        temp_amplitude = copy_amp
        ax.clear()
        amplitudes = temp_frames[0, :, -1 * 10:]
        # currentSubcarrier = searchVariance(amplitudes, 256, k=12)
        for subcarrier in range(256):
            amplitudes = temp_frames[0, subcarrier, :]
            # plt.imshow(amplitudes, interpolation="nearest", aspect="auto", cmap="jet")
            # plt.colorbar()
            ax.plot(range(window_size), amplitudes, label=str(subcarrier))

    ax.legend()
    ax.set_xlabel("Index")
    ax.set_ylabel("Value")
    ax.set_title(f"Frame {frame}")


if __name__ == "__main__":
    plotter = Plotter("../generated/data/falling-1.pcap", 200, 80)
    plotter.heatmap()
    # plotter.mean_difference()