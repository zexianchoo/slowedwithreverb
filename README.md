# yt-slowed

# Getting your `client_secrets.json`
- Please access https://console.cloud.google.com/ to create your credentials and OAuth 2.0 Client IDS.
- Save the `client_secrets.json` to the root directory.

## `config.env`
```
SPOTIFY_CLIENT_ID = "..."
SPOTIFY_CLIENT_SECRET = "..."
PLAYLIST_ID = "..."
GIPHY_API = "..."
```

There will have to be a manual sign-in at the beginning for Google's authentication.

# Usage:

Run redis-server on local port 6379 (default).
  - db which handles saving of which gifs and which songs have been downloaded

Run main.py `python main.py` with all of the following configured
  - config.env
    - This includes setting up GIPHY api, as well as spotify API
  - client_secrets.json
    - This includes setting up Google Youtube Data API