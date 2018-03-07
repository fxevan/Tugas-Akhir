#Constant
ind = 1.07 * 1e-3 #H/km
cap = 10.938 * 1e-9 #F/km
fs = 1e6
orde = 16
linelength = 100

#Import libraries
import csv
import pywt

import plotly.plotly as py
import plotly.graph_objs as go
from plotly.tools import FigureFactory as FF

import numpy as np
import pandas as pd
import scipy
import peakutils

#Import fault voltage data from csv file
with open("ABG85.csv", "rb") as csvfile :
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

#verifikasi
#B = vsignal[0:, 0]
#C = vsignal[0:, 1]
#A = vsignal[0:, 2]

#trace3 = go.Scatter(x=[j for j in range(len(A))], y=A, mode = 'lines', name = 'VA')
#trace4 = go.Scatter(x=[j for j in range(len(B))], y=B, mode = 'lines', name = 'VB')
#trace5 = go.Scatter(x=[j for j in range(len(C))], y=C, mode = 'lines', name = 'VC')
#datav = [trace3,trace4,trace5]
#py.plot(datav, filename='vsignal')


#Clarke Transformation matrix
t = np.array([[1, 1, 1], [2, -1, -1], [0, np.sqrt(3), np.sqrt(3)]])

#Acquire the modal signal using Clarke transformation                     
smode = np.matmul(vsignal, t)
gnd = smode[0:, 0]
alpha = smode[0:, 1]
beta = smode[0:, 2]

#verifikasi
#trace6 = go.Scatter(x=[j for j in range(len(gnd))], y=gnd, mode = 'lines', name = 'VGnd')
#trace7 = go.Scatter(x=[j for j in range(len(alpha))], y=alpha, mode = 'lines', name = 'VAlpha')
#trace8 = go.Scatter(x=[j for j in range(len(beta))], y=beta, mode = 'lines', name = 'VBeta')
#datavmod = [trace6,trace7,trace8]
#py.plot(datavmod, filename='vmodal')

#Alpha signal wavelet transform to locate fault
coeffs = pywt.wavedec(alpha, 'db4', level = 4)
cA, cD4, cD3, cD2, cD1 = coeffs

wtcabs = np.absolute(cD4)

trace = go.Scatter(x=[j for j in range(len(wtcabs))], y=wtcabs)
py.plot([trace], filename='numpy-array-ex1')

indices = peakutils.indexes(wtcabs, thres=0.05, min_dist=3)

trace2 = go.Scatter(x=indices, y=[wtcabs[j] for j in indices],
                    mode='markers',
                    marker=dict(
                        size=8,
                            color='rgb(255,0,0)',
                        symbol='cross'
                        ),
                    name='Detected Peaks'
                    )

data = [trace, trace2]
py.plot(data, filename='wtcabs-with-peak')

#Find maxindex
for k in range(len(wtcabs)):
    if wtcabs[k] == max(wtcabs):
        maxindex = k

for k in range(len(indices)):
    if indices[k] == maxindex:
        secindex = indices[k+1]

#Fault Location Calculation
v = 1/(np.sqrt(cap * ind))
deltat = (secindex - maxindex) * orde / fs
dist = deltat*v/2

if dist > linelength/2:
    loc = dist
else if maxindex > 639:
    loc = linelength - dist

print(loc)
