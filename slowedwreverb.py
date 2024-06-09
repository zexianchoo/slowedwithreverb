from pedalboard import Pedalboard, Reverb
import soundfile as sf
import subprocess
import os
import numpy as np
from math import trunc

SLOWED_OUTPATH="./slowed"
os.makedirs(SLOWED_OUTPATH, exist_ok=True)

def slowedreverb(input_file, room_size = 0.75, damping = 0.5, wet_level = 0.08, dry_level = 0.2, delay = 2, slowfactor = 0.08):
    
    # using tmp wav
    if '.wav' not in input_file:
        print('Audio needs to be .wav! Converting...')
        subprocess.call(f'ffmpeg -hide_banner -loglevel error -y -i "{audio}" ./tmp.wav', shell = True)
        audio = './tmp.wav'
        
        audio, sample_rate = sf.read(audio)
        
    else:
        audio, sample_rate = sf.read(input_file)
    sample_rate -= trunc(sample_rate*slowfactor)

    # Add reverb
    board = Pedalboard([Reverb(
        room_size=room_size,
        damping=damping,
        wet_level=wet_level,
        dry_level=dry_level
        )])

    # Add surround sound effects
    effected = board(audio, sample_rate)
    channel1 = effected[:, 0]
    channel2 = effected[:, 1]
    shift_len = delay*1000
    shifted_channel1 = np.concatenate((np.zeros(shift_len), channel1[:-shift_len]))
    combined_signal = np.hstack((shifted_channel1.reshape(-1, 1), channel2.reshape(-1, 1)))

    # get output path
    output_path = os.path.join(SLOWED_OUTPATH, os.path.basename(input_file))
    sf.write(output_path, combined_signal, sample_rate)
    
    return output_path