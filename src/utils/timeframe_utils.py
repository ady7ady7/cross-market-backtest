"""
Timeframe normalization and conversion utilities.

Handles different timeframe naming conventions across:
- Database format: m1, m5, h1, d1
- Human-readable format: 1m, 5m, 1h, 1d
- Long format: 1min, 5min, 1hour, 1day
"""

from typing import Optional, Dict, List
import re


class TimeframeNormalizer:
    """
    Normalizes timeframe formats across different naming conventions.

    Supports conversions between:
    - Database format: m1, m5, m15, h1, h4, d1
    - Standard format: 1m, 5m, 15m, 1h, 4h, 1d
    """

    # Mapping of standard formats to database formats
    STANDARD_TO_DB = {
        '1m': 'm1',
        '5m': 'm5',
        '15m': 'm15',
        '30m': 'm30',
        '1h': 'h1',
        '2h': 'h2',
        '4h': 'h4',
        '6h': 'h6',
        '8h': 'h8',
        '12h': 'h12',
        '1d': 'd1',
        '1w': 'w1',
        '1M': 'M1'  # Month
    }

    # Reverse mapping
    DB_TO_STANDARD = {v: k for k, v in STANDARD_TO_DB.items()}

    # Timeframe to minutes conversion
    TIMEFRAME_TO_MINUTES = {
        'm1': 1, '1m': 1,
        'm5': 5, '5m': 5,
        'm15': 15, '15m': 15,
        'm30': 30, '30m': 30,
        'h1': 60, '1h': 60,
        'h2': 120, '2h': 120,
        'h4': 240, '4h': 240,
        'h6': 360, '6h': 360,
        'h8': 480, '8h': 480,
        'h12': 720, '12h': 720,
        'd1': 1440, '1d': 1440,
        'w1': 10080, '1w': 10080,
        'M1': 43200, '1M': 43200
    }

    @classmethod
    def to_standard(cls, timeframe: str) -> str:
        """
        Convert any timeframe format to standard format (1m, 5m, 1h, etc.).

        Args:
            timeframe: Timeframe in any format (m5, 5m, etc.)

        Returns:
            Standardized timeframe string

        Examples:
            >>> TimeframeNormalizer.to_standard('m5')
            '5m'
            >>> TimeframeNormalizer.to_standard('h1')
            '1h'
        """
        if not timeframe:
            return None

        # Already in standard format
        if timeframe in cls.STANDARD_TO_DB:
            return timeframe

        # In database format
        if timeframe in cls.DB_TO_STANDARD:
            return cls.DB_TO_STANDARD[timeframe]

        # Try parsing with regex
        match = re.match(r'^([mhdwM])(\d+)$', timeframe)
        if match:
            unit, num = match.groups()
            return f"{num}{unit}"

        # Unknown format, return as-is
        return timeframe

    @classmethod
    def to_db_format(cls, timeframe: str) -> str:
        """
        Convert any timeframe format to database format (m5, h1, etc.).

        Args:
            timeframe: Timeframe in any format (5m, 1h, etc.)

        Returns:
            Database format timeframe string

        Examples:
            >>> TimeframeNormalizer.to_db_format('5m')
            'm5'
            >>> TimeframeNormalizer.to_db_format('1h')
            'h1'
        """
        if not timeframe:
            return None

        # Already in database format
        if timeframe in cls.DB_TO_STANDARD:
            return timeframe

        # In standard format
        if timeframe in cls.STANDARD_TO_DB:
            return cls.STANDARD_TO_DB[timeframe]

        # Try parsing with regex
        match = re.match(r'^(\d+)([mhdwM])$', timeframe)
        if match:
            num, unit = match.groups()
            return f"{unit}{num}"

        # Unknown format, return as-is
        return timeframe

    @classmethod
    def normalize_list(cls, timeframes: List[str], target_format: str = 'standard') -> List[str]:
        """
        Normalize a list of timeframes to a consistent format.

        Args:
            timeframes: List of timeframes in various formats
            target_format: Target format ('standard' or 'db')

        Returns:
            List of normalized timeframes
        """
        if not timeframes:
            return []

        if target_format == 'db':
            return [cls.to_db_format(tf) for tf in timeframes]
        else:
            return [cls.to_standard(tf) for tf in timeframes]

    @classmethod
    def to_minutes(cls, timeframe: str) -> Optional[int]:
        """
        Convert timeframe to minutes.

        Args:
            timeframe: Timeframe in any format

        Returns:
            Number of minutes or None if unknown
        """
        # Try direct lookup
        if timeframe in cls.TIMEFRAME_TO_MINUTES:
            return cls.TIMEFRAME_TO_MINUTES[timeframe]

        # Try normalizing first
        normalized = cls.to_standard(timeframe)
        return cls.TIMEFRAME_TO_MINUTES.get(normalized)

    @classmethod
    def are_equivalent(cls, tf1: str, tf2: str) -> bool:
        """
        Check if two timeframes are equivalent (same duration, different format).

        Args:
            tf1: First timeframe
            tf2: Second timeframe

        Returns:
            True if timeframes represent the same duration

        Examples:
            >>> TimeframeNormalizer.are_equivalent('m5', '5m')
            True
            >>> TimeframeNormalizer.are_equivalent('h1', '1h')
            True
        """
        return cls.to_standard(tf1) == cls.to_standard(tf2)

    @classmethod
    def find_matching_timeframe(cls, target: str, available: List[str]) -> Optional[str]:
        """
        Find a matching timeframe from available list, accounting for format differences.

        Args:
            target: Target timeframe to find
            available: List of available timeframes

        Returns:
            Matching timeframe from available list, or None

        Examples:
            >>> TimeframeNormalizer.find_matching_timeframe('5m', ['m1', 'm5', 'h1'])
            'm5'
            >>> TimeframeNormalizer.find_matching_timeframe('1h', ['m5', 'h1', 'd1'])
            'h1'
        """
        target_standard = cls.to_standard(target)

        for tf in available:
            if cls.to_standard(tf) == target_standard:
                return tf

        return None

    @classmethod
    def get_column_prefix(cls, timeframe: str, available_columns: List[str]) -> Optional[str]:
        """
        Get the actual column prefix used in a DataFrame for a given timeframe.

        This handles cases where data might use 'm5_close' or '5m_close'.

        Args:
            timeframe: Desired timeframe
            available_columns: List of available column names

        Returns:
            The actual prefix used (e.g., 'm5', '5m'), or None if not found

        Examples:
            >>> cols = ['timestamp', 'close', 'm5_close', 'h1_close']
            >>> TimeframeNormalizer.get_column_prefix('5m', cols)
            'm5'
        """
        # Try both formats
        db_format = cls.to_db_format(timeframe)
        standard_format = cls.to_standard(timeframe)

        for prefix in [db_format, standard_format, timeframe]:
            # Check if any column starts with this prefix
            for col in available_columns:
                if col.startswith(f"{prefix}_"):
                    return prefix

        return None


# Convenience functions for quick access
def normalize_timeframe(tf: str, target_format: str = 'standard') -> str:
    """Normalize a single timeframe."""
    if target_format == 'db':
        return TimeframeNormalizer.to_db_format(tf)
    return TimeframeNormalizer.to_standard(tf)


def find_matching_timeframes(required: List[str], available: List[str]) -> Dict[str, Optional[str]]:
    """
    Find matching timeframes for a list of required timeframes.

    Returns:
        Dictionary mapping required timeframe to matched available timeframe
    """
    return {
        req: TimeframeNormalizer.find_matching_timeframe(req, available)
        for req in required
    }
