import os
from dotenv import load_dotenv, dotenv_values
import redis
from spotifyapi import authorize, getTopSongs
from ytdl import downloadAudio
from slowedwreverb import slowedreverb
from videocreation import getNewGIF, createVideoFromGIF

global redis_server

def shutdown():
    # shutdown the Redis server
    try:
        redis_server.shutdown()
        print("Redis server shutdown.")
        exit(0)
    except redis.exceptions.ConnectionError:
        print("Redis server is already shut down or not reachable.")
        exit(1)
        
if __name__ == "__main__":
    
    # load secrets
    load_dotenv("config.env") 
    
    # spin up redis server
    redis_server = redis.Redis(host='127.0.0.1', port=6379, socket_connect_timeout=1)
    print("redis_server started!")
    
    # authorize and get songs from top 50:
    access_token = authorize(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
    top_songs_ret = getTopSongs(access_token, os.environ['PLAYLIST_ID'])
    
    if top_songs_ret.status_code != 200:
        print("Error occurred! Caught status code: ", top_songs_ret.status_code)
        # shutdown()
    
    # parse json
    top_songs = top_songs_ret.json()
    for tr in top_songs['items']:
        track = tr['track']
        search_query = "{0} {1}".format(track['name'], track['artists'][0]['name'])
        
        # testing only
        if redis_server.exists(search_query):
            redis_server.delete(search_query)
            
        # searches if we have done this before
        if not redis_server.exists(search_query):
            
            # download audio and save to redis if it was successful
            retcode, audio_path = downloadAudio(track)
            if (retcode == 0):
                redis_server.set(search_query, 1)
        
                # apply slowed w reverb to it
                slowed_audio_path = slowedreverb(audio_path, )
                if os.path.isfile(slowed_audio_path):
                    print("Successfully slowed {0}! Saved to {1}".format(search_query, slowed_audio_path))
                    
                    # now, we will create the video
                    # get a new GIF:
                    gif_path = getNewGIF(redis_server, os.environ['GIPHY_API'])
                    
                    yt_vidname = "{0} - {1} (slowed & reverbed)".format(track['name'], track['artists'][0]['name'])
                    createVideoFromGIF(slowed_audio_path, gif_path, yt_vidname)
                    break
                    
                    
                    redis_server.set("search_query", 1)
                
        
    # shutdown()


    
    
    