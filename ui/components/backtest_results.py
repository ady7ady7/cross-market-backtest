"""
Backtesting results visualization components.

Displays equity curves, performance metrics, trade analysis, and charts.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, Any


class BacktestResults:
    """Manages backtest results visualization"""

    @staticmethod
    def show_results(results: Dict[str, Any], symbol: str):
        """
        Display comprehensive backtest results.

        Args:
            results: Dictionary containing backtest results
            symbol: Symbol that was backtested
        """
        st.header(f"📊 Backtest Results: {symbol}")

        overall_metrics = results['overall_metrics']
        strategy_metrics = results.get('strategy_metrics', {})
        equity_df = results['equity_curve']
        drawdown_df = results['drawdown_curve']
        trades_df = results['trades']

        # Summary metrics at top
        BacktestResults._show_summary_metrics(overall_metrics)

        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Equity Curve",
            "📉 Drawdown Analysis",
            "💼 Trade Analysis",
            "📋 Detailed Metrics"
        ])

        with tab1:
            BacktestResults._show_equity_curve(equity_df, overall_metrics)

        with tab2:
            BacktestResults._show_drawdown_analysis(drawdown_df, overall_metrics)

        with tab3:
            BacktestResults._show_trade_analysis(trades_df, results.get('all_positions', []))

        with tab4:
            BacktestResults._show_detailed_metrics(overall_metrics, strategy_metrics)

        # Strategy-specific results if multiple strategies
        if len(strategy_metrics) > 1:
            st.markdown("---")
            st.subheader("📊 Per-Strategy Performance")
            BacktestResults._show_strategy_comparison(strategy_metrics)

    @staticmethod
    def _show_summary_metrics(metrics):
        """Display key metrics in a summary card"""
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Return",
                f"${metrics.total_return:,.0f}",
                f"{metrics.total_return_pct:.2f}%"
            )

        with col2:
            st.metric(
                "Win Rate",
                f"{metrics.win_rate:.1f}%",
                f"{metrics.winning_trades}/{metrics.total_trades} trades"
            )

        with col3:
            st.metric(
                "Profit Factor",
                f"{metrics.profit_factor:.2f}",
                "Higher is better"
            )

        with col4:
            st.metric(
                "Max Drawdown",
                f"{metrics.max_drawdown_pct:.2f}%",
                f"${metrics.max_drawdown:,.0f}"
            )

        with col5:
            st.metric(
                "Sharpe Ratio",
                f"{metrics.sharpe_ratio:.2f}",
                "Risk-adjusted"
            )

    @staticmethod
    def _show_equity_curve(equity_df: pd.DataFrame, metrics):
        """Display equity curve with realized and unrealized components"""
        st.subheader("Equity Curve")

        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=("Total Equity", "Unrealized P&L"),
            vertical_spacing=0.1
        )

        # Total equity
        fig.add_trace(
            go.Scatter(
                x=equity_df['timestamp'],
                y=equity_df['equity'],
                name='Total Equity',
                line=dict(color='#00CC96', width=2),
                fill='tonexty',
                fillcolor='rgba(0, 204, 150, 0.1)'
            ),
            row=1, col=1
        )

        # Starting capital line
        fig.add_trace(
            go.Scatter(
                x=equity_df['timestamp'],
                y=[metrics.initial_capital] * len(equity_df),
                name='Initial Capital',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )

        # Unrealized P&L
        fig.add_trace(
            go.Scatter(
                x=equity_df['timestamp'],
                y=equity_df['unrealized'],
                name='Unrealized P&L',
                line=dict(color='#FFA500', width=1),
                fill='tozeroy'
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        fig.update_yaxes(title_text="P&L ($)", row=2, col=1)

        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, width="stretch")

        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Initial Capital", f"${metrics.initial_capital:,.0f}")
        with col2:
            st.metric("Final Capital", f"${metrics.final_capital:,.0f}")
        with col3:
            st.metric("Peak Capital", f"${equity_df['equity'].max():,.0f}")

    @staticmethod
    def _show_drawdown_analysis(drawdown_df: pd.DataFrame, metrics):
        """Display drawdown analysis"""
        st.subheader("Drawdown Analysis")

        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.5, 0.5],
            subplot_titles=("Equity vs Peak", "Drawdown %"),
            vertical_spacing=0.15
        )

        # Equity vs Peak
        fig.add_trace(
            go.Scatter(
                x=drawdown_df['timestamp'],
                y=drawdown_df['equity'],
                name='Equity',
                line=dict(color='#00CC96', width=2)
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=drawdown_df['timestamp'],
                y=drawdown_df['peak'],
                name='Peak Equity',
                line=dict(color='#636EFA', width=1, dash='dash')
            ),
            row=1, col=1
        )

        # Drawdown percentage
        fig.add_trace(
            go.Scatter(
                x=drawdown_df['timestamp'],
                y=-drawdown_df['drawdown_pct'],  # Negative for visual
                name='Drawdown %',
                line=dict(color='#EF553B', width=2),
                fill='tozeroy',
                fillcolor='rgba(239, 85, 59, 0.3)'
            ),
            row=2, col=1
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Equity ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        fig.update_layout(
            height=600,
            hovermode='x unified',
            showlegend=True
        )

        st.plotly_chart(fig, width="stretch")

        # Drawdown statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%")
        with col2:
            st.metric("Max DD ($)", f"${metrics.max_drawdown:,.0f}")
        with col3:
            st.metric("Avg Drawdown", f"{metrics.avg_drawdown_pct:.2f}%")
        with col4:
            st.metric("Max DD Duration", f"{metrics.max_drawdown_duration_days} days")

    @staticmethod
    def _show_trade_analysis(trades_df: pd.DataFrame, positions: list):
        """Display trade-by-trade analysis"""
        st.subheader("Trade Analysis")

        if trades_df.empty:
            st.info("No trades executed")
            return

        # Filter for entry/exit trades
        entries = trades_df[trades_df['action'] == 'ENTRY']
        exits = trades_df[trades_df['action'] == 'EXIT']

        st.markdown(f"**Total Signals: {len(entries)}** | **Closed Trades: {len(exits)}**")

        # Trade distribution chart
        if len(exits) > 0:
            col1, col2 = st.columns(2)

            with col1:
                # P&L distribution
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=exits['pnl'],
                    nbinsx=30,
                    name='P&L Distribution',
                    marker_color='#00CC96'
                ))
                fig.update_layout(
                    title="P&L Distribution",
                    xaxis_title="P&L ($)",
                    yaxis_title="Number of Trades",
                    height=300
                )
                st.plotly_chart(fig, width="stretch")

            with col2:
                # R-multiple distribution
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=exits['r_multiple'],
                    nbinsx=30,
                    name='R-Multiple Distribution',
                    marker_color='#636EFA'
                ))
                fig.update_layout(
                    title="R-Multiple Distribution",
                    xaxis_title="R-Multiple",
                    yaxis_title="Number of Trades",
                    height=300
                )
                st.plotly_chart(fig, width="stretch")

        # Trade log table
        st.markdown("**Recent Trades**")

        if len(exits) > 0:
            # Create display dataframe with all important columns
            display_df = exits[['side', 'entry_time', 'entry_price', 'timestamp', 'exit_type', 'price', 'pnl', 'r_multiple', 'strategy']].copy()

            # Rename columns for clarity
            display_df = display_df.rename(columns={
                'side': 'Type',
                'entry_time': 'Entry Time',
                'entry_price': 'Entry Price',
                'timestamp': 'Exit Time',
                'exit_type': 'Exit Type',
                'price': 'Exit Price',
                'pnl': 'P&L',
                'r_multiple': 'R-Multiple',
                'strategy': 'Strategy'
            })

            # Format columns
            display_df['Entry Price'] = display_df['Entry Price'].apply(lambda x: f"${x:,.4f}")
            display_df['Exit Price'] = display_df['Exit Price'].apply(lambda x: f"${x:,.4f}")
            display_df['P&L'] = display_df['P&L'].apply(lambda x: f"${x:,.2f}")
            display_df['R-Multiple'] = display_df['R-Multiple'].apply(lambda x: f"{x:.2f}R")

            st.dataframe(
                display_df.tail(50),
                width="stretch",
                hide_index=True
            )

            # Download trades
            csv = trades_df.to_csv(index=False)
            st.download_button(
                label="📥 Download All Trades (CSV)",
                data=csv,
                file_name="backtest_trades.csv",
                mime="text/csv"
            )

    @staticmethod
    def _show_detailed_metrics(overall_metrics, strategy_metrics):
        """Display detailed performance metrics"""
        st.subheader("Detailed Performance Metrics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Trade Statistics**")
            st.write(f"Total Trades: {overall_metrics.total_trades}")
            st.write(f"Winning Trades: {overall_metrics.winning_trades}")
            st.write(f"Losing Trades: {overall_metrics.losing_trades}")
            st.write(f"Win Rate: {overall_metrics.win_rate:.2f}%")

            st.markdown("**💰 P&L Metrics**")
            st.write(f"Total P&L: ${overall_metrics.total_pnl:,.2f}")
            st.write(f"Average Win: ${overall_metrics.avg_win:,.2f}")
            st.write(f"Average Loss: ${overall_metrics.avg_loss:,.2f}")
            st.write(f"Average Trade: ${overall_metrics.avg_trade:,.2f}")
            st.write(f"Largest Win: ${overall_metrics.max_win:,.2f}")
            st.write(f"Largest Loss: ${overall_metrics.max_loss:,.2f}")
            st.write(f"Profit Factor: {overall_metrics.profit_factor:.2f}")

        with col2:
            st.markdown("**📉 Risk Metrics**")
            st.write(f"Max Drawdown: ${overall_metrics.max_drawdown:,.2f}")
            st.write(f"Max DD %: {overall_metrics.max_drawdown_pct:.2f}%")
            st.write(f"Avg Drawdown: ${overall_metrics.avg_drawdown:,.2f}")
            st.write(f"Avg DD %: {overall_metrics.avg_drawdown_pct:.2f}%")
            st.write(f"Max DD Duration: {overall_metrics.max_drawdown_duration_days} days")

            st.markdown("**📈 Risk-Adjusted Returns**")
            st.write(f"Sharpe Ratio: {overall_metrics.sharpe_ratio:.2f}")
            st.write(f"Sortino Ratio: {overall_metrics.sortino_ratio:.2f}")
            st.write(f"Calmar Ratio: {overall_metrics.calmar_ratio:.2f}")

            st.markdown("**⏱️ Trade Duration**")
            st.write(f"Avg Duration: {overall_metrics.avg_trade_duration_bars:.1f} bars")
            st.write(f"Max Duration: {overall_metrics.max_trade_duration_bars} bars")

            st.markdown("**🎯 Expectancy**")
            st.write(f"Avg R-Multiple: {overall_metrics.avg_r_multiple:.2f}R")
            st.write(f"Expectancy: ${overall_metrics.expectancy:.2f}")

    @staticmethod
    def _show_strategy_comparison(strategy_metrics: Dict):
        """Compare performance across multiple strategies"""
        comparison_data = []

        for strategy_name, metrics in strategy_metrics.items():
            comparison_data.append({
                'Strategy': strategy_name,
                'Total Trades': metrics.total_trades,
                'Win Rate': f"{metrics.win_rate:.2f}%",
                'Total P&L': f"${metrics.total_pnl:,.2f}",
                'Profit Factor': f"{metrics.profit_factor:.2f}",
                'Avg R': f"{metrics.avg_r_multiple:.2f}R",
                'Sharpe': f"{metrics.sharpe_ratio:.2f}"
            })

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, width="stretch", hide_index=True)