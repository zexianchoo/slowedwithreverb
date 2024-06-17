# slowedwithreverb

## If you just want a video created with no uploads nothing i gotchu:

1. run `pip install -r requirements.txt`
2. Download ffmpeg
3. Run the following:
``` bash
python main.py -s "<song name>" -g "<path/to/gif>"
```

For example, `python main.py -s "stress relief" -g "media/gifs/ABCD.gif"`
output will be at `media/videos`.

Be sure to include both params!

As always, you can tune the slowed+reverb settings in `constants.py`
--------
# Pipeline:
  1. Tracks songs from a spotify playlist
  2. Downloads the song from youtube with yt-dl (yt-dlp fork)
  3. Slows + Reverbs the song (Pedalboard)
  4. Downloads GIFS from GIPHY
  5. Creates video, overlaying gif with slowed+reverb audio
  6. Uploads video to youtube

### Create your own slowed with reverb videos here!
  - example: https://www.youtube.com/watch?v=SNfFyMW7zak

# PreReqs:

## Getting your `client_secrets.json`
- Please access https://console.cloud.google.com/ to create your credentials and OAuth 2.0 Client IDS.
- Save the `client_secrets.json` to the root directory.

## Create a  `config.env`
```
SPOTIFY_CLIENT_ID = "..."
SPOTIFY_CLIENT_SECRET = "..."
PLAYLIST_ID = "..."
GIPHY_API = "..."
```
-------

# Usage:

1. Run redis-server on local port 6379 (default).
     - DB which handles saving of which gifs and which songs have been downloaded

2. Run main.py `python main.py` with all of the following configured
     - config.env
       - This includes setting up GIPHY api, as well as spotify API
     - client_secrets.json
       - This includes setting up Google Youtube Data API
     - ffmpeg on PATH or in local directory with some edits to code
     - constants.py
       - Change the reverb / slowed settings as you wish!
There will be a one-time (hopefully) manual sign-in at the beginning for Google's authentication.

3. Change the settings in constants.py as you wish! `argparse` will take precedence over `constants.py`.

``` bash
usage: main.py [-h] [--spotify_client SPOTIFY_CLIENT]
               [--spotify_secret SPOTIFY_SECRET] [--playlist_id PLAYLIST_ID]       
               [--giphy_api GIPHY_API] [--timeout TIMEOUT] [--noupload]
               [--song SONG] [--gif GIF]

Slowed with Reverb Pipeline

options:
  -h, --help            show this help message and exit
  --spotify_client SPOTIFY_CLIENT
                        Spotify API's client id
  --spotify_secret SPOTIFY_SECRET
                        Spotify API's client secret
  --playlist_id PLAYLIST_ID
                        Spotify API's playlist ID (e.g. 37i9dQZF1DZ06evO0KmqXv)    
  --giphy_api GIPHY_API
                        GIPHY API's authorization
  --timeout TIMEOUT     Seconds between upload to youtube
  --noupload, -nu       Flag indicating no upload to youtube
  --song SONG, -s SONG  Single song name (make sure to use double quotes for song  
                        names with spaces e.g. "stress relief")
  --gif GIF, -g GIF     Path to gif
```