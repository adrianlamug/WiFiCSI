import numpy as np
import matplotlib.pyplot as plt
from trial1.decoders.realtimecsi import hampel_filter, moving_average, searchVariance
from time import time
from scipy import signal
import matplotlib.animation as animation
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

        self.window = True
        self.nsub = int(bandwidth * 3.2)
        # self.fig = plt.figure(figsize=(18, 10))
        # self.ax1 = plt.subplot(311)

        self.fig, axs = plt.subplots(2, figsize=(15, 10))

        self.ax_amp = axs[0]
        self.ax_pha = axs[1]
        self.ax_spec = axs[1]

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
        if sequence % self.var1 == 0 and self.window:
            duration = time() - self.start
            self.ax_amp.clear()
            self.ax_pha.clear()
            # self.ax1.clear()

            # These are also cleared with clear()
            self.ax_amp.set_ylabel('Amplitude')
            self.ax_pha.set_ylabel('Phase')
            self.ax_pha.set_xlabel('Subcarrier Sequence')
            self.fig.suptitle(f'Nexmon CSI Real Time Explorer - {duration} s')
            self.start = time()

        self.cascade(csi, sequence)

        if sequence % self.window_size == 0 and sequence != 0:
            self.window = True

        if sequence % self.var1 == 0 and sequence != 0 and self.window:
            amplitudes = self.temp_frames[0, :, -1 * self.var1:]

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

            currentSubcarrier = searchVariance(amplitudes, self.nsub, k=12)

            # Plotting stored values of each subcarrier
            try:
                for subcarrier in currentSubcarrier:
                    amplitudes = self.temp_frames[0, subcarrier, :]
                    phases = self.temp_frames[1, subcarrier, :]

                    if self._amp:
                        self.ax_amp.plot(range(self.window_size), amplitudes, label=str(subcarrier))

                    if self._phase:
                        np.unwrap(phases)
                        self.ax_pha.plot(range(self.window_size), phases, label=str(subcarrier))

            except ValueError as err:
                print(
                    f'A ValueError occurred. Is the bandwidth {self.bandwidth} MHz correct?\nError: ', err
                )
                exit(-1)
            self.ax_amp.legend()
            self.ax_pha.legend()
            plt.draw()
            plt.pause(0.001)

    def __del__(self):
        pass