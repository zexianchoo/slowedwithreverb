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
    
    artist = track['artists'][0]['name']
    output_filename = "{0}/{1}_{2}".format(OUT_PATH, artist, track['name'])
    search_query = "{0} {1}".format(track['name'], artist)
    print(output_filename)
    yt_opts = {
        'noplaylist': True,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        "outtmpl": output_filename,
        'prefer_ffmpeg': True
    }

    with YoutubeDL(yt_opts) as ydl:
        ydl.download(f"ytsearch:{search_query}" )
    
    # return the filepath 
    return 