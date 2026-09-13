"""
Weather Service Module
Handles fetching and parsing meteorological data from wttr.in JSON API.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
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


# Mapping weather condition keywords/codes to visual icons/emojis
WEATHER_ICONS = {
    "sunny": "☀️",
    "clear": "☀️",
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "mist": "🌫️",
    "fog": "🌫️",
    "freezing fog": "🌫️",
    "patchy rain": "🌦️",
    "light rain": "🌦️",
    "moderate rain": "🌧️",
    "heavy rain": "🌧️",
    "torrential rain": "🌧️",
    "thunder": "⛈️",
    "thundery": "⛈️",
    "snow": "❄️",
    "light snow": "🌨️",
    "heavy snow": "❄️",
    "blizzard": "🌨️",
    "sleet": "🌧️❄️",
    "drizzle": "🌦️",
    "shower": "🚿",
}


def get_weather_icon(condition: str) -> str:
    """Returns an appropriate emoji icon based on weather description."""
    cond_lower = condition.lower()
    for key, icon in WEATHER_ICONS.items():
        if key in cond_lower:
            return icon
    return "🌡️"


class WeatherService:
    """Client for querying wttr.in weather data."""

    BASE_URL = "https://wttr.in"
    DEFAULT_TIMEOUT = 10  # seconds

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "WeatherFetcherCLI/1.0",
            "Accept": "application/json"
        })

    def fetch_weather(self, city: str) -> WeatherData:
        """
        Fetches current weather information for the specified city.

        Args:
            city: Name of the city (e.g. 'London', 'Tokyo', 'San Francisco')

        Returns:
            WeatherData dataclass populated with current conditions.

        Raises:
            CityNotFoundError: If city does not exist or cannot be resolved.
            NetworkConnectionError: If network is unreachable.
            RequestTimeoutError: If the server does not respond within timeout.
            APIResponseError: If server responds with invalid status or schema.
        """
        cleaned_city = city.strip()
        if not cleaned_city:
            raise CityNotFoundError("City name cannot be empty.")

        url = f"{self.BASE_URL}/{requests.utils.quote(cleaned_city)}?format=j1"

        try:
            response = self.session.get(url, timeout=self.timeout)
        except requests.exceptions.Timeout as err:
            raise RequestTimeoutError(
                f"Request to weather service timed out after {self.timeout}s."
            ) from err
        except requests.exceptions.ConnectionError as err:
            raise NetworkConnectionError(
                "Unable to connect to weather server. Check your internet connection."
            ) from err
        except requests.exceptions.RequestException as err:
            raise APIResponseError(f"Network error occurred: {err}") from err

        # wttr.in often returns HTTP 404 or 500 with 'location not found' plaintext
        resp_text_lower = response.text.lower()
        if (
            response.status_code == 404
            or "location not found" in resp_text_lower
            or "unknown location" in resp_text_lower
            or "not found" in resp_text_lower
        ):
            raise CityNotFoundError(f"City '{cleaned_city}' was not found.")
        elif response.status_code != 200:
            raise APIResponseError(
                f"Weather service returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
        except ValueError as err:
            # wttr.in returns plaintext/HTML if location is not found or service overloaded
            if "unknown location" in response.text.lower() or "not found" in response.text.lower():
                raise CityNotFoundError(f"City '{cleaned_city}' was not found.") from err
            raise APIResponseError("Failed to parse weather service response as JSON.") from err

        return self._parse_response(cleaned_city, data)

    def _parse_response(self, query_city: str, data: Dict[str, Any]) -> WeatherData:
        """Parses the wttr.in JSON payload into a WeatherData dataclass."""
        try:
            current_list = data.get("current_condition")
            if not current_list or not isinstance(current_list, list):
                raise CityNotFoundError(f"No weather data available for '{query_city}'.")

            current = current_list[0]
            nearest_area_list = data.get("nearest_area", [{}])
            nearest = nearest_area_list[0] if nearest_area_list else {}

            # Extract location details
            area_names = nearest.get("areaName", [{}])
            resolved_city = area_names[0].get("value", query_city) if area_names else query_city

            region_names = nearest.get("region", [{}])
            resolved_region = region_names[0].get("value", "") if region_names else ""

            country_names = nearest.get("country", [{}])
            resolved_country = country_names[0].get("value", "") if country_names else ""

            # Extract condition description
            weather_desc_list = current.get("weatherDesc", [{}])
            condition_desc = (
                weather_desc_list[0].get("value", "Unknown") if weather_desc_list else "Unknown"
            )

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
                condition=condition_desc,
                weather_code=str(current.get("weatherCode", "")),
                pressure_hpa=float(current.get("pressure", 0)),
                uv_index=int(current.get("uvIndex", 0)),
                visibility_km=float(current.get("visibility", 0)),
                cloud_cover=int(current.get("cloudcover", 0)),
                observation_time=str(current.get("localObsDateTime", "Just now")),
            )
        except (KeyError, IndexError, ValueError, TypeError) as err:
            raise APIResponseError(f"Unexpected response format from weather service: {err}") from err
