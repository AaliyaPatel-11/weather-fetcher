#!/usr/bin/env python3
"""
Command-Line Weather Fetcher
Main CLI entry point for retrieving and displaying real-time weather.
"""

import sys
import os
import argparse
from typing import Optional, Any

# Ensure UTF-8 output encoding across Windows terminals
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from weather_service import (
    WeatherService,
    CityNotFoundError,
    NetworkConnectionError,
    RequestTimeoutError,
    APIResponseError,
    WeatherFetcherException,
)
from formatter import display_weather, display_error

try:
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.panel import Panel
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


__version__ = "1.0.0"


def create_parser() -> argparse.ArgumentParser:
    """Configures command-line argument parsing."""
    parser = argparse.ArgumentParser(
        prog="weather",
        description="🌤️  Command-Line Weather Fetcher: Retrieve current meteorological conditions for any city worldwide.",
        epilog="Examples:\n"
               "  python weather.py Tokyo\n"
               "  python weather.py \"New York\" --unit imperial\n"
               "  python weather.py Paris --unit both\n"
               "  python weather.py (starts interactive mode)\n",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "city_pos",
        nargs="?",
        default=None,
        metavar="CITY",
        help="Name of the city to look up (e.g. London, Paris, Tokyo)"
    )
    parser.add_argument(
        "-c", "--city",
        dest="city_opt",
        type=str,
        default=None,
        help="Specify city name explicitly"
    )
    parser.add_argument(
        "-u", "--unit",
        choices=["metric", "imperial", "both"],
        default="metric",
        help="Measurement units: 'metric' (°C, km/h), 'imperial' (°F, mph), or 'both' (default: metric)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive prompt mode"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    return parser


def handle_fetch(service: WeatherService, city: str, unit: str, console: Optional[Any] = None) -> bool:
    """
    Fetches and displays weather for a given city, handling all exceptions cleanly.

    Returns:
        bool: True if fetch succeeded, False otherwise.
    """
    try:
        if RICH_AVAILABLE and console is not None:
            with console.status(f"[bold cyan]Fetching weather for '{city}'...[/bold cyan]", spinner="dots"):
                weather_data = service.fetch_weather(city)
        else:
            weather_data = service.fetch_weather(city)

        display_weather(weather_data, unit=unit, console=console)
        return True

    except CityNotFoundError as err:
        display_error(
            title="City Not Found",
            message=str(err),
            suggestion="Double-check the spelling or try adding a country name (e.g. 'Paris, France' or 'Cambridge, UK').",
            console=console
        )
    except NetworkConnectionError as err:
        display_error(
            title="Network Error",
            message=str(err),
            suggestion="Check your internet connection, proxy settings, or DNS configuration.",
            console=console
        )
    except RequestTimeoutError as err:
        display_error(
            title="Request Timed Out",
            message=str(err),
            suggestion="The weather service took too long to respond. Please try again in a few moments.",
            console=console
        )
    except APIResponseError as err:
        display_error(
            title="API Error",
            message=str(err),
            suggestion="The weather provider returned an unexpected response. Please try again later.",
            console=console
        )
    except WeatherFetcherException as err:
        display_error(
            title="Error",
            message=str(err),
            suggestion="An unexpected weather service error occurred.",
            console=console
        )
    except Exception as err:
        display_error(
            title="Unexpected Error",
            message=f"An unexpected system error occurred: {err}",
            suggestion="Please file an issue or check your Python environment.",
            console=console
        )

    return False


def run_interactive_mode(service: WeatherService, unit: str, console: Optional[Any] = None) -> None:
    """Runs the interactive REPL prompt."""
    if RICH_AVAILABLE and console is not None:
        console.print(Panel(
            "[bold cyan]🌤️  Command-Line Weather Fetcher (Interactive Mode)[/bold cyan]\n"
            "[dim]Type a city name to get live weather, or type [bold red]'exit'[/bold red] / [bold red]'q'[/bold red] to quit.[/dim]",
            border_style="cyan"
        ))
    else:
        print("\n=== Command-Line Weather Fetcher ===")
        print("Type a city name to get live weather, or type 'exit' / 'q' to quit.\n")

    while True:
        try:
            if RICH_AVAILABLE and console is not None:
                user_input = Prompt.ask("\n[bold green]🌍 Enter city name[/bold green]")
            else:
                user_input = input("\n🌍 Enter city name: ")

            user_input = user_input.strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q", ":q"):
                if RICH_AVAILABLE and console is not None:
                    console.print("[yellow]👋 Goodbye! Have a great day.[/yellow]\n")
                else:
                    print("Goodbye! Have a great day.\n")
                break

            handle_fetch(service, user_input, unit=unit, console=console)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


def main() -> int:
    """Main CLI execution flow."""
    parser = create_parser()
    args = parser.parse_args()

    console = Console(legacy_windows=False) if RICH_AVAILABLE else None
    service = WeatherService(timeout=args.timeout)

    target_city = args.city_opt if args.city_opt is not None else args.city_pos

    # If interactive flag is passed OR no city argument is provided, launch interactive mode
    if args.interactive or target_city is None:
        run_interactive_mode(service, unit=args.unit, console=console)
        return 0

    # Otherwise, execute single lookup
    success = handle_fetch(service, target_city, unit=args.unit, console=console)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
