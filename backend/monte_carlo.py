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
        # forces the random shocks to respect the historical correlation between your assets
        L = np.linalg.cholesky(cov_matrix)

        # The Geometric Brownian Motion Loop
        for t in range(1, self.time_horizon + 1):
            # Generate pure random shocks (standard normal distribution)
            Z = np.random.standard_normal((len(weights), self.num_simulations))
            
            # Correlate the shocks using the Cholesky matrix
            correlated_shocks = np.dot(L, Z)
            
            # Calculate the daily returns for each asset using GBM
            daily_returns = np.exp(
                (mu - 0.5 * np.diag(cov_matrix))[:, None] + correlated_shocks
            )
            
            # Apply the portfolio weights to the simulated asset returns
            portfolio_daily_return = np.dot(weights, daily_returns)
            
            # Calculate the new dollar value of the portfolio for day 't'
            self.simulated_paths[t] = self.simulated_paths[t - 1] * portfolio_daily_return
            
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