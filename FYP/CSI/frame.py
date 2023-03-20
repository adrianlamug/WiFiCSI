import numpy as np

class NexmonCSIMetadata:
    """
        Format produced by nexmon_csi, developed by Seemoo Lab.
        ...
        Attributes
        ----------
        timestamp : int
            Epoch timestamp for the frame.
        rssi : int
            Additional field added in mzakharo's PR: https://github.com/seemoo-lab/nexmon_csi/pull/46
            Observed signal strength in dB.
        fctl : int
            Additional field added in mzakharo's PR: https://github.com/seemoo-lab/nexmon_csi/pull/46
            Frame Control bitmask.
            Can be used to identify the type/purpose of an 802.11 frame.
            Bit definitions: https://dox.ipxe.org/group__ieee80211__fc.html
        mac : int
            Source MAC address for the received frame.
        seq : int
            Sequential index of the given frame.
        core : int
            Core used for frame transmission.
        spatial_stream : int
            Spatial stream used for frame transmission.
        channel_spec : int
            Broadcom chanspec value, containing the bandwidth/frequency/channel used for frame transmission.
        chip : str
            Broadcom Chipset identifier.
        csi : np.array
            Matrix of CSI values.
    """

    __slots__ = [
        "rssi",
        "fctl",
        "mac",
        "seq"
        "core",
        "spatial_stream",
        "channel_spec",
        "chip",
        "csi"
    ]

    def __init__(self, header_block: dict, csi: np.array):
        self.rssi = header_block["rssi"]
        self.frame_control = header_block["frame_control"]
        self.source_mac = header_block["source_mac"]
        self.sequence_no = header_block["sequence_no"]
        self.core = header_block["core"]
        self.spatial_stream = header_block["spatial_stream"]
        self.channel_spec = header_block["channel_spec"]
        self.chip = header_block["chip"]
        self.csi = csi
