"""
Trading Strategies Module

This module contains all trading strategies for backtesting.
Each strategy should be in its own file and inherit from BaseStrategy.
"""

from .base_strategy_template import StrategyMetadata
from .simple_ma_crossover import SimpleMAStrategy
from .hts_trend_follow import HTSTrendFollowStrategy

# Strategy Registry - automatically populated for UI
AVAILABLE_STRATEGIES = {
    'simple_ma': SimpleMAStrategy,
    'hts_trend': HTSTrendFollowStrategy,
}


def get_strategy_class(strategy_id: str):
    """Get strategy class by ID"""
    return AVAILABLE_STRATEGIES.get(strategy_id)


def list_strategies():
    """List all available strategies with metadata"""
    return {
        strategy_id: strategy_class.get_metadata()
        for strategy_id, strategy_class in AVAILABLE_STRATEGIES.items()
    }
