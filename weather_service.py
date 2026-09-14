"""
Weather Service Module
Handles fetching and parsing meteorological data using Open-Meteo and wttr.in fallback.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import requests


class WeatherFetcherException(Exception):
    """Base exception for weather fetcher errors."""
    pass


class CityNotFoundError(WeatherFetcherException):
    """Raised when the specified city or location is not found."""
    pass


class NetworkConnectionError(WeatherFetcherException):
    """Raised when there is a network connectivity or DNS error."""
    pass


class RequestTimeoutError(WeatherFetcherException):
    """Raised when the weather API request times out."""
    pass


class APIResponseError(WeatherFetcherException):
    """Raised when the API returns an unexpected or malformed response."""
    pass


@dataclass
class WeatherData:
    """Structured representation of current meteorological conditions."""
    city: str
    region: str
    country: str
    temp_c: float
    temp_f: float
    feels_like_c: float
    feels_like_f: float
    humidity: int
    wind_speed_kmph: float
    wind_speed_mph: float
    wind_direction: str
    condition: str
    weather_code: str
    pressure_hpa: float
    uv_index: int
    visibility_km: float
    cloud_cover: int
    observation_time: str


# Mapping weather condition keywords to visual emojis
WEATHER_ICONS = {
    "sunny": "☀️",
    "clear": "☀️",
    "mainly clear": "🌤️",
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "fog": "🌫️",
    "mist": "🌫️",
    "drizzle": "🌦️",
    "freezing drizzle": "🌧️❄️",
    "light rain": "🌦️",
    "moderate rain": "🌧️",
    "heavy rain": "🌧️",
    "rain": "🌧️",
    "freezing rain": "🌧️❄️",
    "snow": "❄️",
    "light snow": "🌨️",
    "heavy snow": "❄️",
    "blizzard": "🌨️",
    "thunder": "⛈️",
    "thunderstorm": "⛈️",
    "shower": "🚿",
}

# WMO Weather interpretation codes (WW) from Open-Meteo
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

COMPASS_POINTS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
]


def degrees_to_compass(degrees: float) -> str:
    """Converts wind direction in degrees to 16-point cardinal compass string."""
    idx = int(round(degrees / 22.5)) % 16
    return COMPASS_POINTS[idx]


def get_weather_icon(condition: str) -> str:
    """Returns an appropriate emoji icon based on weather description."""
    cond_lower = condition.lower()
    for key, icon in WEATHER_ICONS.items():
        if key in cond_lower:
            return icon
    return "🌡️"


class WeatherService:
    """
    High-reliability weather service querying Open-Meteo with wttr.in fallback.
    Both providers are completely free and require zero API keys.
    """

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
    WTTR_URL = "https://wttr.in"
    DEFAULT_TIMEOUT = 8  # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WeatherFetcherCLI/1.1",
            "Accept": "application/json"
        })

    def fetch_weather(self, city: str) -> WeatherData:
        """
        Fetches current weather information for the specified city.
        Tries Open-Meteo first for high speed & reliability, falling back to wttr.in.
        """
        cleaned_city = city.strip()
        if not cleaned_city:
            raise CityNotFoundError("City name cannot be empty.")

        # Try Open-Meteo primary
        try:
            return self._fetch_open_meteo(cleaned_city)
        except CityNotFoundError:
            # If city is definitively not found by geocoder, don't waste time retrying
            raise
        except (NetworkConnectionError, RequestTimeoutError, APIResponseError, Exception):
            # If Open-Meteo has network/API failure, try wttr.in fallback
            try:
                return self._fetch_wttr(cleaned_city)
            except Exception:
                # Re-raise the primary error if both fail
                raise

    def _fetch_open_meteo(self, city: str) -> WeatherData:
        """Queries Open-Meteo Geocoding + Weather endpoints."""
        try:
            geo_resp = self.session.get(
                self.GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as err:
            raise RequestTimeoutError(f"Geocoding request timed out after {self.timeout}s.") from err
        except requests.exceptions.ConnectionError as err:
            raise NetworkConnectionError("Unable to connect to weather server. Check your connection.") from err
        except requests.exceptions.RequestException as err:
            raise APIResponseError(f"Geocoding network error: {err}") from err

        if geo_resp.status_code != 200:
            raise APIResponseError(f"Geocoding returned HTTP {geo_resp.status_code}.")

        try:
            geo_data = geo_resp.json()
        except ValueError as err:
            raise APIResponseError("Invalid JSON from geocoding service.") from err

        results = geo_data.get("results")
        if not results:
            raise CityNotFoundError(f"City '{city}' was not found.")

        location = results[0]
        lat = location.get("latitude")
        lon = location.get("longitude")
        resolved_city = location.get("name", city)
        resolved_region = location.get("admin1", "")
        resolved_country = location.get("country", "")

        # Fetch meteorological conditions
        try:
            weather_resp = self.session.get(
                self.OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,surface_pressure,wind_speed_10m,wind_direction_10m,cloud_cover,visibility",
                    "daily": "uv_index_max",
                    "timezone": "auto"
                },
                timeout=self.timeout
            )
        except requests.exceptions.Timeout as err:
            raise RequestTimeoutError(f"Weather request timed out after {self.timeout}s.") from err
        except requests.exceptions.ConnectionError as err:
            raise NetworkConnectionError("Unable to connect to weather server.") from err
        except requests.exceptions.RequestException as err:
            raise APIResponseError(f"Weather API network error: {err}") from err

        if weather_resp.status_code != 200:
            raise APIResponseError(f"Weather service returned HTTP {weather_resp.status_code}.")

        try:
            weather_data = weather_resp.json()
        except ValueError as err:
            raise APIResponseError("Invalid JSON from weather service.") from err

        current = weather_data.get("current", {})
        daily = weather_data.get("daily", {})

        temp_c = float(current.get("temperature_2m", 0))
        temp_f = (temp_c * 9 / 5) + 32
        feels_like_c = float(current.get("apparent_temperature", temp_c))
        feels_like_f = (feels_like_c * 9 / 5) + 32
        humidity = int(current.get("relative_humidity_2m", 0))
        wind_kmph = float(current.get("wind_speed_10m", 0))
        wind_mph = wind_kmph * 0.621371
        wind_deg = float(current.get("wind_direction_10m", 0))
        wind_dir = degrees_to_compass(wind_deg)

        wmo_code = current.get("weather_code", 0)
        condition_str = WMO_CODE_MAP.get(wmo_code, "Clear")

        pressure = float(current.get("surface_pressure", 1013.25))
        cloud_cover = int(current.get("cloud_cover", 0))
        visibility_m = float(current.get("visibility", 10000.0))
        visibility_km = visibility_m / 1000.0

        uv_list = daily.get("uv_index_max", [])
        uv_index = int(round(uv_list[0])) if uv_list else 0

        obs_time = str(current.get("time", "Just now")).replace("T", " ")

        return WeatherData(
            city=resolved_city,
            region=resolved_region,
            country=resolved_country,
            temp_c=round(temp_c, 1),
            temp_f=round(temp_f, 1),
            feels_like_c=round(feels_like_c, 1),
            feels_like_f=round(feels_like_f, 1),
            humidity=humidity,
            wind_speed_kmph=round(wind_kmph, 1),
            wind_speed_mph=round(wind_mph, 1),
            wind_direction=wind_dir,
            condition=condition_str,
            weather_code=str(wmo_code),
            pressure_hpa=round(pressure, 1),
            uv_index=uv_index,
            visibility_km=round(visibility_km, 1),
            cloud_cover=cloud_cover,
            observation_time=obs_time,
        )

    def _fetch_wttr(self, city: str) -> WeatherData:
        """Fallback querying wttr.in JSON endpoint."""
        url = f"{self.WTTR_URL}/{requests.utils.quote(city)}?format=j1"
        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.exceptions.Timeout as err:
            raise RequestTimeoutError(f"wttr.in timed out after {self.timeout}s.") from err
        except requests.exceptions.ConnectionError as err:
            raise NetworkConnectionError("Unable to connect to weather service.") from err
        except requests.exceptions.RequestException as err:
            raise APIResponseError(f"Network error: {err}") from err

        resp_text_lower = response.text.lower()
        if (
            response.status_code == 404
            or "location not found" in resp_text_lower
            or "unknown location" in resp_text_lower
            or "not found" in resp_text_lower
        ):
            raise CityNotFoundError(f"City '{city}' was not found.")
        elif response.status_code != 200:
            raise APIResponseError(f"Weather service returned HTTP {response.status_code}.")

        try:
            data = response.json()
        except ValueError as err:
            raise APIResponseError("Failed to parse wttr.in JSON.") from err

        current_list = data.get("current_condition", [])
        if not current_list:
            raise CityNotFoundError(f"No data available for '{city}'.")
        current = current_list[0]
        nearest_area = data.get("nearest_area", [{}])[0]

        resolved_city = nearest_area.get("areaName", [{}])[0].get("value", city)
        resolved_region = nearest_area.get("region", [{}])[0].get("value", "")
        resolved_country = nearest_area.get("country", [{}])[0].get("value", "")
        condition = current.get("weatherDesc", [{}])[0].get("value", "Unknown")

        return WeatherData(
            city=resolved_city,
            region=resolved_region,
            country=resolved_country,
            temp_c=float(current.get("temp_C", 0)),
            temp_f=float(current.get("temp_F", 0)),
            feels_like_c=float(current.get("FeelsLikeC", 0)),
            feels_like_f=float(current.get("FeelsLikeF", 0)),
            humidity=int(current.get("humidity", 0)),
            wind_speed_kmph=float(current.get("windspeedKmph", 0)),
            wind_speed_mph=float(current.get("windspeedMiles", 0)),
            wind_direction=str(current.get("winddir16Point", "N/A")),
            condition=condition,
            weather_code=str(current.get("weatherCode", "")),
            pressure_hpa=float(current.get("pressure", 0)),
            uv_index=int(current.get("uvIndex", 0)),
            visibility_km=float(current.get("visibility", 0)),
            cloud_cover=int(current.get("cloudcover", 0)),
            observation_time=str(current.get("localObsDateTime", "Just now")),
        )
