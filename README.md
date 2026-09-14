
# Command-Line Weather Fetcher

[![Python Version](https://img.shields.io/badge/Python-3.8%2B-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Test Suite](https://img.shields.io/badge/Tests-14%20Passing-success.svg?style=flat)](test_weather.py)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-black.svg?style=flat)](https://www.python.org/dev/peps/pep-0008/)

A robust, lightweight Command-Line Interface (CLI) application developed in Python that retrieves and displays real-time meteorological conditions for user-specified locations worldwide. 

The application utilizes high-availability public weather APIs requiring zero API keys, features an interactive REPL mode, supports dynamic unit conversions, and provides structured terminal output with comprehensive exception handling.

---
## Demonstration

The following 1–2 minute walkthrough demonstrates:
- Entering a city name
- Fetching and displaying current weather details
- Handling an invalid location 

https://github.com/user-attachments/assets/9f805619-60c0-41fa-8cc0-3236ecc48cc3

---

## Features

- **Multi-Provider Weather Integration**: Primary queries are routed through Open-Meteo for high throughput and sub-second response times, with automatic failover to wttr.in. Neither provider requires API keys or authentication credentials.
- **Dual Execution Interfaces**:
  - **Direct CLI Arguments**: Execute single queries for scripting and automated pipelines.
  - **Interactive REPL Mode**: Continuous search environment with prompt handling and clean termination commands (`exit`, `quit`, `q`).
- **Structured Terminal Presentation**: Formatted visual panels powered by `rich`, color-coded temperature badges, meteorological metrics, and clean typography.
- **Flexible Measurement Units**: Seamlessly switch between **Metric** (°C, km/h), **Imperial** (°F, mph), or **Dual Mode** (simultaneous °C/°F and km/h/mph).
- **Fault-Tolerant Error Handling**: Friendly, actionable diagnostics for invalid locations, network disconnects, request timeouts, and upstream API errors.
- **Automated Test Coverage**: 100% test pass rate across 14 unit test suites utilizing `pytest` and mocked HTTP requests.

---

## Meteorological Metrics Displayed

| Parameter | Description | Standard Metric | Imperial |
| :--- | :--- | :--- | :--- |
| **Location** | Resolved city, administrative region, and country | Text | Text |
| **Condition** | Atmospheric condition summary with descriptive icon | Text | Text |
| **Temperature** | Real-time ambient temperature | °C | °F |
| **Feels Like** | Perceived temperature index | °C | °F |
| **Relative Humidity** | Atmospheric moisture saturation | % | % |
| **Wind Speed & Direction** | Velocity with 16-point cardinal compass direction | km/h | mph |
| **UV Index** | Maximum ultraviolet radiation index | Numeric (0–11+) | Numeric (0–11+) |
| **Atmospheric Pressure** | Surface barometric pressure | hPa | hPa |
| **Cloud Cover** | Percentage of sky covered by clouds | % | % |
| **Visibility** | Horizontal visual range | km | km |

---

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Git

### 1. Clone Repository
```bash
git clone https://github.com/AaliyaPatel-11/weather-fetcher.git
cd weather-fetcher
```

### 2. (Optional) Set Up Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## CLI Reference & Usage Examples

### 1. Standard City Lookup (Metric)
```bash
python weather.py London
```

```text
╭───────────── 📍 London, England, United Kingdom ──────────────╮
│                                                               │
│                          ☁️  Overcast                          │
│                                                               │
│  🌡️  Temperature:  20.7°C       💧  Humidity:      79%         │
│  🤔  Feels Like:   21.7°C      💨  Wind Speed:    10.4 km/h   │
│                                (SW)                           │
│  ☀️  UV Index:     3            ⏲️  Pressure:      1020 hPa     │
│  ☁️  Cloud Cover:  99%          👁️  Visibility:    11.1 km      │
│                                                               │
╰───────────────── Observed: 2026-09-14 11:00 ──────────────────╯
```

---

### 2. Imperial Measurement Units
```bash
python weather.py "New York" --unit imperial
```

---

### 3. Dual Unit Display
```bash
python weather.py Paris --unit both
```

---

### 4. Interactive REPL Mode
Running the script without parameters or with the `-i` flag initiates interactive session mode:
```bash
python weather.py
```

```text
╭──────────────────────────────────────────────────────────────╮
│ 🌤️  Command-Line Weather Fetcher (Interactive Mode)           │
│ Type a city name to get live weather, or 'exit'/'q' to quit. │
╰──────────────────────────────────────────────────────────────╯

🌍 Enter city name: Tokyo
[Displays formatted weather card]

🌍 Enter city name: exit
👋 Goodbye! Have a great day.
```

---

### 5. Full Command Options
```bash
python weather.py --help
```

```text
usage: weather [-h] [-c CITY_OPT] [-u {metric,imperial,both}] [-t TIMEOUT] [-i] [-v] [CITY]

Command-Line Weather Fetcher: Retrieve current meteorological conditions for any city worldwide.

positional arguments:
  CITY                  Name of the city to look up (e.g. London, Paris, Tokyo)

options:
  -h, --help            show this help message and exit
  -c, --city CITY_OPT   Specify city name explicitly
  -u, --unit {metric,imperial,both}
                        Measurement units: 'metric' (°C, km/h), 'imperial' (°F, mph), or 'both' (default: metric)
  -t, --timeout TIMEOUT
                        Request timeout in seconds (default: 10)
  -i, --interactive     Run in interactive prompt mode
  -v, --version         show program's version number and exit
```

---

## Error Handling & Resilience

The application implements defensive input validation and exception catching to ensure smooth terminal execution:

| Scenario | Handled Condition | User Feedback |
| :--- | :--- | :--- |
| **Invalid Location** | Unresolvable query string or typo | Displays "City Not Found" with spelling guidance. |
| **Network Loss** | DNS resolution failure / offline state | Displays "Network Error" with connection troubleshooting tips. |
| **Service Timeout** | Upstream latency exceeding threshold | Displays "Request Timed Out" with retry suggestions. |
| **Malformed Response** | Invalid JSON / HTTP 5xx codes | Graceful failover to secondary provider or error alert. |

**Example Error Output:**
```text
╭───────────────────────────── ❌ City Not Found ──────────────────────────────╮
│                                                                              │
│  City 'NonExistentCityXYZ' was not found.                                    │
│                                                                              │
│  💡 Tip: Double-check the spelling or try adding a country name (e.g.        │
│  'Paris, France' or 'Cambridge, UK').                                        │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

## Automated Testing

The project includes an automated unit test suite executed via `pytest`. All external network interactions are mocked to enable deterministic, offline validation:

```bash
pytest test_weather.py -v
```

### Test Suite Execution Output:
```text
test_weather.py::TestWeatherService::test_fetch_weather_open_meteo_success PASSED
test_weather.py::TestWeatherService::test_empty_city_raises_city_not_found PASSED
test_weather.py::TestWeatherService::test_city_not_found_geocoding_empty PASSED
test_weather.py::TestWeatherService::test_fallback_to_wttr_on_open_meteo_server_error PASSED
test_weather.py::TestWeatherService::test_connection_error_raises_network_error PASSED
test_weather.py::TestWeatherService::test_timeout_raises_request_timeout_error PASSED
test_weather.py::TestHelpersAndFormatting::test_degrees_to_compass PASSED
test_weather.py::TestHelpersAndFormatting::test_get_weather_icon PASSED
test_weather.py::TestHelpersAndFormatting::test_get_temp_color PASSED
test_weather.py::TestHelpersAndFormatting::test_display_weather_runs_cleanly PASSED
test_weather.py::TestHelpersAndFormatting::test_display_error_runs_cleanly PASSED
test_weather.py::TestCliAndArgumentParsing::test_cli_parser_positional_arg PASSED
test_weather.py::TestCliAndArgumentParsing::test_cli_parser_optional_city PASSED
test_weather.py::TestCliAndArgumentParsing::test_handle_fetch_success_and_failure PASSED

============================== 14 passed in 1.20s ==============================
```

---

## Project Structure

```text
weather-fetcher/
├── weather.py            # CLI entry point, argument parser, and interactive REPL
├── weather_service.py    # Multi-provider weather client and data normalization
├── formatter.py          # Terminal rendering, layout panels, and color styling
├── test_weather.py       # Automated unit test suite with mocked network calls
├── requirements.txt      # Production and testing dependencies
├── .gitignore            # Git exclusion rules
├── LICENSE               # MIT License
└── assets/
    ├── demo_preview.gif  # Animated demonstration preview for README
    └── demo_video.mp4    # Full-length video walkthrough (MP4)
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
