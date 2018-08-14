#Import libraries
import threading
from serial import Serial
from datetime import datetime
from dateutil.relativedelta import relativedelta
import RPi.GPIO as GPIO
import os
import shutil

import csv
import pywt
import sys

import numpy as np
import scipy
from scipy import stats
from numpy import NaN, Inf, arange, isscalar, asarray, array
from matplotlib.pyplot import plot, scatter, show

import tkinter as tk
from tkinter import ttk
from tkinter import *

global faultdetect
faultdetect = False

def GUI() :
	FONTTYPE1 = ("Verdana", 24)
	FONTTYPE2 = ("Verdana", 18)
	BACKGROUND = "#CEECF5" 
	FOREGROUND = "#000d50"

	lt = 0
	ind = 0
	cap = 0
	gd1 = 0
	gd2 = 0

	fs = 1e6
	orde = 16
	ig = 11.71213
	Va = 105839.4
	Vb = 105983.3
	Vc = 106389.6
	
	class MainApp(tk.Tk):
		
		global floc, ftype
		
		def __init__(self, *args, **kwargs):
			
			tk.Tk.__init__(self, *args, **kwargs)
			
			tk.Tk.wm_title(self, "Fault Locator")
			tk.Tk.geometry(self,'1024x600')
			tk.Tk.config(self, background = BACKGROUND)
			tk.Tk.resizable(self, width=False, height=False)
			container = tk.Frame(self)
			container.pack(side="top", fill="both", expand=True)
			container.grid_rowconfigure(0, weight=1)
			container.grid_columnconfigure(0, weight=1)
			
			self.frames = {}
			
			for F in (MainPage, InputPage):
			
				frame = F(container, self)
				self.frames[F] = frame
				
				frame.grid(row=0, column=0, sticky="nsew")
				frame.configure(background = BACKGROUND)
			
			self.show_frame(InputPage)
			
		def show_frame(self, cont):
			frame = self.frames[cont]
			frame.tkraise()
			
	class MainPage(tk.Frame):
		
		global distance
		distance = 0		
		
		def __init__(self, parent, controller):
			global faultfilename
			
			tk.Frame.__init__(self, parent)
			title = tk.Label(self, text="FAULT LOCATOR", bg=BACKGROUND, fg=FOREGROUND, font=FONTTYPE1)
			title.pack(pady=10, padx=10)
			
			container = tk.Frame(self)
			container.pack(side=tk.TOP, padx=10, pady=10)
			status_label = tk.Label(container, text="Status", font=FONTTYPE2, anchor=tk.W)
			status_label.pack(side = tk.LEFT)
			self.entry_st = tk.Entry(container)
			self.entry_st.pack(side=tk.LEFT)
			
			container2 = tk.Frame(self)
			container2.pack(side=tk.TOP, padx=10, pady=10)
			time_label = tk.Label(container2, text="Time", font=FONTTYPE2, anchor="w")
			time_label.pack(side = tk.LEFT)
			self.entry_tm = tk.Entry(container2)
			self.entry_tm.pack(side=tk.LEFT)
			
			container3 = tk.Frame(self)
			container3.pack(side=tk.TOP, padx=10, pady=10)
			faults_label = tk.Label(container3, text="Type of Faults", font=FONTTYPE2, anchor="w")
			faults_label.pack(side = tk.LEFT)
			self.entry_tf = tk.Entry(container3)
			self.entry_tf.pack(side=tk.LEFT)
			
			container4 = tk.Frame(self)
			container4.pack(side=tk.TOP, padx=10, pady=10)
			dist_label = tk.Label(container4, text="Distance", font=FONTTYPE2, anchor="w")
			dist_label.pack(side = tk.LEFT)
			self.entry_ds = tk.Entry(container4)
			self.entry_ds.pack(side=tk.LEFT)
			
			container5 = tk.Frame(self)
			container5.pack(side=tk.TOP, padx=10, pady=10)
			coordinate_label = tk.Label(container5, text="Coordinate", font=FONTTYPE2, anchor="w")
			coordinate_label.pack(side=tk.LEFT)
			self.entry_cr = tk.Entry(container5)
			self.entry_cr.pack(side=tk.LEFT)
			
			self.set_text(self.entry_st, "NO FAULT")
			self.set_text(self.entry_tm, "-")
			self.set_text(self.entry_tf, "-")
			self.set_text(self.entry_ds, "-")
			self.set_text(self.entry_cr, "-")
			
			buttonbuzzoff = ttk.Button(self, text="Turn OFF \n Buzzer", command = lambda:[self.buzzeroff()])
			buttonbuzzoff.pack()
			
			buttonnoted = ttk.Button(self, text="Fault Acknowledged", command = lambda:[self.faultdetectfalse()])
			buttonnoted.pack()
			
		if faultdetect:
			#GPIO.output(LedPIN, GPIO.HIGH)
			self.define_widgets(faultfilename)
	
		def set_text(self, entryField, text):
			distance = text
			entryField.delete(0,tk.END)
			entryField.insert(0,distance)

		def buzzeroff(self):
			global buzzer
			buzzer = False
			
		def faultdetectfalse(self):
			global faultdetect
			faultdetect = False

		#FAULT CALCULATION PART
		#Function definition
		def peakdet(self, v, delta, x = None):
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
			
		def matrix_ext(self, filename, startRow, startCol, Rowsize, Colsize):
			with open(filename, 'r') as csvfile :
				fault_file = csv.reader(csvfile, delimiter = ",")
				next(fault_file)
				next(fault_file)
				next(fault_file)
				
				x = list(fault_file)
				fault_signal = np.array(x).astype("float")
				
				x = np.array(fault_signal)
				
			return x[startRow:startRow+Rowsize, startCol:startCol+Colsize]
	
		def wavelet_transf(self, alpha):
			coeffs = pywt.wavedec(alpha, 'db4', level = 4)
			cA, cD4, cD3, cD2, cD1 = coeffs
			wtcabsolute = np.absolute(cD4)
			return cD4, wtcabsolute
			
		def thresholding(self, wtcabsolute):
			wtcthr = wtcabsolute
			thrflags = wtcthr < 0.06995*max(wtcabsolute)
			wtcthr[thrflags] = 0
			return(wtcthr)
			
		def loc_det(self, maxtab, cD4, capacitance, inductance, linelength):
			indices = maxtab[:,0]
			maxima = maxtab[:,1]
			k = 0
			firstindex = indices[k]
			secindex = indices[k+1]
			while (secindex-firstindex) < 3 or (secindex-firstindex) > 43:
				k = k+1
				firstindex = indices[k]
				secindex = indices[k+1]
				
			#Fault Location Calculation
			v = 1/(np.sqrt(capacitance * inductance))
			deltat = (secindex - firstindex) * orde / fs
			dist = deltat*v/2
			
			if dist > 50:
				loc = dist
			elif(self.rms(self.Ignd) < 14.5*ig):
				loc = dist
			else :
				if cD4[int(firstindex)] < 0:
					loc = dist
				elif cD4[int(firstindex)] > 0:
					loc = lengthfloat - dist
					
			return loc
			
		def rms(self, y):
			return(np.sqrt(np.mean(y**2)))
			
		def classification(self, vsignal, isignal, Ignd):
			VA = vsignal[:,0]
			VB = vsignal[:,1]
			VC = vsignal[:,2]
			IA = isignal[:,0]
			IB = isignal[:,1]
			IC = isignal[:,2]
			deltaA = self.rms(VA) - Va
			deltaB = self.rms(VB) - Vb
			deltaC = self.rms(VC) - Vc
			
			deltathrA = Va*0.002
			deltathrB = Vb*0.002
			deltathrC = Vc*0.002
			
			#Grounded Fault
			if(self.rms(self.Ignd) > 14.5*ig):
				if(deltaA < 0) and (deltaB < 0) and (deltaC < 0):
					faulttype = 'Fault 3 Fasa A, B, dan C ke Ground'
				elif (deltaA < 0) and (deltaB < 0):
					faulttype = 'Fault 2 Fasa A dan B ke Ground'
				elif (deltaA < 0) and (deltaC < 0):
					faulttype = 'Fault 2 Fasa A dan C ke Ground'
				elif (deltaB < 0) and (deltaC < 0):
					faulttype = 'Fault 2 Fasa B dan C ke Ground'
				elif(deltaA < 0):
					faulttype = 'Fault 1 Fasa A ke Ground'
				elif(deltaB < 0):
					faulttype = 'Fault 1 Fasa B ke Ground'
				elif(deltaC < 0):
					faulttype = 'Fault 1 Fasa C ke Ground';
					
			#Ungrounded Fault
			elif(self.rms(self.Ignd) < 14.5*ig):
				#3 Phase
				if (abs(deltaA) > deltathrA) and (abs(deltaB) > deltathrB) and (abs(deltaC) > deltathrC):
					faulttype = 'Fault 3 Fasa A, B, dan C';
				#2 Phase
				elif (abs(deltaA) > deltathrA) and (abs(deltaB) > deltathrB):
					faulttype = 'Fault 2 Fasa A dan B'
				elif (abs(deltaA) > deltathrA) and (abs(deltaC) > deltathrC):
					faulttype = 'Fault 2 Fasa A dan C'
				elif (abs(deltaB) > deltathrB) and (abs(deltaC) > deltathrC):
					faulttype = 'Fault 2 Fasa B dan C'
			
			return faulttype

		def define_widgets(self, filename):
			self.filename = faultfilename
			print("masuk sini 1")
			
			self.vsignal = self.matrix_ext(self.filename, 0, 1, 140002, 3)
			#print("masuk sini 1A")
			self.isignal = self.matrix_ext(self.filename, 0, 4, 140002, 6)
			#print("masuk sini 1B")
			#Acquire the modal signal using Clarke transformation
			self.t = np.array([[1, 1, 1], [2, -1, -1], [0, np.sqrt(3), np.sqrt(3)]])
			self.Vsmode = np.matmul(self.t, self.vsignal.T)
			self.Vgnd = self.Vsmode.T[0:, 0]
			self.Valpha = self.Vsmode.T[0:, 1]
			self.Vbeta = self.Vsmode.T[0:, 2]
			
			self.Ismode = np.matmul(self.t, self.isignal.T)
			self.Ignd = self.Ismode.T[0:, 0]
			self.Ialpha = self.Ismode.T[0:, 1]
			self.Ibeta = self.Ismode.T[0:, 2]
			#print("masuk sini 2")

			lineprop = self.get_allvalue()
			#print("masuk sini 3")

			self.capacitance = lineprop[0]
			self.inductance = lineprop[1]
			self.linelength = lineprop[2]
			self.cD4, self.wtcabs = self.wavelet_transf(self.Valpha)
			self.wtcthr = self.thresholding(self.wtcabs)
			self.maxtab, self.mintab = self.peakdet(self.wtcthr, 0.1)
			floc = self.loc_det(self.maxtab, self.cD4, self.capacitance, self.inductance, self.linelength)
			ftype = self.classification(self.vsignal, self.isignal, self.Ignd)
			
			#print("masuk sini")
			
			self.set_text(self.entry_st, "FAULT DETECTED")
			self.set_text(self.entry_tm, "-")
			self.set_text(self.entry_tf, ftype)
			self.set_text(self.entry_ds, floc)
			self.set_text(self.entry_cr, "-")
		
		def get_allvalue (self):		
			#get value from every integer entry
			self.lt = lt
			self.ind = ind
			self.cap = cap
			self.gd1 = gd1
			self.gd2 = gd2
			
			#function check
			print(self.lt)
			print(self.ind)
			print(self.cap)
			print(self.gd1)
			print(self.gd2)

			return (lt, ind, cap, gd1, gd2)

	class InputPage(tk.Frame):

		def __init__(self, parent, controller):
			
			tk.Frame.__init__(self, parent)
			
			self.controller = controller
			
			title = tk.Label(self, text="FAULT LOCATOR", bg=BACKGROUND, fg=FOREGROUND, font=FONTTYPE1)
			title.pack(pady=10, padx=10)
			
			subtitle1 = tk.Label(self, text="Input Page", bg=BACKGROUND, fg=FOREGROUND, font=FONTTYPE2)
			subtitle1.pack(pady=10, padx=10)
			
			subtitle2 = tk.Label(self, text="Line Properties", bg=BACKGROUND, fg=FOREGROUND, font=FONTTYPE2)
			subtitle2.pack(pady=10, padx=10)
			
			container6 = tk.Frame(self)
			container6.pack(side=tk.TOP, padx=10, pady=10)
			length_label = tk.Label(container6, text="Length", anchor=tk.W)
			length_label.pack(side = tk.LEFT)
			self.entry_lt = tk.Entry(container6)
			self.entry_lt.pack(side=tk.LEFT)
			
			container7 = tk.Frame(self)
			container7.pack(side=tk.TOP, padx=10, pady=10)
			inductance_label = tk.Label(container7, text="Inductance", anchor="w")
			inductance_label.pack(side = tk.LEFT)
			self.entry_ind = tk.Entry(container7)
			self.entry_ind.pack(side=tk.LEFT)
			
			container8 = tk.Frame(self)
			container8.pack(side=tk.TOP, padx=10, pady=10)
			capacitance_label = tk.Label(container8, text="Capacitance", anchor="w")
			capacitance_label.pack(side = tk.LEFT)
			self.entry_cap = tk.Entry(container8)
			self.entry_cap.pack(side=tk.LEFT)
			
			subtitle3 = tk.Label(self, text="Power House Properties", bg=BACKGROUND, fg=FOREGROUND, font=FONTTYPE2)
			subtitle3.pack(pady=10, padx=10)
			
			container9 = tk.Frame(self)
			container9.pack(side=tk.TOP, padx=10, pady=10)
			gardu1_label = tk.Label(container9, text="Coordinate 1 (start)", anchor=tk.W)
			gardu1_label.pack(side = tk.LEFT)
			self.entry_gd1 = tk.Entry(container9)
			self.entry_gd1.pack(side=tk.LEFT)
			
			container10 = tk.Frame(self)
			container10.pack(side=tk.TOP, padx=10, pady=10)
			gardu2_label = tk.Label(container10, text="Coordinate 2 (end)", anchor=tk.W)
			gardu2_label.pack(side = tk.LEFT)
			self.entry_gd2 = tk.Entry(container10)
			self.entry_gd2.pack(side=tk.LEFT)
			
			container11 = tk.Frame(self)
			container11.pack(side=tk.TOP, padx=10, pady=10)
			pole_label = tk.Label(container11, text="Number of Pole", anchor="w")
			pole_label.pack(side = tk.LEFT)
			self.entry_pl = tk.Entry(container11)
			self.entry_pl.pack(side=tk.LEFT)
			
			button1 = ttk.Button(self, text="input pole number", command = lambda:[self.input_jumlah()])
			button1.pack()
			
		def input_jumlah(self):
			global lt
			global cap
			global ind
			global gd1
			global gd2
			
			lt = int(self.entry_lt.get())
			cap = float(self.entry_cap.get())
			ind = float(self.entry_ind.get())
			gd1 = int(self.entry_gd1.get())
			gd2 = int(self.entry_gd2.get())
			
			jumlahst = self.entry_pl.get()
			jumlah = int(jumlahst)
				
			label = []
			entry_x = []
			entry_y = []
			frames = []
			
			for i in range(jumlah):
				frames.append(tk.Frame(self))
				teks = "Tiang " + str(i)
				label.append(tk.Label(frames[i], text=teks))
				entry_x.append(tk.Entry(frames[i]))
				entry_y.append(tk.Entry(frames[i]))
				
			for i in range(jumlah):
				frames[i].pack(side=tk.TOP, pady=10)
				label[i].pack(side=tk.LEFT, padx=10)
				entry_x[i].pack(side=tk.LEFT, padx=10)
				entry_y[i].pack(side=tk.LEFT)
				
			button2 = ttk.Button(self, text="Submit", command=lambda: [self.controller.show_frame(MainPage)])
			button2.pack()
			
	root = Tk()
	app = MainApp(root)
	app.update()
	
	
def ReadSerial():
	global faultdetect
	global faultfilename
	global buzzer

	buzzer = False
	LedPIN = 18

	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	GPIO.setup(LedPIN, GPIO.OUT)

	port        = '/dev/ttyACM0' #Nama port usb yang digunakan
	baudrate    = 9600
	
	currentthreshold = 5

	ser = Serial(port,baudrate)
	
	#Menginisiasi folder utama perangkat
	home	= os.path.join(os.getcwd(),'TA171801018') 
	if not os.path.exists(home): 
		os.makedirs(home)
	os.chdir(home)
	
	while True:
		#Program Looping
		read = ser.readline()
		
		iphaseA = float(read)
		iphaseB = 0
		iphaseC = 0

		nowtime = str(datetime.now())
		tmicrosecond = str(datetime.now().microsecond)
		tsecond = str(datetime.now().second)
		time = tsecond +'.' + tmicrosecond 
		
		#Membuat directory/folder penyimpanan berdasarkan waktu 
		activdir = os.path.join(home,str(datetime.now().strftime('%Y/%B/%d/%H')))
		if not os.path.exists(activdir):
			os.makedirs(activdir)
		os.chdir(activdir)

		#Menyimpan dalam file penyimpanan
		filename = str(datetime.now().strftime('%M%S'))+'.csv'
		f = open(filename,'a') 
		writedata = time+', '+str(read)
		f.write(writedata)
		f.close()

		# Deteksi Fault		
		if ((currentthreshold < abs(iphaseA)) or (currentthreshold < abs(iphaseB)) or (currentthreshold < abs(iphaseC))) and not(faultdetect) :
			faultdetect = True
			faultfilename = "BG30.csv"
			buzzer = True
			print ("Fault Detected")
				
		if (buzzer):
			GPIO.output(LedPIN, GPIO.HIGH)
		else :
			GPIO.output(LedPIN, GPIO.LOW)

		#Menghapus Folder Lama
		lasthour = datetime.now() - relativedelta(hours=1)
		lasthourdir = os.path.join(home,str(lasthour.strftime('%Y/%B/%d/%H')))
		if os.path.exists(lasthourdir):
			shutil.rmtree(lasthourdir)
		
if __name__ == "__main__":
	p1	= threading.Thread(target=ReadSerial,args=())
	p2	= threading.Thread(target=GUI,args=())
	
	p1.start()
	p2.start()
	
	p1.join()
	p2.join()
