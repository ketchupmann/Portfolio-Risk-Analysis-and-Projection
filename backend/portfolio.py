import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.asset import Asset

class Portfolio:
    def __init__(self, tickers, weights, years_back=3):
        """
        Initializes the portfolio with a list of tickers and their corresponding weights.
        """
        self.tickers = [t.upper() for t in tickers]
        self.weights = np.array(weights)
        self.years_back = years_back

        if not np.isclose(sum(self.weights), 1.0):
            raise ValueError("CRITICAL: Portfolio weights must sum to exactly 1.0")
        if len(self.tickers) != len(self.weights):
            raise ValueError("CRITICAL: Number of tickers must match number of weights")
        
        self.assets = {}
        self.daily_mean_returns = None
        self.daily_covariance_matrix = None
        
        # annualized metrics 
        self.expected_annual_return = np.nan
        self.annual_volatility = np.nan

        # risk metrics
        self.sharpe_ratio = np.nan
        self.sortino_ratio = np.nan
    
    def fetch_all_data(self):
        returns_dict = {}
        for ticker in self.tickers:
            asset = Asset(ticker)
            raw_data = asset.fetch_data(years_back=self.years_back)
            self.assets[ticker] = asset

            col_name = 'Close'
            daily_returns = raw_data[col_name].pct_change().dropna()
        
            returns_dict[ticker] = daily_returns
        self.returns_df = pd.DataFrame(returns_dict)
        self.returns_df.dropna(inplace=True)

    def calculate_portfolio_metrics(self, rf_rate):
        """
        Calculates portfolio-level expected return and covariance.
        """
        if self.returns_df.empty:
            raise ValueError("CRITICAL: No return data available.")
        self.daily_mean_returns = self.returns_df.mean()
        self.daily_covariance_matrix = self.returns_df.cov()
    
        # Annualized Metrics 
        annualized_returns = self.daily_mean_returns * 252
    
        # Expected Annual Return: Dot product of weights and annualized returns
        self.expected_annual_return = np.dot(self.weights, annualized_returns)
    
        # Annualized Portfolio Volatility (Standard Deviation)
        # matrix multiplication accounts for the correlation between assets
        annualized_cov = self.daily_covariance_matrix * 252
        portfolio_variance = np.dot(self.weights.T, np.dot(annualized_cov, self.weights))
    
        # Volatility is the square root of variance
        self.annual_volatility = np.sqrt(portfolio_variance)

        # risk metric calculations
        # Sharpe
        self.sharpe_ratio = (self.expected_annual_return - rf_rate) / self.annual_volatility

        # Sortino
        portfolio_daily_returns = self.returns_df.dot(self.weights)
        negative_returns = portfolio_daily_returns[portfolio_daily_returns < 0]
        downside_volatility = negative_returns.std() * np.sqrt(252)
        # prevent div by 0
        if downside_volatility > 0:
            self.sortino_ratio = (self.expected_annual_return - rf_rate) / downside_volatility
        else:
            self.sortino_ratio = np.nan
    
        # MDD
        cumulative_returns = (1 + portfolio_daily_returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns / running_max) - 1
        self.max_drawdown = drawdown.min()