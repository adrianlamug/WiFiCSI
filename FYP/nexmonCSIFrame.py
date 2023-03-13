import numpy as np
class NexmonCSIFrame:
    """CSIFrame subclass for Nexmon-compatible Broadcom hardware.
            Format produced by nexmon_csi, developed by Seemoo Lab.
            ...
            Attributes
            ----------
            timestamp : int
                Epoch timestamp for the frame.
            rssi : int
                Additional field added in mzakharo's PR: https://github.com/seemoo-lab/nexmon_csi/pull/46
                Observed signal strength in dB.
            frame_control : int
                Additional field added in mzakharo's PR: https://github.com/seemoo-lab/nexmon_csi/pull/46
                Frame Control bitmask.
                Can be used to identify the type/purpose of an 802.11 frame.
                Bit definitions: https://dox.ipxe.org/group__ieee80211__fc.html
            source_mac : int
                Source MAC address for the received frame.
            sequence_no : int
                Sequential index of the given frame.
            core : int
                Core used for frame transmission.
            spatial_stream : int
                Spatial stream used for frame transmission.
            channel_spec : int
                Broadcom chanspec value, containing the bandwidth/frequency/channel used for frame transmission.
            chip : str
                Broadcom Chipset identifier.
            csi_matrix : np.array
                Matrix of CSI values.
        """

    def __init__(self, header: dict, csi_matrix: np.array):
        self.timestamp = header["timestamp"]
        self.rssi = header["rssi"]
        self.frame_control = header["frame_control"]
        self.source_mac = header["source_mac"]
        self.sequence_no = header["sequence_no"]
        self.core = header["core"]
        self.spatial_stream = header["spatial_stream"]
        self.channel_spec = header["channel_spec"]
        self.chip = header["chip"]

        if "agcGain" in header:
            self.agcGain = header["agcGain"]

        self.csi_matrix = header["csi_matrix"]