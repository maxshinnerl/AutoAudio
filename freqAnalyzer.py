import sys
import pyaudio
import aubio
import audioop
import math
import numpy as np 
import warnings
warnings.simplefilter("ignore", DeprecationWarning)

#linking together
import KeyChart

FRAME_SIZE = 1024 * 2
FRAMES_PER_FFT = 16 # FFT = Fast Fourier Transform
# FORMAT = pyaudio.paInt16 # Bytes per sample
#FORMAT = pyaudio.paInt16
FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100 # Samples per second
CHUNK = 1024 # Number of data samples (Bytes)
#CHUNK = 2048
RECORD_SECONDS = 5
TOLERANCE = 0.8
WAVE_OUTPUT_NAME = "def_output.wav"

class Note(object):
    def __init__(self, pitch, duration):
        self.pitch = pitch
        self.duration = duration

    def printNote(self):
        print("Pitch: ", self.pitch, "| Duration :", self.duration)

# I don't really understand FFT 
'''
SAMPLES_PER_FFT = FRAME_SIZE * FRAMES_PER_FFT
FREQ_STEP = float(RATE) / SAMPLES_PER_FFT 
'''

# Open the stream
p = pyaudio.PyAudio()

stream = p.open(
    format = FORMAT,
    channels = CHANNELS,
    rate = RATE,
    input = True,
    frames_per_buffer = CHUNK
)


if len(sys.argv) > 1: # If file-name specified on cmdline
    WAVE_OUTPUT_NAME = sys.argv[1] # output file with this name
    outputsink = aubio.sink(WAVE_OUTPUT_NAME, RATE)
else:
    outputsink = aubio.sink(WAVE_OUTPUT_NAME, RATE)

# Aubio's Pitch Recognition
fDetection = aubio.pitch("default", 2048, 1024, RATE)
fDetection.set_unit("Hz")
fDetection.set_silence(-40)
fDetection.set_tolerance(TOLERANCE)




print("* RECORDING")

#NUM_CHUNKS = int((RATE / CHUNK) * RECORD_SECONDS)

'''
# RATE * TIME_RECORDED / CHUNKS = NUM CHUNKS
for i in range(0, NUM_CHUNKS): 
    data = stream.read(CHUNK)
    frames.append(data)
'''

staff = ""
prev_note = "NONE"
my_notes = []

#while stream.is_active()
while True:
    try:
        data = stream.read(CHUNK)

        samples = np.fromstring(data, dtype = aubio.float_type)

        freq = fDetection(samples)[0]
        confidence = fDetection.get_confidence()
        #volume = np.sum(samples**2)/len(samples)
        #f_volume = "{:.6f}".format(volume)
        #rms = audioop.rms(data,1)
        #decibel = 20 * np.log10(rms) #dB = 20 * log10(Amp)
        #print(decibel)
        #uncomment to print original stuff
        #print("{} / {}".format(freq, confidence))


        # if note is too low, don't print
        if outputsink:
            outputsink(samples, len(samples))
        
        if(freq > 25.0):
           #call KeyChart
           idx = KeyChart.findNote(freq)
           #note name
           nn = KeyChart.alternate(idx)
           print("all :", nn)

           #if new note
           if (nn != prev_note):
              prev_note = nn
              
              #create new note
              newNote = Note(nn, 1)
              #append to list of notes
              my_notes.append(newNote)
              #note name formated (added space)
              nnf = nn + " " 
              # Adding the notes to the string
              staff += nnf
#              print(nn)

           #else if same note
           else:
              #increment current note's durationy
              my_notes[len(my_notes)-1].duration += 1              
              
        else:
           prev_note = "NONE"
        

    except KeyboardInterrupt:
        print ("User Ctrl+C. Exiting...")
        break

print("* RECORDING STOPPED")


#CODE TO REMOVE OUTLIER FREQUENCIES

newStaff = ""

#print all recorded notes (shortened)
print("before outlier cleanup")
for noteObj in my_notes:
   noteObj.printNote()

#remove all recorded notes with duration of 1
new_my_notes = []
for noteObj in my_notes:
   if noteObj.duration > 2:
      new_my_notes.append(noteObj)
      noteHolder = noteObj.pitch + " "
      newStaff += noteHolder

#prints correctly
print("after outlier cleanup")
for noteObj in new_my_notes:
   noteObj.printNote()

#following is correct
print("staff: ", staff)         #with duration 1 notes
print("newStaff: ", newStaff)   #without duration 1 notes

#copy newStaff into staff for convenience
staff = newStaff
print("staff: ", staff)         #without duration 1 notes


# Open the file
fh = open('output.ly', "w")


# Setting up the ly file
v = "version"
vn = '"2.18.2"'
version = r"\{} {}".format(v, vn)
l = "language"
lang = '"english"'
language = r"\{} {}".format(l, lang)

# Writing setup into file
fh.write(version + "\n")
fh.write(language + "\n")

# Setting up header block
title = r"""\header {
  title = "My Song"
  composer = "Username"
  tagline = "Copyright: Username"
}"""

# Writing header into file
fh.write(title + "\n")

#Setting up 
relative = r"\{} {}".format("relative","c'")
#fh.write(relative + "\n")
staffh = "{\n\n"
staffh += r"  \clef treble " + staff + "\n"  
staffh += "\n}\n"

fh.write(staffh + "\n")

# Closing stream
stream.stop_stream()
stream.close()
p.terminate()

# Closing file handling
fh.close()
