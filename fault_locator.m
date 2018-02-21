%Constant
ind = 1.07 * 1e-3; %H/km
cap = 10.398 * 1e-9; %F/km
fs = 2e6;
orde = 16;


%Voltage signal load and processing
T = [1 1 1; 2 -1 -1; 0 sqrt(3) sqrt(3)]; %Matriks Transformasi Clarke
signal = csvread('V_AtoG_2MHz_30km_resistance 1 (fault only).csv');%Load sinyal tegangan
Smode = signal * T; %Transformasi ke tegangan modal
x1 = Smode(:,1); x2 = Smode(:,2); x3 = Smode(:,3);
[c,l] = wavedec(x2, 4, 'db4');%Transformasi Wavelet orde 4 dengan 'db4' untuk sinyal Alpha
[cd1, cd2, cd3, cd4] = detcoef(c,l,[1 2 3 4]);

%plotting
%figure(1); plot(cd4); title('Scale 4');

wtcsq = cd4.^2;
wtcden = wtcsq;
wtcden (wtcsq < 50000) = 0;
%wtcabs = abs(cd4); Opsi lainnya pake absolute
figure(2); plot(wtcsq); title('WTC square');
figure(3); plot(wtcden); title('WTC Square Denoised');

%thresholding
[thr, sorh, keepapp] = ddencmp('den' ,'wv', Smode);
ythard = wthresh(wtcden,'h',thr);
figure(4); plot(ythard); title('Threshold hard');

L = length(cd4); Msq = max(wtcsq);

%Find Peaks
[pks, locs] = findpeaks(ythard);
%plot(sample, ythard, sample(locs), pks, 'or');

[maxValue, indexOfMax] = max(pks);
secIdx = indexOfMax + 1;
secpeak = pks(secIdx);
sample = 1:1:L;

for i = 1:L
    if wtcsq(i) == maxValue
        maxindex = i;
    end
    if wtcsq(i) == secpeak
        secmaxindex = i;
    end
end

%Fault Location Calculation
v = 1/(sqrt(cap * ind));s
deltat = (secmaxindex - maxindex) * orde / fs;
loc = deltat * v / 2;
