#!/usr/bin/env python3
"""
Analyze and visualize futures vs options data distribution in the dataset.
Creates two charts showing daily record counts for futures and options separately.
"""

import json
import pandas as pd
from datetime import datetime
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def categorize_symbol(symbol):
    """
    Categorize a symbol as futures or options.
    
    Futures: HO followed by month/year code (e.g., HOF5, HOG5)
    Options: OH followed by month/year code, space, then C/P and strike (e.g., OHF5 C27800)
    """
    if symbol.startswith('OH') and (' C' in symbol or ' P' in symbol):
        return 'options'
    elif symbol.startswith('HO'):
        return 'futures'
    else:
        return 'other'

def analyze_data():
    """Load and analyze the data file."""
    data_file = '/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json'
    
    # Count records by date and type
    futures_counts = defaultdict(int)
    options_counts = defaultdict(int)
    
    # Sample data for analysis
    futures_samples = []
    options_samples = []
    
    print("Reading data file...")
    with open(data_file, 'r') as f:
        for line_num, line in enumerate(f):
            if line_num % 100000 == 0:
                print(f"Processed {line_num:,} lines...")
            
            try:
                record = json.loads(line.strip())
                symbol = record.get('symbol', '')
                ts_event = record['hd']['ts_event']
                
                # Extract date from timestamp
                date = ts_event.split('T')[0]
                
                # Categorize symbol
                category = categorize_symbol(symbol)
                
                if category == 'futures':
                    futures_counts[date] += 1
                    if len(futures_samples) < 10:
                        futures_samples.append((date, symbol))
                elif category == 'options':
                    options_counts[date] += 1
                    if len(options_samples) < 10:
                        options_samples.append((date, symbol))
                        
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing line {line_num}: {e}")
    
    print(f"\nTotal lines processed: {line_num:,}")
    
    # Convert to DataFrames
    futures_df = pd.DataFrame(list(futures_counts.items()), columns=['date', 'count'])
    futures_df['date'] = pd.to_datetime(futures_df['date'])
    futures_df = futures_df.sort_values('date')
    
    options_df = pd.DataFrame(list(options_counts.items()), columns=['date', 'count'])
    options_df['date'] = pd.to_datetime(options_df['date'])
    options_df = options_df.sort_values('date')
    
    # Print summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    print(f"\nFutures Data:")
    print(f"  Total days with data: {len(futures_df):,}")
    print(f"  Total records: {futures_df['count'].sum():,}")
    print(f"  Average records per day: {futures_df['count'].mean():.1f}")
    print(f"  Date range: {futures_df['date'].min()} to {futures_df['date'].max()}")
    print(f"  Sample symbols: {[s[1] for s in futures_samples[:5]]}")
    
    print(f"\nOptions Data:")
    print(f"  Total days with data: {len(options_df):,}")
    print(f"  Total records: {options_df['count'].sum():,}")
    print(f"  Average records per day: {options_df['count'].mean():.1f}")
    print(f"  Date range: {options_df['date'].min()} to {options_df['date'].max()}")
    print(f"  Sample symbols: {[s[1] for s in options_samples[:5]]}")
    
    return futures_df, options_df

def create_visualization(futures_df, options_df):
    """Create interactive visualization with two charts."""
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Futures Data (HO symbols)', 'Options Data (OH symbols)'),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Add futures trace
    fig.add_trace(
        go.Scatter(
            x=futures_df['date'],
            y=futures_df['count'],
            mode='lines',
            name='Futures',
            line=dict(color='blue', width=1),
            hovertemplate='Date: %{x|%Y-%m-%d}<br>Records: %{y}<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Add options trace
    fig.add_trace(
        go.Scatter(
            x=options_df['date'],
            y=options_df['count'],
            mode='lines',
            name='Options',
            line=dict(color='green', width=1),
            hovertemplate='Date: %{x|%Y-%m-%d}<br>Records: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Daily Record Count", row=1, col=1)
    fig.update_yaxes(title_text="Daily Record Count", row=2, col=1)
    
    fig.update_layout(
        title={
            'text': 'Databento HO/OH Data Analysis: Futures vs Options',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        height=800,
        showlegend=False,
        hovermode='x unified'
    )
    
    # Save HTML
    output_file = '/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data_gap_analysis/futures_options_split_analysis.html'
    
    # Create full HTML with summary statistics
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Futures vs Options Data Analysis</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .summary {{
                display: flex;
                justify-content: space-around;
                margin: 20px 0;
            }}
            .stat-box {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                flex: 1;
                margin: 0 10px;
            }}
            .stat-box h3 {{
                margin-top: 0;
                color: #333;
            }}
            .stat {{
                margin: 5px 0;
                font-size: 14px;
            }}
            .stat-value {{
                font-weight: bold;
                color: #2e7d32;
            }}
            #myDiv {{
                width: 100%;
                height: 800px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Databento HO/OH Data Analysis: Futures vs Options</h1>
            
            <div class="summary">
                <div class="stat-box">
                    <h3>📊 Futures Data (HO symbols)</h3>
                    <div class="stat">Total Days: <span class="stat-value">{len(futures_df):,}</span></div>
                    <div class="stat">Total Records: <span class="stat-value">{futures_df['count'].sum():,}</span></div>
                    <div class="stat">Avg Records/Day: <span class="stat-value">{futures_df['count'].mean():.1f}</span></div>
                    <div class="stat">Date Range: <span class="stat-value">{futures_df['date'].min().strftime('%Y-%m-%d')} to {futures_df['date'].max().strftime('%Y-%m-%d')}</span></div>
                </div>
                
                <div class="stat-box">
                    <h3>📈 Options Data (OH symbols)</h3>
                    <div class="stat">Total Days: <span class="stat-value">{len(options_df):,}</span></div>
                    <div class="stat">Total Records: <span class="stat-value">{options_df['count'].sum():,}</span></div>
                    <div class="stat">Avg Records/Day: <span class="stat-value">{options_df['count'].mean():.1f}</span></div>
                    <div class="stat">Date Range: <span class="stat-value">{options_df['date'].min().strftime('%Y-%m-%d')} to {options_df['date'].max().strftime('%Y-%m-%d')}</span></div>
                </div>
            </div>
            
            <div id="myDiv"></div>
        </div>
        
        <script>
            var data = {fig.to_json()};
            var layout = data.layout;
            var config = {{responsive: true}};
            Plotly.newPlot('myDiv', data.data, layout, config);
        </script>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"\nVisualization saved to: {output_file}")
    
    return output_file

def main():
    """Main execution function."""
    print("Analyzing Databento HO/OH data...")
    
    # Analyze data
    futures_df, options_df = analyze_data()
    
    # Create visualization
    output_file = create_visualization(futures_df, options_df)
    
    print("\nAnalysis complete!")
    print(f"Open the HTML file to view the interactive charts: {output_file}")

if __name__ == "__main__":
    main()