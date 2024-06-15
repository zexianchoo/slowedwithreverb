from requests import get
from yt_dlp import YoutubeDL
import os

# create the out path to store the audio files
OUT_PATH="./audiofiles"
os.makedirs(OUT_PATH, exist_ok=True)
"""
Uses yt-dlp to download audio files into the outpath.
"""
def downloadAudio(track):
    final_filename = None
    
    artist = track['artists'][0]['name'].replace(' ', '')
    output_filename = "{0}/{1}_{2}".format(OUT_PATH, artist, track['name']).replace(' ', '')
    search_query = "{0} {1} audio".format(track['name'], artist)
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