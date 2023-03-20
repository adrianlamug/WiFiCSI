import numpy as np

from readers.pcap import Pcap


def get_csi(pcap: Pcap):

    # pcap frame has (1,512)
    for i in range(1000):
        x = pcap.frames[i].payload_header
    # Convert CSI bytes to numpy array
    print("hello world")
    # csi_np = np.frombuffer(
    #     csi,
    #     dtype=np.int16,
    #     count=nsub * 2 * nsamples
    # )
    #
    # # Cast numpy 1-d array to matrix
    # csi_np = csi_np.reshape((nsamples, nsub * 2))
    #
    # # Convert csi into complex numbers
    # csi_cmplx = np.fft.fftshift(
    #     csi_np[:nsamples, ::2] + 1.j * csi_np[:nsamples, 1::2], axes=(1,)
    # )