#!/usr/bin/env python3
"""
Data Gap Analysis - Find Missing Days/Hours in Databento Dataset
Identifies exactly which time periods have no data coverage.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

class DataGapAnalyzer:
    """Analyzes data gaps in the Databento dataset."""
    
    def __init__(self, data_file):
        self.data_file = Path(data_file)
        
    def load_and_analyze_timestamps(self, sample_size=50000):
        """Load data and extract all timestamps for gap analysis."""
        print(f"🔍 Analyzing timestamps from {self.data_file.name}...")
        
        timestamps = []
        record_count = 0
        
        with open(self.data_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= sample_size:
                    break
                try:
                    record = json.loads(line.strip())
                    ts_event = record.get('hd', {}).get('ts_event', '')
                    if ts_event:
                        # Parse timestamp
                        dt = pd.to_datetime(ts_event)
                        timestamps.append({
                            'datetime': dt,
                            'date': dt.date(),
                            'hour': dt.hour,
                            'day_of_week': dt.dayofweek,  # 0=Monday, 6=Sunday
                            'symbol': record.get('symbol', ''),
                            'volume': int(record.get('volume', 0))
                        })
                        record_count += 1
                except Exception as e:
                    continue
        
        print(f"✅ Loaded {record_count:,} timestamps")
        return pd.DataFrame(timestamps)
    
    def find_missing_dates(self, df):
        """Find missing dates in the dataset."""
        print("📅 Analyzing missing dates...")
        
        # Get date range
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        # Create complete date range
        date_range = pd.date_range(start=min_date, end=max_date, freq='D').date
        existing_dates = set(df['date'].unique())
        
        missing_dates = [d for d in date_range if d not in existing_dates]
        
        # Analyze patterns
        total_days = len(date_range)
        missing_days = len(missing_dates)
        coverage_pct = ((total_days - missing_days) / total_days) * 100
        
        print(f"📊 Date Coverage Analysis:")
        print(f"   • Date Range: {min_date} to {max_date}")
        print(f"   • Total Days: {total_days:,}")
        print(f"   • Days with Data: {total_days - missing_days:,}")
        print(f"   • Missing Days: {missing_days:,}")
        print(f"   • Coverage: {coverage_pct:.1f}%")
        
        return missing_dates, coverage_pct
    
    def analyze_hourly_patterns(self, df):
        """Analyze hourly trading patterns."""
        print("⏰ Analyzing hourly patterns...")
        
        # Group by hour
        hourly_counts = df.groupby('hour').size()
        hourly_volume = df.groupby('hour')['volume'].sum()
        
        # Find missing hours
        all_hours = set(range(24))
        existing_hours = set(hourly_counts.index)
        missing_hours = sorted(all_hours - existing_hours)
        
        print(f"📊 Hourly Coverage:")
        print(f"   • Hours with Data: {len(existing_hours)}/24")
        print(f"   • Missing Hours: {missing_hours}")
        print(f"   • Peak Hour: {hourly_counts.idxmax()} ({hourly_counts.max():,} records)")
        print(f"   • Quiet Hour: {hourly_counts.idxmin()} ({hourly_counts.min():,} records)")
        
        return hourly_counts, hourly_volume, missing_hours
    
    def analyze_weekly_patterns(self, df):
        """Analyze day-of-week patterns."""
        print("📈 Analyzing weekly patterns...")
        
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_counts = df.groupby('day_of_week').size()
        daily_volume = df.groupby('day_of_week')['volume'].sum()
        
        # Find missing days of week
        all_days = set(range(7))
        existing_days = set(daily_counts.index)
        missing_days = sorted(all_days - existing_days)
        
        print(f"📊 Weekly Coverage:")
        print(f"   • Days of Week with Data: {len(existing_days)}/7")
        if missing_days:
            missing_day_names = [day_names[d] for d in missing_days]
            print(f"   • Missing Days: {missing_day_names}")
        
        for day_idx, count in daily_counts.items():
            day_name = day_names[day_idx]
            volume = daily_volume.get(day_idx, 0)
            print(f"   • {day_name}: {count:,} records, {volume:,} volume")
        
        return daily_counts, daily_volume, missing_days
    
    def create_gap_visualizations(self, df):
        """Create comprehensive gap visualizations."""
        print("📊 Creating gap visualizations...")
        
        # 1. Daily record counts over time
        daily_counts = df.groupby('date').size().reset_index(name='record_count')
        daily_counts['date'] = pd.to_datetime(daily_counts['date'])
        
        # 2. Hourly heatmap
        df['datetime_only'] = df['datetime'].dt.floor('H')
        hourly_data = df.groupby(['date', 'hour']).size().reset_index(name='count')
        
        # Create the visualization
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Daily Record Counts Over Time', 'Hourly Distribution',
                'Day-of-Week Patterns', 'Data Density Heatmap',
                'Missing Data Calendar View', 'Volume vs Record Count'
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # 1. Daily record counts
        fig.add_trace(
            go.Scatter(
                x=daily_counts['date'],
                y=daily_counts['record_count'],
                mode='lines+markers',
                name='Daily Records',
                line=dict(width=2),
                hovertemplate='Date: %{x}<br>Records: %{y:,}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Hourly distribution
        hourly_counts = df.groupby('hour').size()
        fig.add_trace(
            go.Bar(
                x=list(hourly_counts.index),
                y=list(hourly_counts.values),
                name='Hourly Distribution',
                hovertemplate='Hour: %{x}<br>Records: %{y:,}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. Day-of-week patterns
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_counts_dow = df.groupby('day_of_week').size()
        fig.add_trace(
            go.Bar(
                x=[day_names[i] for i in daily_counts_dow.index],
                y=list(daily_counts_dow.values),
                name='Weekly Pattern',
                hovertemplate='Day: %{x}<br>Records: %{y:,}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # 4. Data density heatmap (sample)
        if len(hourly_data) > 0:
            # Create pivot for heatmap
            heatmap_data = hourly_data.head(100).pivot(index='date', columns='hour', values='count').fillna(0)
            
            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data.values,
                    x=heatmap_data.columns,
                    y=[d.strftime('%m-%d') for d in heatmap_data.index],
                    colorscale='Viridis',
                    name='Data Density',
                    hovertemplate='Hour: %{x}<br>Date: %{y}<br>Records: %{z}<extra></extra>'
                ),
                row=2, col=2
            )
        
        # 5. Missing data analysis
        missing_dates, coverage_pct = self.find_missing_dates(df)
        
        # Create binary coverage data
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        coverage_data = []
        for date in date_range:
            has_data = date.date() in df['date'].values
            coverage_data.append({
                'date': date,
                'has_data': 1 if has_data else 0
            })
        
        coverage_df = pd.DataFrame(coverage_data)
        
        fig.add_trace(
            go.Scatter(
                x=coverage_df['date'],
                y=coverage_df['has_data'],
                mode='markers',
                marker=dict(
                    color=coverage_df['has_data'],
                    colorscale=[[0, 'red'], [1, 'green']],
                    size=6
                ),
                name='Data Coverage',
                hovertemplate='Date: %{x}<br>Has Data: %{text}<extra></extra>',
                text=['Yes' if x else 'No' for x in coverage_df['has_data']]
            ),
            row=3, col=1
        )
        
        # 6. Volume vs Record Count
        daily_volume = df.groupby('date')['volume'].sum().reset_index()
        daily_volume['date'] = pd.to_datetime(daily_volume['date'])
        
        # Merge with daily_counts
        volume_records = pd.merge(daily_counts, daily_volume, on='date', how='inner')
        
        fig.add_trace(
            go.Scatter(
                x=volume_records['record_count'],
                y=volume_records['volume'],
                mode='markers',
                marker=dict(size=8, opacity=0.6),
                name='Volume vs Records',
                hovertemplate='Records: %{x:,}<br>Volume: %{y:,}<extra></extra>'
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title={
                'text': f'Data Gap Analysis - Coverage: {coverage_pct:.1f}%',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            showlegend=True
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Record Count", row=1, col=1)
        fig.update_xaxes(title_text="Hour of Day", row=1, col=2)
        fig.update_yaxes(title_text="Record Count", row=1, col=2)
        fig.update_xaxes(title_text="Day of Week", row=2, col=1)
        fig.update_yaxes(title_text="Record Count", row=2, col=1)
        fig.update_xaxes(title_text="Hour", row=2, col=2)
        fig.update_yaxes(title_text="Date", row=2, col=2)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Has Data (1=Yes, 0=No)", row=3, col=1)
        fig.update_xaxes(title_text="Record Count", row=3, col=2)
        fig.update_yaxes(title_text="Volume", row=3, col=2)
        
        return fig
    
    def generate_gap_report(self, df):
        """Generate comprehensive gap analysis report."""
        print("📝 Generating gap analysis report...")
        
        missing_dates, coverage_pct = self.find_missing_dates(df)
        hourly_counts, hourly_volume, missing_hours = self.analyze_hourly_patterns(df)
        daily_counts, daily_volume, missing_days = self.analyze_weekly_patterns(df)
        
        # Additional statistics
        total_records = len(df)
        unique_dates = df['date'].nunique()
        date_range = (df['date'].max() - df['date'].min()).days + 1
        
        # Find largest gaps
        missing_dates_sorted = sorted(missing_dates)
        gaps = []
        if missing_dates_sorted:
            current_gap_start = missing_dates_sorted[0]
            current_gap_end = missing_dates_sorted[0]
            
            for i in range(1, len(missing_dates_sorted)):
                if (missing_dates_sorted[i] - missing_dates_sorted[i-1]).days == 1:
                    current_gap_end = missing_dates_sorted[i]
                else:
                    gap_days = (current_gap_end - current_gap_start).days + 1
                    gaps.append((current_gap_start, current_gap_end, gap_days))
                    current_gap_start = missing_dates_sorted[i]
                    current_gap_end = missing_dates_sorted[i]
            
            # Add the last gap
            gap_days = (current_gap_end - current_gap_start).days + 1
            gaps.append((current_gap_start, current_gap_end, gap_days))
        
        # Sort gaps by size
        gaps.sort(key=lambda x: x[2], reverse=True)
        
        report = {
            'summary': {
                'total_records': total_records,
                'unique_dates': unique_dates,
                'date_range_days': date_range,
                'coverage_percentage': coverage_pct,
                'missing_dates_count': len(missing_dates)
            },
            'missing_dates': missing_dates[:20],  # First 20 missing dates
            'largest_gaps': gaps[:10],  # Top 10 largest gaps
            'hourly_analysis': {
                'missing_hours': missing_hours,
                'peak_hour': hourly_counts.idxmax(),
                'peak_hour_count': hourly_counts.max(),
                'quiet_hour': hourly_counts.idxmin(),
                'quiet_hour_count': hourly_counts.min()
            },
            'weekly_analysis': {
                'missing_days_of_week': missing_days,
                'daily_counts': daily_counts.to_dict()
            }
        }
        
        return report

def main():
    """Main execution function."""
    data_file = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data/glbx-mdp3-20100606-20250617.ohlcv-1d.json"
    
    analyzer = DataGapAnalyzer(data_file)
    
    # Load and analyze data
    df = analyzer.load_and_analyze_timestamps(sample_size=75000)  # Larger sample
    
    # Generate comprehensive analysis
    missing_dates, coverage_pct = analyzer.find_missing_dates(df)
    hourly_counts, hourly_volume, missing_hours = analyzer.analyze_hourly_patterns(df)
    daily_counts, daily_volume, missing_days = analyzer.analyze_weekly_patterns(df)
    
    # Create visualizations
    fig = analyzer.create_gap_visualizations(df)
    
    # Save visualization
    output_dir = Path("data_gap_analysis")
    output_dir.mkdir(exist_ok=True)
    
    fig.write_html(output_dir / "data_gap_analysis.html")
    
    # Generate detailed report
    report = analyzer.generate_gap_report(df)
    
    # Print summary
    print(f"\n🎯 DATA GAP ANALYSIS SUMMARY:")
    print(f"═══════════════════════════════")
    print(f"📊 Total Records Analyzed: {report['summary']['total_records']:,}")
    print(f"📅 Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"📈 Coverage: {report['summary']['coverage_percentage']:.1f}%")
    print(f"❌ Missing Days: {report['summary']['missing_dates_count']:,}")
    
    if report['largest_gaps']:
        print(f"\n🔍 LARGEST DATA GAPS:")
        for i, (start, end, days) in enumerate(report['largest_gaps'][:5], 1):
            print(f"   {i}. {start} to {end} ({days} days)")
    
    if missing_hours:
        print(f"\n⏰ Missing Hours: {missing_hours}")
    else:
        print(f"\n⏰ All 24 hours have data coverage")
    
    print(f"\n📁 Detailed analysis saved to: {output_dir}/data_gap_analysis.html")

if __name__ == "__main__":
    main()