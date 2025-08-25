# 💰 Finance Coach

## Overview

**Finance Coach** is an intelligent personal finance web application designed to help users manage money smarter. It tracks income, expenses, and financial goals while providing **tax recommendations, personalized savings suggestions, and expense optimization advice**. Additionally, it can adapt its guidance based on **real-time stock market data**, giving users actionable insights for smarter financial decisions.

---

## 🛠 Tech Stack

* **Backend:** Django (Python)
* **Frontend:** HTML, CSS, JavaScript
* **Database:** SQLite
* **APIs:** Real-time stock data APIs (yfinance)
* **Authentication:** Django’s built-in authentication system

---

## ⚙️ Setup

1. **Clone the repository**

```bash
git clone https://github.com/RajulBengani/Finance-Coach
cd finance-coach
```

2. **Apply migrations**

```bash
python manage.py migrate
```

3. **Create a superuser (optional, for admin access)**

```bash
python manage.py createsuperuser
```

4. **Run the server**

```bash
python manage.py runserver
```

5. **Open in browser**
   Visit `http://127.0.0.1:8000/coach`

---

## ✨ Features

* **Transaction Management:** Add, edit, or delete income and expense records.
* **Category Management:** Organize transactions for better insights.
* **Goal Setting:** Set and track financial goals.
* **Dashboard Analytics:** Visualize spending trends, savings, and remaining budgets.
* **Tax Recommendations:** Suggestions to optimize tax savings based on income and expenses.
* **Savings Suggestions:** Personalized advice to increase your savings efficiently.
* **Expense Optimization Advice:** Tips to reduce unnecessary spending and balance your budget.
* **Adaptive Investment Advice:** Guidance adapts based on real-time stock data.
* **User Authentication:** Secure login and signup system.
* **Responsive Design:** Accessible on both desktop and mobile devices.

---

## 🧩 Technical Workflow

1. **User Authentication:** Secure registration and login using Django.
2. **Transaction & Goal Management:** Users log income, expenses, and financial goals.
3. **Financial Analysis:** Backend calculates budgets, trends, and savings potential.
4. **Tax & Savings Recommendations:** AI-powered suggestions based on user data and tax rules.
5. **Expense Advice:** System identifies unnecessary expenditures and provides optimization tips.
6. **Adaptive Investment Guidance:** Real-time stock data is fetched via APIs to provide timely investment suggestions.
7. **Data Storage:** All transactions, categories, goals, and recommendations are stored securely in the database.
8. **User Dashboard:** Frontend visualizes analytics, recommendations, and investment advice interactively.
