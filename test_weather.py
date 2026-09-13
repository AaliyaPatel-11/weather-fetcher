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
)
from formatter import display_weather, display_error, get_temp_color
from weather import create_parser, handle_fetch


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

    def test_fetch_weather_success(self):
        """Test successful weather fetching and parsing."""
        service = WeatherService(timeout=5)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_WTTR_PAYLOAD

        with patch.object(service.session, "get", return_value=mock_resp) as mock_get:
            data = service.fetch_weather("Paris")
            mock_get.assert_called_once()

            assert isinstance(data, WeatherData)
            assert data.city == "Paris"
            assert data.region == "Ile-de-France"
            assert data.country == "France"
            assert data.temp_c == 24.0
            assert data.temp_f == 75.0
            assert data.humidity == 60
            assert data.wind_speed_kmph == 18.0
            assert data.wind_speed_mph == 11.0
            assert data.wind_direction == "SSW"
            assert data.condition == "Sunny"
            assert data.uv_index == 6
            assert data.pressure_hpa == 1012.0

    def test_empty_city_raises_city_not_found(self):
        """Test that an empty city string raises CityNotFoundError immediately."""
        service = WeatherService()
        with pytest.raises(CityNotFoundError, match="City name cannot be empty"):
            service.fetch_weather("   ")

    def test_http_404_raises_city_not_found(self):
        """Test that HTTP 404 response raises CityNotFoundError."""
        service = WeatherService()
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch.object(service.session, "get", return_value=mock_resp):
            with pytest.raises(CityNotFoundError, match="was not found"):
                service.fetch_weather("NonExistentCityXYZ")

    def test_non_json_unknown_location_raises_city_not_found(self):
        """Test when wttr.in returns HTML with unknown location."""
        service = WeatherService()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_resp.text = "Unknown location; please try another query"

        with patch.object(service.session, "get", return_value=mock_resp):
            with pytest.raises(CityNotFoundError, match="was not found"):
                service.fetch_weather("UnknownCity12345")

    def test_connection_error_raises_network_error(self):
        """Test network connection error handling."""
        service = WeatherService()
        with patch.object(service.session, "get", side_effect=requests.exceptions.ConnectionError):
            with pytest.raises(NetworkConnectionError, match="Unable to connect"):
                service.fetch_weather("Tokyo")

    def test_timeout_raises_request_timeout_error(self):
        """Test request timeout handling."""
        service = WeatherService(timeout=3)
        with patch.object(service.session, "get", side_effect=requests.exceptions.Timeout):
            with pytest.raises(RequestTimeoutError, match="timed out"):
                service.fetch_weather("Tokyo")

    def test_http_500_raises_api_response_error(self):
        """Test HTTP 500 error handling."""
        service = WeatherService()
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch.object(service.session, "get", return_value=mock_resp):
            with pytest.raises(APIResponseError, match="HTTP 500"):
                service.fetch_weather("London")


class TestHelpersAndFormatting:
    """Test suite for helper functions and output formatting."""

    def test_get_weather_icon(self):
        """Test icon lookup mapping."""
        assert get_weather_icon("Clear sky") == "☀️"
        assert get_weather_icon("Partly cloudy") == "⛅"
        assert get_weather_icon("Heavy Rain") == "🌧️"
        assert get_weather_icon("Blizzard condition") == "🌨️"
        assert get_weather_icon("Unrecognized weather condition") == "🌡️"

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
            weather_code="116",
            pressure_hpa=1016.0,
            uv_index=4,
            visibility_km=10.0,
            cloud_cover=30,
            observation_time="10:00 AM",
        )
        # Should not raise exception
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
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_WTTR_PAYLOAD

        with patch.object(service.session, "get", return_value=mock_resp):
            success = handle_fetch(service, "Paris", unit="metric")
            assert success is True

        # Test failure case
        with patch.object(service.session, "get", side_effect=requests.exceptions.ConnectionError):
            success = handle_fetch(service, "Paris", unit="metric")
            assert success is False
