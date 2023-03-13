import os
import time

import pandas as pd
from trial1.decoders.realtimecsi import hampel_filter, moving_average, searchVariance

# from trial1.plotters.newPlotter import Plotter
# import trial1.decoders.realtimecsi as decoder
from trial1.decoders.realtimecsi import read_frame
import socket
import numpy as np
import matplotlib.animation as animation
import matplotlib.pyplot as plt

remove_null_subcarriers = True
remove_pilot_subcarriers = True
apply_hampel = True
apply_smoothing = False
_amplitude = True
_fase = False

# set to 500 so our images generate 5s = 100Hz Frequency
# 100 samples per second as our ping is in intervals of 0.01
windowSize = 1000
updates= 100

bandwidth = int(input("Bandwidth:"))
nsub = bandwidth * 3.2

# TCP_IP = "169.254.177.92"
# TCP_IP = "169.254.103.233"
TCP_IP = "192.168.1.6"
TCP_PORT = 5501
BUFFER_SIZE = 512*4  # must store the bytes of each packet (n_sub * 4) + header nexmon (18 bytes)
temporary_frames = np.zeros((2, windowSize, int(nsub)))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((TCP_IP, TCP_PORT))
    print("Waiting for connections...")
    s.listen(1)
    conn, addr = s.accept()
    print('Connected by', addr)
    print("\n\n")

    # plotter = Plotter(bandwidth, apply_hampel=apply_hampel, apply_smoothing=apply_smoothing,
    #                   plot_phase=_fase, plot_amp=_amplitude, window_size=windowSize,
    #                   packets_refresh=updates)
    # plotter = Plotter(80, False, False, False, True, 200, 10)
    n_frame = 0

    start = time.time()
    while n_frame<windowSize:
        # while n_frame < 10:
            # if n_frame %10 ==0:
            #     time.sleep(2)
            # receiving frames from packets
        frame = conn.recv(BUFFER_SIZE)
        print(frame[:2])
        # checking if the frame is correct
        if frame[:2] != b'\x11\x11':
            continue

        # processing CSI information
        frame_info = read_frame(frame, bandwidth)
        if frame_info == -1:
            continue

        frame_info.print(0, n_frame=n_frame)
        csi = frame_info.get_csi(
            0,
            remove_null_subcarriers,
            remove_pilot_subcarriers
        )
        amplitudeValues = np.abs(csi)
        phaseValues = np.angle(csi)
        temporary_frames[0, n_frame, :] = amplitudeValues
        temporary_frames[1, n_frame, :] = phaseValues

        # plotter.update(csi, n_frame)
        n_frame += 1
        del frame_info

total_time = time.time() - start
frequency = f"{(n_frame/total_time):.2f}".split(".")
frequency = "_".join(frequency)

ampDF = pd.DataFrame(temporary_frames[0])
phaDF = pd.DataFrame(temporary_frames[1])

print(frequency)



ampDF.to_csv(f"{os.getcwd()+'/'+'data'}/test-amp.csv", mode='w',index=False)
phaDF.to_csv(f"{os.getcwd()+'/'+'data'}/test-pha.csv", mode='w', index=False)