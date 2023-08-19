import numpy as np
import sounddevice as sd
import aubio
import time
from scipy.signal import savgol_filter

tuning_frequencies = {
    'E4': 329.63,
    'A4': 440.00,
    'D4': 293.66,
    'G3': 196.00,
}

correction_factors = {
    'E4': 0,
    'A4': 0,
    'D4': 0,
    'G3': 0,
}

min_cent_difference = float('inf')
min_cent_note_status = ""

def find_nearest_tuning_frequency(frequency):
    nearest_note = min(tuning_frequencies, key=lambda note: abs(tuning_frequencies[note] - frequency))
    corrected_cent_difference = 1200 * np.log2(frequency / tuning_frequencies[nearest_note]) + correction_factors[nearest_note]
    return nearest_note, corrected_cent_difference

def get_note_status(cent_difference):
    if cent_difference > 5:
        return "make flat"
    elif cent_difference < -5:
        return "make sharp"
    else:
        return "in tune"

def audio_callback(indata, frames, callback_time, status):
    global min_cent_difference
    global min_cent_note_status
    
    if status:
        print(status)
    
    samples = indata[:, 0]
    
    pitch_o = aubio.pitch("yinfft", 2048, 2048, sample_rate)
    pitch_o.set_unit("Hz")
    pitch_o.set_tolerance(0.8)
    
    pitch_sum = 0
    num_frames = 0
    
    for i in range(0, len(samples), block_size):
        pitch = pitch_o(samples[i:i+block_size])[0]
        if pitch != 0:
            pitch_sum += pitch
            num_frames += 1
            
    if num_frames > 0:
        average_pitch = pitch_sum / num_frames
        
        nearest_note, cent_difference = find_nearest_tuning_frequency(average_pitch)
        note_status = get_note_status(cent_difference)
        
        print(f"freq: {average_pitch:.2f}hz, note: {nearest_note}, cent diff: {cent_difference:.2f} ({note_status})")
        
        if cent_difference < min_cent_difference:
            min_cent_difference = cent_difference
            min_cent_note_status = note_status
        
        cent_differences.append((cent_difference, time.time()))

sample_rate = 44100
block_size = 2048

cent_differences = []

time_interval = 2.5

start_time = time.time()

with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate, blocksize=block_size):
    print("violin tuner started, awaiting input")
    
    try:
        while True:
            if time.time() - start_time >= time_interval:
                break
            sd.sleep(100)
    except KeyboardInterrupt:
        pass

print(f"lowest cent: {min_cent_difference:.2f} ({min_cent_note_status})")
