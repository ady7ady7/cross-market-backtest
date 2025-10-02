"""
Performance tracking and metrics calculation.

Tracks equity curve, drawdowns, and various performance metrics.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """
    Comprehensive performance metrics for backtesting results.
    """
    # Basic metrics
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # P&L metrics
    total_pnl: float
    avg_win: float
    avg_loss: float
    avg_trade: float
    max_win: float
    max_loss: float
    profit_factor: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_pct: float
    avg_drawdown: float
    avg_drawdown_pct: float
    max_drawdown_duration_days: int

    # Risk-adjusted returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade duration
    avg_trade_duration_bars: float
    max_trade_duration_bars: int

    # R-multiples
    avg_r_multiple: float
    expectancy: float  # Average $ per trade


class PerformanceTracker:
    """
    Tracks performance metrics during backtesting.
    """

    def __init__(self, initial_capital: float):
        """
        Initialize performance tracker.

        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital

        # Equity tracking
        self.equity_curve: List[Dict] = []
        self.equity_timestamps: List[datetime] = []
        self.equity_values: List[float] = []

        # Drawdown tracking
        self.peak_equity = initial_capital
        self.current_drawdown = 0.0
        self.drawdown_start_time: Optional[datetime] = None
        self.drawdowns: List[Dict] = []

    def update(self, timestamp: datetime, current_capital: float,
               open_positions_pnl: float = 0.0):
        """
        Update equity curve and drawdown tracking.

        Args:
            timestamp: Current timestamp
            current_capital: Current account balance (realized)
            open_positions_pnl: Unrealized P&L from open positions
        """
        # Total equity = realized capital + unrealized P&L
        total_equity = current_capital + open_positions_pnl

        # Update equity curve
        self.equity_timestamps.append(timestamp)
        self.equity_values.append(total_equity)
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity,
            'realized': current_capital,
            'unrealized': open_positions_pnl
        })

        # Update drawdown
        if total_equity > self.peak_equity:
            # New peak, close any open drawdown
            if self.drawdown_start_time is not None:
                self.drawdowns.append({
                    'start_time': self.drawdown_start_time,
                    'end_time': timestamp,
                    'max_drawdown': self.current_drawdown,
                    'max_drawdown_pct': (self.current_drawdown / self.peak_equity) * 100
                })
                self.drawdown_start_time = None

            self.peak_equity = total_equity
            self.current_drawdown = 0.0
        else:
            # In drawdown
            drawdown = self.peak_equity - total_equity
            if drawdown > self.current_drawdown:
                self.current_drawdown = drawdown
                if self.drawdown_start_time is None:
                    self.drawdown_start_time = timestamp

    def calculate_metrics(self, closed_positions: List) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            closed_positions: List of closed Position objects

        Returns:
            PerformanceMetrics object
        """
        if not self.equity_values:
            print(f"Debug: equity_timestamps count: {len(self.equity_timestamps)}")
            print(f"Debug: equity_curve count: {len(self.equity_curve)}")
            print(f"Debug: closed_positions count: {len(closed_positions)}")
            raise ValueError("No equity data to calculate metrics. The backtest loop may not have run or update() was never called.")

        final_capital = self.equity_values[-1]

        # Basic metrics
        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100

        # Trade statistics
        total_trades = len(closed_positions)
        wins = [p for p in closed_positions if p.realized_pnl > 0]
        losses = [p for p in closed_positions if p.realized_pnl < 0]
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L metrics
        total_pnl = sum(p.realized_pnl for p in closed_positions)
        avg_win = np.mean([p.realized_pnl for p in wins]) if wins else 0.0
        avg_loss = np.mean([p.realized_pnl for p in losses]) if losses else 0.0
        avg_trade = total_pnl / total_trades if total_trades > 0 else 0.0
        max_win = max([p.realized_pnl for p in wins]) if wins else 0.0
        max_loss = min([p.realized_pnl for p in losses]) if losses else 0.0

        # Profit factor
        gross_profit = sum(p.realized_pnl for p in wins)
        gross_loss = abs(sum(p.realized_pnl for p in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Drawdown metrics
        max_dd, max_dd_pct, avg_dd, avg_dd_pct, max_dd_duration = self._calculate_drawdown_metrics()

        # Risk-adjusted returns
        sharpe = self._calculate_sharpe_ratio()
        sortino = self._calculate_sortino_ratio()
        calmar = abs(total_return_pct / max_dd_pct) if max_dd_pct != 0 else 0.0

        # Trade duration
        durations = [p.bars_held for p in closed_positions]
        avg_duration = np.mean(durations) if durations else 0.0
        max_duration = max(durations) if durations else 0

        # R-multiples
        r_multiples = [p.r_multiple for p in closed_positions if p.r_multiple != 0]
        avg_r = np.mean(r_multiples) if r_multiples else 0.0
        expectancy = avg_trade  # Average $ per trade

        return PerformanceMetrics(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            max_win=max_win,
            max_loss=max_loss,
            profit_factor=profit_factor,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            avg_drawdown=avg_dd,
            avg_drawdown_pct=avg_dd_pct,
            max_drawdown_duration_days=max_dd_duration,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            avg_trade_duration_bars=avg_duration,
            max_trade_duration_bars=max_duration,
            avg_r_multiple=avg_r,
            expectancy=expectancy
        )

    def _calculate_drawdown_metrics(self) -> tuple:
        """Calculate drawdown metrics from equity curve"""
        equity_array = np.array(self.equity_values)

        # Calculate running maximum
        running_max = np.maximum.accumulate(equity_array)

        # Calculate drawdown in dollars
        drawdown = running_max - equity_array

        # Calculate drawdown in percentage
        drawdown_pct = (drawdown / running_max) * 100

        max_dd = np.max(drawdown)
        max_dd_pct = np.max(drawdown_pct)

        # Average drawdown (when in drawdown)
        drawdowns_only = drawdown[drawdown > 0]
        avg_dd = np.mean(drawdowns_only) if len(drawdowns_only) > 0 else 0.0

        drawdown_pct_only = drawdown_pct[drawdown_pct > 0]
        avg_dd_pct = np.mean(drawdown_pct_only) if len(drawdown_pct_only) > 0 else 0.0

        # Maximum drawdown duration
        max_dd_duration = 0
        if self.drawdowns:
            for dd in self.drawdowns:
                duration = (dd['end_time'] - dd['start_time']).days
                max_dd_duration = max(max_dd_duration, duration)

        return max_dd, max_dd_pct, avg_dd, avg_dd_pct, max_dd_duration

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0,
                                periods_per_year: int = 252) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            risk_free_rate: Annual risk-free rate (default 0%)
            periods_per_year: Number of trading periods per year (252 for daily)

        Returns:
            Sharpe ratio
        """
        if len(self.equity_values) < 2:
            return 0.0

        # Calculate returns
        returns = pd.Series(self.equity_values).pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return 0.0

        # Annualized return
        total_return = (self.equity_values[-1] / self.equity_values[0]) - 1
        periods = len(self.equity_values)
        annualized_return = (1 + total_return) ** (periods_per_year / periods) - 1

        # Annualized volatility
        annualized_vol = returns.std() * np.sqrt(periods_per_year)

        # Sharpe ratio
        sharpe = (annualized_return - risk_free_rate) / annualized_vol

        return sharpe

    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.0,
                                 periods_per_year: int = 252) -> float:
        """
        Calculate Sortino ratio (similar to Sharpe but only considers downside deviation).

        Args:
            risk_free_rate: Annual risk-free rate (default 0%)
            periods_per_year: Number of trading periods per year

        Returns:
            Sortino ratio
        """
        if len(self.equity_values) < 2:
            return 0.0

        # Calculate returns
        returns = pd.Series(self.equity_values).pct_change().dropna()

        if len(returns) == 0:
            return 0.0

        # Annualized return
        total_return = (self.equity_values[-1] / self.equity_values[0]) - 1
        periods = len(self.equity_values)
        annualized_return = (1 + total_return) ** (periods_per_year / periods) - 1

        # Downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf')  # No downside = infinite Sortino

        downside_deviation = downside_returns.std() * np.sqrt(periods_per_year)

        # Sortino ratio
        sortino = (annualized_return - risk_free_rate) / downside_deviation

        return sortino

    def get_equity_dataframe(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve)

    def get_drawdown_dataframe(self) -> pd.DataFrame:
        """Get drawdown history as DataFrame"""
        if not self.equity_values:
            return pd.DataFrame()

        equity_array = np.array(self.equity_values)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = running_max - equity_array
        drawdown_pct = (drawdown / running_max) * 100

        return pd.DataFrame({
            'timestamp': self.equity_timestamps,
            'equity': equity_array,
            'peak': running_max,
            'drawdown': drawdown,
            'drawdown_pct': drawdown_pct
        })