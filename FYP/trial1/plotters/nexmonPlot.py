import socket
import threading


import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

class NexmonPlotter():
    def __init__(self, bandwidth):
        self.bandwidth = bandwidth

        nsub = int(bandwidth * 3.2)
        self.x_amp = np.arange(-1 * nsub / 2, nsub / 2)
        self.x_pha = np.arange(-1 * nsub / 2, nsub / 2)

        self.fig, axs = plt.subplots()
        plt.title("csi-amplitude")
        plt.xlabel("subccarrier")
        plt.ylabel("amplitude")

        self.ax_amp = axs[0]
        self.ax_pha = axs[1]

        self.fig.suptitle('Amplitude and Phase Plotter CSI')

        plt.ion()
        plt.show()

    def update(self, i):
        global cache_data4, mutex
        mutex.acquire()
        line4.set_ydata(np.abs(cache_data4))
        mutex.release()
        return line4
    fig, ax = plt.subplots()
    plt.title('csi-amplitude')
    plt.xlabel('subcarrier')
    plt.ylabel('amplitude')
    ax.set_ylim(0, 4000)
    ax.set_xlim(0, 256)
    x = np.arange(0, 256)

    line4,  = ax.plot(x, np.abs(cache_data4), linewidth=1.0, label='subcarrier_256')
    plt.legend()

    def init():
        line4.set_ydata([np.nan] * 256)
        return line4,

    def update(i):
        global cache_data4, mutex
        mutex.acquire()
        line4.set_ydata(np.abs(cache_data4))
        mutex.release()
        return line4,

    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=250, blit=True)
    plt.show()
