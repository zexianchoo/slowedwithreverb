import os
from dotenv import load_dotenv
import redis
import subprocess
import time

from src.spotifyapi import authorize, getTopSongs
from src.ytdl import downloadAudio
from src.slowedwreverb import slowedreverb
from src.videocreation import getNewGIF, createVideoFromGIF
from constants import *


global redis_server

if __name__ == "__main__":
    
    # load secrets
    load_dotenv("config.env") 
    
    # create folder to store all of the media
    os.makedirs(MEDIA_PATH, exist_ok=True)
    
    # spin up redis server
    redis_server = redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=1)
    print("Connected to redis_server...")
    
    # authorize and get songs from top 50:
    
    # main loop
    while True:
        access_token = authorize(os.environ['SPOTIFY_CLIENT_ID'], os.environ['SPOTIFY_CLIENT_SECRET'])
        
        # you can set PLAYLIST_ID to whatever playlist id you want from spotify
        # the default is spotify top 50 global
        top_songs_ret = getTopSongs(access_token, os.environ['PLAYLIST_ID']) 
        
        if top_songs_ret.status_code != 200:
            print("Error occurred! Caught status code: ", top_songs_ret.status_code)
            # shutdown()
        
        # parse json
        top_songs = top_songs_ret.json()
        for tr in top_songs['items']:
            track = tr['track']
            search_query = "{0} {1}".format(track['name'], track['artists'][0]['name'])

            # searches if we have done this before
            if not redis_server.exists(search_query):
                
                # download audio and save to redis if it was successful
                retcode, audio_path = downloadAudio(track)
                if (retcode == 0):
            
                    # apply slowed w reverb to it
                    slowed_audio_path = slowedreverb(audio_path, ROOM_SIZE, DAMPING, WET_LEVEL, DRY_LEVEL, DELAY, SLOWFACTOR)
                    if os.path.isfile(slowed_audio_path):
                        print("Successfully slowed {0}! Saved to {1}".format(search_query, slowed_audio_path))
                        
                        # now, we will create the video
                        # get a new GIF:
                        gif_path, gif_url = getNewGIF(redis_server, os.environ['GIPHY_API'])
                        
                        yt_vidname = "{0} - {1} (slowed & reverbed)".format(track['name'], track['artists'][0]['name'])
                        yt_vidpath = createVideoFromGIF(slowed_audio_path, gif_path, yt_vidname)
                        
                        description = \
                            """{0}
Hey guys! This video was made entirely using a pipeline which tracks a spotify playlist, edits the music and video and uploads slowed + reverb versions of the song onto youtube. 
The pipeline is running on an EC2 instance deployed on AWS.
This project's source code is here: github.com/zexianchoo/yt-slowed

GIPHY was used for the gifs, and of course all credits go to the respective artists. 
The GIF url is here: {1}

I do not monetize these videos.

Check out my website here: zexianchoo.github.io :)
                            """.format(yt_vidname, gif_url)
                        command = (
                            'python uploadvideo.py '
                            '--file="{0}" '
                            '--title="{1}" '
                            '--description="{2}" '
                            '--keywords="Slowed,reverb,with,slowedwithreverb,aesthetic,coding,github{1}" '
                            '--category=10 '
                            '--privacyStatus="public" '
                            '--noauth_local_webserver'
                        ).format(yt_vidpath, yt_vidname, description)
                        
                        child = subprocess.Popen(command, stdout=subprocess.PIPE)
                        streamdata = child.communicate()[0]
                        retcode = child.returncode
                        if retcode == 0:
                            print("Uploaded {}!".format(yt_vidname))
                            
                            # ensure unique uploads
                            redis_server.set(search_query, 1)
                            
                            # (TODO: fix busywaits, and probably make an easier config file separate from secrets)
                            time.sleep(86400)
                        else:
                            print("Error in uploading...")


    
    
    