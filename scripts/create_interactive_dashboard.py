#!/usr/bin/env python3
"""
Interactive Data Coverage Dashboard
Creates an interactive HTML dashboard using Plotly for exploring the Databento dataset.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
from collections import defaultdict, Counter
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class InteractiveDashboardCreator:
    """Creates interactive dashboards for the Databento dataset."""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.main_file = self.data_dir / "glbx-mdp3-20100606-20250617.ohlcv-1d.json"
        self.symbology_file = self.data_dir / "symbology.json"
        
    def analyze_january_data(self, sample_size=2500):
        """Analyze January 2025 data in detail."""
        print("🔍 Analyzing sample dataset...")
        
        records = []
        with open(self.main_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= sample_size:
                    break
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except:
                    continue
        
        # Convert to DataFrame for analysis
        data = []
        for record in records:
            try:
                ts_event = record.get('hd', {}).get('ts_event', '')
                date = pd.to_datetime(ts_event).date()
                symbol = record.get('symbol', '')
                
                data.append({
                    'date': date,
                    'symbol': symbol,
                    'open': float(record.get('open', 0)),
                    'high': float(record.get('high', 0)),
                    'low': float(record.get('low', 0)),
                    'close': float(record.get('close', 0)),
                    'volume': int(record.get('volume', 0)),
                    'symbol_type': self._classify_symbol(symbol)
                })
            except:
                continue
        
        return pd.DataFrame(data)
    
    def _classify_symbol(self, symbol):
        """Classify symbol type."""
        if symbol.startswith('HO') and ' ' not in symbol:
            return 'HO_Futures'
        elif symbol.startswith('OH') and ' ' in symbol:
            if ' C' in symbol:
                return 'OH_Call_Options'
            elif ' P' in symbol:
                return 'OH_Put_Options'
            else:
                return 'OH_Options'
        elif 'HO' in symbol and '-' in symbol:
            return 'HO_Spreads'
        else:
            return 'Other'
    
    def create_interactive_dashboard(self):
        """Create comprehensive interactive dashboard."""
        print("📊 Creating interactive dashboard...")
        
        # Load data
        df = self.analyze_january_data()
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=2,
            subplot_titles=(
                'Volume by Symbol Type Over Time', 'Price Distribution by Symbol Type',
                'Daily Trading Activity Heatmap', 'Options Strike Price Analysis',
                'Volume vs Price Correlation', 'Symbol Type Distribution',
                'Time Series: Most Active Symbols', 'Daily Statistics'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"type": "pie"}],
                   [{"colspan": 2}, None]],
            vertical_spacing=0.08,
            horizontal_spacing=0.1
        )
        
        # 1. Volume by Symbol Type Over Time
        volume_by_date_type = df.groupby(['date', 'symbol_type'])['volume'].sum().reset_index()
        for symbol_type in volume_by_date_type['symbol_type'].unique():
            data_subset = volume_by_date_type[volume_by_date_type['symbol_type'] == symbol_type]
            fig.add_trace(
                go.Scatter(
                    x=data_subset['date'],
                    y=data_subset['volume'],
                    mode='lines+markers',
                    name=f'{symbol_type} Volume',
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Date: %{x}<br>' +
                                 'Volume: %{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # 2. Price Distribution by Symbol Type
        for i, symbol_type in enumerate(df['symbol_type'].unique()):
            symbol_data = df[df['symbol_type'] == symbol_type]
            fig.add_trace(
                go.Box(
                    y=symbol_data['close'],
                    name=symbol_type,
                    boxpoints='outliers',
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Price: $%{y:.4f}<extra></extra>'
                ),
                row=1, col=2
            )
        
        # 3. Daily Trading Activity Heatmap
        daily_activity = df.groupby(['date', 'symbol_type']).size().reset_index(name='count')
        pivot_activity = daily_activity.pivot(index='date', columns='symbol_type', values='count').fillna(0)
        
        fig.add_trace(
            go.Heatmap(
                z=pivot_activity.values,
                x=pivot_activity.columns,
                y=[d.strftime('%m-%d') for d in pivot_activity.index],
                colorscale='Viridis',
                name='Activity Heatmap',
                hovertemplate='Date: %{y}<br>' +
                             'Type: %{x}<br>' +
                             'Records: %{z}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 4. Options Strike Price Analysis (for options only)
        options_data = df[df['symbol_type'].str.contains('Options')]
        if not options_data.empty:
            # Extract strike prices from option symbols
            strikes = []
            for symbol in options_data['symbol'].unique():
                try:
                    if ' C' in symbol or ' P' in symbol:
                        strike_part = symbol.split(' ')[1][1:]  # Remove C/P prefix
                        strike = float(strike_part) / 10000.0  # Convert to dollars
                        strikes.extend([strike] * len(options_data[options_data['symbol'] == symbol]))
                except:
                    continue
            
            if strikes:
                fig.add_trace(
                    go.Histogram(
                        x=strikes,
                        nbinsx=20,
                        name='Strike Distribution',
                        hovertemplate='Strike: $%{x:.2f}<br>' +
                                     'Count: %{y}<extra></extra>'
                    ),
                    row=2, col=2
                )
        
        # 5. Volume vs Price Correlation
        fig.add_trace(
            go.Scatter(
                x=df['volume'],
                y=df['close'],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df['symbol_type'].astype('category').cat.codes,
                    colorscale='Viridis',
                    opacity=0.6
                ),
                name='Volume vs Price',
                hovertemplate='Symbol: %{text}<br>' +
                             'Volume: %{x:,.0f}<br>' +
                             'Price: $%{y:.4f}<extra></extra>',
                text=df['symbol']
            ),
            row=3, col=1
        )
        
        # 6. Symbol Type Distribution (Pie Chart)
        type_counts = df['symbol_type'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=type_counts.index,
                values=type_counts.values,
                name="Symbol Distribution",
                hovertemplate='<b>%{label}</b><br>' +
                             'Count: %{value}<br>' +
                             'Percentage: %{percent}<extra></extra>'
            ),
            row=3, col=2
        )
        
        # 7. Time Series: Most Active Symbols (bottom spanning both columns)
        most_active_symbols = df.groupby('symbol')['volume'].sum().nlargest(10).index
        for symbol in most_active_symbols[:5]:  # Show top 5 to avoid clutter
            symbol_data = df[df['symbol'] == symbol].groupby('date')['close'].mean().reset_index()
            fig.add_trace(
                go.Scatter(
                    x=symbol_data['date'],
                    y=symbol_data['close'],
                    mode='lines+markers',
                    name=f'{symbol}',
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Date: %{x}<br>' +
                                 'Price: $%{y:.4f}<extra></extra>'
                ),
                row=4, col=1
            )
        
        # Update layout
        fig.update_layout(
            height=1600,
            title={
                'text': 'Interactive Databento Options Dataset Dashboard - January 2025',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=2)
        fig.update_xaxes(title_text="Symbol Type", row=2, col=1)
        fig.update_yaxes(title_text="Date", row=2, col=1)
        fig.update_xaxes(title_text="Strike Price ($)", row=2, col=2)
        fig.update_yaxes(title_text="Count", row=2, col=2)
        fig.update_xaxes(title_text="Volume", row=3, col=1)
        fig.update_yaxes(title_text="Price ($)", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=4, col=1)
        fig.update_yaxes(title_text="Price ($)", row=4, col=1)
        
        return fig
    
    def create_3d_visualization(self):
        """Create 3D visualization of options data."""
        print("📊 Creating 3D options visualization...")
        
        df = self.analyze_january_data()
        
        # Filter for options only
        options_df = df[df['symbol_type'].str.contains('Options')]
        
        if options_df.empty:
            print("⚠️ No options data found for 3D visualization")
            return None
        
        # Extract strike prices and create 3D plot
        plot_data = []
        for _, row in options_df.iterrows():
            try:
                symbol = row['symbol']
                if ' C' in symbol or ' P' in symbol:
                    strike_part = symbol.split(' ')[1][1:]  # Remove C/P prefix
                    strike = float(strike_part) / 10000.0  # Convert to dollars
                    
                    plot_data.append({
                        'date': row['date'],
                        'strike': strike,
                        'price': row['close'],
                        'volume': row['volume'],
                        'option_type': 'Call' if ' C' in symbol else 'Put'
                    })
            except:
                continue
        
        if not plot_data:
            print("⚠️ No valid options data for 3D visualization")
            return None
        
        plot_df = pd.DataFrame(plot_data)
        
        # Create 3D scatter plot
        fig = go.Figure()
        
        for option_type in plot_df['option_type'].unique():
            type_data = plot_df[plot_df['option_type'] == option_type]
            
            fig.add_trace(go.Scatter3d(
                x=type_data['date'],
                y=type_data['strike'],
                z=type_data['price'],
                mode='markers',
                marker=dict(
                    size=np.sqrt(type_data['volume']) * 2,  # Size by volume
                    color=type_data['volume'],
                    colorscale='Viridis',
                    opacity=0.7,
                    colorbar=dict(title="Volume")
                ),
                name=f'{option_type} Options',
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Date: %{x}<br>' +
                             'Strike: $%{y:.2f}<br>' +
                             'Price: $%{z:.4f}<br>' +
                             'Volume: %{text}<extra></extra>',
                text=type_data['volume']
            ))
        
        fig.update_layout(
            title={
                'text': '3D Options Visualization: Date × Strike × Price (Size = Volume)',
                'x': 0.5,
                'xanchor': 'center'
            },
            scene=dict(
                xaxis_title='Date',
                yaxis_title='Strike Price ($)',
                zaxis_title='Option Price ($)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=700
        )
        
        return fig
    
    def generate_summary_stats(self):
        """Generate summary statistics."""
        df = self.analyze_january_data()
        
        stats = {
            'total_records': len(df),
            'unique_symbols': df['symbol'].nunique(),
            'date_range': (df['date'].min(), df['date'].max()),
            'symbol_types': df['symbol_type'].value_counts().to_dict(),
            'total_volume': df['volume'].sum(),
            'avg_price': df['close'].mean(),
            'price_range': (df['close'].min(), df['close'].max()),
            'most_active_symbol': df.groupby('symbol')['volume'].sum().idxmax(),
            'trading_days': df['date'].nunique()
        }
        
        return stats
    
    def save_dashboards(self, output_dir="interactive_visualizations"):
        """Save all interactive dashboards."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"💾 Saving interactive dashboards to {output_path}/")
        
        # Create main dashboard
        main_dashboard = self.create_interactive_dashboard()
        main_dashboard.write_html(output_path / "main_dashboard.html")
        
        # Create 3D visualization
        viz_3d = self.create_3d_visualization()
        if viz_3d:
            viz_3d.write_html(output_path / "3d_options_visualization.html")
        
        # Generate summary report
        stats = self.generate_summary_stats()
        self._create_summary_report(stats, output_path)
        
        print("✅ Interactive dashboards saved:")
        print(f"   • {output_path}/main_dashboard.html")
        print(f"   • {output_path}/3d_options_visualization.html")
        print(f"   • {output_path}/summary_report.html")
        
        return output_path
    
    def _create_summary_report(self, stats, output_path):
        """Create HTML summary report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Databento Dataset Summary Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .stat {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }}
        .highlight {{ color: #e74c3c; font-weight: bold; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        .symbol-type {{ background: #3498db; color: white; padding: 8px 12px; margin: 5px; border-radius: 20px; display: inline-block; }}
        .recommendations {{ background: #2ecc71; color: white; padding: 20px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Databento Options Dataset Analysis Report</h1>
        
        <h2>📈 Dataset Overview</h2>
        <div class="stat">
            <strong>Total Records:</strong> <span class="highlight">{stats['total_records']:,}</span>
        </div>
        <div class="stat">
            <strong>Unique Symbols:</strong> <span class="highlight">{stats['unique_symbols']:,}</span>
        </div>
        <div class="stat">
            <strong>Date Range:</strong> <span class="highlight">{stats['date_range'][0]} to {stats['date_range'][1]}</span>
        </div>
        <div class="stat">
            <strong>Trading Days:</strong> <span class="highlight">{stats['trading_days']}</span>
        </div>
        
        <h2>💰 Market Data Summary</h2>
        <div class="grid">
            <div class="stat">
                <strong>Total Volume:</strong><br>
                <span class="highlight">{stats['total_volume']:,.0f}</span> contracts
            </div>
            <div class="stat">
                <strong>Average Price:</strong><br>
                <span class="highlight">${stats['avg_price']:.4f}</span>
            </div>
        </div>
        <div class="grid">
            <div class="stat">
                <strong>Price Range:</strong><br>
                <span class="highlight">${stats['price_range'][0]:.4f} - ${stats['price_range'][1]:.4f}</span>
            </div>
            <div class="stat">
                <strong>Most Active Symbol:</strong><br>
                <span class="highlight">{stats['most_active_symbol']}</span>
            </div>
        </div>
        
        <h2>🎯 Symbol Type Breakdown</h2>
        <div style="text-align: center; margin: 20px 0;">
"""
        
        for symbol_type, count in stats['symbol_types'].items():
            html_content += f'<span class="symbol-type">{symbol_type}: {count:,}</span>'
        
        html_content += f"""
        </div>
        
        <h2>📊 Visualization Files Generated</h2>
        <div class="stat">
            <strong>Main Dashboard:</strong> <a href="main_dashboard.html">Interactive Multi-Panel Dashboard</a><br>
            <em>Comprehensive overview with volume trends, price distributions, and trading activity</em>
        </div>
        <div class="stat">
            <strong>3D Visualization:</strong> <a href="3d_options_visualization.html">3D Options Analysis</a><br>
            <em>Three-dimensional view of options data showing Date × Strike × Price relationships</em>
        </div>
        
        <div class="recommendations">
            <h2 style="margin-top: 0;">🎯 Key Insights & Recommendations</h2>
            <ul>
                <li><strong>Rich Dataset:</strong> {stats['total_records']:,} records across {stats['trading_days']} trading days</li>
                <li><strong>Multiple Instrument Types:</strong> Futures, options, and spread contracts</li>
                <li><strong>Volume Analysis:</strong> Total volume of {stats['total_volume']:,.0f} contracts indicates active trading</li>
                <li><strong>Price Precision:</strong> High-precision pricing data suitable for quantitative analysis</li>
                <li><strong>Time Series:</strong> Perfect for trend analysis and volatility modeling</li>
            </ul>
            
            <h3>Best Visualization Approaches:</h3>
            <ul>
                <li><strong>Time Series Analysis:</strong> Volume and price trends over time</li>
                <li><strong>Heatmaps:</strong> Trading activity by date and instrument type</li>
                <li><strong>3D Surfaces:</strong> Options pricing across strike and time dimensions</li>
                <li><strong>Interactive Dashboards:</strong> Multi-dimensional exploration</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin-top: 30px; color: #7f8c8d;">
            <em>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path / "summary_report.html", 'w') as f:
            f.write(html_content)


def main():
    """Main execution function."""
    data_dir = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data"
    
    creator = InteractiveDashboardCreator(data_dir)
    output_path = creator.save_dashboards()
    
    print(f"\n🎉 Interactive visualizations complete!")
    print(f"📁 Open the following files in your browser:")
    print(f"   • {output_path}/main_dashboard.html")
    print(f"   • {output_path}/3d_options_visualization.html") 
    print(f"   • {output_path}/summary_report.html")


if __name__ == "__main__":
    main()