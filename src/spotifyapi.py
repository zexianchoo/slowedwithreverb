import requests
import base64

"""
Authenticates with the server and create an access token for future use.

"""
def authorize(client_id, client_secret):
    # URLS
    TOKEN_URL = 'https://accounts.spotify.com/api/token'

    auth_header = base64.urlsafe_b64encode((client_id + ':' + client_secret).encode())
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic %s' % auth_header.decode()
    }

    payload = {
        'grant_type': 'client_credentials',
    }

    # Make a request to the /token endpoint to get an access token
    access_token_request = requests.post(url=TOKEN_URL, data=payload, headers=headers)

    # convert the response to JSON
    access_token_response_data = access_token_request.json()

    # # save the access token
    access_token = access_token_response_data['access_token']
    return access_token


"""
Calls a GET to get all of the most popular songs.
"""
def getTopSongs(access_token, playlist_id):
    NEW_RELEASES = "https://api.spotify.com/v1/playlists/" + str(playlist_id) + "/tracks"
    headers = {
        'Authorization': 'Bearer %s' % access_token
    }
    res = requests.get(url=NEW_RELEASES, headers=headers)
    return res

