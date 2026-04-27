# Portfolio Risk Analysis and Projection Application
An institutional-grade portfolio risk analysis dashboard built with Python, Plotly Dash, and Pandas. This engine performs Ex-Ante risk modeling by running 5,000-path Monte Carlo simulations to project portfolio distributions and calculate severe tail-risk metrics.

## 📊 Live Dashboard
**[[Insert Your Live Deployment Link Here](https://portfolio-risk-analysis-and-projection.onrender.com/)]**
<img width="1499" height="861" alt="image" src="https://github.com/user-attachments/assets/8e8aff38-2eb0-44cd-af2b-e6a1a2e03348" />

## 🎯 Core Capabilities
* **Historical Baseline Metrics:** Dynamically calculates annualized expected return, volatility, Sharpe ratio, Sortino ratio, and Maximum Drawdown based on 3-year historical daily closes.
* **Stochastic Forecasting:** Utilizes Geometric Brownian Motion (GBM) within a Monte Carlo framework to project the "Cone of Uncertainty" across custom time horizons (1-5 years).
* **Tail Risk Quantification:** Extracts 95% Value at Risk (VaR) and Conditional Value at Risk (CVaR / Expected Shortfall) directly from the simulated distribution tails.
* **Deterministic Macro Stress Testing:** Features an institutional scenario engine that shocks historical volatility and return parameters to model specific market crises (e.g., 2008 GFC, 2020 Liquidity Crash).

## 🛠 Tech Stack
* **Frontend:** Plotly Dash, HTML/CSS (Custom Dark Theme UI)
* **Backend:** Python (Object-Oriented Architecture), Pandas, NumPy
* **Data Integration:** EODHD API for historical daily adjusted closes. 
* **Deployment:** Docker, Gunicorn, Render

## 🚀 Local Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/quant-risk-engine.git](https://github.com/yourusername/quant-risk-engine.git)
   cd quant-risk-engine
