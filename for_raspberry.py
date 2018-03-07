#Constant
ind = 1.07 * 1e-3 #H/km
cap = 10.938 * 1e-9 #F/km
fs = 1e6
orde = 16
linelength = 100

#Import libraries
import csv
import pywt
import sys

import numpy as np
import scipy
from numpy import NaN, Inf, arange, isscalar, asarray, array
from matplotlib.pyplot import plot, scatter, show

#peakdet function
import sys

from numpy import NaN, Inf, arange, isscalar, asarray, array

def peakdet(v, delta, x = None):
    maxtab = []
    mintab = []
       
    if x is None:
        x = arange(len(v))
    
    v = asarray(v)
    
    if len(v) != len(x):
        sys.exit('Input vectors v and x must have same length')
    
    if not isscalar(delta):
        sys.exit('Input argument delta must be a scalar')
    
    if delta <= 0:
        sys.exit('Input argument delta must be positive')
    
    mn, mx = Inf, -Inf
    mnpos, mxpos = NaN, NaN
    
    lookformax = True
    
    for i in arange(len(v)):
        this = v[i]
        if this > mx:
            mx = this
            mxpos = x[i]
        if this < mn:
            mn = this
            mnpos = x[i]
        
        if lookformax:
            if this < mx-delta:
                maxtab.append((mxpos, mx))
                mn = this
                mnpos = x[i]
                lookformax = False
        else:
            if this > mn+delta:
                mintab.append((mnpos, mn))
                mx = this
                mxpos = x[i]
                lookformax = True

    return array(maxtab), array(mintab)

#Import fault voltage data from csv file
with open("ACG40.csv", "rb") as csvfile :
    fault_file = csv.reader(csvfile, delimiter = ",")
    next(fault_file)
    next(fault_file)
    next(fault_file)

    x = list(fault_file)
    fault_signal = np.array(x).astype("float")

#Matrix extraction
x = np.array(fault_signal)
def submatrix(matrix, startRow, startCol, Rowsize, Colsize):
    return x[startRow:startRow+Rowsize, startCol:startCol+Colsize]

vsignal = submatrix(fault_signal, 0, 1, 28000, 3)
isignal = submatrix(fault_signal, 0, 4, 28000, 3)

#Clarke Transformation matrix
t = np.array([[1, 1, 1], [2, -1, -1], [0, np.sqrt(3), np.sqrt(3)]])

#Acquire the modal signal using Clarke transformation                     
smode = np.matmul(vsignal, t)
gnd = smode[0:, 0]
alpha = smode[0:, 1]
beta = smode[0:, 2]

#Alpha signal wavelet transform to locate fault
coeffs = pywt.wavedec(alpha, 'db4', level = 4)
cA, cD4, cD3, cD2, cD1 = coeffs

wtcabs = np.absolute(cD4)

maxtab, mintab = peakdet(wtcabs, 0.05*max(wtcabs))

#Find maxindex
indices = maxtab[:,0]
maxima = maxtab[:,1]

for k in range(len(wtcabs)):
    if wtcabs[k] == max(wtcabs):
        maxindex = k
print(maxindex)

for k in range(len(indices)):
    if indices[k] == maxindex:
        secindex = indices[k+1]
print(secindex)

#Fault Location Calculation
v = 1/(np.sqrt(cap * ind))
deltat = (secindex - maxindex) * orde / fs
dist = deltat*v/2
loc = dist

if maxindex > 639:
    loc = linelength - dist
if dist > linelength/2:
    loc = dist 

print(loc)
