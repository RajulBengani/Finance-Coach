def adaptive_advice(income, expenses, savings, investments):
    try:
        income_f, expenses_f, savings_f = float(income), float(expenses), float(savings)
    except Exception:
        return "Add at least one income entry to unlock advice."

    high_vol = any(
        isinstance(inv.get("volatility_1m"), (int, float)) and inv["volatility_1m"] >= 0.02
        for inv in (investments or [])
    )

    if income_f == 0:
        return "Add at least one income entry to unlock personalized investing advice."
    if expenses_f > income_f * 0.9:
        return "⚠️ Expenses are ~90% of income. Reduce spending before high-risk investments."
    if savings_f < income_f * 0.1:
        return "💡 Save ≥10% of income before taking market risk."
    if high_vol:
        return "⚠️ Several suggestions are volatile. Balance with ETFs or bonds."
    return "✅ Good balance! Explore more opportunities fitting your horizon."
