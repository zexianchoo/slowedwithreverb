import os
from dotenv import load_dotenv, dotenv_values
import redis
from spotifyapi import authorize, getTopSongs
from ytdl import downloadAudio


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
    redis_server = redis.Redis(host='localhost', port=6379, decode_responses=True)

    # authorize and get songs from top 50:
    access_token = authorize(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
    top_songs_ret = getTopSongs(access_token, os.environ['PLAYLIST_ID'])
    
    if top_songs_ret.status_code != 200:
        print("Error occurred! Caught status code: ", top_songs_ret.status_code)
        shutdown()
    
    # parse json
    top_songs = top_songs_ret.json()
    for tr in top_songs['items']:
        track = tr['track']
        downloadAudio(track)
        break
        
    shutdown()


    
    
    