"""
Base Strategy Template

This file provides a template and documentation for creating new strategies.
All strategies should follow this pattern for consistent UI integration.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from ..backtesting.strategy import BaseStrategy


@dataclass
class StrategyMetadata:
    """
    Strategy metadata for UI display and configuration.

    This tells the UI:
    - What timeframes are required
    - What SL/TP settings the strategy uses
    - What parameters can be configured
    """
    # Basic info
    id: str                           # Unique identifier (e.g., 'hts_trend')
    name: str                         # Display name (e.g., 'HTS Trend Follow')
    description: str                  # Short description for UI

    # Timeframe requirements
    required_timeframes: List[str]    # e.g., ['5m', '1h'] - MUST be selected
    base_timeframe: str               # e.g., '5m' - primary timeframe for entries

    # SL/TP configuration
    uses_custom_sl: bool = False      # True if strategy sets SL dynamically
    uses_custom_tp: bool = False      # True if strategy sets TP dynamically
    default_sl_type: str = 'percent'  # 'percent', 'price', 'time', 'condition'
    default_tp_type: str = 'rr'       # 'percent', 'rr', 'time', 'condition'

    # UI configuration
    configurable_params: Dict[str, Dict] = None  # Parameters user can adjust

    def __post_init__(self):
        if self.configurable_params is None:
            self.configurable_params = {}


# Example strategy template
class StrategyTemplate(BaseStrategy):
    """
    Template for creating new strategies.

    INSTRUCTIONS:
    1. Copy this template to a new file (e.g., my_strategy.py)
    2. Rename the class
    3. Fill in get_metadata() with your strategy's requirements
    4. Implement generate_signals() and should_exit()
    5. Add to __init__.py AVAILABLE_STRATEGIES

    IMPORTANT CONCEPTS:

    A) SL/TP Configuration:

       Option 1: Use UI settings (user controls everything)
       - Set uses_custom_sl = False, uses_custom_tp = False
       - Strategy respects whatever user sets in UI

       Option 2: Strategy controls SL/TP (like HTS)
       - Set uses_custom_sl = True and/or uses_custom_tp = True
       - In signal metadata, set 'sl_price' or 'tp_price'
       - UI will show "Strategy-controlled" instead of inputs

    B) Timeframes:

       - List ALL required timeframes in required_timeframes
       - UI will auto-select them and show warning if missing
       - Access via self.timeframes in your code

    C) Parameters:

       - Define in configurable_params for UI inputs
       - Access via self.config['param_name'] in your code
    """

    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        """
        Return strategy metadata for UI integration.

        This is the KEY method that tells the UI:
        - What this strategy needs
        - How to configure it
        - What SL/TP behavior to expect
        """
        return StrategyMetadata(
            id='template',
            name='Strategy Template',
            description='Example template for creating strategies',

            # Timeframes this strategy uses
            required_timeframes=['5m'],  # Can be multiple: ['5m', '1h']
            base_timeframe='5m',

            # Does strategy control SL/TP or does user?
            uses_custom_sl=False,  # False = user sets in UI
            uses_custom_tp=False,  # False = user sets in UI
            default_sl_type='percent',
            default_tp_type='rr',

            # Parameters user can configure in UI
            configurable_params={
                'example_period': {
                    'type': 'number',
                    'label': 'Example Period',
                    'default': 20,
                    'min': 5,
                    'max': 200,
                    'help': 'Period for calculation'
                }
            }
        )

    def __init__(self, config: dict = None):
        """Initialize strategy with config"""
        metadata = self.get_metadata()

        default_config = {
            'risk_percent': 1.0,
            'timeframes': metadata.required_timeframes,
            # Add defaults from metadata
            **{k: v['default'] for k, v in metadata.configurable_params.items()}
        }

        if config:
            default_config.update(config)

        super().__init__(
            name=metadata.name,
            timeframes=default_config['timeframes'],
            config=default_config
        )

    def generate_signals(self, data, timestamp):
        """
        Generate trading signals.

        If uses_custom_sl/tp = True, set in signal.metadata:
            signal.metadata['sl_price'] = your_sl_level
            signal.metadata['tp_price'] = your_tp_level

        Otherwise, position manager uses UI settings.
        """
        # Your strategy logic here
        return None

    def should_exit(self, position, data, timestamp):
        """Check strategy-specific exit conditions"""
        return False
