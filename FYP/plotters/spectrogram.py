import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
class Spectrogram():
    def __init__(self, csi_data, window_size, step_size):
        self.csi_data = csi_data
        self.window_size = window_size
        self.step_size = step_size

    def calculate(self):
        f, t, Sxx = signal.stft(self.csi_data, window='hann', nperseg=self.window_size,
                                noverlap=self.window_size - self.step_size)
        plt.pcolormesh(t, f, np.abs(Sxx), cmap='viridis')
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.show()