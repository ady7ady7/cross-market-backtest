"""
Chart utilities for creating interactive financial charts.
Designed to be modular and reusable for different components.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_interactive_candlestick_chart(chart_data, symbol_name, height=600):
    """
    Create an interactive candlestick chart with enhanced zoom and pan functionality.

    Args:
        chart_data: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close']
        symbol_name: String name of the symbol for chart title
        height: Chart height in pixels (default 600)

    Returns:
        tuple: (plotly figure, plotly config dict)
    """

    fig = go.Figure()

    # Add candlestick trace with enhanced dark theme colors
    fig.add_trace(go.Candlestick(
        x=chart_data['timestamp'],
        open=chart_data['open'],
        high=chart_data['high'],
        low=chart_data['low'],
        close=chart_data['close'],
        name=symbol_name,
        increasing_line_color='#00dd77',
        decreasing_line_color='#ff5555',
        increasing_fillcolor='rgba(0, 221, 119, 0.8)',
        decreasing_fillcolor='rgba(255, 85, 85, 0.8)'
    ))

    # Enhanced layout for smooth interactivity with dark theme
    fig.update_layout(
        title=dict(
            text=f"{symbol_name} Price Chart - Interactive",
            font=dict(color='#e0e0e0', size=16)
        ),
        xaxis_title="Time",
        yaxis_title="Price",
        height=height,
        font=dict(color='#e0e0e0'),

        # Enhanced interactivity settings
        dragmode='pan',

        # Smooth zoom and pan configuration
        xaxis=dict(
            rangeslider=dict(visible=False),  # Disable range slider for cleaner look
            type='date',
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            showline=True,
            showgrid=True,
            gridcolor='#404040',
            linecolor='#606060',
            tickfont=dict(color='#e0e0e0'),
            titlefont=dict(color='#e0e0e0'),
            fixedrange=False,  # Allow zoom on x-axis
            # Improved axis interaction
            autorange=True,
            constrain="domain"
        ),

        yaxis=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            showline=True,
            showgrid=True,
            gridcolor='#404040',
            linecolor='#606060',
            tickfont=dict(color='#e0e0e0'),
            titlefont=dict(color='#e0e0e0'),
            fixedrange=False,  # Allow zoom on y-axis
            # Improved axis interaction
            autorange=True,
            constrain="domain"
        ),

        # Hover configuration for better UX
        hovermode='x unified',

        # Dark theme styling
        plot_bgcolor='#1e1e1e',
        paper_bgcolor='#2d2d2d',

        # Remove margins for more chart space
        margin=dict(l=0, r=0, t=40, b=0),

        # Enhanced interaction configuration
        updatemenus=[],
        annotations=[]
    )

    # Configure advanced interactivity - clean and focused
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': [
            'lasso2d', 'select2d', 'drawline', 'drawopenpath',
            'drawclosedpath', 'drawcircle', 'drawrect', 'eraseshape'
        ],
        'scrollZoom': True,  # Enable mouse wheel zoom
        'doubleClick': 'reset+autosize',  # Double click to reset zoom
        'showTips': True,
        'responsive': True,
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'{symbol_name}_chart',
            'height': height,
            'width': 1200,
            'scale': 1
        }
    }

    return fig, config


def add_trade_markers(fig, trades_data):
    """
    Add trade entry/exit markers to an existing chart.

    Args:
        fig: Existing plotly figure
        trades_data: DataFrame with columns ['timestamp', 'type', 'price']
                    where type is 'entry' or 'exit'

    Returns:
        plotly figure with trade markers added
    """

    if trades_data is None or trades_data.empty:
        return fig

    # Add entry markers
    entry_trades = trades_data[trades_data['type'] == 'entry']
    if not entry_trades.empty:
        fig.add_trace(go.Scatter(
            x=entry_trades['timestamp'],
            y=entry_trades['price'],
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=12,
                color='#00ff00',
                line=dict(width=2, color='#008800')
            ),
            name='Trade Entry',
            showlegend=True
        ))

    # Add exit markers
    exit_trades = trades_data[trades_data['type'] == 'exit']
    if not exit_trades.empty:
        fig.add_trace(go.Scatter(
            x=exit_trades['timestamp'],
            y=exit_trades['price'],
            mode='markers',
            marker=dict(
                symbol='triangle-down',
                size=12,
                color='#ff0000',
                line=dict(width=2, color='#880000')
            ),
            name='Trade Exit',
            showlegend=True
        ))

    return fig


def create_chart_with_trades(chart_data, symbol_name, trades_data=None, height=600):
    """
    Create an interactive chart with optional trade markers.
    Convenience function that combines candlestick chart with trade visualization.

    Args:
        chart_data: DataFrame with OHLC data
        symbol_name: String name of the symbol
        trades_data: Optional DataFrame with trade data
        height: Chart height in pixels

    Returns:
        tuple: (plotly figure, plotly config dict)
    """

    # Create base chart
    fig, config = create_interactive_candlestick_chart(chart_data, symbol_name, height)

    # Add trades if provided
    if trades_data is not None:
        fig = add_trade_markers(fig, trades_data)

    return fig, config