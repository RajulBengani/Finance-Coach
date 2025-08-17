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
    if income_total <= 250000:
        return "No tax liability (Income ≤ ₹2.5L)."
    elif income_total <= 500000:
        tax = (income_total - 250000) * Decimal('0.05')
        return f"Estimated Tax: ₹{tax:.2f} (5% Slab)."
    elif income_total <= 1000000:
        tax = Decimal('12500') + (income_total - 500000) * Decimal('0.20')
        return f"Estimated Tax: ₹{tax:.2f} (20% Slab)."
    else:
        tax = Decimal('112500') + (income_total - 1000000) * Decimal('0.30')
        return f"Estimated Tax: ₹{tax:.2f} (30% Slab)."

def generate_category_expense_recommendation(user):
    income_total=Transaction.objects.filter(
        user=user, type='income'
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal ('0.00')

    if income_total == 0:
        return "You have no income recorded. Please add your income to get expense recommendations."
    
    category_expenses=Transaction.objects.filter(
        user=user, type='expense'
        ).values('category__name'
                 ).annotate(total=Sum('amount'))
    
    recommendations=[]
    for ce in category_expenses:
        category_name = ce['category__name']
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
                f"Good! Spending on {category_name} is {category_ratio:.0f}% of your income."
            )

    if not recommendations:
        recommendations.append("No expenses recorded yet.")

    return recommendations

from django.core.cache import cache
import certifi
import yfinance as yf

def get_usd_to_inr():
    cache_key = "fx_usd_inr"
    cached = cache.get(cache_key)
    if cached:
        return cached
    try:
        fx = yf.Ticker("USDINR=X")
        data = fx.history(period="1d",auto_adjust=False, back_adjust=False)
        if not data.empty:
            return float(data["Close"].iloc[-1])
            cache.set(cache_key, rate, 3600)
            return rate
    except Exception as e:
        pass
    fallback=83.0
    cache.set(cache_key, fallback, 3600)
    return fallback  # fallback (approx current USD→INR rate)

# Map risk tolerance to categories
RISK_MAPPING = {
    "no_risk": ["^IRX"],  # 13 Week Treasury Bill
    "low": ["BND", "VTI"],  # Bond ETF + Diversified ETF
    "medium": ["AAPL", "MSFT"],  # Blue chip stocks
    "high": ["TSLA", "AMZN"],  # Growth stocks
    "very_high": ["COIN", "NVDA"],  # Super risky / volatile
}
def _cached_history(ticker: str, period: str = "1y", interval: str | None = None):
    """
    Small cache wrapper around yfinance.history to avoid rate-limits & speed up dashboards.
    """
    key = f"yf_hist:{ticker}:{period}:{interval or '1d'}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period, interval=interval) if interval else t.history(period=period)
        cache.set(key, hist, 300)  # 5 minutes
        return hist
    except Exception:
        return None

def _compute_metrics(ticker: str, usd_to_inr: float):
    """
    Compute richer metrics safely: last price (USD, INR), 1M/1Y returns,
    simple volatility (1M), intraday trend (5d/1h), dividend yield, and name.
    """
    tkr = yf.Ticker(ticker)

    # Name (safe)
    try:
        name = tkr.info.get("shortName") or ticker
    except Exception:
        name = ticker

    # Last close in USD
    price_usd = None
    try:
        h1d = _cached_history(ticker, period="1d")
        if h1d is not None and not h1d.empty:
            price_usd = float(round(h1d["Close"].iloc[-1], 2))
    except Exception:
        pass

    price_inr = round(price_usd * usd_to_inr, 2) if isinstance(price_usd, (int, float)) else None

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

    # Volatility (1M stddev of daily returns)
    vol_1m = None
    try:
        if h1m is not None and len(h1m) > 5:
            pct = h1m["Close"].pct_change().dropna()
            vol_1m = float(pct.std())  # ~daily stdev
    except Exception:
        pass

    # Intraday trend (5d, 1h)
    trend = None
    try:
        h5d = _cached_history(ticker, period="5d", interval="1h")
        if h5d is not None and not h5d.empty:
            mean_5d = float(h5d["Close"].mean())
            last_5d = float(h5d["Close"].iloc[-1])
            trend = "📈 Uptrend" if last_5d > mean_5d else "📉 Downtrend"
    except Exception:
        pass

    # Dividend yield
    div_yield = None
    try:
        dy = tkr.info.get("dividendYield")
        if dy is not None:
            div_yield = float(dy)  # already fraction (e.g., 0.006)
    except Exception:
        pass

    return {
        "ticker": ticker,
        "name": name,
        "price_usd": price_usd if price_usd is not None else "N/A",
        "price_inr": price_inr if price_inr is not None else "N/A",
        "return_1m": ret_1m,     # float fraction, e.g., 0.043
        "return_1y": ret_1y,     # float fraction
        "volatility_1m": vol_1m, # daily stdev fraction, e.g., 0.018
        "trend": trend,          # "📈 Uptrend" / "📉 Downtrend" / None
        "dividend_yield": div_yield,  # fraction or None
    }

def get_investment_opportunities(user):
    try:
        profile = UserProfile.objects.get(user=user)
        risk_level = profile.risk_tolerance
    except UserProfile.DoesNotExist:
        return [{"error": "No profile found. Please update your risk tolerance."}]

    if risk_level not in RISK_MAPPING:
        return [{"error": f"Unknown risk level '{risk_level}'. Please update your profile."}]

    # Cache per-user + risk to avoid repeated API calls during page refreshes
    cache_key = f"invest_ops:{user.id}:{risk_level}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    usd_to_inr = get_usd_to_inr()
    tickers = RISK_MAPPING[risk_level]
    results = []

    for ticker in tickers:
        metrics = _compute_metrics(ticker, usd_to_inr)

        # Simple horizon suggestion based on volatility (can be replaced with profile.horizon)
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

        # Compose the final item (keeps your existing keys + new ones)
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

    # Cache for 5 minutes
    cache.set(cache_key, results, 300)
    return results



       

