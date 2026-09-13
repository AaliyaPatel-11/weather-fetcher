"""
Formatter Module
Renders meteorological data and error messages with rich styling.
"""

import sys
from typing import Optional, Any
from weather_service import WeatherData, get_weather_icon

# Ensure UTF-8 output encoding across Windows terminals
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_temp_color(temp_c: float) -> str:
    """Returns a color string based on the temperature in Celsius."""
    if temp_c <= 0:
        return "bold bright_cyan"
    elif temp_c <= 15:
        return "bold cyan"
    elif temp_c <= 25:
        return "bold green"
    elif temp_c <= 32:
        return "bold yellow"
    else:
        return "bold bright_red"


def display_weather(data: WeatherData, unit: str = "metric", console: Optional[Any] = None) -> None:
    """
    Renders the WeatherData in a rich formatted card.

    Args:
        data: WeatherData object.
        unit: 'metric' (default, °C/kmph), 'imperial' (°F/mph), or 'both'.
        console: Optional Rich console instance.
    """
    if not RICH_AVAILABLE:
        # Plain text fallback
        _display_plain(data, unit)
        return

    if console is None:
        console = Console(legacy_windows=False)

    icon = get_weather_icon(data.condition)
    temp_color = get_temp_color(data.temp_c)

    # Header location formatting
    loc_parts = [data.city]
    if data.region and data.region != data.city:
        loc_parts.append(data.region)
    if data.country:
        loc_parts.append(data.country)
    full_location = ", ".join(loc_parts)

    # Construct temperature and wind strings based on unit selection
    if unit == "imperial":
        temp_str = f"[{temp_color}]{data.temp_f:.1f}°F[/]"
        feels_str = f"{data.feels_like_f:.1f}°F"
        wind_str = f"{data.wind_speed_mph:.1f} mph ({data.wind_direction})"
    elif unit == "both":
        temp_str = f"[{temp_color}]{data.temp_c:.1f}°C / {data.temp_f:.1f}°F[/]"
        feels_str = f"{data.feels_like_c:.1f}°C / {data.feels_like_f:.1f}°F"
        wind_str = f"{data.wind_speed_kmph:.1f} km/h ({data.wind_speed_mph:.1f} mph, {data.wind_direction})"
    else:  # metric
        temp_str = f"[{temp_color}]{data.temp_c:.1f}°C[/]"
        feels_str = f"{data.feels_like_c:.1f}°C"
        wind_str = f"{data.wind_speed_kmph:.1f} km/h ({data.wind_direction})"

    # Create metrics grid
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="left", ratio=1)

    grid.add_row(
        f"🌡️  [bold]Temperature:[/]  {temp_str}",
        f"💧  [bold]Humidity:[/]      [cyan]{data.humidity}%[/]"
    )
    grid.add_row(
        f"🤔  [bold]Feels Like:[/]   {feels_str}",
        f"💨  [bold]Wind Speed:[/]    [cyan]{wind_str}[/]"
    )
    grid.add_row(
        f"☀️  [bold]UV Index:[/]     [yellow]{data.uv_index}[/]",
        f"⏲️  [bold]Pressure:[/]      [magenta]{data.pressure_hpa:.0f} hPa[/]"
    )
    grid.add_row(
        f"☁️  [bold]Cloud Cover:[/]  [white]{data.cloud_cover}%[/]",
        f"👁️  [bold]Visibility:[/]    [white]{data.visibility_km:.1f} km[/]"
    )

    # Main content layout inside Panel
    title_text = f"[bold cyan]📍 {full_location}[/bold cyan]"
    subtitle_text = f"[italic dim]Observed: {data.observation_time}[/italic dim]"
    condition_banner = f"[bold]{icon}  {data.condition}[/bold]\n"

    panel_content = Table.grid(expand=True)
    panel_content.add_column(justify="center")
    panel_content.add_row(condition_banner)
    panel_content.add_row(grid)

    panel = Panel(
        panel_content,
        title=title_text,
        subtitle=subtitle_text,
        border_style="bright_blue",
        padding=(1, 2),
        expand=False
    )

    console.print()
    console.print(panel)
    console.print()


def display_error(title: str, message: str, suggestion: Optional[str] = None, console: Optional[Any] = None) -> None:
    """
    Renders a friendly error card.
    """
    if not RICH_AVAILABLE:
        print(f"\n[ERROR] {title}: {message}")
        if suggestion:
            print(f"Suggestion: {suggestion}\n")
        return

    if console is None:
        console = Console(legacy_windows=False)

    body = f"[bold red]{message}[/bold red]"
    if suggestion:
        body += f"\n\n[yellow]💡 Tip:[/] [dim]{suggestion}[/dim]"

    panel = Panel(
        body,
        title=f"[bold bright_red]❌ {title}[/bold bright_red]",
        border_style="red",
        padding=(1, 2),
        expand=False
    )
    console.print()
    console.print(panel)
    console.print()


def _display_plain(data: WeatherData, unit: str = "metric") -> None:
    """Plain text representation when rich is not available."""
    print("=" * 45)
    print(f" Weather for: {data.city}, {data.country}")
    print(f" Condition:   {data.condition}")
    if unit == "imperial":
        print(f" Temperature: {data.temp_f:.1f}°F (Feels like {data.feels_like_f:.1f}°F)")
        print(f" Wind:        {data.wind_speed_mph:.1f} mph ({data.wind_direction})")
    elif unit == "both":
        print(f" Temperature: {data.temp_c:.1f}°C / {data.temp_f:.1f}°F")
        print(f" Wind:        {data.wind_speed_kmph:.1f} km/h / {data.wind_speed_mph:.1f} mph")
    else:
        print(f" Temperature: {data.temp_c:.1f}°C (Feels like {data.feels_like_c:.1f}°C)")
        print(f" Wind:        {data.wind_speed_kmph:.1f} km/h ({data.wind_direction})")
    print(f" Humidity:    {data.humidity}%")
    print(f" Pressure:    {data.pressure_hpa:.0f} hPa")
    print(f" UV Index:    {data.uv_index}")
    print(f" Observed at: {data.observation_time}")
    print("=" * 45)
