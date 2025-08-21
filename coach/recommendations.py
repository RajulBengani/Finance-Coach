from django.db import models
from .models import Transaction, UserProfile
from decimal import Decimal
from django.db.models import Sum
from django.contrib.auth.models import User


def generate_savings_recommendation(user):
    income_total=Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    savings_total=Transaction.objects.filter(
        user=user, type='savings'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')


    if income_total ==0:
        return "You have no income recorded. Please add your income to get savings recommendations."
    
    saving_ratio= (savings_total / income_total) * 100 if income_total > 0 else 0

    if saving_ratio < 10:
        return "Your savings ratio is below 10%. Consider increasing your savings to improve your financial health."
    elif saving_ratio < 20:
        return "Your savings ratio is between 10% and 20%. This is a good start, but you can aim for a higher savings rate."
    elif saving_ratio < 30:
        return "Your savings ratio is between 20% and 30%. You're doing well, but there's room for improvement."
    else:
        return "Great job! Your savings ratio is above 30%. Keep up the good work!"

def generate_expense_recommendation(user):
    income_total = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    expenses_total = Transaction.objects.filter(
        user=user, type='expense'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
    

    if income_total == 0:
        return "You have no income recorded. Please add your income to get expense recommendations."
    
    expense_ratio = (expenses_total / income_total) * 100 if income_total > 0 else 0
    if expense_ratio > 90:
        return "⚠️ Your expenses are above 90% of your income. Try reducing discretionary spending."
    elif expense_ratio > 70:
        return "Your expenses are a bit high (70–90% of income). Consider saving more aggressively."
    elif expense_ratio > 50:
        return "Balanced spending. Aim to keep expenses under 50% for better savings."
    else:
        return "Great job! Your expenses are well under control."

def calculate_tax_recommendation(user):
    income_total = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    if income_total == 0:
        return "You have no income recorded. Please add your income to get tax recommendations."

    # Example tax brackets (these should be updated based on actual tax laws)
    
    if income_total <= 400000:
        return "No tax liability (Income ≤ ₹4L)."
    elif income_total <= 800000:
        tax = (income_total - 400000) * Decimal('0.05')
    elif income_total <= 1200000:
        tax = Decimal('20000') + (income_total - 800000) * Decimal('0.10')
    elif income_total <= 1600000:
        tax = Decimal('60000') + (income_total - 1200000) * Decimal('0.15')
    elif income_total <= 2000000:
        tax = Decimal('120000') + (income_total - 1600000) * Decimal('0.20')
    elif income_total <= 2400000:
        tax = Decimal('200000') + (income_total - 2000000) * Decimal('0.25')
    else:
        tax = Decimal('300000') + (income_total - 2400000) * Decimal('0.30')

    # Apply Section 87A rebate if eligible
    if income_total <= 1200000:
        rebate = min(tax, Decimal('60000'))
        tax -= rebate
        return f"Estimated Tax: ₹{tax:.2f} (Rebate applied under Section 87A)."
    else:
        return f"Estimated Tax: ₹{tax:.2f} (No rebate)."


def generate_category_expense_recommendation(user):
    income_total = Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    if income_total == 0:
        return ["You have no income recorded. Please add your income to get expense recommendations."]

    category_expenses = Transaction.objects.filter(
        user=user, type='expense'
    ).values('category__name').annotate(total=Sum('amount'))

    recommendations = []
    for ce in category_expenses:
        category_name = ce['category__name'] or "Uncategorized"
        category_total = ce['total'] or Decimal('0')
        category_ratio = (category_total / income_total) * 100

        if category_ratio > 25:
            recommendations.append(
                f"⚠️ You spend {category_ratio:.0f}% of your income on {category_name}. Consider reducing to ≤25%."
            )
        elif category_ratio > 15:
            recommendations.append(
                f"Your spending on {category_name} is {category_ratio:.0f}% of income. Monitor it closely."
            )
        else:
            recommendations.append(
                f"✅ Good! Spending on {category_name} is {category_ratio:.0f}% of your income."
            )

    if not recommendations:
        recommendations.append("No expenses recorded yet.")

    return recommendations


from django.core.cache import cache
import yfinance as yf
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Map risk tolerance to tickers
RISK_MAPPING = {
    "no_risk": ["^IRX"],  # 13 Week Treasury Bill
    "low": ["BND", "VTI"],  # Bond ETF + Diversified ETF
    "medium": ["AAPL", "MSFT"],  # Blue chip stocks
    "high": ["TSLA", "AMZN"],  # Growth stocks
    "very_high": ["COIN", "NVDA"],  # Super risky / volatile
}

# --- Currency Conversion ---
def get_usd_to_inr() -> float:
    """Fetch USD → INR rate, cached for 1 hour, fallback to 83.0."""
    cache_key = "fx_usd_inr"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        fx = yf.Ticker("USDINR=X")
        data = fx.history(period="1d")
        if not data.empty:
            rate = float(data["Close"].iloc[-1])
            cache.set(cache_key, rate, 3600)
            return rate
    except Exception as e:
        logger.warning("USD→INR fetch failed: %s", e)

    fallback = 83.0
    cache.set(cache_key, fallback, 3600)
    return fallback

# --- Cached yfinance wrapper ---
def _cached_history(ticker: str, period: str = "1y", interval: Optional[str] = None):
    """Cache yfinance history to reduce API calls."""
    key = f"yf_hist:{ticker}:{period}:{interval or '1d'}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval) if interval else t.history(period=period)
        cache.set(key, hist, 300)  # Cache 5 minutes
        return hist
    except Exception as e:
        logger.warning("YFinance history fetch failed for %s: %s", ticker, e)
        return None

# --- Compute metrics ---
def _compute_metrics(ticker: str, usd_to_inr: float) -> dict:
    """Compute metrics like last price, returns, volatility, trend, dividend yield."""
    tkr = yf.Ticker(ticker)

    # Name
    try:
        name = tkr.info.get("shortName") or ticker
    except Exception:
        name = ticker

    # Last close price USD
    price_usd = None
    try:
        h1d = _cached_history(ticker, period="1d")
        if h1d is not None and not h1d.empty:
            price_usd = round(float(h1d["Close"].iloc[-1]), 2)
    except Exception:
        pass

    price_inr = round(price_usd * usd_to_inr, 2) if isinstance(price_usd, (int, float)) else "N/A"

    # 1M return
    ret_1m = None
    try:
        h1m = _cached_history(ticker, period="1mo")
        if h1m is not None and len(h1m) >= 2:
            ret_1m = float(h1m["Close"].iloc[-1] / h1m["Close"].iloc[0] - 1.0)
    except Exception:
        pass

    # 1Y return
    ret_1y = None
    try:
        h1y = _cached_history(ticker, period="1y")
        if h1y is not None and len(h1y) >= 2:
            ret_1y = float(h1y["Close"].iloc[-1] / h1y["Close"].iloc[0] - 1.0)
    except Exception:
        pass

    # 1M volatility
    vol_1m = None
    try:
        if h1m is not None and len(h1m) > 5:
            vol_1m = float(h1m["Close"].pct_change().dropna().std())
    except Exception:
        pass

    # Intraday trend (5d/1h)
    trend = None
    try:
        h5d = _cached_history(ticker, period="5d", interval="1h")
        if h5d is not None and not h5d.empty:
            trend = "📈 Uptrend" if h5d["Close"].iloc[-1] > h5d["Close"].mean() else "📉 Downtrend"
    except Exception:
        pass

    # Dividend yield
    div_yield = None
    try:
        dy = tkr.info.get("dividendYield")
        if dy is not None:
            div_yield = float(dy)
    except Exception:
        pass

    return {
        "ticker": ticker,
        "name": name,
        "price_usd": price_usd or "N/A",
        "price_inr": price_inr,
        "return_1m": ret_1m,
        "return_1y": ret_1y,
        "volatility_1m": vol_1m,
        "trend": trend,
        "dividend_yield": div_yield,
    }

# --- Get investment opportunities ---
def get_investment_opportunities(user):
    """Fetch investments based on user risk profile, cached for 5 mins."""
    from .models import UserProfile  # local import to avoid circular issues

    try:
        profile = UserProfile.objects.get(user=user)
        risk_level = profile.risk_tolerance
    except UserProfile.DoesNotExist:
        return [{"error": "No profile found. Please update your risk tolerance."}]

    if risk_level not in RISK_MAPPING:
        return [{"error": f"Unknown risk level '{risk_level}'. Please update your profile."}]

    cache_key = f"invest_ops:{user.id}:{risk_level}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    usd_to_inr = get_usd_to_inr()
    results = []

    for ticker in RISK_MAPPING[risk_level]:
        metrics = _compute_metrics(ticker, usd_to_inr)

        # Simple horizon suggestion based on volatility
        vol = metrics.get("volatility_1m")
        if isinstance(vol, (int, float)):
            if vol < 0.01:
                horizon = "Long-term"
            elif vol < 0.02:
                horizon = "Mid-term"
            else:
                horizon = "Short-term / Speculative"
        else:
            horizon = "Unknown"

        results.append({
            "ticker": metrics["ticker"],
            "name": metrics["name"],
            "price_usd": metrics["price_usd"],
            "price_inr": metrics["price_inr"],
            "risk": risk_level.capitalize(),
            "trend": metrics["trend"],
            "return_1m": metrics["return_1m"],
            "return_1y": metrics["return_1y"],
            "volatility_1m": metrics["volatility_1m"],
            "dividend_yield": metrics["dividend_yield"],
            "horizon": horizon,
        })

    cache.set(cache_key, results, 300)  # Cache 5 mins
    return results




       

