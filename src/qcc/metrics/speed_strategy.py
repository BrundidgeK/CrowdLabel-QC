from __future__ import annotations  # future annotations

<<<<<<< HEAD
"""
tagging-speed strategy implementation.
=======
"""10% trimmed mean seconds-per-tag strategy.

This module implements a tagging-speed strategy that computes the
10% trimmed mean of raw seconds-per-tag intervals between consecutive
`TagAssignment.timestamp` values. The implementation returns seconds-per-tag
directly (no log transformation). The method `speed_log2` is a legacy name
kept for compatibility with the `TaggingSpeedStrategy` Protocol.
"""  # module docstring
>>>>>>> 3433ff6 (Revert to compute raw seconds no log transform)

from typing import List  # typing import
import statistics  # statistics import

<<<<<<< HEAD
from typing import List
import math
import statistics
=======
from .interfaces import TaggingSpeedStrategy  # base strategy import
>>>>>>> 3433ff6 (Revert to compute raw seconds no log transform)

TRIM_FRACTION = 0.1  # fraction to trim from upper tail


<<<<<<< HEAD
class TrimmedMeanTaggingSpeed(TaggingSpeedStrategy):
    """Tagging speed: trimmed mean of inter-tag intervals in seconds.

    For a given tagger, compute the time in seconds between consecutive
    tag assignments, sort those intervals, drop the slowest
    TRIM_FRACTION fraction, and return the mean of the remaining
    intervals. The result is "seconds per tag" ignoring long idle gaps.
    """

    def speed_seconds(self, tagger: "Tagger") -> float:
        valid = [
            ta for ta in (tagger.tagassignments or [])
            if getattr(ta, "timestamp", None) is not None
        ]
        if len(valid) < 2:
            return 0.0

        sorted_assignments = sorted(valid, key=lambda ta: ta.timestamp)
        intervals: List[float] = []
        for i in range(1, len(sorted_assignments)):
            t0 = sorted_assignments[i - 1].timestamp
            t1 = sorted_assignments[i].timestamp
=======
class LogTrimTaggingSpeed(TaggingSpeedStrategy):
    """Tagging-speed strategy using 10% upper-tail trimming on raw seconds.

    NOTE: The class name `LogTrimTaggingSpeed` is kept for backward compatibility.
    Earlier versions of this strategy applied a log2 transform to time gaps.
    The current implementation does NOT use log2 and computes mean seconds-per-tag
    after trimming the slowest 10% of intervals.

    The name remains unchanged to avoid breaking existing imports and strategy
    wiring that depend on this identifier.
    """

    def speed_log2(self, tagger: "Tagger") -> float:  # keep method name required by Protocol
        """Return mean seconds per tag between consecutive assignments.

        NOTE: historically this method returned the mean of log2(seconds).
        NOTE: it now returns the mean seconds-per-tag (raw seconds) instead.
        NOTE: the name `speed_log2` remains for compatibility with callers.
        """  # method docstring

        # collect assignments or empty list
        all_assignments = tagger.tagassignments or []  # get assignments list
        # filter out assignments missing timestamps
        valid = [ta for ta in all_assignments if getattr(ta, "timestamp", None) is not None]  # filter timestamps
        # need at least two valid timestamps to form a delta
        if len(valid) < 2:  # check count
            return 0.0  # not enough data

        # sort by timestamp to get chronological order
        sorted_assignments = sorted(valid, key=lambda ta: ta.timestamp)  # sort by time
        # prepare list of positive deltas in seconds
        deltas: List[float] = []  # list for deltas
        # iterate consecutive pairs to compute deltas
        for i in range(1, len(sorted_assignments)):  # loop pairs
            # previous timestamp
            t0 = sorted_assignments[i - 1].timestamp  # previous ts
            # current timestamp
            t1 = sorted_assignments[i].timestamp  # current ts
            # compute difference in seconds between consecutive timestamps
>>>>>>> 3433ff6 (Revert to compute raw seconds no log transform)
            try:
                delta_seconds = (t1 - t0).total_seconds()  # compute delta
            except Exception:
<<<<<<< HEAD
                continue
            if delta_seconds > 0:
                intervals.append(delta_seconds)

        if not intervals:
            return 0.0

        intervals_sorted = sorted(intervals)
        n = len(intervals_sorted)
        trim_count = int(math.floor(n * TRIM_FRACTION))  # 10%

        if trim_count > 0:
            trimmed = intervals_sorted[: max(1, n - trim_count)]
        else:
            trimmed = intervals_sorted

=======
                # skip pairs that error during subtraction
                continue  # skip on error
            # keep only strictly positive intervals
            if delta_seconds > 0:  # positive check
                deltas.append(delta_seconds)  # add to deltas

        # if no positive deltas, return zero as default
        if not deltas:  # nothing to average
            return 0.0  # fallback

        # compute how many to trim from the upper tail (floor)
        n = len(deltas)  # number of deltas
        trim_count = int(n * TRIM_FRACTION)  # floor trim count
        # sort deltas ascending so we can drop the largest ones
        sorted_deltas = sorted(deltas)  # sort ascending
        # remove largest trim_count deltas from the end
        if trim_count <= 0:  # nothing to trim
            trimmed = sorted_deltas[:]  # keep all
        else:
            trimmed = sorted_deltas[: max(0, len(sorted_deltas) - trim_count)]  # drop largest
        # if trimming removed everything, fallback to the full set
        if not trimmed:  # ensure non-empty
            trimmed = sorted_deltas  # fallback to sorted
        # compute mean of the trimmed set and return as float
>>>>>>> 3433ff6 (Revert to compute raw seconds no log transform)
        try:
            return float(statistics.mean(trimmed))  # return mean seconds per tag
        except statistics.StatisticsError:
<<<<<<< HEAD
            return 0.0
=======
            # return zero on any statistics error during mean calculation
            return 0.0  # error fallback
>>>>>>> 3433ff6 (Revert to compute raw seconds no log transform)
