# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 10:01:50 2017

@author: SMAHESH
"""

from sklearn.model_selection import RandomizedSearchCV
import tensorflow as tf
sess = tf.Session()

from numpy.random import uniform
import keras
from keras.models import Sequential
from keras.wrappers.scikit_learn import KerasClassifier
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv3D, MaxPooling3D, BatchNormalization
from keras.optimizers import Adam
from keras import backend as K
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
K.set_session(sess)
import time
start_time = time.time()
print("--- %s seconds ---" % (time.time() - start_time))

import pickle
import gc
import pandas as pd
from collections import OrderedDict
import numpy as np
import random
random.seed(10)

start_time = time.time()
print("--- %s seconds ---" % (time.time() - start_time))

modelfile = '4.2weights.17-0.04.hdf5'
modelx = keras.models.load_model(modelfile)

#setup
savepath = '/home/cc/Data/'
Xsize = 40
Ysize = 40
Zsize = 18

XYstride = 20
Zstride = 9


thresholds = [x/100 for x in list(range(1, 100))]
thresholds.extend([x/1000 for x in list(range(991, 1000))])
thresholds.extend([x/10000 for x in list(range(9991, 10000))])
FPrates = []
sensitivities = []
fakeSensitivities = []
FPrates = []
sensitivities = []
fakeSensitivities = []

noduleBoxes = None
with open(savepath+"noduleBoxes.pickle", "rb") as f:
    noduleBoxes = pickle.load(f)
fakeNoduleBoxes = None
with open(savepath+"fakeNoduleBoxes.pickle", "rb") as f:
    fakeNoduleBoxes = pickle.load(f)
sliceList = None
with open(savepath+"sliceamount.pickle", "rb") as f:
    sliceList = pickle.load(f)    
valSeries = None
with open(savepath+"workingValidationSeries.pickle", "rb") as f:
    valSeries = pickle.load(f)
numScans = len(valSeries)

sumofFPs = []
sumofTPs = []  
numDetected = [] 
numFakesDetected = [] 
for o in range(len(thresholds)):
    sumofFPs.append(0)
    sumofTPs.append(0)
    numDetected.append(0)
    numFakesDetected.append(0)
k = 0
numNodules = 0
numFakes = 0

Xlow = 0
allboxXs = []
allboxYs = []
Xhigh = Xsize
while Xhigh < 512:
    allboxXs.append([Xlow, Xhigh])
    allboxYs.append([Xlow, Xhigh])
    Xlow += XYstride
    Xhigh += XYstride              
counterx = 0       
for seriesID in valSeries:
    counterx += 1
    print ("File: " + str(counterx))
    inputs = None
    with open(savepath+"ValClipped" + seriesID + ".pickle", 'rb') as f:
        inputs = pickle.load(f)
    inputs = np.array(inputs)
    inputs = inputs.reshape(inputs.shape[0], Xsize, Ysize, Zsize, 1)
    predictions = modelx.predict(inputs, batch_size=48)
    
    Zlow = 0
    Zhigh = Zsize
    allboxZs = []
    coords = []
    numSlices = sliceList[k]
    k += 1
    
    while Zhigh < numSlices:
        allboxZs.append([Zlow, Zhigh])
        Zlow += Zstride
        Zhigh += Zstride
    allboxZs.append([numSlices - Zsize, numSlices]) 
    for boxZ in allboxZs:
            for boxY in allboxYs:
                for boxX in allboxXs:
                    coords.append([boxX, boxY, boxZ])
                     
    for num in range(len(thresholds)):
        FPs = 0
        TPs = 0
        nodulesFound = set()
        fakeNodulesFound = set()
        for i in range(len(predictions)):
            if predictions[i][0] >= thresholds[num]:
                detection = coords[i]
                FP = True
                TP = False
                for node in noduleBoxes[seriesID]:
                    if detection in noduleBoxes[seriesID][node]:
                        nodulesFound.add(node)
                        FP = False
                        TP = True
                for node in fakeNoduleBoxes[seriesID]:
                    if detection in fakeNoduleBoxes[seriesID][node]:
                        fakeNodulesFound.add(node)
                        FP = False
                if FP:
                    FPs += 1 
                if TP:
                    TPs += 1         
        numDetected[num] += len(nodulesFound)
        numFakesDetected[num] += len(fakeNodulesFound)
        sumofFPs[num] += FPs
        sumofTPs[num] += TPs        
    
    numNodules += len(noduleBoxes[seriesID])
    numFakes += len(fakeNoduleBoxes[seriesID])
         
#need to double check if conresponding indcies work            
#sensitivities = numDetected / numNodules
#FPrates = sumofFPs / numScans
#Will this work??
sensitivities = [(x*1.0)/numNodules for x in numDetected]
FPrates = [(x*1.0)/numScans for x in sumofFPs]
FPratesAdj = [(a / c) * b / numScans for a, b, c in zip(numDetected, sumofFPs, sumofTPs)]
fakeSensitivities = [((a + b) * 1.0) / (numNodules + numFakes) for a, b in zip(numDetected, numFakesDetected)]


with open(savepath+"sensitivities1.pickle", 'wb') as handle:
    pickle.dump(sensitivities, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open(savepath+"FPrates1.pickle", 'wb') as handle:
    pickle.dump(FPrates, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open(savepath+"FPratesAdj1.pickle", 'wb') as handle:
    pickle.dump(FPratesAdj, handle, protocol=pickle.HIGHEST_PROTOCOL)    
with open(savepath+"fakeSensitivities1.pickle", 'wb') as handle:
    pickle.dump(fakeSensitivities, handle, protocol=pickle.HIGHEST_PROTOCOL)  
with open(savepath+"sumofTPs1.pickle", 'wb') as handle:
    pickle.dump(sumofTPs, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open(savepath+"sumofFPs1.pickle", 'wb') as handle:
    pickle.dump(sumofFPs, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open(savepath+"numDetected1.pickle", 'wb') as handle:
    pickle.dump(numDetected, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open(savepath+"numFakesDetected1.pickle", 'wb') as handle:
    pickle.dump(numFakesDetected, handle, protocol=pickle.HIGHEST_PROTOCOL)             
#plot line graph of FPrates vs sensitivities
#idk if this will actually work, it's modified from a stack overflow post


plt.plot(FPrates, sensitivities)
plt.xlabel('FPs per Scan', fontsize = 16)
plt.ylabel("% Nodules Detected", fontsize = 16)
plt.title("FROC Curve, Certain Nodules", fontsize = 24)
plt.ylim([0,1])
plt.tick_params(labelsize = 12)

plt.savefig('FROC_plot1.png')            


plt.gcf().clear()
plt.plot(FPratesAdj, sensitivities)
plt.xlabel('FPs per Scan, Adjusted', fontsize = 16)
plt.ylabel("% Nodules Detected", fontsize = 16)
plt.title("FROC Curve, Certain Nodules", fontsize = 24)
plt.ylim([0,1])
plt.tick_params(labelsize = 12)

plt.savefig('FROC_plotAdj1.png')

            
plt.gcf().clear()
plt.plot(FPrates, fakeSensitivities)
plt.xlabel('FPs per Scan', fontsize = 16)
plt.ylabel("% Nodules Detected", fontsize = 16)
plt.title("FROC Curve, All Nodules", fontsize = 24)
plt.ylim([0,1])
plt.tick_params(labelsize = 12)

plt.savefig('FROC_plot21.png')         