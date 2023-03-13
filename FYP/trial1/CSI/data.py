import itertools
from typing import Tuple

import numpy as np

from trial1.CSI.frame import NexmonCSIMetadata
from trial1.Frame.pcap import PcapFrame

class CSIData:

    def __init__(self, filename: str = "", backend: str = "", chipset: str = "", filter_mac: str = None):

        self.frames = []
        self.timestamps = []

        self.expected_frames = 0
        self.skipped_frames = 0

        self.bandwidth = 0

        self.filename = filename
        self.backend = backend
        self.chipset = chipset
        self.filter_mac = filter_mac

    def set_chipset(self, chipset: str):
        self.chipset = chipset

    def set_backend(self, backend: str):
        self.backend = backend

    def push_frame(self, frame: PcapFrame):
        if self.filter_mac is not None:
            if hasattr(frame, "mac"):
                if self.filter_mac.casefold() == frame.mac.casefold():
                    self.frames.append(frame)
        else:
            self.frames.append(frame)

    def get_metadata(self) -> NexmonCSIMetadata:
        chipset = self.chipset
        backend = self.backend

        bandwidth = self.bandwidth

        unmodified_csi_matrix = self.frames[0].csi_matrix
        _, no_frames, no_subcarriers = get_CSI(self)

        rx_count = (0, 0)
        tx_count = (0, 0)

        if len(unmodified_csi_matrix.shape) <= 2:
            rx_count, tx_count = (1, 1)
        elif len(unmodified_csi_matrix.shape) == 3:
            rx_count, tx_count = unmodified_csi_matrix.shape[1:]

        antenna_config_string = "{} Rx, {} Tx".format(rx_count, tx_count)

        timestamps = self.timestamps
        final_timestamp = timestamps[-1]

        # Check if timestamp is relative or epoch.

        time_length = 0
        if len(str(final_timestamp)) > 9:
            # Likely an epoch timestamp.
            # Get diff between first and last.
            time_length = final_timestamp - timestamps[0]
        else:
            time_length = round(float(final_timestamp), 1)

        average_sample_rate = 0
        if time_length > 0 and final_timestamp != 0:
            average_sample_rate = round(no_frames / time_length, 1)

        rss_total = []
        if hasattr(self.frames[0], "rssi"):
            rss_total = [x.rssi for x in self.frames]
        else:
            rss_total = [max(frame.rssi_a, frame.rssi_b, frame.rssi_c) for frame in self.frames]
            # Must sum a/b/c.
            # for frame in self.frames:
            #     total_rss_for_frame = 0
            #     divisor = 0
            #     if frame.rssi_a != 0:
            #         total_rss_for_frame += frame.rssi_a
            #         divisor += 1
            #     if frame.rssi_b != 0:
            #         total_rss_for_frame += frame.rssi_b
            #         divisor += 1
            #     if frame.rssi_c != 0:
            #         total_rss_for_frame += frame.rssi_c
            #         divisor += 1
            #     total_rss_for_frame /= divisor
            #     rss_total.append(total_rss_for_frame)

        average_rssi = round(np.mean(rss_total), 1)

        data = {
            "chipset": chipset,
            "backend": backend,
            "bandwidth": bandwidth,
            "antenna_config": antenna_config_string,
            "frames": no_frames,
            "subcarriers": no_subcarriers,
            "time_length": time_length,
            "average_sample_rate": average_sample_rate,
            "average_rssi": average_rssi,
            "csi_shape": unmodified_csi_matrix.shape
        }

        return NexmonCSIMetadata(data)

def get_CSI(csi_data: 'CSIData', metric: str = "amplitude", extract_as_dBm: bool = True,
            squeeze_output: bool = False) -> Tuple[np.array, int, int]:
    # TODO: Add proper error handling.

    # This looks a little ugly.
    frames = csi_data.frames
    csi_shape = frames[0].csi_matrix.shape

    no_frames = len(frames)
    no_subcarriers = csi_shape[0]

    # Matrices should be Frames * Subcarriers * Rx * Tx.
    # Single Rx/Tx streams should be squeezed.
    if len(csi_shape) == 3:
        # Intel data comes as Subcarriers * Rx * Tx.
        no_rx_antennas = csi_shape[1]
        no_tx_antennas = csi_shape[2]
    elif len(csi_shape) == 2 or len(csi_shape) == 1:
        # Single antenna stream.
        no_rx_antennas = 1
        no_tx_antennas = 1
    else:
        # Error. Unknown CSI shape.
        print("Error: Unknown CSI shape.")

    csi = np.zeros((no_frames, no_subcarriers, no_rx_antennas, no_tx_antennas), dtype=complex)

    ranges = itertools.product(*[range(n) for n in [no_frames, no_subcarriers, no_rx_antennas, no_tx_antennas]])
    is_single_antenna = no_rx_antennas == 1 and no_tx_antennas == 1

    drop_indices = []

    for frame, subcarrier, rx_antenna_index, tx_antenna_index in ranges:
        frame_data = frames[frame].csi_matrix
        if subcarrier >= frame_data.shape[0]:
            # Inhomogenous component
            # Skip frame for now. Need a better method soon.
            continue

        subcarrier_data = frame_data[subcarrier]
        if subcarrier_data.shape != (no_rx_antennas, no_tx_antennas) and not is_single_antenna:
            if rx_antenna_index >= subcarrier_data.shape[0] or tx_antenna_index >= subcarrier_data.shape[1]:
                # Inhomogenous component
                # Skip frame for now. Need a better method soon.
                drop_indices.append(frame)
                continue

        csi[frame][subcarrier][rx_antenna_index][tx_antenna_index] = subcarrier_data if is_single_antenna else \
            subcarrier_data[rx_antenna_index][tx_antenna_index]

    csi = np.delete(csi, drop_indices, 0)
    csi_data.timestamps = [x for i, x in enumerate(csi_data.timestamps) if i not in drop_indices]

    if metric == "amplitude":
        csi = abs(csi)
        if extract_as_dBm:
            csi = db(csi)
    elif metric == "phase":
        csi = np.angle(csi)

    if squeeze_output:
        csi = np.squeeze(csi)

    return (csi, no_frames, no_subcarriers)