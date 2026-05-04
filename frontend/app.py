import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np
from functools import lru_cache

from backend.portfolio import Portfolio
from backend.monte_carlo import MonteCarloEngine

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# --- THEME VARIABLES ---
BG_MAIN = '#0F172A'      
BG_PANEL = '#1E293B'     
BORDER_COLOR = '#334155' 
CYAN_HEX = '#00E5FF'     
TEXT_MAIN = '#F8FAFC'    

# CSS TO REMOVE WHITE BROWSER SIDES (and fetch font from google)---
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ 
                margin: 0; 
                background-color: {BG_MAIN}; 
                font-family: 'Inter', sans-serif;
            }}
            /* Ensure inputs also inherit the font */
            input, button, select {{
                font-family: 'Inter', sans-serif;
            }}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
    </body>
</html>
'''

# --- FIX 1: DEFINE THE INITIAL EMPTY GRAPH ---
empty_fig = go.Figure()
empty_fig.update_layout(
    template='plotly_dark',
    plot_bgcolor=BG_MAIN,
    paper_bgcolor=BG_MAIN,
    xaxis=dict(visible=False), 
    yaxis=dict(visible=False), 
    annotations=[dict(
        text="Awaiting Valid Input", 
        x=0.5, y=0.5, 
        showarrow=False, 
        font=dict(color=BORDER_COLOR, size=20)
    )]
)

app.layout = html.Div(style={'fontFamily': '"Inter", sans-serif', 'padding': '20px', 'maxWidth': '1400px', 'margin': '0 auto', 'color': TEXT_MAIN, 'minHeight': '100vh'}, children=[
    
    html.H1("How Cooked is Your Portfolio? - Monte Carlo Simulation", style={'textAlign': 'center', 'color': TEXT_MAIN, 'fontWeight': '300', 'letterSpacing': '1px', 'marginBottom': '30px'}),
    
    # --- CONTROL PANEL ---
    html.Div(style={'display': 'flex', 'flexDirection': 'column', 'gap': '20px', 'marginBottom': '30px', 'padding': '25px', 'backgroundColor': BG_PANEL, 'borderRadius': '12px', 'border': f'1px solid {BORDER_COLOR}', 'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'}, children=[
        
        # Row 1: Core Portfolio Inputs
        html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
            html.Div([
                html.Label("Tickers (comma separated, include exchange ID for tickers):", style={'fontWeight': 'bold', 'color': '#94A3B8', 'marginBottom': '8px', 'display': 'block', 'fontSize': '12px', 'textTransform': 'uppercase'}),
                dcc.Input(id='input-tickers', value='AAPL, MSFT', type='text', style={'width': '100%', 'padding': '10px', 'backgroundColor': BG_MAIN, 'color': TEXT_MAIN, 'border': f'1px solid {BORDER_COLOR}', 'borderRadius': '6px', 'outlineColor': CYAN_HEX})
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Weights (comma separated):", style={'fontWeight': 'bold', 'color': '#94A3B8', 'marginBottom': '8px', 'display': 'block', 'fontSize': '12px', 'textTransform': 'uppercase'}),
                dcc.Input(id='input-weights', value='0.6, 0.4', type='text', style={'width': '100%', 'padding': '10px', 'backgroundColor': BG_MAIN, 'color': TEXT_MAIN, 'border': f'1px solid {BORDER_COLOR}', 'borderRadius': '6px', 'outlineColor': CYAN_HEX})
            ], style={'flex': '1'}),
            
            html.Div([
                html.Label("Initial Capital ($):", style={'fontWeight': 'bold', 'color': '#94A3B8', 'marginBottom': '8px', 'display': 'block', 'fontSize': '12px', 'textTransform': 'uppercase'}),
                dcc.Input(id='input-capital', value=100000, type='number', style={'width': '100%', 'padding': '10px', 'backgroundColor': BG_MAIN, 'color': TEXT_MAIN, 'border': f'1px solid {BORDER_COLOR}', 'borderRadius': '6px', 'outlineColor': CYAN_HEX})
            ], style={'flex': '1'}),
        ]),

        # Row 2: Environmental Parameters & Submit
        html.Div(style={'display': 'flex', 'gap': '20px', 'alignItems': 'flex-end'}, children=[
            
            html.Div([
                html.Label("Risk-Free Rate (%):", style={'fontWeight': 'bold', 'color': '#94A3B8', 'marginBottom': '8px', 'display': 'block', 'fontSize': '12px', 'textTransform': 'uppercase'}),
                dcc.Input(id='input-rf-rate', value=4.5, type='number', step=0.1, style={'width': '100%', 'padding': '10px', 'backgroundColor': BG_MAIN, 'color': TEXT_MAIN, 'border': f'1px solid {BORDER_COLOR}', 'borderRadius': '6px', 'outlineColor': CYAN_HEX})
            ], style={'flex': '0.5'}),

            html.Div([
                html.Label("Time Horizon (Years):", style={'fontWeight': 'bold', 'color': '#94A3B8', 'marginBottom': '8px', 'display': 'block', 'fontSize': '12px', 'textTransform': 'uppercase'}),
                dcc.Slider(
                    id='input-horizon', 
                    min=1, 
                    max=5, 
                    step=1, 
                    value=1, 
                    # FIX 1: Add 'whiteSpace': 'nowrap' to the style dict here
                    marks={i: {'label': f'{i} Yr', 'style': {'color': TEXT_MAIN, 'whiteSpace': 'nowrap'}} for i in range(1, 6)}
                )
            # FIX 2: Add 'paddingRight': '15px' and 'paddingLeft': '5px' to the container style
            ], style={'flex': '1.5', 'paddingBottom': '10px', 'paddingRight': '15px', 'paddingLeft': '5px'}),
            html.Div([
                html.Button('Run Simulation', id='run-button', n_clicks=0, 
                            style={'width': '100%', 'padding': '12px', 'backgroundColor': CYAN_HEX, 'color': '#0F172A', 'border': 'none', 'borderRadius': '6px', 'cursor': 'pointer', 'fontWeight': 'bold', 'boxShadow': '0 0 10px rgba(0, 229, 255, 0.2)'})
            ], style={'flex': '0.75'})
        ])
    ]),
    
    html.Div(id='error-message', style={'color': '#FF4C4C', 'fontWeight': 'bold', 'marginBottom': '20px', 'textAlign': 'center'}),
    
    # --- MAIN DASHBOARD AREA (Split Layout) ---
    html.Div(style={'display': 'flex', 'gap': '20px'}, children=[
        
        # Left Sidebar: Risk Metrics Ledger
        html.Div(id='metrics-output', style={
            'flex': '0.25', 
            'backgroundColor': BG_PANEL, 
            'borderRadius': '12px', 
            'border': f'1px solid {BORDER_COLOR}', 
            'padding': '25px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.3)',
            'minWidth': '260px' 
        }),
        
        # Right Main Canvas: The Monte Carlo Cone
        html.Div(style={
            'flex': '0.75', 
            'backgroundColor': BG_PANEL, 
            'borderRadius': '12px', 
            'border': f'1px solid {BORDER_COLOR}', 
            'padding': '15px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.3)'
        }, children=[
            dcc.Loading(
                id="loading-graph", 
                type="default", 
                color=CYAN_HEX, 
                children=[dcc.Graph(id='monte-carlo-graph', figure=empty_fig, style={'height': '550px'})]
            )
        ])
    ])
])

# ------------------------------------------------------------------------------
# SERVER-SIDE MEMOIZATION CACHE
# ------------------------------------------------------------------------------
@lru_cache(maxsize=32)
def get_cached_portfolio(tickers_tuple, weights_tuple, years_back):
    # Convert tuples back to lists for the Portfolio class
    tickers = list(tickers_tuple)
    weights = list(weights_tuple)
    
    portfolio = Portfolio(tickers=tickers, weights=weights, years_back=years_back)
    portfolio.fetch_all_data()
    return portfolio

# ------------------------------------------------------------------------------
# App Logic 
# ------------------------------------------------------------------------------
@app.callback(
    [Output('monte-carlo-graph', 'figure'),
     Output('metrics-output', 'children'),
     Output('error-message', 'children')],
    [Input('run-button', 'n_clicks')],
    [State('input-tickers', 'value'),
     State('input-weights', 'value'),
     State('input-capital', 'value'),
     State('input-rf-rate', 'value'),     
     State('input-horizon', 'value')]     
)
def update_dashboard(n_clicks, tickers_str, weights_str, capital, rf_rate_pct, horizon_years):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, ""
        
    try:
        tickers = [t.strip().upper() for t in tickers_str.split(',')]
        weights = [float(w.strip()) for w in weights_str.split(',')]
        rf_rate = rf_rate_pct / 100.0  
        
        if len(tickers) != len(weights):
            return empty_fig, "", "Error: Number of tickers must match number of weights."
        if not np.isclose(sum(weights), 1.0):
            return empty_fig, "", f"Error: Weights must sum to 1.0 (Current sum: {sum(weights)})"

        # --- CACHED DATA FETCHING ---
        tickers_tuple = tuple(tickers)
        weights_tuple = tuple(weights)
        
        # This will hit the internet the first time, and RAM every time after that.
        portfolio = get_cached_portfolio(tickers_tuple, weights_tuple, 3)
        
        portfolio.calculate_portfolio_metrics(rf_rate=rf_rate) 
        
        trading_days = int(horizon_years * 252)
        
        engine = MonteCarloEngine(portfolio=portfolio, initial_capital=capital, time_horizon=trading_days, num_simulations=5000)
        simulated_paths = engine.run_simulation()
        risk_metrics = engine.calculate_risk_metrics(confidence_level=0.95)

        fig = go.Figure()
        days = list(range(trading_days + 1)) 
        
        p5 = np.percentile(simulated_paths, 5, axis=1)
        p25 = np.percentile(simulated_paths, 25, axis=1)
        p75 = np.percentile(simulated_paths, 75, axis=1)
        p95 = np.percentile(simulated_paths, 95, axis=1)
        mean_path = simulated_paths.mean(axis=1)

        fig.add_trace(go.Scatter(x=days + days[::-1], y=list(p95) + list(p5)[::-1], fill='toself', fillcolor='rgba(0, 229, 255, 0.1)', line=dict(color='rgba(255,255,255,0)'), name='5th - 95th Percentile'))
        fig.add_trace(go.Scatter(x=days + days[::-1], y=list(p75) + list(p25)[::-1], fill='toself', fillcolor='rgba(0, 229, 255, 0.25)', line=dict(color='rgba(255,255,255,0)'), name='25th - 75th Percentile'))
        fig.add_trace(go.Scatter(x=days, y=mean_path, mode='lines', name='Expected Value', line=dict(color=CYAN_HEX, width=3)))

        fig.update_layout(
            template='plotly_dark', 
            title=f"Simulated Portfolio Value: Confidence Interval Cone ({horizon_years}-Year Horizon)",
            xaxis_title="Trading Days",
            yaxis_title="Portfolio Value ($)",
            plot_bgcolor=BG_MAIN, paper_bgcolor=BG_MAIN, hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=BORDER_COLOR)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=BORDER_COLOR, tickprefix="$")

        # --- BUILD THE VERTICAL LEDGER ---
        def create_metric_row(label, value, color=TEXT_MAIN, is_last=False):
            return html.Div(style={
                'display': 'flex', 
                'justifyContent': 'space-between', 
                'alignItems': 'center', 
                'borderBottom': 'none' if is_last else f'1px solid {BORDER_COLOR}', 
                'paddingBottom': '12px', 
                'marginBottom': '12px'
            }, children=[
                html.Div(label, style={'color': '#94A3B8', 'fontSize': '12px', 'textTransform': 'uppercase', 'fontWeight': '600', 'letterSpacing': '0.5px'}),
                
                html.Div(value, style={
                    'color': color, 
                    'fontWeight': '500',                   
                    'fontSize': '17px',                    
                    'fontVariantNumeric': 'tabular-nums',  
                    'letterSpacing': '-0.5px'              
                })
            ])

        metrics_html = html.Div(style={'display': 'flex', 'flexDirection': 'column', 'height': '100%'}, children=[
            
            html.H3("Risk Profile", style={'color': TEXT_MAIN, 'marginTop': '0', 'marginBottom': '25px', 'fontSize': '14px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),
            
            # Core Performance
            create_metric_row("Expected Return", f"{portfolio.expected_annual_return:.2%}", '#00FF7F'),
            create_metric_row("Volatility", f"{portfolio.annual_volatility:.2%}", TEXT_MAIN),
            create_metric_row("Sharpe Ratio", f"{getattr(portfolio, 'sharpe_ratio', np.nan):.2f}", CYAN_HEX),
            create_metric_row("Sortino Ratio", f"{getattr(portfolio, 'sortino_ratio', np.nan):.2f}", CYAN_HEX),
            
            html.Div(style={'height': '20px'}),
            html.H3("Tail Risk", style={'color': '#FF6B6B', 'marginTop': '0', 'marginBottom': '20px', 'fontSize': '14px', 'fontWeight': 'bold', 'textTransform': 'uppercase', 'letterSpacing': '1px'}),
            
            create_metric_row("Max Drawdown", f"{getattr(portfolio, 'max_drawdown', np.nan):.2%}", '#FF4C4C'),
            create_metric_row("95% VaR", f"-${abs(risk_metrics['VaR']):,.0f}", '#FF6B6B'),
            create_metric_row("CVaR (Shortfall)", f"-${abs(risk_metrics['CVaR']):,.0f}", '#FF4C4C', is_last=True)
        ])

        return fig, metrics_html, ""

    except Exception as e:
        return empty_fig, "", f"System Error: {str(e)}"

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)