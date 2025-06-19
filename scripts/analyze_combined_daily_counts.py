#!/usr/bin/env python3
"""
Analyze Databento data and create a single chart showing daily counts for both futures and options.
"""

import json
from collections import defaultdict
from datetime import datetime
import os

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def analyze_futures_options_data():
    """Analyze the Databento data file and separate futures vs options records."""
    
    data_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json"
    
    print("Analyzing Databento HO/OH data...")
    print(f"Reading data file...")
    
    # Initialize counters
    futures_daily_counts = defaultdict(int)
    options_daily_counts = defaultdict(int)
    total_lines = 0
    
    # Read and process the file
    with open(data_file, 'r') as f:
        for line_num, line in enumerate(f):
            try:
                record = json.loads(line.strip())
                total_lines += 1
                
                # Get symbol and timestamp
                symbol = record.get('symbol', '')
                ts_event = record.get('hd', {}).get('ts_event')
                
                if not ts_event:
                    continue
                
                # Parse timestamp to date
                try:
                    timestamp = datetime.fromisoformat(ts_event.replace('Z', '+00:00'))
                    date = timestamp.date()
                except:
                    continue
                
                # Categorize based on symbol
                if symbol.startswith('HO'):
                    # It's a futures contract
                    futures_daily_counts[date] += 1
                elif symbol.startswith('OH'):
                    # It's an options contract
                    options_daily_counts[date] += 1
                
                # Progress indicator
                if line_num % 100000 == 0 and line_num > 0:
                    print(f"Processed {line_num:,} lines...")
                    
            except json.JSONDecodeError:
                continue
    
    print(f"\nTotal lines processed: {total_lines:,}")
    
    # Convert to sorted lists for plotting
    all_dates = sorted(set(futures_daily_counts.keys()) | set(options_daily_counts.keys()))
    
    futures_dates = []
    futures_counts = []
    options_dates = []
    options_counts = []
    
    for date in all_dates:
        if date in futures_daily_counts:
            futures_dates.append(date)
            futures_counts.append(futures_daily_counts[date])
        if date in options_daily_counts:
            options_dates.append(date)
            options_counts.append(options_daily_counts[date])
    
    # Create the visualization
    create_combined_visualization(futures_dates, futures_counts, options_dates, options_counts)

def create_combined_visualization(futures_dates, futures_counts, options_dates, options_counts):
    """Create a single interactive chart with both futures and options daily counts."""
    
    # Create figure
    fig = go.Figure()
    
    # Add futures trace
    fig.add_trace(go.Scatter(
        x=futures_dates,
        y=futures_counts,
        mode='lines',
        name='Futures (HO)',
        line=dict(color='#1f77b4', width=1),
        hovertemplate='Date: %{x}<br>Futures Count: %{y}<extra></extra>'
    ))
    
    # Add options trace
    fig.add_trace(go.Scatter(
        x=options_dates,
        y=options_counts,
        mode='lines',
        name='Options (OH)',
        line=dict(color='#ff7f0e', width=1),
        hovertemplate='Date: %{x}<br>Options Count: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': 'Daily Record Counts - Futures vs Options',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24}
        },
        xaxis_title='Date',
        yaxis_title='Records per Day',
        hovermode='x unified',
        height=600,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor='white',
        paper_bgcolor='#f5f5f5',
        xaxis=dict(
            gridcolor='#e0e0e0',
            showgrid=True,
            rangeslider=dict(visible=True),
            type='date'
        ),
        yaxis=dict(
            gridcolor='#e0e0e0',
            showgrid=True,
            zeroline=True,
            zerolinecolor='#e0e0e0'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Daily Record Counts - Futures vs Options</title>
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
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }}
            .stat-group {{
                text-align: center;
            }}
            .stat-label {{
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
            #myDiv {{
                width: 100%;
                height: 600px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="summary">
                <div class="stat-group">
                    <div class="stat-label">Total Days</div>
                    <div class="stat-value">{len(set(futures_dates) | set(options_dates)):,}</div>
                </div>
                <div class="stat-group">
                    <div class="stat-label">Date Range</div>
                    <div class="stat-value">{min(min(futures_dates), min(options_dates)).strftime('%b %Y')} - {max(max(futures_dates), max(options_dates)).strftime('%b %Y')}</div>
                </div>
                <div class="stat-group">
                    <div class="stat-label">Avg Futures/Day</div>
                    <div class="stat-value">{sum(futures_counts) / len(futures_counts):.1f}</div>
                </div>
                <div class="stat-group">
                    <div class="stat-label">Avg Options/Day</div>
                    <div class="stat-value">{sum(options_counts) / len(options_counts):.1f}</div>
                </div>
            </div>
            <div id="myDiv"></div>
        </div>
        
        <script>
            var data = {fig.to_json()};
            Plotly.newPlot('myDiv', data.data, data.layout);
        </script>
    </body>
    </html>
    """
    
    # Save the HTML file
    output_path = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data_gap_analysis/data_gap_analysis.html"
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"\nVisualization saved to: {output_path}")
    print(f"\nAnalysis complete!")

if __name__ == "__main__":
    analyze_futures_options_data()