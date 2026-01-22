"""
Real-time plotting utilities for CD48 measurements.

Provides matplotlib-based visualization for count rates.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from matplotlib.animation import FuncAnimation
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D

    from .cd48 import CD48

# Lazy import matplotlib to avoid import errors if not installed
_plt = None
_FuncAnimation = None

# Plotting defaults and constants
# Default channels to plot: A, B, and A+B coincidence
DEFAULT_PLOT_CHANNELS: list[int] = [0, 1, 4]
# Default maximum number of historical data points to display
DEFAULT_MAX_POINTS: int = 100
# Default measurement/update interval in seconds
DEFAULT_UPDATE_INTERVAL: float = 1.0
# Default figure size in inches (width, height)
DEFAULT_FIGURE_SIZE: tuple[float, float] = (10, 6)
# Grid line transparency (0=invisible, 1=opaque)
GRID_ALPHA: float = 0.3
# Minimum Y-axis limit in Hz to ensure visibility at low rates
MIN_Y_AXIS_LIMIT: float = 10.0
# Y-axis scaling factor: max_rate * this value (110% headroom)
Y_AXIS_SCALE_FACTOR: float = 1.1
# Milliseconds per second for interval conversion
MS_PER_SECOND: int = 1000


def _ensure_matplotlib() -> None:
    """Lazy import matplotlib."""
    global _plt, _FuncAnimation
    if _plt is None:
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation

        _plt = plt
        _FuncAnimation = FuncAnimation


class RatePlotter:
    """
    Real-time count rate plotter.

    Example:
    --------
    >>> with CD48() as cd48:
    ...     plotter = RatePlotter(cd48, channels=[0, 1, 4])
    ...     plotter.run(duration=60)  # Plot for 60 seconds
    """

    def __init__(
        self,
        cd48: CD48,
        channels: list[int] | None = None,
        max_points: int = DEFAULT_MAX_POINTS,
        interval: float = DEFAULT_UPDATE_INTERVAL,
    ):
        """
        Initialize rate plotter.

        Parameters:
        -----------
        cd48 : CD48
            Connected CD48 instance
        channels : list of int, optional
            Channels to plot (default: [0, 1, 4] for A, B, and A+B)
        max_points : int
            Maximum number of points to display (older points scroll off)
        interval : float
            Update interval in seconds
        """
        _ensure_matplotlib()

        self.cd48 = cd48
        self.channels = channels if channels is not None else DEFAULT_PLOT_CHANNELS
        self.max_points = max_points
        self.interval = interval

        self._times: list[float] = []
        self._rates: dict[int, list[float]] = {ch: [] for ch in self.channels}
        self._start_time: float = 0

        self._fig: Figure | None = None
        self._ax: Axes | None = None
        self._lines: dict[int, Line2D] = {}
        self._animation: FuncAnimation | None = None

    def _init_plot(self) -> list[Line2D]:
        """Initialize the plot."""
        assert _plt is not None, "Matplotlib not loaded"
        self._fig, self._ax = _plt.subplots(figsize=DEFAULT_FIGURE_SIZE)
        self._ax.set_xlabel("Time (s)")
        self._ax.set_ylabel("Count Rate (Hz)")
        self._ax.set_title("CD48 Real-time Count Rates")
        self._ax.grid(True, alpha=GRID_ALPHA)

        channel_names = {
            0: "Ch0 (A)",
            1: "Ch1 (B)",
            2: "Ch2 (C)",
            3: "Ch3 (D)",
            4: "Ch4 (A+B)",
            5: "Ch5 (A+C)",
            6: "Ch6 (A+D)",
            7: "Ch7 (B+C+D)",
        }

        for ch in self.channels:
            (line,) = self._ax.plot([], [], label=channel_names.get(ch, f"Ch{ch}"))
            self._lines[ch] = line

        self._ax.legend(loc="upper right")
        return list(self._lines.values())

    def _update(self, frame: int) -> list[Line2D]:
        """Update function for animation."""
        assert self._ax is not None, "Plot not initialized"
        # Read counts
        data = self.cd48.get_counts(human_readable=False)
        now = time.time() - self._start_time

        # Calculate rates
        self._times.append(now)
        for ch in self.channels:
            rate = data["counts"][ch] / self.interval
            self._rates[ch].append(rate)

        # Trim to max_points
        if len(self._times) > self.max_points:
            self._times = self._times[-self.max_points :]
            for ch in self.channels:
                self._rates[ch] = self._rates[ch][-self.max_points :]

        # Update plot data
        for ch in self.channels:
            self._lines[ch].set_data(self._times, self._rates[ch])

        # Adjust axes
        if self._times:
            x_min = max(0, self._times[-1] - self.max_points * self.interval)
            x_max = self._times[-1] + self.interval
            self._ax.set_xlim(x_min, x_max)
            all_rates = [r for ch_rates in self._rates.values() for r in ch_rates]
            if all_rates:
                max_rate = max(all_rates)
                self._ax.set_ylim(0, max(MIN_Y_AXIS_LIMIT, max_rate * Y_AXIS_SCALE_FACTOR))

        return list(self._lines.values())

    def run(self, duration: float | None = None) -> None:
        """
        Start the real-time plot.

        Parameters:
        -----------
        duration : float, optional
            How long to run in seconds. If None, runs until window is closed.
        """
        self._init_plot()
        self._start_time = time.time()
        self.cd48.clear_counts()

        frames = None
        if duration is not None:
            frames = int(duration / self.interval)

        assert self._fig is not None, "Plot not initialized"
        if _FuncAnimation:
            self._animation = _FuncAnimation(
                self._fig,
                self._update,
                frames=frames,
                interval=int(self.interval * MS_PER_SECOND),
                blit=False,
                repeat=False,
            )

        if _plt:
            _plt.show()

    def save_animation(self, filename: str, duration: float, fps: int = 1) -> None:
        """
        Save animation to file.

        Parameters:
        -----------
        filename : str
            Output filename (e.g., 'rates.gif' or 'rates.mp4')
        duration : float
            Recording duration in seconds
        fps : int
            Frames per second
        """
        self._init_plot()
        self._start_time = time.time()
        self.cd48.clear_counts()

        frames = int(duration / self.interval)
        assert self._fig is not None, "Plot not initialized"
        if _FuncAnimation:
            self._animation = _FuncAnimation(
                self._fig,
                self._update,
                frames=frames,
                interval=int(self.interval * MS_PER_SECOND),
                blit=False,
                repeat=False,
            )

        if self._animation:
            self._animation.save(filename, fps=fps)
        if _plt:
            _plt.close()


def plot_rates(
    cd48: CD48,
    duration: float = 60,
    channels: list[int] | None = None,
    interval: float = 1.0,
) -> None:
    """
    Convenience function for real-time rate plotting.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 instance
    duration : float
        How long to plot in seconds
    channels : list of int, optional
        Channels to plot
    interval : float
        Update interval in seconds

    Example:
    --------
    >>> with CD48() as cd48:
    ...     plot_rates(cd48, duration=120, channels=[0, 1])
    """
    plotter = RatePlotter(cd48, channels=channels, interval=interval)
    plotter.run(duration=duration)
