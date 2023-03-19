import pandas as pd
import numpy as np
import statistics
import matplotlib.pyplot as plt
from FYP.trial1.decoders.interleaved import read_pcap
import os
from tensorflow.keras.models import load_model
from scipy.interpolate import interp1d
from FYP.trial1.utils.matlab import db
from numpy import inf


activities = ["static", "standing", "walking" , "falling"]
FS = 100

def loadFromDat(inputFile, windowSize=FS, step=50):
    #     print(int((csi_data.nsamples-1)*(100/average_sample_rate)+1))

    csi_data = read_pcap(inputFile)
    csi = csi_data.csi

    first_timestamp = float(csi_data.timestamps[0])
    last_timestamp = float(csi_data.timestamps[-1])
    final_timestamp = last_timestamp - first_timestamp
    average_sample_rate = csi_data.nsamples / final_timestamp

    interp_func = interp1d(csi_data.timestamps, csi_data.csi, kind='linear', axis=0, fill_value="extrapolate")
    t_new = np.linspace(first_timestamp, last_timestamp, (csi_data.nsamples - 1) * int((100 / average_sample_rate) + 1))
    csi_interp = interp_func(t_new)
    csi = csi_interp

    csi = db(np.abs(csi))
    finalData = csi[:, :, 0]
    finalData = np.transpose(finalData)

    new_average_sample_rate = len(csi_interp) / final_timestamp

    if new_average_sample_rate > FS:
        downsample_factor = int(new_average_sample_rate / FS)
        csi = csi[::downsample_factor]
    index = 0
    positiveInput = []

    while index + windowSize <= csi.shape[0]:
        curFeature = np.zeros((1, windowSize, 256))
        curFeature[0] = csi[index:index + windowSize, :].reshape(100, 256)
        positiveInput.append(curFeature)
        index += step
    try:
        positiveInput = np.concatenate(positiveInput, axis=0)
    except ValueError as e:
        positiveInput = np.zeros((1, windowSize, 256))
    positiveInput[positiveInput == -inf] = 0

    return positiveInput

def classify(pcapFile, model):
    best_network = load_model(model)
    x = loadFromDat(pcapFile)
    x_pred = best_network.predict(x)
    print(x_pred)
    ensemble = []
    for i in range(len(x_pred)):
        ensemble.append(np.argmax(x_pred[i]))
    mode_value = statistics.mode(ensemble)
    return f"The activity classified is: {activities[mode_value]}"

if __name__ == '__main__':
    test_dir = os.path.join("generated/data")
    pcapFile = f"{test_dir}/walking-1.pcap"
    model = "current_best_network.h5"
    print(classify(pcapFile, model))