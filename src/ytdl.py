from requests import get
from yt_dlp import YoutubeDL
import os
from constants import *

# create the out path to store the audio files
OUT_PATH= os.path.join(MEDIA_PATH, AUDIO_BASENAME)
os.makedirs(OUT_PATH, exist_ok=True)
"""
Uses yt-dlp to download audio files into the outpath.
"""
def downloadAudio(song_name, artist=""):
    
    output_filename = "{0}/{1}_{2}".format(OUT_PATH, artist, song_name).replace(' ', '')
    search_query = "{0} {1} lyrics".format(song_name, artist)
    print(output_filename)
    yt_opts = {
        'noplaylist': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        "outtmpl": output_filename,
        'prefer_ffmpeg': True,
        'verbose': False,
        'quiet': True, 
        'noprogress': True
    }
    with YoutubeDL(yt_opts) as ydl:
        retcode = ydl.download(f"ytsearch:{search_query}" )
        print("output_filename: ", output_filename)
    # return the return code 
    return retcode, output_filename + ".wav"