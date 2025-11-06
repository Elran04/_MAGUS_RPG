"""
Performance profiling and FPS tracking for MAGUS Pygame.
"""

import time
from collections import deque
from typing import Any


class PerformanceProfiler:
    """Tracks FPS, frame times, and performance metrics."""

    def __init__(self, sample_size: int = 60) -> None:
        """Initialize profiler with rolling window for metrics.
        
        Args:
            sample_size: Number of frames to track for averaging
        """
        self.sample_size = sample_size
        self.frame_times: deque[float] = deque(maxlen=sample_size)
        self.last_time = time.time()
        self.frame_count = 0

    def start_frame(self) -> None:
        """Mark the start of a new frame."""
        current_time = time.time()
        if self.frame_count > 0:
            frame_time = current_time - self.last_time
            self.frame_times.append(frame_time)
        self.last_time = current_time
        self.frame_count += 1

    def get_fps(self) -> float:
        """Get current average FPS.
        
        Returns:
            Average FPS over the sample window
        """
        if not self.frame_times:
            return 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0

    def get_frame_time_ms(self) -> float:
        """Get current average frame time in milliseconds.
        
        Returns:
            Average frame time in ms
        """
        if not self.frame_times:
            return 0.0
        return (sum(self.frame_times) / len(self.frame_times)) * 1000.0

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics.
        
        Returns:
            Dict with fps, frame_time_ms, min_fps, max_fps
        """
        if not self.frame_times:
            return {
                "fps": 0.0,
                "frame_time_ms": 0.0,
                "min_fps": 0.0,
                "max_fps": 0.0,
            }

        frame_times_list = list(self.frame_times)
        min_time = min(frame_times_list)
        max_time = max(frame_times_list)

        return {
            "fps": self.get_fps(),
            "frame_time_ms": self.get_frame_time_ms(),
            "min_fps": 1.0 / max_time if max_time > 0 else 0.0,
            "max_fps": 1.0 / min_time if min_time > 0 else 0.0,
        }


# Global profiler instance
_profiler: PerformanceProfiler | None = None


def get_profiler() -> PerformanceProfiler:
    """Get or create the global profiler instance.
    
    Returns:
        The global PerformanceProfiler instance
    """
    global _profiler
    if _profiler is None:
        _profiler = PerformanceProfiler()
    return _profiler
