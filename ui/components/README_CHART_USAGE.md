# Chart Utils Usage Examples

## Basic Interactive Chart
```python
from ui.components.chart_utils import create_interactive_candlestick_chart

# Create chart with your data
fig, config = create_interactive_candlestick_chart(df, "AAPL")

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True, config=config)
```

## Chart with Trade Markers (Future Use)
```python
from ui.components.chart_utils import create_chart_with_trades

# Prepare trade data (example format)
trades_data = pd.DataFrame({
    'timestamp': [...],
    'type': ['entry', 'exit', 'entry'],  # 'entry' or 'exit'
    'price': [100.5, 105.2, 98.7]
})

# Create chart with trades
fig, config = create_chart_with_trades(
    chart_data=df,
    symbol_name="AAPL",
    trades_data=trades_data
)

st.plotly_chart(fig, use_container_width=True, config=config)
```

## Features Implemented
- ✅ Mouse wheel zoom (both X and Y axes)
- ✅ Click and drag panning
- ✅ Smooth, frictionless scaling
- ✅ Double-click to reset zoom
- ✅ Drawing tools for analysis
- ✅ Modular design for reuse
- ✅ Future trade visualization support