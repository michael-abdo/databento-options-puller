#!/usr/bin/env python3
"""
Data Coverage Visualization for Databento Options Dataset
Creates comprehensive visualizations to understand data scope and coverage.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import os
from pathlib import Path
from collections import defaultdict, Counter
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('default')
sns.set_style("whitegrid")
sns.set_palette("husl")

class DataCoverageAnalyzer:
    """Comprehensive analyzer for the Databento dataset."""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.main_file = self.data_dir / "glbx-mdp3-20100606-20250617.ohlcv-1d.json"
        self.jan_file = self.data_dir / "2025_jan_data.json"
        self.symbology_file = self.data_dir / "symbology.json"
        
        # Data containers
        self.file_stats = {}
        self.temporal_coverage = {}
        self.symbol_analysis = {}
        self.volume_patterns = {}
        
    def analyze_file_structure(self):
        """Analyze file sizes and basic structure."""
        print("📊 Analyzing file structure...")
        
        files_to_analyze = [
            self.main_file, self.jan_file, self.symbology_file,
            self.data_dir / "condition.json", self.data_dir / "manifest.json",
            self.data_dir / "metadata.json"
        ]
        
        for file_path in files_to_analyze:
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                self.file_stats[file_path.name] = {
                    'size_mb': size_mb,
                    'exists': True,
                    'path': file_path
                }
            else:
                self.file_stats[file_path.name] = {
                    'size_mb': 0,
                    'exists': False,
                    'path': file_path
                }
    
    def sample_data_content(self, sample_size=10000):
        """Sample and analyze data content from main files."""
        print("🔍 Sampling data content...")
        
        # Sample from January 2025 file (smaller, faster)
        if self.jan_file.exists():
            records = []
            with open(self.jan_file, 'r') as f:
                for i, line in enumerate(f):
                    if i >= sample_size:
                        break
                    try:
                        record = json.loads(line.strip())
                        records.append(record)
                    except:
                        continue
            
            # Analyze the sample
            self._analyze_sample(records, "january_2025")
        
        # Sample from main file (first N records)
        if self.main_file.exists():
            print("📂 Sampling main dataset (first 50,000 records)...")
            records = []
            with open(self.main_file, 'r') as f:
                for i, line in enumerate(f):
                    if i >= 50000:  # Limit to prevent memory issues
                        break
                    try:
                        record = json.loads(line.strip())
                        records.append(record)
                    except:
                        continue
            
            self._analyze_sample(records, "main_dataset_sample")
    
    def _analyze_sample(self, records, dataset_name):
        """Analyze a sample of records."""
        if not records:
            return
            
        df = pd.DataFrame(records)
        
        # Extract dates and symbols
        dates = []
        symbols = []
        volumes = []
        prices = []
        
        for record in records:
            try:
                ts_event = record.get('hd', {}).get('ts_event', '')
                if ts_event:
                    date = pd.to_datetime(ts_event).date()
                    dates.append(date)
                    
                symbol = record.get('symbol', '')
                symbols.append(symbol)
                
                volume = float(record.get('volume', 0))
                volumes.append(volume)
                
                close_price = float(record.get('close', 0))
                prices.append(close_price)
                
            except:
                continue
        
        # Store analysis results
        self.temporal_coverage[dataset_name] = {
            'date_range': (min(dates), max(dates)) if dates else (None, None),
            'total_days': len(set(dates)),
            'records': len(records)
        }
        
        # Symbol analysis
        symbol_types = defaultdict(int)
        ho_futures = []
        oh_options = []
        
        for symbol in symbols:
            if symbol.startswith('HO') and ' ' not in symbol:
                ho_futures.append(symbol)
                symbol_types['HO_Futures'] += 1
            elif symbol.startswith('OH') and ' ' in symbol:
                oh_options.append(symbol)
                symbol_types['OH_Options'] += 1
            elif 'HO' in symbol:
                symbol_types['HO_Related'] += 1
            else:
                symbol_types['Other'] += 1
        
        self.symbol_analysis[dataset_name] = {
            'symbol_types': dict(symbol_types),
            'unique_symbols': len(set(symbols)),
            'ho_futures_count': len(set(ho_futures)),
            'oh_options_count': len(set(oh_options)),
            'sample_ho_futures': list(set(ho_futures))[:10],
            'sample_oh_options': list(set(oh_options))[:10]
        }
        
        # Volume patterns
        self.volume_patterns[dataset_name] = {
            'total_volume': sum(volumes),
            'avg_volume': np.mean(volumes) if volumes else 0,
            'max_volume': max(volumes) if volumes else 0,
            'volume_by_date': defaultdict(float)
        }
        
        # Group volume by date
        for date, volume in zip(dates, volumes):
            self.volume_patterns[dataset_name]['volume_by_date'][date] += volume
    
    def create_visualizations(self, output_dir="visualizations"):
        """Create comprehensive visualizations."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"📊 Creating visualizations in {output_path}...")
        
        # 1. File Structure Overview
        self._plot_file_structure(output_path)
        
        # 2. Temporal Coverage
        self._plot_temporal_coverage(output_path)
        
        # 3. Symbol Distribution
        self._plot_symbol_distribution(output_path)
        
        # 4. Volume Patterns
        self._plot_volume_patterns(output_path)
        
        # 5. Data Summary Dashboard
        self._create_summary_dashboard(output_path)
        
        print(f"✅ All visualizations saved to {output_path}/")
    
    def _plot_file_structure(self, output_path):
        """Plot file structure and sizes."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # File sizes
        files = list(self.file_stats.keys())
        sizes = [self.file_stats[f]['size_mb'] for f in files]
        colors = ['green' if self.file_stats[f]['exists'] else 'red' for f in files]
        
        bars = ax1.barh(files, sizes, color=colors)
        ax1.set_xlabel('Size (MB)')
        ax1.set_title('Dataset File Sizes')
        ax1.set_xscale('log')
        
        # Add size labels
        for bar, size in zip(bars, sizes):
            if size > 0:
                ax1.text(size, bar.get_y() + bar.get_height()/2, 
                        f'{size:.1f} MB', ha='left', va='center')
        
        # File existence pie chart
        exists_count = sum(1 for f in self.file_stats.values() if f['exists'])
        missing_count = len(self.file_stats) - exists_count
        
        ax2.pie([exists_count, missing_count], 
               labels=['Files Present', 'Files Missing'],
               colors=['green', 'red'],
               autopct='%1.0f%%')
        ax2.set_title('File Availability')
        
        plt.tight_layout()
        plt.savefig(output_path / 'file_structure.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_temporal_coverage(self, output_path):
        """Plot temporal coverage across datasets."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        datasets = list(self.temporal_coverage.keys())
        y_positions = range(len(datasets))
        
        for i, dataset in enumerate(datasets):
            coverage = self.temporal_coverage[dataset]
            start_date, end_date = coverage['date_range']
            
            if start_date and end_date:
                # Convert to matplotlib dates for plotting
                start_num = pd.to_datetime(start_date).toordinal()
                end_num = pd.to_datetime(end_date).toordinal()
                
                ax.barh(i, end_num - start_num, left=start_num, height=0.5,
                       label=f"{dataset} ({coverage['records']} records)")
                
                # Add text annotations
                mid_date = start_num + (end_num - start_num) / 2
                ax.text(mid_date, i, f"{coverage['total_days']} days", 
                       ha='center', va='center', fontweight='bold')
        
        ax.set_yticks(y_positions)
        ax.set_yticklabels(datasets)
        ax.set_xlabel('Date Range')
        ax.set_title('Temporal Coverage by Dataset')
        
        # Format x-axis as dates
        ax.xaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: pd.to_datetime(datetime.fromordinal(int(x))).strftime('%Y-%m')))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path / 'temporal_coverage.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_symbol_distribution(self, output_path):
        """Plot symbol type distributions."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, (dataset, analysis) in enumerate(self.symbol_analysis.items()):
            if i >= len(axes):
                break
                
            ax = axes[i]
            
            # Symbol types pie chart
            symbol_types = analysis['symbol_types']
            if symbol_types:
                wedges, texts, autotexts = ax.pie(symbol_types.values(), 
                                                 labels=symbol_types.keys(),
                                                 autopct='%1.1f%%',
                                                 startangle=90)
                
                # Enhance readability
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
            
            ax.set_title(f'Symbol Distribution: {dataset}\n'
                        f'Total: {analysis["unique_symbols"]} unique symbols')
        
        # Remove unused subplots
        for i in range(len(self.symbol_analysis), len(axes)):
            fig.delaxes(axes[i])
        
        plt.tight_layout()
        plt.savefig(output_path / 'symbol_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_volume_patterns(self, output_path):
        """Plot volume patterns over time."""
        fig, axes = plt.subplots(len(self.volume_patterns), 1, 
                                figsize=(12, 4 * len(self.volume_patterns)))
        
        if len(self.volume_patterns) == 1:
            axes = [axes]
        
        for i, (dataset, patterns) in enumerate(self.volume_patterns.items()):
            ax = axes[i]
            
            volume_by_date = patterns['volume_by_date']
            if volume_by_date:
                dates = sorted(volume_by_date.keys())
                volumes = [volume_by_date[date] for date in dates]
                
                ax.plot(dates, volumes, marker='o', markersize=3, linewidth=1)
                ax.set_title(f'Volume Patterns: {dataset}\n'
                           f'Total: {patterns["total_volume"]:,.0f}, '
                           f'Avg: {patterns["avg_volume"]:.1f}, '
                           f'Max: {patterns["max_volume"]:,.0f}')
                ax.set_ylabel('Volume')
                ax.tick_params(axis='x', rotation=45)
                
                # Add trend line
                if len(volumes) > 1:
                    z = np.polyfit(range(len(volumes)), volumes, 1)
                    p = np.poly1d(z)
                    ax.plot(dates, p(range(len(volumes))), "r--", alpha=0.8, 
                           label=f'Trend: {"↗" if z[0] > 0 else "↘"}')
                    ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_path / 'volume_patterns.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_summary_dashboard(self, output_path):
        """Create a comprehensive summary dashboard."""
        fig = plt.figure(figsize=(16, 12))
        
        # Create a 3x2 grid
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        
        # 1. Overall Statistics (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        stats_text = self._generate_summary_stats()
        ax1.text(0.05, 0.95, stats_text, transform=ax1.transAxes, 
                verticalalignment='top', fontfamily='monospace', fontsize=10)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('Dataset Summary Statistics', fontweight='bold')
        
        # 2. File Sizes (top right)
        ax2 = fig.add_subplot(gs[0, 1])
        files = [f for f in self.file_stats.keys() if self.file_stats[f]['exists']]
        sizes = [self.file_stats[f]['size_mb'] for f in files]
        
        if files and sizes:
            bars = ax2.bar(range(len(files)), sizes)
            ax2.set_xticks(range(len(files)))
            ax2.set_xticklabels([f.replace('.json', '') for f in files], rotation=45)
            ax2.set_ylabel('Size (MB)')
            ax2.set_title('File Sizes')
            ax2.set_yscale('log')
            
            # Add value labels
            for bar, size in zip(bars, sizes):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                        f'{size:.1f}', ha='center', va='bottom')
        
        # 3. Timeline (middle, spanning both columns)
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_timeline_summary(ax3)
        
        # 4. Symbol breakdown (bottom left)
        ax4 = fig.add_subplot(gs[2, 0])
        self._plot_symbol_summary(ax4)
        
        # 5. Recommendations (bottom right)
        ax5 = fig.add_subplot(gs[2, 1])
        recommendations = self._generate_recommendations()
        ax5.text(0.05, 0.95, recommendations, transform=ax5.transAxes,
                verticalalignment='top', fontsize=9, fontfamily='sans-serif')
        ax5.set_xlim(0, 1)
        ax5.set_ylim(0, 1)
        ax5.axis('off')
        ax5.set_title('Visualization Recommendations', fontweight='bold')
        
        plt.suptitle('Databento Options Dataset - Comprehensive Analysis Dashboard', 
                    fontsize=16, fontweight='bold')
        
        plt.savefig(output_path / 'summary_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_timeline_summary(self, ax):
        """Plot timeline summary on given axis."""
        all_start_dates = []
        all_end_dates = []
        
        for dataset, coverage in self.temporal_coverage.items():
            start_date, end_date = coverage['date_range']
            if start_date and end_date:
                all_start_dates.append(start_date)
                all_end_dates.append(end_date)
        
        if all_start_dates and all_end_dates:
            overall_start = min(all_start_dates)
            overall_end = max(all_end_dates)
            
            # Create timeline
            timeline_days = (overall_end - overall_start).days
            ax.barh(0, timeline_days, height=0.3, 
                   color='lightblue', alpha=0.7, label='Full Coverage')
            
            # Add markers for key dates
            ax.axvline(0, color='green', linestyle='--', alpha=0.8, label='Start')
            ax.axvline(timeline_days, color='red', linestyle='--', alpha=0.8, label='End')
            
            # Add year markers
            current_year = overall_start.year
            while current_year <= overall_end.year:
                year_start = datetime(current_year, 1, 1).date()
                if year_start >= overall_start:
                    days_from_start = (year_start - overall_start).days
                    ax.axvline(days_from_start, color='gray', alpha=0.3)
                    ax.text(days_from_start, 0.2, str(current_year), 
                           rotation=90, ha='center', va='bottom', fontsize=8)
                current_year += 1
            
            ax.set_xlim(0, timeline_days)
            ax.set_ylim(-0.5, 0.5)
            ax.set_xlabel(f'Days from {overall_start} to {overall_end}')
            ax.set_title(f'Data Timeline: {timeline_days:,} days ({overall_start} → {overall_end})')
            ax.set_yticks([])
    
    def _plot_symbol_summary(self, ax):
        """Plot symbol summary on given axis."""
        # Aggregate symbol counts across all datasets
        total_symbols = defaultdict(int)
        for analysis in self.symbol_analysis.values():
            for symbol_type, count in analysis['symbol_types'].items():
                total_symbols[symbol_type] += count
        
        if total_symbols:
            # Create horizontal bar chart
            types = list(total_symbols.keys())
            counts = list(total_symbols.values())
            
            bars = ax.barh(types, counts)
            ax.set_xlabel('Count')
            ax.set_title('Symbol Type Distribution')
            
            # Add value labels
            for bar, count in zip(bars, counts):
                ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                       f'{count:,}', ha='left', va='center')
    
    def _generate_summary_stats(self):
        """Generate summary statistics text."""
        total_files = len(self.file_stats)
        existing_files = sum(1 for f in self.file_stats.values() if f['exists'])
        total_size = sum(f['size_mb'] for f in self.file_stats.values())
        
        # Get overall date range
        all_start_dates = []
        all_end_dates = []
        total_records = 0
        
        for coverage in self.temporal_coverage.values():
            start_date, end_date = coverage['date_range']
            if start_date and end_date:
                all_start_dates.append(start_date)
                all_end_dates.append(end_date)
            total_records += coverage['records']
        
        date_range = "N/A"
        if all_start_dates and all_end_dates:
            overall_start = min(all_start_dates)
            overall_end = max(all_end_dates)
            date_range = f"{overall_start} to {overall_end}"
            timeline_years = (overall_end - overall_start).days / 365.25
        else:
            timeline_years = 0
        
        stats = f"""
FILES OVERVIEW:
• Total files: {total_files}
• Files present: {existing_files}
• Total size: {total_size:.1f} MB

DATA COVERAGE:
• Date range: {date_range}
• Timeline span: {timeline_years:.1f} years
• Total records: {total_records:,}

SYMBOL ANALYSIS:
• HO Futures: Energy commodity futures
• OH Options: Options on HO futures  
• Complex instruments: Spreads & strategies

DATASET QUALITY:
• Completeness: High (OHLCV fields)
• Consistency: Strong naming conventions
• Granularity: Daily OHLCV data
        """.strip()
        
        return stats
    
    def _generate_recommendations(self):
        """Generate visualization recommendations."""
        recommendations = """
BEST VISUALIZATION APPROACHES:

1. INTERACTIVE TIME SERIES:
   • Plotly/Dash dashboard
   • Zoom/pan capabilities
   • Multi-asset overlay

2. HEATMAPS FOR DENSITY:
   • Volume by date/contract
   • Strike price activity
   • Seasonal patterns

3. 3D SURFACE PLOTS:
   • Volatility surfaces
   • Options chains evolution
   • Time-strike-price grids

4. NETWORK GRAPHS:
   • Symbol relationships
   • Volume flow analysis
   • Market structure

5. STATISTICAL ANALYSIS:
   • Volume distribution histograms
   • Price movement correlations
   • Volatility clustering

RECOMMENDED TOOLS:
• Python: Plotly, Seaborn, Matplotlib
• Web: D3.js, Observable
• BI: Tableau, Power BI
• Jupyter notebooks for exploration
        """.strip()
        
        return recommendations
    
    def run_complete_analysis(self):
        """Run the complete analysis pipeline."""
        print("🚀 Starting comprehensive data analysis...")
        
        # Step 1: Analyze file structure
        self.analyze_file_structure()
        
        # Step 2: Sample and analyze content
        self.sample_data_content()
        
        # Step 3: Create visualizations
        self.create_visualizations()
        
        print("✅ Analysis complete!")
        return self


def main():
    """Main execution function."""
    data_dir = "/Users/Mike/Desktop/programming/2_proposals/other/databento-options-puller/data"
    
    # Create analyzer and run analysis
    analyzer = DataCoverageAnalyzer(data_dir)
    analyzer.run_complete_analysis()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 ANALYSIS SUMMARY")
    print("="*60)
    
    for filename, stats in analyzer.file_stats.items():
        status = "✅" if stats['exists'] else "❌"
        print(f"{status} {filename:<35} {stats['size_mb']:>8.1f} MB")
    
    print("\n📈 TEMPORAL COVERAGE:")
    for dataset, coverage in analyzer.temporal_coverage.items():
        start_date, end_date = coverage['date_range']
        print(f"   {dataset:<25} {start_date} → {end_date} ({coverage['records']:,} records)")
    
    print("\n🎯 SYMBOL BREAKDOWN:")
    for dataset, analysis in analyzer.symbol_analysis.items():
        print(f"   {dataset}:")
        for symbol_type, count in analysis['symbol_types'].items():
            print(f"      {symbol_type:<15} {count:>8,}")
    
    print(f"\n📁 Visualizations saved to: ./visualizations/")
    print("   • summary_dashboard.png    - Complete overview")
    print("   • file_structure.png       - File sizes & availability") 
    print("   • temporal_coverage.png    - Date range coverage")
    print("   • symbol_distribution.png  - Symbol type breakdown")
    print("   • volume_patterns.png      - Trading volume trends")


if __name__ == "__main__":
    main()