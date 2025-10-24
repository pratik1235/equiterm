"""
Utility functions for financial calculations and formatting.
"""

from typing import Optional


def calculate_etf_premium(nav: float, market_price: float) -> float:
    """
    Calculate ETF premium/discount percentage.
    
    Args:
        nav: Net Asset Value
        market_price: Current market price
        
    Returns:
        Premium percentage (positive for premium, negative for discount)
    """
    if nav == 0:
        return 0.0
    return ((market_price - nav) / nav) * 100


def calculate_change_percent(current: float, previous: float) -> float:
    """
    Calculate percentage change between two values.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Percentage change
    """
    if previous == 0:
        return 0.0
    return ((current - previous) / previous) * 100


def format_currency(value: Optional[float], currency: str = "₹") -> str:
    """
    Format currency value with exact numbers and 2 decimal places.
    
    Args:
        value: Currency value to format
        currency: Currency symbol
        
    Returns:
        Formatted currency string with comma separators
    """
    if value is None:
        return "N/A"
    
    # Format with 2 decimal places and comma separators
    return f"{currency}{value:,.2f}"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """
    Format percentage value.
    
    Args:
        value: Percentage value
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    if value is None:
        return "N/A"
    
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_number(value: Optional[float], decimals: int = 2) -> str:
    """
    Format number with proper formatting for large values.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    if value is None:
        return "N/A"
    
    if value >= 1e7:  # 1 crore
        return f"{value/1e7:.{decimals}f}Cr"
    elif value >= 1e5:  # 1 lakh
        return f"{value/1e5:.{decimals}f}L"
    elif value >= 1e3:  # 1 thousand
        return f"{value/1e3:.{decimals}f}K"
    else:
        return f"{value:.{decimals}f}"


def get_color_for_change(change_percent: Optional[float]) -> str:
    """
    Get color code for change percentage.
    
    Args:
        change_percent: Change percentage
        
    Returns:
        Color name for Textual styling
    """
    if change_percent is None:
        return "white"
    elif change_percent > 0:
        return "green"
    elif change_percent < 0:
        return "red"
    else:
        return "white"
