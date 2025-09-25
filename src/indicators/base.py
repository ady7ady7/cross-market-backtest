"""
Base indicator class for all technical indicators.
Provides common interface and utilities for indicator calculations.
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional


class BaseIndicator(ABC):
    """
    Abstract base class for all technical indicators.
    """

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize base indicator.

        Args:
            name: Indicator name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.data = None
        self.calculated = False

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values.

        Args:
            data: OHLCV DataFrame with timestamp, open, high, low, close, volume

        Returns:
            DataFrame with indicator values and timestamps
        """
        pass

    @abstractmethod
    def get_plot_data(self) -> Dict[str, Any]:
        """
        Get data formatted for plotting.

        Returns:
            Dictionary with plot configuration and data
        """
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data format.

        Args:
            data: Input DataFrame

        Returns:
            True if data is valid
        """
        required_columns = ['timestamp', 'open', 'high', 'low', 'close']
        return all(col in data.columns for col in required_columns)

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema for UI generation.

        Returns:
            Dictionary describing configuration options
        """
        return {
            'name': self.name,
            'parameters': {}
        }