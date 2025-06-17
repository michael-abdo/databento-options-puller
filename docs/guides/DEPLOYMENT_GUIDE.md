# Deployment Guide - Databento Options Puller

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Installation Methods](#installation-methods)
3. [Configuration Management](#configuration-management)
4. [Performance Tuning](#performance-tuning)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Scheduling and Automation](#scheduling-and-automation)
7. [Troubleshooting Production Issues](#troubleshooting-production-issues)
8. [Scaling Considerations](#scaling-considerations)

## Pre-Deployment Checklist

### System Requirements
- [ ] Python 3.8 or higher installed
- [ ] At least 4GB RAM available
- [ ] 10GB free disk space for data and logs
- [ ] Stable internet connection
- [ ] Databento API key obtained

### Environment Setup
```bash
# 1. Verify Python version
python --version  # Should be 3.8+

# 2. Create dedicated user (optional but recommended)
sudo adduser databento-service
sudo usermod -aG sudo databento-service

# 3. Create application directory
sudo mkdir -p /opt/databento-options
sudo chown databento-service:databento-service /opt/databento-options

# 4. Set up virtual environment
cd /opt/databento-options
python -m venv venv
source venv/bin/activate
```

### Security Checklist
- [ ] API key stored securely (not in code)
- [ ] File permissions properly set
- [ ] Network firewall configured
- [ ] SSL/TLS for any web interfaces
- [ ] Regular security updates scheduled

## Installation Methods

### Method 1: Package Installation
```bash
# Install from package
pip install databento-options-puller

# Or install from source
git clone https://github.com/your-repo/databento-options-puller.git
cd databento-options-puller
pip install -e .
```

### Method 2: Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DATABENTO_API_KEY=""

CMD ["python", "databento_options_puller.py"]
```

Build and run:
```bash
docker build -t databento-options .
docker run -e DATABENTO_API_KEY=$DATABENTO_API_KEY \
           -v $(pwd)/output:/app/output \
           databento-options \
           --start-date "2021-12-01" \
           --end-date "2022-03-31"
```

### Method 3: Cloud Deployment (AWS Lambda)
```python
# lambda_handler.py
import os
from datetime import datetime
from databento_options_puller import DatabentoOptionsPuller

def lambda_handler(event, context):
    puller = DatabentoOptionsPuller(
        api_key=os.environ['DATABENTO_API_KEY']
    )
    
    df = puller.run(
        start_date=datetime.fromisoformat(event['start_date']),
        end_date=datetime.fromisoformat(event['end_date'])
    )
    
    # Save to S3
    s3_path = f"s3://your-bucket/options-data/{event['start_date']}.csv"
    df.to_csv(s3_path, index=False)
    
    return {
        'statusCode': 200,
        'body': f'Processed {len(df)} rows'
    }
```

## Configuration Management

### Environment Variables
```bash
# /etc/environment or .env file
DATABENTO_API_KEY="your_production_key"
DATABENTO_ENV="production"
LOG_LEVEL="INFO"
OUTPUT_DIR="/data/databento/output"
CACHE_DIR="/data/databento/cache"
```

### Configuration Hierarchy
1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration file
4. Default values (lowest priority)

### Production Config Example
```yaml
# config/production.yaml
databento:
  api_key: ${DATABENTO_API_KEY}
  timeout: 60
  max_retries: 5

strategy:
  target_delta: 0.15
  months_ahead: 2

performance:
  chunk_size: "1M"
  parallel_enabled: true
  max_workers: 8

logging:
  level: "WARNING"
  file_path: "/var/log/databento/options.log"
```

## Performance Tuning

### Memory Optimization
```python
# config/performance.yaml
processing:
  # Process in smaller chunks for large date ranges
  chunk_size: "2W"  # 2-week chunks
  
  # Limit memory usage
  max_memory_gb: 8
  
  # Enable garbage collection
  gc_threshold: 1000  # Force GC every 1000 iterations
```

### API Rate Management
```python
# Implement rate limiting
from ratelimit import limits, sleep_and_retry

class OptimizedDatabentoBridge:
    @sleep_and_retry
    @limits(calls=10, period=1)  # 10 calls per second
    def fetch_data(self, *args, **kwargs):
        return super().fetch_data(*args, **kwargs)
```

### Caching Strategy
```yaml
cache:
  # Use Redis for distributed caching
  backend: "redis"
  redis_url: "redis://localhost:6379/0"
  
  # Aggressive caching for production
  options_chain_ttl: 3600    # 1 hour
  volatility_ttl: 86400      # 24 hours
  futures_ttl: 600           # 10 minutes
```

### Database Storage (Optional)
```python
# Store results in database for faster access
import sqlalchemy as sa

engine = sa.create_engine('postgresql://user:pass@localhost/databento')

# Save to database
df.to_sql('options_data', engine, if_exists='append', index=False)
```

## Monitoring and Logging

### Logging Configuration
```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/databento/options.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'address': '/dev/log',
            'formatter': 'syslog',
        },
    },
    'formatters': {
        'detailed': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'syslog': {
            'format': 'databento[%(process)d]: %(levelname)s %(message)s'
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file', 'syslog']
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Metrics Collection
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
api_calls = Counter('databento_api_calls_total', 
                   'Total API calls made')
api_errors = Counter('databento_api_errors_total', 
                    'Total API errors')
processing_time = Histogram('databento_processing_seconds',
                           'Processing time in seconds')
active_contracts = Gauge('databento_active_contracts',
                        'Number of active option contracts')
```

### Health Checks
```python
# healthcheck.py
from flask import Flask, jsonify
import psutil

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'last_run': get_last_run_time(),
        'cache_size': get_cache_size()
    })

@app.route('/ready')
def ready():
    # Check if system is ready to process
    checks = {
        'api_key_set': os.environ.get('DATABENTO_API_KEY') is not None,
        'cache_writable': test_cache_write(),
        'output_writable': test_output_write()
    }
    
    if all(checks.values()):
        return jsonify({'status': 'ready', 'checks': checks}), 200
    else:
        return jsonify({'status': 'not ready', 'checks': checks}), 503
```

## Scheduling and Automation

### Cron Job Setup
```bash
# Daily run at 6 PM CT (after market close)
0 18 * * * /opt/databento-options/venv/bin/python /opt/databento-options/databento_options_puller.py --start-date $(date -d "1 month ago" +\%Y-\%m-\%d) --end-date $(date +\%Y-\%m-\%d) >> /var/log/databento/cron.log 2>&1
```

### Systemd Service
```ini
# /etc/systemd/system/databento-options.service
[Unit]
Description=Databento Options Data Puller
After=network.target

[Service]
Type=oneshot
User=databento-service
WorkingDirectory=/opt/databento-options
Environment="PATH=/opt/databento-options/venv/bin"
ExecStart=/opt/databento-options/venv/bin/python databento_options_puller.py --config config/production.yaml

[Install]
WantedBy=multi-user.target
```

### Airflow DAG
```python
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

def pull_options_data(**context):
    from databento_options_puller import DatabentoOptionsPuller
    
    execution_date = context['execution_date']
    start_date = execution_date - timedelta(days=30)
    
    puller = DatabentoOptionsPuller()
    df = puller.run(start_date, execution_date)
    
    # Save to data warehouse
    df.to_parquet(f"s3://data-lake/options/{execution_date}.parquet")

dag = DAG(
    'databento_options_daily',
    default_args={
        'owner': 'data-team',
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    },
    description='Pull daily options data',
    schedule_interval='0 18 * * *',  # 6 PM daily
    start_date=datetime(2021, 1, 1),
    catchup=False,
)

pull_task = PythonOperator(
    task_id='pull_options_data',
    python_callable=pull_options_data,
    dag=dag,
)
```

## Troubleshooting Production Issues

### Common Issues and Solutions

#### 1. API Rate Limiting
```python
# Implement exponential backoff
import time
from functools import wraps

def retry_with_backoff(max_retries=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
            raise
        return wrapper
    return decorator
```

#### 2. Memory Leaks
```python
# Monitor memory usage
import gc
import tracemalloc

tracemalloc.start()

# ... run processing ...

current, peak = tracemalloc.get_traced_memory()
logger.info(f"Current memory usage: {current / 10**6:.1f} MB")
logger.info(f"Peak memory usage: {peak / 10**6:.1f} MB")

# Force garbage collection
gc.collect()
```

#### 3. Data Quality Issues
```python
# Add data validation
def validate_output(df):
    issues = []
    
    # Check for missing data
    if df['Futures_Price'].isna().any():
        issues.append("Missing futures prices detected")
    
    # Check for outliers
    for col in df.select_dtypes(include=[float]).columns:
        if (df[col] < 0).any():
            issues.append(f"Negative values in {col}")
    
    if issues:
        raise DataQualityError(f"Validation failed: {issues}")
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DATABENTO_DEBUG=true

# Run with verbose output
python databento_options_puller.py \
    --start-date "2021-12-01" \
    --end-date "2021-12-31" \
    --log-level DEBUG \
    --dry-run  # Don't save output
```

## Scaling Considerations

### Horizontal Scaling
```python
# Distribute work across multiple instances
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

def process_month(year_month):
    start = pd.Timestamp(year_month)
    end = start + pd.offsets.MonthEnd(0)
    
    puller = DatabentoOptionsPuller()
    return puller.run(start, end)

# Process multiple months in parallel
months = pd.date_range('2021-01-01', '2022-12-31', freq='MS')
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_month, months))

# Combine results
final_df = pd.concat(results, ignore_index=True)
```

### Cloud Architecture
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: databento-options
spec:
  replicas: 3
  selector:
    matchLabels:
      app: databento-options
  template:
    metadata:
      labels:
        app: databento-options
    spec:
      containers:
      - name: puller
        image: databento-options:latest
        env:
        - name: DATABENTO_API_KEY
          valueFrom:
            secretKeyRef:
              name: databento-secret
              key: api-key
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Performance Benchmarks
- Single day processing: ~5 seconds
- One month processing: ~2 minutes
- One year processing: ~15 minutes
- Memory usage: ~500MB per month of data
- API calls: ~50 per month processed

## Maintenance and Updates

### Regular Maintenance Tasks
1. **Weekly**: Check log files for errors
2. **Monthly**: Clean up old cache files
3. **Quarterly**: Review and optimize configuration
4. **Annually**: Update dependencies and Python version

### Update Procedure
```bash
# 1. Test in staging environment
git checkout develop
pip install -r requirements.txt
python run_tests.py

# 2. Deploy to production
git checkout main
git merge develop
sudo systemctl stop databento-options
pip install -r requirements.txt
sudo systemctl start databento-options

# 3. Verify deployment
curl http://localhost:8080/health
tail -f /var/log/databento/options.log
```