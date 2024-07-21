import os
from dotenv import load_dotenv
import redis
import subprocess
import time
import argparse

from src.spotifyapi import authorize, getTopSongs
from src.ytdl import downloadAudio
from src.slowedwreverb import slowedreverb
from src.videocreation import getNewGIF, createVideoFromGIF, uploadToYoutube
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
    parser.add_argument('--noupload', '-nu', action='store_false', default=True, help='Flag indicating no upload to youtube')
    parser.add_argument('--song', '-s',type=str, help='Single song name (make sure to use double quotes for song names with spaces e.g. "stress relief") ')
    parser.add_argument('--gif', '-g',type=str, help='Path to gif')
    
    args = parser.parse_args()
    
    # load secrets
    load_dotenv("config.env") 
    
    # create folder to store all of the media
    os.makedirs(MEDIA_PATH, exist_ok=True)
    
    # single song
    if args.song is not None:
        if args.gif is None:
            raise ArgumentError("Need a gif path if we are inputting a song.")
        if not os.path.exists(args.gif):
            raise FileNotFoundError("Couldn't find gif file")
        retcode, audio_path = downloadAudio(args.song)
        slowed_audio_path = slowedreverb(audio_path, ROOM_SIZE, DAMPING, WET_LEVEL, DRY_LEVEL, DELAY, SLOWFACTOR)
        yt_vidpath = createVideoFromGIF(slowed_audio_path, args.gif, args.song)
        print("Video has been output at {}".format(yt_vidpath))
        exit(0)
                        
    # playlist:
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
                artist = track['artists'][0]['name'].replace(' ', '')
                retcode, audio_path = downloadAudio(track['name'], artist)
                if (retcode == 0):
            
                    # apply slowed w reverb to it
                    slowed_audio_path = slowedreverb(audio_path, ROOM_SIZE, DAMPING, WET_LEVEL, DRY_LEVEL, DELAY, SLOWFACTOR)
                    if os.path.isfile(slowed_audio_path):
                        print("Successfully slowed {0}! Saved to {1}".format(search_query, slowed_audio_path))
                        
                        # now, we will create the video
                        # get a new GIF:
                        gif_path, gif_url = getNewGIF(redis_server, \
                                                      os.environ['GIPHY_API'] if os.environ['GIPHY_API'] is not None else args.giphy_api)
                        print(gif_path)
                       
                        yt_vidname = "{0} - {1} (slowed + reverb)".format(track['name'], track['artists'][0]['name'])
                        yt_vidpath = createVideoFromGIF(slowed_audio_path, gif_path, yt_vidname)
                        
                        if args.noupload: #defaults to true
                            retcode = uploadToYoutube(yt_vidpath, yt_vidname, gif_url)
                            if retcode == 0:
                                print("Uploaded {}!".format(yt_vidname))
                                
                                # ensure unique uploads
                                redis_server.set(search_query, 1)
                                
                                # (TODO: fix busywaits, and probably make an easier config file separate from secrets)
                                time.sleep(TIMEOUT if TIMEOUT is not None else args.timeout)
                            else:
                                print("Error in uploading...")
                                exit(1)
                        else:
                            print("Video has been output at {}".format(yt_vidpath))


    
    
    