import numpy as np;
chip = '43455c0'
bw = 80
file = "trial1/output.pcap"
maxUDPS = 1000

headerOffset = 16
nfft = bw*3.2
# pcapFile =
p = open(file)
# while True:
#         next_frame = p.read(np.uint32)
PCAP_HEADER_DTYPE = np.dtype([
        ("magic_number", np.uint32),
        ("version_major", np.uint16),
        ("version_minor", np.uint16),
        ("thiszone", np.int32),
        ("sigfigs", np.uint32),
        ("snaplen", np.uint32),
        ("network", np.uint32)
    ])