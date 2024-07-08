import base64
import json
import os
import random
from dataclasses import dataclass
from dotenv import load_dotenv
from requests import post, get
from playlists import WEATHER_PLAYLISTS  # Use an absolute import

load_dotenv()

@dataclass
class SpotifyData:
    CLIENT_ID: str = os.getenv('SPOTIPY_CLIENT_ID')
    CLIENT_SECRET: str = os.getenv('SPOTIPY_CLIENT_SECRET')

class SpotifyAccess(SpotifyData):
    def _get_token(self):
        auth_string = f'{self.CLIENT_ID}:{self.CLIENT_SECRET}'
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"grant_type": "client_credentials"}
        result = post(url, headers=headers, data=data)

        if result.status_code != 200:
            print("Error obtaining token. Status Code:", result.status_code)
            print("Response content:", result.content)
            return None

        json_result = json.loads(result.content)
        token = json_result["access_token"]
        print("Obtained token:", token)  # Debugging print
        return token

    @staticmethod
    def _get_auth_header(token: str):
        return {"Authorization": "Bearer " + token, 'Content-Type': 'application/json'}

class SpotifyCategoryHandler(SpotifyAccess):
    def _search_playlist(self, token: str, playlist_id: str):
        url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        headers = self._get_auth_header(token)
        params = {'market': 'ES'}

        result = get(url, headers=headers, params=params)

        if result.status_code != 200:
            print("Error searching playlist. Status Code:", result.status_code)
            print("Response content:", result.content)
            raise Exception("Nie działa")

        json_result = json.loads(result.content)
        playlist_url = json_result['external_urls']['spotify']
        print("Retrieved playlist_url:", playlist_url)  # Debugging print
        return playlist_url

    def get_random_playlist(self, token: str, weather_desc: str):
        for weather_key in WEATHER_PLAYLISTS.keys():
            if weather_key in weather_desc:
                playlist_id = random.choice(WEATHER_PLAYLISTS[weather_key])[1]
                print("Selected playlist_id:", playlist_id)  # Debugging print
                try:
                    playlist_url = self._search_playlist(token, playlist_id)
                    return playlist_url
                except Exception as e:
                    print("Error retrieving playlist:", str(e))  # Debugging print
                    return None

        # Handle the case where weather_desc doesn't match any playlists
        print("No matching playlist found for weather_desc:", weather_desc)  # Debugging print
        return None

if __name__ == "__main__":
    spotify_handler = SpotifyCategoryHandler()
    token = spotify_handler._get_token()

    if token:
        # Test getting a random playlist
        weather_description = "rainy"
        playlist_url = spotify_handler.get_random_playlist(token, weather_description)
        print("Final Playlist URL:", playlist_url)
