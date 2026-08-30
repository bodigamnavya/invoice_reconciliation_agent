import re
from datetime import datetime, date

def parse_date_string(date_str: str) -> date:
    """Safely parse multiple date formats into date object."""
    if not date_str:
        return date.today()
    if isinstance(date_str, (date, datetime)):
        return date_str if isinstance(date_str, date) else date_str.date()
    
    clean_str = re.sub(r'[^\w\s\-/.]', '', str(date_str)).strip()
    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt).date()
        except ValueError:
            continue
    
    return date.today()

def parse_currency_amount(amount_raw) -> float:
    """
    Extract numeric currency amount from string, float, or int.
    Robustly handles Indian currency formats (e.g. ₹1,50,000.00, Rs. 1,50,000, INR 150000, I150,000.00).
    """
    if amount_raw is None:
        return 0.0
    if isinstance(amount_raw, (int, float)):
        return round(float(amount_raw), 2)
    
    s = str(amount_raw).strip()
    if not s:
        return 0.0

    # Remove common currency text prefixes and symbols
    # Notice: 'I' or 'l' is often extracted when fonts lack the Rupee symbol
    s = re.sub(r'(?i)^(?:inr|rs\.?|rupees?|[₹$€£Il|])\s*', '', s)
    s = re.sub(r'(?i)\s*(?:inr|rs\.?|rupees?|[₹$€£])\s*', '', s)
    
    # Remove any non-digit, non-period, non-comma characters
    cleaned = re.sub(r'[^\d.,]', '', s)
    if not cleaned:
        return 0.0

    # Handle Indian / Western commas: e.g. "1,50,000.00" or "150,000.00" or "1,50,000"
    if "," in cleaned and "." in cleaned:
        # Check if period is the decimal separator (standard)
        if cleaned.rfind(".") > cleaned.rfind(","):
            cleaned = cleaned.replace(",", "")
        else: # European style "150.000,00"
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        # If comma has 2 digits after it at the end (e.g. 150,00), it might be decimal, else thousands separator
        parts = cleaned.split(",")
        if len(parts[-1]) == 2 and len(parts) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")

    try:
        val = float(cleaned)
        return round(val, 2)
    except Exception:
        return 0.0

def format_currency(amount: float, currency_symbol: str = "₹") -> str:
    """Format float into standard currency string with Indian numbering."""
    if amount is None or is_invalid_amount(amount):
        amount = 0.0
    num = float(amount)
    
    # Format with Indian numbering system (e.g. 1,50,000.00)
    try:
        is_neg = num < 0
        abs_num = abs(num)
        s, dec = f"{abs_num:.2f}".split(".")
        if len(s) > 3:
            last_three = s[-3:]
            other_numbers = s[:-3]
            res = ""
            while len(other_numbers) > 2:
                res = "," + other_numbers[-2:] + res
                other_numbers = other_numbers[:-2]
            formatted_int = other_numbers + res + "," + last_three
        else:
            formatted_int = s
        sign = "-" if is_neg else ""
        return f"{sign}{currency_symbol}{formatted_int}.{dec}"
    except Exception:
        return f"{currency_symbol}{num:,.2f}"

def is_invalid_amount(val) -> bool:
    try:
        f = float(val)
        return False
    except (ValueError, TypeError):
        return True
