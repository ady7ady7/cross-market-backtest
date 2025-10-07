"""Formatting utilities for consistent display of values across the codebase."""

from typing import Optional, Union


def fmt_optional(value: Optional[Union[int, float]], format_spec: str = ".2f", none_text: str = "None") -> str:
    """
    Format an optional numeric value with a format specifier, or return a placeholder if None.

    This utility solves the problem of conditional formatting in f-strings, which is not allowed:

    WRONG: f"TP: {take_profit:.2f if take_profit else 'None'}"
    RIGHT: f"TP: {fmt_optional(take_profit, '.2f')}"

    Args:
        value: The numeric value to format, or None
        format_spec: Format specifier (e.g., '.2f', '.4f', 'd') - default '.2f'
        none_text: Text to display when value is None - default 'None'

    Returns:
        Formatted string representation of the value or none_text

    Examples:
        >>> fmt_optional(123.456, '.2f')
        '123.46'
        >>> fmt_optional(None, '.2f')
        'None'
        >>> fmt_optional(None, '.2f', 'N/A')
        'N/A'
        >>> fmt_optional(100, 'd')
        '100'
    """
    if value is None:
        return none_text
    return f"{value:{format_spec}}"


def fmt_price(price: Optional[float], decimals: int = 2) -> str:
    """
    Format a price value with specified decimal places, or 'None' if not set.

    Args:
        price: Price value or None
        decimals: Number of decimal places (default 2)

    Returns:
        Formatted price string

    Examples:
        >>> fmt_price(1234.567)
        '1234.57'
        >>> fmt_price(None)
        'None'
    """
    return fmt_optional(price, f".{decimals}f")


def fmt_pct(value: Optional[float], decimals: int = 2, suffix: bool = True) -> str:
    """
    Format a percentage value with specified decimal places, or 'None' if not set.

    Args:
        value: Percentage value (e.g., 2.5 for 2.5%) or None
        decimals: Number of decimal places (default 2)
        suffix: Whether to add '%' suffix (default True)

    Returns:
        Formatted percentage string

    Examples:
        >>> fmt_pct(2.5)
        '2.50%'
        >>> fmt_pct(None)
        'None'
        >>> fmt_pct(2.5, suffix=False)
        '2.50'
    """
    result = fmt_optional(value, f".{decimals}f")
    if suffix and result != "None":
        result += "%"
    return result


def fmt_units(units: Optional[float], decimals: int = 4) -> str:
    """
    Format position size in units with specified decimal places, or 'None' if not set.

    Args:
        units: Position size in units or None
        decimals: Number of decimal places (default 4)

    Returns:
        Formatted units string

    Examples:
        >>> fmt_units(62.3441)
        '62.3441'
        >>> fmt_units(None)
        'None'
    """
    return fmt_optional(units, f".{decimals}f")
