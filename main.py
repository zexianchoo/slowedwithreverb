import os
from dotenv import load_dotenv
import redis
import subprocess
import time
import argparse

from src.spotifyapi import authorize, getTopSongs
from src.ytdl import downloadAudio
from src.slowedwreverb import slowedreverb
from src.videocreation import getNewGIF, createVideoFromGIF
from constants import *

global redis_server

# TODO: argparser for easier configurability
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Slowed with Reverb Pipeline')
    parser.add_argument('--spotify_client', type=str, help='Spotify API\'s client id')
    parser.add_argument('--spotify_secret', type=str, help='Spotify API\'s client secret')
    parser.add_argument('--playlist_id', type=str, help='Spotify API\'s playlist ID (e.g. 37i9dQZF1DZ06evO0KmqXv)')
    parser.add_argument('--giphy_api', type=str, help='GIPHY API\'s authorization')
    parser.add_argument('--timeout', type=int, help='Seconds between upload to youtube')
    
    args = parser.parse_args()
    
    # load secrets
    load_dotenv("config.env") 
    
    # create folder to store all of the media
    os.makedirs(MEDIA_PATH, exist_ok=True)
    
    # spin up redis server
    redis_server = redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=1)
    print("Connected to redis_server...")
    
    # main loop
    while True:
        # authorize and get songs from top 50:
        access_token = authorize( \
            os.environ['SPOTIFY_CLIENT_ID'] if os.environ['SPOTIFY_CLIENT_ID'] is not None else args.spotify_client, \
            os.environ['SPOTIFY_CLIENT_SECRET'] if os.environ['SPOTIFY_CLIENT_SECRET'] is not None else args.spotify_secret)
        
        # you can set PLAYLIST_ID to whatever playlist id you want from spotify
        # the default is spotify top 50 global
        top_songs_ret = getTopSongs(access_token, PLAYLIST_ID if PLAYLIST_ID is not None else args.playlist_id) 
        
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
                        gif_path, gif_url = getNewGIF(redis_server, \
                                                      os.environ['GIPHY_API'] if os.environ['GIPHY_API'] is not None else args.giphy_api)
                        
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
                        
                        upload_video_path = os.path.join("src", "uploadvideo.py")
                        command = (
                            'python {0} '
                            '--file="{1}" '
                            '--title="{2}" '
                            '--description="{3}" '
                            '--keywords="Slowed,reverb,with,slowedwithreverb,aesthetic,coding,github{1}" '
                            '--category=10 '
                            '--privacyStatus="public" '
                            '--noauth_local_webserver'
                        ).format(upload_video_path, yt_vidpath, yt_vidname, description)
                        
                        retcode = subprocess.call(command, shell=True)
                        if retcode == 0:
                            print("Uploaded {}!".format(yt_vidname))
                            
                            # ensure unique uploads
                            redis_server.set(search_query, 1)
                            
                            # (TODO: fix busywaits, and probably make an easier config file separate from secrets)
                            time.sleep(TIMEOUT if TIMEOUT is not None else args.timeout)
                        else:
                            print("Error in uploading...")


    
    
    