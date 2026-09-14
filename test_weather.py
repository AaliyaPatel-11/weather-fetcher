"""
Unit Tests for Command-Line Weather Fetcher
"""

import pytest
from unittest.mock import MagicMock, patch
import requests

from weather_service import (
    WeatherService,
    WeatherData,
    CityNotFoundError,
    NetworkConnectionError,
    RequestTimeoutError,
    APIResponseError,
    get_weather_icon,
    degrees_to_compass,
)
from formatter import display_weather, display_error, get_temp_color
from weather import create_parser, handle_fetch


# Sample mock payloads for Open-Meteo
MOCK_GEO_PAYLOAD = {
    "results": [
        {
            "id": 2988507,
            "name": "Paris",
            "latitude": 48.85341,
            "longitude": 2.3488,
            "country": "France",
            "admin1": "Ile-de-France",
        }
    ]
}

MOCK_OPEN_METEO_PAYLOAD = {
    "current": {
        "time": "2026-09-14T12:00",
        "temperature_2m": 24.0,
        "relative_humidity_2m": 60,
        "apparent_temperature": 25.0,
        "weather_code": 0,
        "surface_pressure": 1012.0,
        "wind_speed_10m": 18.0,
        "wind_direction_10m": 200,
        "cloud_cover": 15,
        "visibility": 10000.0,
    },
    "daily": {
        "uv_index_max": [6.0],
    },
}

# Sample mock payload matching wttr.in format=j1 schema
MOCK_WTTR_PAYLOAD = {
    "current_condition": [
        {
            "temp_C": "24",
            "temp_F": "75",
            "FeelsLikeC": "25",
            "FeelsLikeF": "77",
            "humidity": "60",
            "windspeedKmph": "18",
            "windspeedMiles": "11",
            "winddir16Point": "SSW",
            "weatherDesc": [{"value": "Sunny"}],
            "weatherCode": "113",
            "pressure": "1012",
            "uvIndex": "6",
            "visibility": "10",
            "cloudcover": "15",
            "localObsDateTime": "2026-09-14 12:00 PM",
        }
    ],
    "nearest_area": [
        {
            "areaName": [{"value": "Paris"}],
            "region": [{"value": "Ile-de-France"}],
            "country": [{"value": "France"}],
        }
    ],
}


class TestWeatherService:
    """Test suite for WeatherService API interactions and parsing."""

    def test_fetch_weather_open_meteo_success(self):
        """Test successful weather fetching via Open-Meteo."""
        service = WeatherService(timeout=5)
        geo_resp = MagicMock(status_code=200, json=lambda: MOCK_GEO_PAYLOAD)
        weather_resp = MagicMock(status_code=200, json=lambda: MOCK_OPEN_METEO_PAYLOAD)

        with patch.object(service.session, "get", side_effect=[geo_resp, weather_resp]):
            data = service.fetch_weather("Paris")

            assert isinstance(data, WeatherData)
            assert data.city == "Paris"
            assert data.region == "Ile-de-France"
            assert data.country == "France"
            assert data.temp_c == 24.0
            assert data.temp_f == 75.2
            assert data.humidity == 60
            assert data.wind_speed_kmph == 18.0
            assert data.wind_direction == "SSW"
            assert data.condition == "Clear sky"
            assert data.uv_index == 6
            assert data.pressure_hpa == 1012.0

    def test_empty_city_raises_city_not_found(self):
        """Test that an empty city string raises CityNotFoundError immediately."""
        service = WeatherService()
        with pytest.raises(CityNotFoundError, match="City name cannot be empty"):
            service.fetch_weather("   ")

    def test_city_not_found_geocoding_empty(self):
        """Test that missing results in geocoding raises CityNotFoundError."""
        service = WeatherService()
        geo_resp = MagicMock(status_code=200, json=lambda: {"results": []})

        with patch.object(service.session, "get", return_value=geo_resp):
            with pytest.raises(CityNotFoundError, match="was not found"):
                service.fetch_weather("NonExistentCityXYZ")

    def test_fallback_to_wttr_on_open_meteo_server_error(self):
        """Test automatic fallback to wttr.in if Open-Meteo server fails."""
        service = WeatherService()
        geo_err_resp = MagicMock(status_code=500)
        wttr_resp = MagicMock(status_code=200, json=lambda: MOCK_WTTR_PAYLOAD)

        with patch.object(service.session, "get", side_effect=[geo_err_resp, wttr_resp]):
            data = service.fetch_weather("Paris")
            assert data.city == "Paris"
            assert data.temp_c == 24.0

    def test_connection_error_raises_network_error(self):
        """Test network connection error handling when both endpoints fail."""
        service = WeatherService()
        with patch.object(service.session, "get", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(NetworkConnectionError, match="Unable to connect"):
                service.fetch_weather("Tokyo")

    def test_timeout_raises_request_timeout_error(self):
        """Test request timeout handling when both endpoints timeout."""
        service = WeatherService(timeout=3)
        with patch.object(service.session, "get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RequestTimeoutError, match="timed out"):
                service.fetch_weather("Tokyo")


class TestHelpersAndFormatting:
    """Test suite for helper functions and output formatting."""

    def test_degrees_to_compass(self):
        """Test degree to cardinal direction conversion."""
        assert degrees_to_compass(0) == "N"
        assert degrees_to_compass(90) == "E"
        assert degrees_to_compass(180) == "S"
        assert degrees_to_compass(270) == "W"
        assert degrees_to_compass(200) == "SSW"

    def test_get_weather_icon(self):
        """Test icon lookup mapping."""
        assert get_weather_icon("Clear sky") == "☀️"
        assert get_weather_icon("Partly cloudy") == "⛅"
        assert get_weather_icon("Heavy Rain") == "🌧️"
        assert get_weather_icon("Blizzard") == "🌨️"
        assert get_weather_icon("Unrecognized condition") == "🌡️"

    def test_get_temp_color(self):
        """Test temperature color thresholds."""
        assert "cyan" in get_temp_color(-5)
        assert "green" in get_temp_color(20)
        assert "yellow" in get_temp_color(28)
        assert "red" in get_temp_color(38)

    def test_display_weather_runs_cleanly(self):
        """Test that display_weather runs without throwing exceptions across units."""
        dummy_data = WeatherData(
            city="Berlin",
            region="Berlin",
            country="Germany",
            temp_c=18.0,
            temp_f=64.4,
            feels_like_c=17.0,
            feels_like_f=62.6,
            humidity=55,
            wind_speed_kmph=12.0,
            wind_speed_mph=7.5,
            wind_direction="W",
            condition="Partly cloudy",
            weather_code="2",
            pressure_hpa=1016.0,
            uv_index=4,
            visibility_km=10.0,
            cloud_cover=30,
            observation_time="2026-09-14 10:00",
        )
        display_weather(dummy_data, unit="metric")
        display_weather(dummy_data, unit="imperial")
        display_weather(dummy_data, unit="both")

    def test_display_error_runs_cleanly(self):
        """Test that display_error executes cleanly."""
        display_error("Test Title", "Test Message", suggestion="Test Suggestion")


class TestCliAndArgumentParsing:
    """Test CLI argument parsing and error flow."""

    def test_cli_parser_positional_arg(self):
        parser = create_parser()
        args = parser.parse_args(["London", "--unit", "imperial"])
        assert args.city_pos == "London"
        assert args.unit == "imperial"

    def test_cli_parser_optional_city(self):
        parser = create_parser()
        args = parser.parse_args(["-c", "San Francisco", "-t", "15"])
        assert args.city_opt == "San Francisco"
        assert args.timeout == 15

    def test_handle_fetch_success_and_failure(self):
        service = WeatherService()
        geo_resp = MagicMock(status_code=200, json=lambda: MOCK_GEO_PAYLOAD)
        weather_resp = MagicMock(status_code=200, json=lambda: MOCK_OPEN_METEO_PAYLOAD)

        with patch.object(service.session, "get", side_effect=[geo_resp, weather_resp]):
            success = handle_fetch(service, "Paris", unit="metric")
            assert success is True

        with patch.object(service.session, "get", side_effect=requests.exceptions.ConnectionError):
            success = handle_fetch(service, "Paris", unit="metric")
            assert success is False
