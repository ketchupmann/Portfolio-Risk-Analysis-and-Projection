import numpy as np

class MonteCarloEngine:
    def __init__(self, portfolio, initial_capital=100000.0, time_horizon=252, num_simulations=5000):
        """
        Initializes the simulation engine.
        """
        self.portfolio = portfolio
        self.initial_capital = initial_capital
        self.time_horizon = time_horizon
        self.num_simulations = num_simulations
        
        # Matrix to hold the final simulated dollar paths
        # Shape: (Days + 1, Number of parallel universes)
        self.simulated_paths = np.zeros((self.time_horizon + 1, self.num_simulations))
        
        # Set the starting capital for day 0 across all simulations
        self.simulated_paths[0] = self.initial_capital

    def run_simulation(self):
        """
        Executes the multi-variate Geometric Brownian Motion simulation.
        """
        
        mu = self.portfolio.daily_mean_returns.values
        cov_matrix = self.portfolio.daily_covariance_matrix.values
        weights = self.portfolio.weights

        # Cholesky Decomposition
        # forces the random shocks to respect the historical correlation between assets
        L = np.linalg.cholesky(cov_matrix)

        # The Geometric Brownian Motion Loop
        # pre gen all random shocks for the entire time horizon at once
        # Shape: (Time_Horizon, Assets, Simulations)
        Z = np.random.standard_normal((self.time_horizon, len(weights), self.num_simulations))
        
        # Correlate shocks across all days simultaneously using Einstein summation
        # L is (Assets, Assets). Z is (Time, Assets, Simulations).
        correlated_shocks = np.einsum('ij,tjk->tik', L, Z)
        
        # add drift and exponentiate for all days at once
        # Reshape drift to (1, Assets, 1) to broadcast across Time and Simulations
        drift = (mu - 0.5 * np.diag(cov_matrix)).reshape(1, len(weights), 1)
        asset_daily_returns = np.exp(drift + correlated_shocks)
        
        # apply portfolio weights across all time steps
        portfolio_daily_returns = np.einsum('n,tns->ts', weights, asset_daily_returns)
        
        # cumulative paths using cumprod and apply initial capital
        self.simulated_paths[1:] = self.initial_capital * np.cumprod(portfolio_daily_returns, axis=0)
            
        print("Simulation complete.")
        return self.simulated_paths

    def calculate_risk_metrics(self, confidence_level=0.95):
        """
        Calculates Value at Risk (VaR) and Conditional VaR (CVaR).
        """
        if self.simulated_paths[-1][0] == self.initial_capital:
            raise ValueError("Run run_simulation() before calculating risk metrics.")
            
        # Extract all ending portfolio values on the final day (Day 252)
        final_values = self.simulated_paths[-1]
        
        # Calculate pure dollar PnL (Profit and Loss) for every single path
        pnl = final_values - self.initial_capital
        
        # Value at Risk (VaR): The worst expected loss at the 95% confidence level
        var_percentile = (1 - confidence_level) * 100
        var_dollar = np.percentile(pnl, var_percentile)
        
        # Conditional Value at Risk (CVaR): The average loss of the worst 5% of scenarios
        cvar_dollar = pnl[pnl <= var_dollar].mean()
        
        return {
            "VaR": round(var_dollar, 2),
            "CVaR": round(cvar_dollar, 2)
        }