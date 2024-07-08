from dotenv import load_dotenv
from datetime import datetime
from pytz import timezone as pytz_timezone
from playlists import WEATHER_PLAYLISTS 
from flask import Flask, render_template, request, jsonify
import json 
import pytz
import requests
load_dotenv()
import random
from datetime import timezone
from datetime import timezone
from datetime import datetime, timezone
from flask import Flask
from datetime import timedelta




app = Flask(__name__)

# Replace with your OpenWeatherMap API key
OPENWEATHERMAP_API_KEY = "71742e7f9e446671bbc4fb40b66f8045"
AIR_QUALITY_API_KEY = "71742e7f9e446671bbc4fb40b66f8045"  # You can use the same key for both services

# Import the SpotifyCategory class from the spotify_integration file
from spotify_integration import SpotifyCategoryHandler


# Create an instance of the SpotifyCategory class
spotify_category = SpotifyCategoryHandler()



# Load air quality data from JSON file
try:
    with open('air_quality_data.json', 'r') as file:
        file_content = file.read()
        if not file_content:
            raise ValueError("JSON file is empty")

        suggestions_data = json.loads(file_content).get("suggestions", {})
except (json.decoder.JSONDecodeError, ValueError) as e:
    print(f"Error loading JSON file: {e}")
    suggestions_data = {}

def get_hourly_forecast(latitude, longitude):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': OPENWEATHERMAP_API_KEY,
        'units': 'metric'
    }

    response = requests.get(url=base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        # Extract relevant information from the forecast data
        hourly_forecast = []
        for forecast in data.get('list', []):
            hourly_forecast.append({
                'timestamp': forecast['dt'],
                'temperature': forecast['main']['temp'],
                'condition': forecast['weather'][0]['main'],
                'description': forecast['weather'][0]['description'],
                'icon': forecast['weather'][0]['icon']
            })

        return hourly_forecast
    else:
        return None
    
def timestamp_to_localtime(timestamp):
    # Assuming the timestamp is in UTC
    utc_time = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
    # Convert to Indian Standard Time (IST)
    local_time = utc_time.astimezone(timezone(timedelta(hours=5, minutes=30)))
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['timestamp_to_localtime'] = timestamp_to_localtime
app.jinja_env.filters['pytz_timezone'] = pytz_timezone
@app.route('/', methods=['GET', 'POST'])
def index():
    city = None
    weather_data = {}
    aqi_data = None
    hourly_forecast = None
    playlist_url = None

    if request.method == 'POST':
        city = request.form['city']
        coordinates = get_coordinates(city)

        if coordinates:
            latitude, longitude = coordinates
            weather_data = get_weather(latitude, longitude)
            aqi_data = get_air_quality(latitude, longitude)
            hourly_forecast = get_hourly_forecast(latitude, longitude)

            # Obtain Spotify API token
            spotify_token = spotify_category._get_token()
            print("Spotify token:", spotify_token)  # Debugging print

            # Get a random Spotify playlist URL based on weather description
            if weather_data and 'weather' in weather_data:
                weather_description = weather_data['weather'].get('description', '').lower()
                print("Weather description:", weather_description)  # Debugging print
                playlist_url = spotify_category.get_random_playlist(spotify_token, weather_description)
                print("Playlist URL:", playlist_url)  # Debugging print

    print("Weather Data:", weather_data)  # Debugging print

    return render_template('index.html', city=city, weather_data=weather_data, aqi_data=aqi_data, hourly_forecast=hourly_forecast, playlist_url=playlist_url, WEATHER_PLAYLISTS=WEATHER_PLAYLISTS)

def get_air_quality(latitude, longitude):
    base_url = "https://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': AIR_QUALITY_API_KEY
    }

    response = requests.get(url=base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        aqi_level = str(data['list'][0]['main']['aqi'])
        aqi_data = {
            'coord': data['coord'],
            'aqi': data['list'][0]['main']['aqi'],
            'components': data['list'][0]['components'],
            'particles': {
                'pm2_5': {
                    'health_concern': get_health_concern(data['list'][0]['components']['pm2_5']),
                    'description': 'Fine Particulate Matter are inhalable pollutant particles with a diameter less than 2.5 micrometers that can enter the lungs and bloodstream, resulting in serious health issues. The most severe impacts are on the lungs and heart. Exposure can result in coughing or difficulty breathing, aggravated asthma, and the development of chronic respiratory disease.',
                    'index': data['list'][0]['components']['pm2_5']
                },
                'pm10': {
                    'health_concern': get_health_concern(data['list'][0]['components']['pm10']),
                    'description': 'Particulate Matter are inhalable pollutant particles with a diameter less than 10 micrometers. Particles that are larger than 2.5 micrometers can be deposited in airways, resulting in health issues. Exposure can result in eye and throat irritation, coughing or difficulty breathing, and aggravated asthma. More frequent and excessive exposure can result in more serious health effects.',
                    'index': data['list'][0]['components']['pm10']
                },
                'co': {
                    'health_concern': get_health_concern(data['list'][0]['components']['co']),
                    'description': 'Carbon Monoxide is a colorless and odorless gas. When inhaled at high levels, it can cause headache, nausea, dizziness, and vomiting. Repeated long-term exposure can lead to heart disease.',
                    'index': data['list'][0]['components']['co']
                },
                'o3': {
                    'health_concern': get_health_concern(data['list'][0]['components']['o3']),
                    'description': 'Ground-level Ozone can aggravate existing respiratory diseases and also lead to throat irritation, headaches, and chest pain.',
                    'index': data['list'][0]['components']['o3']
                },
                'no2': {
                    'health_concern': get_health_concern(data['list'][0]['components']['no2']),
                    'description': 'Breathing in high levels of Nitrogen Dioxide increases the risk of respiratory problems. Coughing and difficulty breathing are common, and more serious health issues such as respiratory infections can occur with longer exposure.',
                    'index': data['list'][0]['components']['no2']
                },
                'so2': {
                    'health_concern': get_health_concern(data['list'][0]['components']['so2']),
                    'description': 'Exposure to Sulfur Dioxide can lead to throat and eye irritation and aggravate asthma as well as chronic bronchitis.',
                    'index': data['list'][0]['components']['so2']
                },
                'nh3': {
                    'health_concern': get_health_concern(data['list'][0]['components']['nh3']),
                    'description': 'Ammonia exposure can cause irritation of the eyes, nose, and throat. High levels can lead to coughing and wheezing.',
                    'index': data['list'][0]['components']['nh3']
                }
            },
            'suggestions': suggestions_data.get(aqi_level, {}),
        }
        return aqi_data
    else:
        return None



@app.route('/suggestions')
def suggestions():
    city = None
    aqi_data = None

    if request.method == 'GET':
        city = request.args.get('city')
        coordinates = get_coordinates(city)

        if coordinates:
            latitude, longitude = coordinates
            aqi_data = get_air_quality(latitude, longitude)

    return render_template('suggestions.html', city=city, aqi_data=aqi_data)



def get_coordinates(city):
    base_url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {
        'q': city,
        'appid': OPENWEATHERMAP_API_KEY
    }

    response = requests.get(url=base_url, params=params)
    data = response.json()

    if response.status_code == 200 and data:
        location = data[0]  # Assuming the first result is the desired one
        return location['lat'], location['lon']
    else:
        return None

def get_weather(latitude, longitude):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': OPENWEATHERMAP_API_KEY,
        'units': 'metric'
    }

    response = requests.get(url=base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        weather_data = {
            'location': {
                'name': data['name'],
                'country': data['sys']['country'],
                'timezone': pytz.timezone('Asia/Kolkata'),
                'latitude': data['coord']['lat'],
                'longitude': data['coord']['lon'],
                'localtime': datetime.fromtimestamp(data['dt'], pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
            },
            'current': {
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max'],
                'pressure': data['main']['pressure'],
                'humidity': data['main']['humidity']
            },
            'weather': {
                'condition': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'icon': data['weather'][0]['icon']
            },
            'visibility': data['visibility'],
            'wind': {
                'speed': data['wind']['speed'],
                'deg': data['wind']['deg']
            },
            'clouds': {
                'all': data['clouds']['all']
            },
            'timestamp': data['dt'],
            'sys': {
                'type': data['sys']['type'],
                'id': data['sys']['id'],
                'sunrise': data['sys']['sunrise'],
                'sunset': data['sys']['sunset']
            },
            'id': data['id'],
            'cod': data['cod']
        }

        return weather_data
    else:
        print(f"Error getting weather data. Status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None

def get_air_quality(latitude, longitude):
    base_url = "https://api.openweathermap.org/data/2.5/air_pollution"
    params = {
        'lat': latitude,
        'lon': longitude,
        'appid': AIR_QUALITY_API_KEY
    }

    response = requests.get(url=base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        aqi_data = {
            'coord': data['coord'],
            'aqi': data['list'][0]['main']['aqi'],
            'components': data['list'][0]['components'],
            'particles': {
                'pm2_5': {
                    'health_concern': get_health_concern(data['list'][0]['components']['pm2_5']),
                    'description': 'Fine Particulate Matter are inhalable pollutant particles with a diameter less than 2.5 micrometers that can enter the lungs and bloodstream, resulting in serious health issues. The most severe impacts are on the lungs and heart. Exposure can result in coughing or difficulty breathing, aggravated asthma, and the development of chronic respiratory disease.',
                    'index': data['list'][0]['components']['pm2_5']
                },
                'pm10': {
                    'health_concern': get_health_concern(data['list'][0]['components']['pm10']),
                    'description': 'Particulate Matter are inhalable pollutant particles with a diameter less than 10 micrometers. Particles that are larger than 2.5 micrometers can be deposited in airways, resulting in health issues. Exposure can result in eye and throat irritation, coughing or difficulty breathing, and aggravated asthma. More frequent and excessive exposure can result in more serious health effects.',
                    'index': data['list'][0]['components']['pm10']
                },
                'co': {
                    'health_concern': get_health_concern(data['list'][0]['components']['co']),
                    'description': 'Carbon Monoxide is a colorless and odorless gas. When inhaled at high levels, it can cause headache, nausea, dizziness, and vomiting. Repeated long-term exposure can lead to heart disease.',
                    'index': data['list'][0]['components']['co']
                },
                'o3': {
                    'health_concern': get_health_concern(data['list'][0]['components']['o3']),
                    'description': 'Ground-level Ozone can aggravate existing respiratory diseases and also lead to throat irritation, headaches, and chest pain.',
                    'index': data['list'][0]['components']['o3']
                },
                'no2': {
                    'health_concern': get_health_concern(data['list'][0]['components']['no2']),
                    'description': 'Breathing in high levels of Nitrogen Dioxide increases the risk of respiratory problems. Coughing and difficulty breathing are common, and more serious health issues such as respiratory infections can occur with longer exposure.',
                    'index': data['list'][0]['components']['no2']
                },
                'so2': {
                    'health_concern': get_health_concern(data['list'][0]['components']['so2']),
                    'description': 'Exposure to Sulfur Dioxide can lead to throat and eye irritation and aggravate asthma as well as chronic bronchitis.',
                    'index': data['list'][0]['components']['so2']
                },
                'nh3': {
                    'health_concern': get_health_concern(data['list'][0]['components']['nh3']),
                    'description': 'Ammonia exposure can cause irritation of the eyes, nose, and throat. High levels can lead to coughing and wheezing.',
                    'index': data['list'][0]['components']['nh3']
                }
            },
            'suggestions': suggestions_data.get(str(data['list'][0]['main']['aqi']), {})
        }
        return aqi_data
    else:
        return None
class SpotifyCategory:
    def __init__(self):
        self.weather_categories = {
            'clouds': WEATHER_PLAYLISTS['cloud'],
            'thunderstorm': WEATHER_PLAYLISTS['thunderstorm'],
            'rain': WEATHER_PLAYLISTS['rain'],
            'snow': WEATHER_PLAYLISTS['snow'],
            'mist': WEATHER_PLAYLISTS['mist'],
            'smoke': WEATHER_PLAYLISTS['smoke'],
            'haze': WEATHER_PLAYLISTS['haze'],
            'dust whirls': WEATHER_PLAYLISTS['dust whirls'],
            'fog': WEATHER_PLAYLISTS['fog'],
            'sand': WEATHER_PLAYLISTS['sand'],
            'dust': WEATHER_PLAYLISTS['dust'],
            'ash': WEATHER_PLAYLISTS['ash'],
            'squalls': WEATHER_PLAYLISTS['squalls'],
            'tornado': WEATHER_PLAYLISTS['tornado'],
            'clear sky': WEATHER_PLAYLISTS['clear sky'],
        }
        # Define a default playlist for unknown weather descriptions
        self.default_playlist = WEATHER_PLAYLISTS['default']

    def get_random_playlist(self, weather_description):
        # Convert to lowercase
        weather_description = weather_description.lower()

        # Get the playlist for the given weather description
        playlists = self.weather_categories.get(weather_description, [])

        # Choose a random playlist from the available ones, or use the default
        if playlists:
            return random.choice(playlists)
        else:
            return self.default_playlist


def get_suggestions(aqi_level):
    suggestions_data = {
        'Good': {
            'recommendation': 'Air quality is good. Enjoy outdoor activities!',
            'message': 'No health impacts. Air quality is considered satisfactory, and air pollution poses little or no risk.'
        },
        'Moderate': {
            'recommendation': 'You can engage in usual outdoor activities.',
            'message': 'Air quality is acceptable; however, some pollutants may be a concern for a very small number of people who are unusually sensitive to air pollution.'
        },
        'Unhealthy for Sensitive Groups': {
            'recommendation': 'Sensitive groups should limit prolonged outdoor exertion.',
            'message': 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.'
        },
        'Unhealthy': {
            'recommendation': 'Everyone may begin to experience adverse health effects, and members of sensitive groups may experience more serious effects.',
            'message': 'Health alert: everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.'
        },
        'Very Unhealthy': {
            'recommendation': 'Health alert: everyone may experience more serious health effects.',
            'message': 'Health warnings of emergency conditions. The entire population is more likely to be affected.'
        },
        'Hazardous': {
            'recommendation': 'Health warning of emergency conditions. The entire population is likely to be affected.',
            'message': 'Health warnings of emergency conditions; the entire population is more likely to be affected.'
        }
    }

    return suggestions_data.get(aqi_level, None)

def get_health_concern(index):
    if 0 <= index <= 50:
        return 'Good'
    elif 50 < index <= 100:
        return 'Moderate'
    elif 100 < index <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif 150 < index <= 200:
        return 'Unhealthy'
    elif 200 < index <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

if __name__ == '__main__':
    app.run(debug=True)
