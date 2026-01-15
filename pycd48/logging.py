"""
Data logging utilities for CD48 measurements.

Provides CSV and JSON logging for long-term data collection.
"""

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .cd48 import CD48


class DataLogger:
    """
    Log CD48 measurements to CSV or JSON files.

    Example:
    --------
    >>> with CD48() as cd48:
    ...     logger = DataLogger("experiment_data.csv")
    ...     for _ in range(100):
    ...         data = cd48.get_counts(human_readable=False)
    ...         logger.log(data["counts"])
    ...         time.sleep(1)
    ...     logger.close()
    """

    def __init__(
        self,
        filename: Union[str, Path],
        channels: Optional[List[int]] = None,
        include_timestamp: bool = True,
    ):
        """
        Initialize data logger.

        Parameters:
        -----------
        filename : str or Path
            Output file path. Extension determines format (.csv or .json)
        channels : list of int, optional
            Which channels to log (default: all 8 channels)
        include_timestamp : bool
            Whether to include timestamps in logged data
        """
        self.filename = Path(filename)
        self.channels = channels if channels is not None else list(range(8))
        self.include_timestamp = include_timestamp
        self.format = self.filename.suffix.lower()

        if self.format not in (".csv", ".json"):
            raise ValueError(f"Unsupported format: {self.format}. Use .csv or .json")

        self._file = None
        self._writer = None
        self._json_data: List[Dict[str, Any]] = []
        self._start_time = time.time()

        self._open()

    def _open(self) -> None:
        """Open file for writing."""
        if self.format == ".csv":
            self._file = open(self.filename, "w", newline="")
            headers = []
            if self.include_timestamp:
                headers.extend(["timestamp", "elapsed_seconds"])
            headers.extend([f"channel_{i}" for i in self.channels])
            self._writer = csv.writer(self._file)
            self._writer.writerow(headers)
        # JSON is accumulated in memory and written on close

    def log(
        self,
        counts: List[int],
        overflow: Optional[int] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a measurement.

        Parameters:
        -----------
        counts : list of int
            Count values from get_counts()
        overflow : int, optional
            Overflow status flag
        extra : dict, optional
            Additional data to include in log entry
        """
        now = time.time()
        elapsed = now - self._start_time

        if self.format == ".csv":
            row = []
            if self.include_timestamp:
                row.append(datetime.now().isoformat())
                row.append(f"{elapsed:.3f}")
            row.extend([counts[i] for i in self.channels])
            self._writer.writerow(row)
            self._file.flush()
        else:
            entry: Dict[str, Any] = {}
            if self.include_timestamp:
                entry["timestamp"] = datetime.now().isoformat()
                entry["elapsed_seconds"] = round(elapsed, 3)
            entry["counts"] = {f"channel_{i}": counts[i] for i in self.channels}
            if overflow is not None:
                entry["overflow"] = overflow
            if extra:
                entry.update(extra)
            self._json_data.append(entry)

    def close(self) -> None:
        """Close the log file."""
        if self.format == ".csv":
            if self._file:
                self._file.close()
                self._file = None
        else:
            with open(self.filename, "w") as f:
                json.dump(self._json_data, f, indent=2)

    def __enter__(self) -> "DataLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def log_continuous(
    cd48: "CD48",
    filename: Union[str, Path],
    duration: float,
    interval: float = 1.0,
    channels: Optional[List[int]] = None,
    callback: Optional[callable] = None,
) -> Path:
    """
    Log continuous measurements to file.

    Parameters:
    -----------
    cd48 : CD48
        Connected CD48 instance
    filename : str or Path
        Output file path
    duration : float
        Total measurement duration in seconds
    interval : float
        Time between measurements in seconds
    channels : list of int, optional
        Which channels to log
    callback : callable, optional
        Function called after each measurement with (counts, elapsed_time)

    Returns:
    --------
    Path : Path to the created log file

    Example:
    --------
    >>> with CD48() as cd48:
    ...     log_continuous(cd48, "data.csv", duration=3600, interval=1.0)
    """
    filepath = Path(filename)

    with DataLogger(filepath, channels=channels) as logger:
        start_time = time.time()
        cd48.clear_counts()

        while time.time() - start_time < duration:
            time.sleep(interval)
            data = cd48.get_counts(human_readable=False)
            logger.log(data["counts"], overflow=data["overflow"])

            if callback:
                callback(data["counts"], time.time() - start_time)

    return filepath
