import numpy as np
import matplotlib.pyplot as plt
from decoders.realtimecsi import hampel_filter, moving_average, searchVariance
from time import time
import pandas as pd
from utils.matlab import db
from scipy import signal
import matplotlib.animation as animation
from statistics import variance
'''
Amplitude and Phase plotter
---------------------------
Plot Amplitude and Phase of CSI frame_info
and update the plots in the same window.
Initiate Plotter with bandwidth, and
call update with CSI value.
'''

__all__ = [
    'Plotter'
]


class Plotter:
    def __init__(self, bandwidth, apply_hampel: bool, apply_smoothing: bool,
                 plot_phase: bool, plot_amp: bool, window_size: int, packets_refresh: int):
        self.bandwidth = bandwidth
        self.hampel = apply_hampel
        self.smoothing = apply_smoothing
        self.start = time()
        self._phase = plot_phase
        self._amp = plot_amp

        self.window_size = window_size
        self.var1 = packets_refresh

        self.prev_frame = None
        self.prev_variance = 0
        self.sti_values = []
        self.corr_values = []

        self.variances = []

        self.window = True
        self.nsub = int(bandwidth * 3.2)
        # self.fig = plt.figure(figsize=(18, 10))
        # self.ax1 = plt.subplot(311)

        self.fig, axs = plt.subplots(1, figsize=(10, 5))

        self.ax_amp = axs
        # self.ax_pha = axs[1]
        # self.ax_mov = axs[1]

        self.fig.suptitle('Nexmon CSI Real Time Explorer')

        # Stores the frames and the values of the subcarriers
        # Stores amplitude and phase and then stores the values for each subcarrier
        # I am also storing the frames which serve as a buffer
        self.temp_frames = np.zeros((2, 256, 200))
        plt.ion()
        plt.show()

    def cascade(self, csi, sequence):
        """
        This function takes the CSI array and adds a new frame to the last position putting all previous frames
        one less position. The frame that occupied the first position of the matrix is dropped.
        """

        if self._amp:

            amplitudes = np.abs(csi)
            temp_amplitudes = amplitudes
            # temp_amplitudes = np.reshape(temp_amplitudes, (256,1))
            # plt.imshow(temp_amplitudes.T,interpolation="nearest", aspect = "auto", cmap="jet")
            # self.ax1.set_title("Amplitude")
            # plt.colorbar()
        if self._phase:
            phase = np.angle(csi, deg=True)
            temp_phase = phase


        if self.window:  # when window is full, the frames are appended to the last position
            for i in range(self.window_size - 1, -1, -1):
                if self._amp:
                    copy_amp = np.copy(self.temp_frames[0, :, i][:])
                    self.temp_frames[0, :, i] = temp_amplitudes
                    temp_amplitudes = copy_amp

                if self._phase:
                    copy_phase = np.copy(self.temp_frames[1, :, i])
                    self.temp_frames[1, :, i] = temp_phase
                    temp_phase = copy_phase


        else:
            position = sequence % self.window_size  # checking which position the csi will enter the buffer at

            if self._amp:
                # how we get the amplitude
                self.temp_frames[0, :, position] = amplitudes
            if self._phase:
                # how we get the phase
                self.temp_frames[1, :, position] = phase

    def update(self, csi, sequence):
        x = csi
        if sequence != 0 and sequence % 2 == 0 and self.window:
            j = self.temp_frames[0, :, -1 * 2:]
            j = np.transpose(j)
            sti = self.get_sti(j[1], j[0])
            corr = self.get_correlation_coefficient(j[1], j[0])
            self.sti_values.append(sti)
            self.corr_values.append(corr)

        if sequence % self.var1 == 0 and self.window:
            duration = time() - self.start
            self.ax_amp.clear()
            # self.ax_pha.clear()
            # self.ax_mov.clear()
            # self.ax1.clear()

            # These are also cleared with clear()
            self.ax_amp.set_ylabel('Amplitude')
            # self.ax_pha.set_ylabel('Phase')
            self.ax_amp.set_xlabel('Subcarrier Sequence')
            self.fig.suptitle(f'Nexmon CSI Real Time Explorer - {duration} s')
            self.start = time()

        self.cascade(csi, sequence)

        if sequence % self.window_size == 0 and sequence != 0:
            self.window = True

        # if sequence % 10 == 0 and sequence != 0 and self.window:
            # var_corr = self.running_variance(self.corr_values, 5)
            # std_corr = self.running_stdev(self.corr_values, 5)

            # diffs, markers, signals, thresh_mov, thresh_nomov = self.slidingpeaks(var_corr, self.corr_values, 0.99, 0.6,
            #                                                                       0.5)
            # mov_vals = []
            # mov_vals2 = []
            # for x in self.corr_values:
            #     if x < 0.95:
            #         mov_vals.append(1)
            #     else:
            #         mov_vals.append(0)
            # mov_vals = np.array(mov_vals)
            # self.ax_mov.plot(range(len(signals)), signals, label=str("movement detected"))
        if sequence % self.var1 == 0 and sequence != 0 and self.window:
            amplitudes = self.temp_frames[0, :, -1 * self.var1:]
            # TEST CODE
            # v = np.mean(amplitudes[46, :])
            # if v < 1300:
            #     self.variances.append(1)
            # else:
            #     self.variances.append(0)
            # self.ax_mov.plot(range(len(self.variances)), self.variances, label=str("movement detected"))

            if self.hampel:
                self.temp_frames[0, :, -1 * self.var1:] = hampel_filter(amplitudes,
                                                                        window_size=4,
                                                                        n_subcarriers=self.nsub)
                amplitudes = self.temp_frames[0, :, -1 * self.var1:]

            if self.smoothing:
                self.temp_frames[0, :, -1 * self.var1:] = moving_average(amplitudes,
                                                                         n_subcarrier=self.nsub,
                                                                         window_size=10)
                amplitudes = self.temp_frames[0, :, -1 * self.var1:]

            # currentSubcarrier = searchVariance(amplitudes, self.nsub, k=12)
            currentSubcarrier = [46]
            # Plotting stored values of each subcarrier
            try:
                for subcarrier in currentSubcarrier:
                    amplitudes = self.temp_frames[0, subcarrier, :]
                    phases = self.temp_frames[1, subcarrier, :]

                    if self._amp:
                        self.ax_amp.plot(range(self.window_size), amplitudes, label=str(subcarrier))

                    # if self._phase:
                    #     np.unwrap(phases)
                    #     self.ax_pha.plot(range(self.window_size), phases, label=str(subcarrier))

            except ValueError as err:
                print(
                    f'A ValueError occurred. Is the bandwidth {self.bandwidth} MHz correct?\nError: ', err
                )
                exit(-1)

            self.ax_amp.legend()
            # self.ax_pha.legend()
            plt.draw()
            plt.pause(0.001)

    def get_h_hat_t(self, csi_vec):
        csi_mean = np.mean(csi_vec)
        translation = csi_vec - csi_mean
        scaling = np.std(csi_vec)

        return translation/scaling

    def get_sti(self, csi_vec1, csi_vec2):
        h1 = self.get_h_hat_t(csi_vec1)
        h2 = self.get_h_hat_t(csi_vec2)

        return np.linalg.norm(h1-h2)

    def get_correlation_coefficient(self, csi_vec1, csi_vec2):
        return np.corrcoef([csi_vec1, csi_vec2])[0,1]

    def running_mean(self, corr_values, window):
        return pd.Series(corr_values).rolling(window=window, min_periods=1, center=True).mean().to_numpy()

    def running_variance(self, corr_values, window):
        return pd.Series(corr_values).rolling(window=window, min_periods=1, center=True).var().to_numpy()

    def running_stdev(self, corr_values, window):
        return pd.Series(corr_values).rolling(window=window, min_periods=1, center=True).std().to_numpy()

    def slidingpeaks(self, y, corr, containsmovement_threshold, moving_threshold, notmoving_threshold):
        window_length = 5
        i = 0
        signals = np.zeros(len(y))
        markers = []
        diffs = []

        is_moving = False

        max_val = max(y)

        while i < len(y):
            first_window = y[i:i + window_length]
            second_window = y[i + window_length:i + window_length*2]

            first_mean = np.mean(first_window) / max_val
            second_mean = np.mean(second_window) / max_val

            diff = np.abs(second_mean - first_mean)

            if min(corr) < containsmovement_threshold:
                if is_moving:
                    # Large diff means movement continues.
                    # Small diff means return to steady.
                    if diff and diff < notmoving_threshold:
                        is_moving = False
                    else:
                        markers.append(i)
                else:
                    if diff > moving_threshold:
                        markers.append(i)
                        is_moving = True

            signals[i] = int(is_moving)
            diffs.append(diff)

            i += 1

        thresh_mov = np.full(len(y), fill_value=moving_threshold)
        thresh_nomov = np.full(len(y), fill_value=notmoving_threshold)


        chunk_size = 5
        for i in range(len(signals)):
            if i % chunk_size == 0:
                # Get previous second's worth of data and check for movement.
                win = signals[i - chunk_size:i]
                if 1 in win:
                    signals[i - chunk_size:i] = 1

        return (diffs, markers, signals, thresh_mov, thresh_nomov)


def __del__(self):
        pass