import moviepy.editor as mp
from  moviepy.editor import ColorClip,TextClip,AudioFileClip
import requests
import os
from constants import *
import random
import subprocess as sp

VIDEO_PATH= os.path.join(MEDIA_PATH, VIDEO_BASENAME)
GIF_PATH= os.path.join(MEDIA_PATH, GIF_BASENAME)
os.makedirs(VIDEO_PATH, exist_ok=True)
os.makedirs(GIF_PATH, exist_ok=True)

GIPHY_ENDPOINT="https://api.giphy.com/v1/gifs/search"

"""
Download new gifs to keep the gif stockpile fresh, adds key value pair to redis
"""
def loadRedisWithGIFS(redis_server, api_key, endpoint=GIPHY_ENDPOINT, search_term=GIF_SEARCH_TERM, limit=50):
    params = {
        'q': search_term,
        'api_key': api_key,
        'rating': 'pg-13', #general,
        'limit': limit
    }
    res = requests.get(url=endpoint, params=params)
    retcode = res.json()['meta']['status']

    # download the gif    
    for gif in res.json()['data']:
        gif_id = "gif:" + gif['id']
        
        # gets the original version's direct url.
        gif_url = gif['images']['original']['url']
        
        # only add new gifs to the redis server
        if not redis_server.exists(gif_id):
            redis_server.hset(gif_id, "gif_url", gif_url)
            redis_server.hset(gif_id, "visited", 0)

    return retcode, gif_id, gif_url

def getNotVisitedHelper(redis_server):
    cursor = 0
    while True: 
        cursor, keys = redis_server.scan(cursor=cursor, match='gif:*', count=100)
        for key in keys:
            visited = redis_server.hget(key, 'visited')
            if visited == b'0':
                # found key that has not been visited
                value = redis_server.hgetall(key)
                
                return key, value[b'gif_url'].decode('utf-8')
        if cursor == 0:
            break 
    return "NULL"

"""
Searches redis for new gifs that have visited flag set to 0, returns the gif path from the url of that gif
if we cant find anything, then we will have to call loadRedisWithGIFS again, or with another search term
"""
def getNotVisited(redis_server, api_key):
    
    res = getNotVisitedHelper(redis_server)
    if res != "NULL":
        return res
    
    # did not find, try to search again:
    loadRedisWithGIFS(redis_server, api_key)
    res = getNotVisitedHelper(redis_server)
    if res != "NULL":
        return res
        
    # still didnt find!!! we will use trending.
    loadRedisWithGIFS(redis_server, api_key, search_term="trending", limit=5)
    res = getNotVisitedHelper(redis_server)
    return res


"""
Helper to download the gif from the url, and save to path
returns output path
"""
def downloadGIF(gif_id, gif_url):
    print("Getting Request for GIF...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(gif_url, headers=headers)
    save_path = os.path.join(GIF_PATH, gif_id.decode('utf-8')[4:] + ".gif")
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Open the file and write the content of the response
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f'GIF saved to {save_path}')
    else:
        print(f'Failed to download GIF. Status code: {response.status_code}')

    return save_path, gif_url

"""
downloads a fresh gif and returns the output path
"""
def getNewGIF(redis_server, api_key):
    
    # get a fresh gif
    key, gif_url = getNotVisited(redis_server, api_key)
    
    output_path, gif_url = downloadGIF(key, gif_url)
    
    # set visited to true
    redis_server.hset(key, "visited", 1)
    return output_path, gif_url
     
def createVideoFromGIF(audio_path, gif_path, yt_vidname):
    
    audio_track = AudioFileClip(audio_path)

    #dark background
    hdres = [1280, 720]
    
    mellow_colors = [
        [255, 165, 0],    # Mellow Orange
        [173, 216, 230],  # Mellow Blue
        [204, 153, 255],  # Mellow Purple
        [255, 218, 185],  # Mellow Peach
        [230, 230, 250],  # Mellow Lavender
        [189, 252, 201],  # Mellow Mint
        [200, 162, 200],  # Mellow Lilac
        [244, 164, 96]    # Mellow Sand
    ]
    
    bg_clip = ColorClip(size = hdres, color = random.choice(mellow_colors)).set_duration(audio_track.duration)

    #selected GIF
    animated_gif = (mp.VideoFileClip(gif_path)
            .resize(width=int(0.75 * bg_clip.size[0]), height=int(0.75 * bg_clip.size[1]))
            .loop()
            .set_duration(audio_track.duration)
            .set_pos(("center","center")))

    #custom made formula to set words below the animated GIF
    var_y = 0.5 * (bg_clip.size[1] - animated_gif.size[1])
    new_y = animated_gif.size[1] + 1.25 * var_y
    new_x = "center" 

    title_clip = TextClip(txt=yt_vidname, fontsize=20, font='Palatino-Italic', color='white').set_duration(audio_track.duration)
    title = title_clip.loop().set_pos((new_x,new_y))

    setaudioclip = animated_gif.set_audio(audio_track)

    file_basename = yt_vidname.replace(' ', '')
    final = mp.CompositeVideoClip([bg_clip, setaudioclip, title])
    output_path = os.path.join(VIDEO_PATH, file_basename) + ".mp4"
    final.write_videofile(output_path, threads=1, codec="libx264")
    
    return output_path


def uploadToYoutube(yt_vidpath, yt_vidname, gif_url):
    description = \
    """{0}
Hey guys! This video was made entirely using a pipeline which tracks a spotify playlist, edits the music and video and uploads slowed + reverb versions of the song onto youtube. 
The pipeline is running on an EC2 instance deployed on AWS.
This project's source code is here: https://github.com/zexianchoo/slowedwithreverb

GIPHY was used for the gifs.
The GIF url is here: {1}

I do not monetize these videos. All credits go to the respective artists. 

Check out my website here: zexianchoo.github.io :)
    """.format(yt_vidname, gif_url)
                        
    upload_video_path = os.path.join("src", "uploadvideo.py")
    command = (
        'python {0} '
        '--file="{1}" '
        '--title="{2}" '
        '--description="{3}" '
        '--keywords="Slowed,reverb,with,slowedwithreverb,aesthetic,coding,github,slowed + reverb,chill,vibes,{1}" '
        '--category=10 '
        '--privacyStatus="public" '
        '--noauth_local_webserver'
    ).format(upload_video_path, yt_vidpath, yt_vidname, description)
    
    retcode = sp.call(command, shell=True)
    return retcode

