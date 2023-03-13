# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
'''
Amplitude and Phase plotter
---------------------------
Plot Amplitude and Phase of CSI samples
and update the plots in the same window.
Initiate Plotter with bandwidth, and
call update with CSI value.
'''

# subcarrier_num = 256
# cache_data4 = [np.nan] * subcarrier_num
# def realtime_plot_nexmon():
#     fig, ax = plt.subplots()
#     plt.title('csi-amplitude')
#     plt.xlabel('subcarrier')
#     plt.ylabel('amplitude')
#     ax.set_ylim(0, 4000)
#     ax.set_xlim(0, subcarrier_num)
#     x = np.arange(0, subcarrier_num)
#
#     line4,  = ax.plot(x, np.abs(cache_data4), linewidth=1.0, label='subcarrier_256')
#     plt.legend()
#
#     def init():
#         line4.set_ydata([np.nan] * subcarrier_num)
#         return line4,
#
#     def animate(i):
#         global cache_data4, mutex
#         mutex.acquire()
#         line4.set_ydata(np.abs(cache_data4))
#         mutex.release()
#         return line4,
#
#     ani = animation.FuncAnimation(fig, animate, init_func=init, interval=1000/25, blit=True)
#     plt.show()

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
# from hampel import hampel
# from scipy.signal import savgol_filter
from scipy import signal
from scipy.signal import butter, lfilter
from pyculiarity import detect_ts



'''
Amplitude and Phase plotter
---------------------------
Plot Amplitude and Phase of CSI samples
and update the plots in the same window.
Initiate Plotter with bandwidth, and
call update with CSI value.
'''

__all__ = [
    'Plotter'
]

init = 0

class Plotter():
    def __init__(self, bandwidth):
        self.bandwidth = bandwidth

        nsub = int(bandwidth * 3.2)
        self.x_amp = np.arange(-1 * nsub / 2, nsub / 2)
        self.x_pha = np.arange(-1 * nsub / 2, nsub / 2)
        # self.x_amp = np.arange(0, 4000)
        # self.x_pha = np.arange(-1 * nsub / 2, nsub / 2)

        self.fig, axs = plt.subplots(2)
        axs[0].set_ylim(0,1000)
        axs[0].set_xlim(0, 256)
        self.ax_amp = axs[0]
        self.ax_pha = axs[1]


        self.fig.suptitle('Amplitude and Phase Plotter CSI')


    def update(self, csi):

        self.ax_amp.clear()
        self.ax_pha.clear()

        # These are also cleared with clear()
        self.ax_amp.set_ylabel('Amplitude')
        self.ax_pha.set_ylabel('Phase')
        self.ax_pha.set_xlabel('Subcarrier')

        try:
            # Apply Savitzky-Golay filter to the data
            # csi_filtered = savgol_filter(np.abs(csi), 50, 3)


            # Apply Butterworth filter to the data
            cutoff = 0.1
            order = 3
            b, a = butter(order, cutoff)
            csi_filtered = lfilter(b, a, np.abs(csi))

            # csi_filtered = detect_ts(np.abs(csi), max_anoms=0.02, direction='both', plot=False)

            # raw csi
            # self.ax_amp.plot(self.x_amp, np.abs(csi))

            # filtered csi
            self.ax_amp.plot(self.x_amp, csi_filtered)


            self.ax_pha.plot(self.x_pha, np.angle(csi, deg=True))

        except ValueError as err:
            print(
                f'A ValueError occurred. Is the bandwidth {self.bandwidth} MHz correct?\nError: ', err
            )
            exit(-1)
        # fig.canvas.flush_events()
        plt.draw()
        plt.pause(0.001)


    def __del__(self):
        pass