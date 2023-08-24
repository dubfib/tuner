# library import for required libraries
import numpy as np
import sounddevice as sd
import aubio
import time
from scipy.signal import savgol_filter

# tuning freq for each note in an object
# from https://pages.mtu.edu/~suits/notefreqs.html
tuning_frequencies = {
    'E5': 659.25,
    'A4': 440.00,
    'D4': 293.66,
    'G3': 196.00,
}

# to track cent diff and current note
min_cent_difference = float('inf')
min_cent_note_status = ""

# calc nearest freq and get cent diff
def find_nearest_tuning_frequency(frequency):
    nearest_note = min(tuning_frequencies, key=lambda note: abs(tuning_frequencies[note] - frequency))
    corrected_cent_difference = 1200 * np.log2(frequency / tuning_frequencies[nearest_note])
    return nearest_note, corrected_cent_difference

# to decide if the note is sharp or flat depending on cent diff (by 5)
def get_note_status(cent_difference):
    if cent_difference > 5:
        return "make flat"
    elif cent_difference < -5:
        return "make sharp"
    else:
        return "in tune"

# callback for audio input, used for audio input stream constructor
# yes i know we don't use frames or callback_time but it crashes without
# it in the audio input stream constructor...
def audio_callback(indata, frames, callback_time, status):
    global min_cent_difference
    global min_cent_note_status
    
    if status:
        print(status)
    
    samples = indata[:, 0]
    
    # pitch detection things.. makes more accurate
    pitch_o = aubio.pitch("yinfft", 2048, 2048, sample_rate)
    pitch_o.set_unit("Hz")
    pitch_o.set_tolerance(0.8)
    
    pitch_sum = 0
    num_frames = 0
    
    # calc the average pitch in blocks
    for i in range(0, len(samples), block_size):
        pitch = pitch_o(samples[i:i+block_size])[0]
        if pitch != 0:
            pitch_sum += pitch
            num_frames += 1
            
    if num_frames > 0:
        average_pitch = pitch_sum / num_frames
        
        # find nearest freq and calc cent diff
        nearest_note, cent_difference = find_nearest_tuning_frequency(average_pitch)
        note_status = get_note_status(cent_difference)
        
        print(f"freq: {average_pitch:.2f}hz, note: {nearest_note}, cent diff: {cent_difference:.2f} ({note_status})")
        
        # update min cent diff
        if cent_difference < min_cent_difference:
            min_cent_difference = cent_difference
            min_cent_note_status = note_status
        
        cent_differences.append((cent_difference, time.time()))

# define audio settings
sample_rate = 44100
block_size = 2048

# store cent differences from the mic pick up
cent_differences = []

# define audio interval length
time_interval = 2.5

# add the start time into a var
start_time = time.time()

# start the audio input stream
with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate, blocksize=block_size):
    print("violin tuner started, awaiting input")
    
    try:
        # run the audio input for 2.5 sec
        while True:
            if time.time() - start_time >= time_interval:
                break
            sd.sleep(100)
    except KeyboardInterrupt:
        pass

# output the lowest cent and if the general pick ups were sharp or flat
print(f"lowest cent: {min_cent_difference:.2f} ({min_cent_note_status})")