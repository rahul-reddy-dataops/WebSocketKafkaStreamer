#!/usr/bin/env python3
"""
Database-Enhanced Real-Time Dashboard
Beautiful visualizations with PostgreSQL persistence
"""

import os
import json
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

# Create Flask app
app = Flask(__name__)
app.secret_key = "database-dashboard-secret-key"

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Data model
class DataRecord(Base):
    __tablename__ = "data_records"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    date = Column(String(20))
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    category = Column(String(100))
    region = Column(String(100))
    status = Column(String(50))
    priority = Column(String(20))
    conversion_rate = Column(Float)
    customer_satisfaction = Column(Float)
    units_sold = Column(Integer)
    page_views = Column(Integer)
    bounce_rate = Column(Float)
    customer_type = Column(String(50))
    acquisition_channel = Column(String(100))
    rating = Column(Float)
    inventory_level = Column(Integer)
    response_time = Column(Float)
    roi = Column(Float)
    data_source = Column(String(100), default='manual')
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def save_data_to_db(data_list, source='manual'):
    """Save data to PostgreSQL database"""
    db = SessionLocal()
    try:
        records_added = 0
        for item in data_list:
            # Create database record
            db_record = DataRecord(
                timestamp=datetime.fromisoformat(item.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00')) if item.get('timestamp') else datetime.now(),
                date=item.get('date', datetime.now().strftime('%Y-%m-%d')),
                revenue=float(item.get('revenue', 0)) if item.get('revenue') is not None else None,
                cost=float(item.get('cost', 0)) if item.get('cost') is not None else None,
                profit=float(item.get('profit', 0)) if item.get('profit') is not None else None,
                category=str(item.get('category', ''))[:100] if item.get('category') else None,
                region=str(item.get('region', ''))[:100] if item.get('region') else None,
                status=str(item.get('status', ''))[:50] if item.get('status') else None,
                priority=str(item.get('priority', ''))[:20] if item.get('priority') else None,
                conversion_rate=float(item.get('conversion_rate', 0)) if item.get('conversion_rate') is not None else None,
                customer_satisfaction=float(item.get('customer_satisfaction', 0)) if item.get('customer_satisfaction') is not None else None,
                units_sold=int(item.get('units_sold', 0)) if item.get('units_sold') is not None else None,
                page_views=int(item.get('page_views', 0)) if item.get('page_views') is not None else None,
                bounce_rate=float(item.get('bounce_rate', 0)) if item.get('bounce_rate') is not None else None,
                customer_type=str(item.get('customer_type', ''))[:50] if item.get('customer_type') else None,
                acquisition_channel=str(item.get('acquisition_channel', ''))[:100] if item.get('acquisition_channel') else None,
                rating=float(item.get('rating', 0)) if item.get('rating') is not None else None,
                inventory_level=int(item.get('inventory_level', 0)) if item.get('inventory_level') is not None else None,
                response_time=float(item.get('response_time', 0)) if item.get('response_time') is not None else None,
                roi=float(item.get('roi', 0)) if item.get('roi') is not None else None,
                data_source=source
            )
            
            db.add(db_record)
            records_added += 1
        
        db.commit()
        return records_added
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
        raise
    finally:
        db.close()

def get_data_from_db(limit=1000):
    """Retrieve data from PostgreSQL database"""
    db = SessionLocal()
    try:
        records = db.query(DataRecord).order_by(DataRecord.created_at.desc()).limit(limit).all()
        
        data_list = []
        for record in records:
            data_dict = {
                'id': record.id,
                'timestamp': record.timestamp.isoformat() if record.timestamp else None,
                'date': record.date,
                'revenue': record.revenue,
                'cost': record.cost,
                'profit': record.profit,
                'category': record.category,
                'region': record.region,
                'status': record.status,
                'priority': record.priority,
                'conversion_rate': record.conversion_rate,
                'customer_satisfaction': record.customer_satisfaction,
                'units_sold': record.units_sold,
                'page_views': record.page_views,
                'bounce_rate': record.bounce_rate,
                'customer_type': record.customer_type,
                'acquisition_channel': record.acquisition_channel,
                'rating': record.rating,
                'inventory_level': record.inventory_level,
                'response_time': record.response_time,
                'roi': record.roi,
                'data_source': record.data_source
            }
            data_list.append(data_dict)
        
        return data_list
    except Exception as e:
        print(f"Error retrieving from database: {e}")
        return []
    finally:
        db.close()

def get_db_analytics():
    """Get analytics from database"""
    db = SessionLocal()
    try:
        total_records = db.query(DataRecord).count()
        
        # Revenue analytics
        revenue_stats = db.query(
            func.sum(DataRecord.revenue).label('total_revenue'),
            func.avg(DataRecord.revenue).label('avg_revenue'),
            func.max(DataRecord.revenue).label('max_revenue')
        ).first()
        
        # Category breakdown
        category_stats = db.query(
            DataRecord.category,
            func.count(DataRecord.id).label('count'),
            func.sum(DataRecord.revenue).label('total_revenue')
        ).group_by(DataRecord.category).all()
        
        # Recent activity
        recent_uploads = db.query(DataRecord.data_source, func.count(DataRecord.id).label('count')).group_by(DataRecord.data_source).all()
        
        return {
            'total_records': total_records,
            'revenue_stats': {
                'total': float(revenue_stats.total_revenue or 0),
                'average': float(revenue_stats.avg_revenue or 0),
                'maximum': float(revenue_stats.max_revenue or 0)
            },
            'category_breakdown': [{'category': cat.category, 'count': cat.count, 'revenue': float(cat.total_revenue or 0)} for cat in category_stats],
            'data_sources': [{'source': src.data_source, 'count': src.count} for src in recent_uploads]
        }
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return {'total_records': 0, 'revenue_stats': {'total': 0, 'average': 0, 'maximum': 0}, 'category_breakdown': [], 'data_sources': []}
    finally:
        db.close()

def create_enhanced_sample_data():
    """Generate rich sample data"""
    np.random.seed(42)
    
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Automotive', 'Health', 'Beauty']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    statuses = ['Active', 'Pending', 'Completed', 'Cancelled']
    priorities = ['High', 'Medium', 'Low']
    
    base_date = datetime.now() - timedelta(days=30)
    
    data = []
    for i in range(200):
        date = base_date + timedelta(days=np.random.randint(0, 30), 
                                   hours=np.random.randint(0, 24),
                                   minutes=np.random.randint(0, 60))
        
        revenue = round(np.random.lognormal(6, 0.5), 2)
        cost = round(np.random.lognormal(5, 0.4), 2)
        
        record = {
            'timestamp': date.isoformat(),
            'date': date.strftime('%Y-%m-%d'),
            'revenue': revenue,
            'cost': cost,
            'profit': round(revenue - cost, 2),
            'conversion_rate': round(np.random.uniform(1, 15), 2),
            'customer_satisfaction': round(np.random.uniform(3.0, 5.0), 1),
            'response_time': round(np.random.exponential(200), 0),
            'units_sold': np.random.randint(1, 100),
            'page_views': np.random.randint(100, 10000),
            'bounce_rate': round(np.random.uniform(20, 80), 1),
            'category': np.random.choice(categories),
            'region': np.random.choice(regions),
            'status': np.random.choice(statuses),
            'priority': np.random.choice(priorities),
            'customer_type': np.random.choice(['New', 'Returning', 'VIP']),
            'acquisition_channel': np.random.choice(['Organic', 'Paid Search', 'Social Media', 'Email', 'Direct']),
            'rating': round(np.random.uniform(1, 5), 1),
            'inventory_level': np.random.randint(0, 1000),
            'roi': round(((revenue - cost) / cost) * 100, 1) if cost > 0 else 0
        }
        
        data.append(record)
    
    return data

def process_file(filepath):
    """Process uploaded JSON or CSV file"""
    try:
        file_ext = os.path.splitext(filepath)[1].lower()
        
        if file_ext == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                return [data]
        
        elif file_ext == '.csv':
            df = pd.read_csv(filepath)
            return df.to_dict('records')
        
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
            
    except Exception as e:
        print(f"Error processing file: {e}")
        raise

@app.route('/')
def index():
    """Database-enhanced dashboard"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database-Enhanced Real-Time Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --info-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --dark-bg: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
        }
        
        body {
            background: var(--dark-bg);
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .dashboard-header {
            background: var(--primary-gradient);
            padding: 2rem 0;
            margin-bottom: 2rem;
            border-radius: 0 0 1rem 1rem;
        }
        
        .database-badge {
            background: var(--success-gradient);
            padding: 0.5rem 1rem;
            border-radius: 2rem;
            font-size: 0.8rem;
            display: inline-block;
            margin-left: 1rem;
        }
        
        .kpi-card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
        }
        
        .kpi-value {
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .kpi-label {
            color: #8b949e;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .kpi-icon {
            font-size: 2rem;
            opacity: 0.8;
            float: right;
            margin-top: -0.5rem;
        }
        
        .chart-container {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            height: 400px;
        }
        
        .btn-gradient {
            background: var(--primary-gradient);
            border: none;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        
        .btn-gradient:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
            color: white;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 0.5rem;
            animation: pulse 2s infinite;
        }
        
        .status-connected { background: #28a745; }
        .status-loading { background: #ffc107; }
        .status-error { background: #dc3545; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .data-table-container {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            overflow: hidden;
        }
        
        .table-dark {
            background: transparent;
        }
        
        .table-dark td, .table-dark th {
            border-color: var(--border-color);
        }
        
        .metric-trend {
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }
        
        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-neutral { color: #6c757d; }
        
        .upload-zone {
            border: 2px dashed var(--border-color);
            border-radius: 1rem;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            background: var(--card-bg);
        }
        
        .upload-zone:hover {
            border-color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
        
        .db-stats {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1rem;
            margin-bottom: 1rem;
        }
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <div class="row">
                <div class="col-12 text-center">
                    <h1 class="display-4 mb-3">
                        <i class="fas fa-database me-3"></i>
                        Database-Enhanced Dashboard
                        <span class="database-badge">
                            <i class="fas fa-server me-1"></i>PostgreSQL Powered
                        </span>
                    </h1>
                    <p class="lead mb-0">Persistent Data Storage with Real-Time Analytics</p>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Database Stats -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="db-stats">
                    <div class="row">
                        <div class="col-md-3 text-center">
                            <i class="fas fa-database fa-2x text-primary mb-2"></i>
                            <h6>Database Records</h6>
                            <h4 id="db-total-records">Loading...</h4>
                        </div>
                        <div class="col-md-3 text-center">
                            <i class="fas fa-chart-line fa-2x text-success mb-2"></i>
                            <h6>Total Revenue</h6>
                            <h4 id="db-total-revenue">Loading...</h4>
                        </div>
                        <div class="col-md-3 text-center">
                            <i class="fas fa-tags fa-2x text-info mb-2"></i>
                            <h6>Categories</h6>
                            <h4 id="db-categories">Loading...</h4>
                        </div>
                        <div class="col-md-3 text-center">
                            <i class="fas fa-clock fa-2x text-warning mb-2"></i>
                            <h6>Last Updated</h6>
                            <h4 id="last-updated">Just now</h4>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="row mb-4">
            <div class="col-12 text-center">
                <button onclick="loadSample()" class="btn btn-gradient btn-lg me-3">
                    <i class="fas fa-play me-2"></i>Load Sample Data
                </button>
                <button onclick="showUpload()" class="btn btn-gradient btn-lg me-3">
                    <i class="fas fa-upload me-2"></i>Upload Data
                </button>
                <button onclick="refreshData()" class="btn btn-gradient btn-lg me-3">
                    <i class="fas fa-sync me-2"></i>Refresh
                </button>
                <button onclick="clearDatabase()" class="btn btn-outline-danger btn-lg">
                    <i class="fas fa-trash me-2"></i>Clear Database
                </button>
            </div>
        </div>

        <!-- Status Bar -->
        <div class="row mb-4">
            <div class="col-12">
                <div id="status" class="alert alert-info text-center">
                    <span class="status-indicator status-connected"></span>
                    Connected to PostgreSQL database - Ready to store data persistently
                </div>
            </div>
        </div>

        <!-- KPI Cards (same as before) -->
        <div class="row" id="kpi-section">
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-database kpi-icon text-primary"></i>
                    <div class="kpi-label">Active Records</div>
                    <div class="kpi-value" id="total-records">0</div>
                    <div class="metric-trend trend-up">
                        <i class="fas fa-arrow-up"></i> Stored in PostgreSQL
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-dollar-sign kpi-icon text-success"></i>
                    <div class="kpi-label">Total Revenue</div>
                    <div class="kpi-value" id="total-revenue">$0</div>
                    <div class="metric-trend trend-up">
                        <i class="fas fa-arrow-up"></i> Persistent storage
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-percentage kpi-icon text-warning"></i>
                    <div class="kpi-label">Avg Conversion</div>
                    <div class="kpi-value" id="conversion-rate">0%</div>
                    <div class="metric-trend trend-up">
                        <i class="fas fa-arrow-up"></i> Real-time calc
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-star kpi-icon text-info"></i>
                    <div class="kpi-label">Satisfaction</div>
                    <div class="kpi-value" id="satisfaction">0.0</div>
                    <div class="metric-trend trend-up">
                        <i class="fas fa-arrow-up"></i> DB aggregated
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Section (same structure as before) -->
        <div class="row" id="charts-section">
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-line me-2"></i>Revenue Trend (from DB)</h5>
                    <canvas id="revenueChart"></canvas>
                </div>
            </div>
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-pie me-2"></i>Category Distribution</h5>
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="row" id="upload-section" style="display: none;">
            <div class="col-md-8 mx-auto">
                <div class="upload-zone" id="uploadZone">
                    <i class="fas fa-cloud-upload-alt fa-3x mb-3 text-muted"></i>
                    <h5>Upload to PostgreSQL Database</h5>
                    <p class="text-muted">Drag & drop files to store permanently in database</p>
                    <input type="file" id="fileInput" accept=".json,.csv" style="display: none;">
                    <button onclick="document.getElementById('fileInput').click()" class="btn btn-gradient mt-2">
                        <i class="fas fa-folder-open me-2"></i>Choose File
                    </button>
                    <button onclick="hideUpload()" class="btn btn-secondary mt-2 ms-2">Cancel</button>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="row mt-4" id="data-section">
            <div class="col-12">
                <div class="data-table-container">
                    <div class="p-3 border-bottom">
                        <h5 class="mb-0">
                            <i class="fas fa-table me-2"></i>Recent Database Records
                            <small class="text-muted ms-2">(Last 10 from PostgreSQL)</small>
                        </h5>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-dark table-hover mb-0" id="dataTable">
                            <thead><tr><th>Loading from database...</th></tr></thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let charts = {};
        
        function loadSample() {
            updateStatus('loading', 'Generating and saving sample data to database...', 'loading');
            
            fetch('/api/sample')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('success', `${data.message} - ${data.records} records saved to PostgreSQL`, 'connected');
                        refreshData();
                        loadDatabaseStats();
                    } else {
                        updateStatus('danger', 'Error: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    updateStatus('danger', 'Network error: ' + error, 'error');
                });
        }

        function refreshData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data.data);
                    updateLastUpdated();
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                });
        }

        function loadDatabaseStats() {
            fetch('/api/analytics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('db-total-records').textContent = data.total_records.toLocaleString();
                    document.getElementById('db-total-revenue').textContent = '$' + data.revenue_stats.total.toLocaleString();
                    document.getElementById('db-categories').textContent = data.category_breakdown.length;
                })
                .catch(error => {
                    console.error('Error loading database stats:', error);
                });
        }

        function clearDatabase() {
            if (confirm('Are you sure you want to clear all data from the database? This action cannot be undone.')) {
                fetch('/api/clear', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            updateStatus('success', 'Database cleared successfully', 'connected');
                            refreshData();
                            loadDatabaseStats();
                        }
                    })
                    .catch(error => {
                        updateStatus('danger', 'Error clearing database: ' + error, 'error');
                    });
            }
        }

        function updateDashboard(data) {
            if (data && data.length > 0) {
                updateKPIs(data);
                updateCharts(data);
                updateTable(data);
            }
        }

        function updateKPIs(data) {
            document.getElementById('total-records').textContent = data.length.toLocaleString();
            
            const revenues = data.map(d => d.revenue || 0).filter(r => !isNaN(r));
            const totalRevenue = revenues.reduce((a, b) => a + b, 0);
            document.getElementById('total-revenue').textContent = '$' + totalRevenue.toLocaleString();
            
            const conversions = data.map(d => d.conversion_rate || 0).filter(c => !isNaN(c));
            const avgConversion = conversions.length > 0 ? 
                (conversions.reduce((a, b) => a + b, 0) / conversions.length) : 0;
            document.getElementById('conversion-rate').textContent = avgConversion.toFixed(1) + '%';
            
            const satisfactions = data.map(d => d.customer_satisfaction || 0).filter(s => !isNaN(s));
            const avgSatisfaction = satisfactions.length > 0 ? 
                (satisfactions.reduce((a, b) => a + b, 0) / satisfactions.length) : 0;
            document.getElementById('satisfaction').textContent = avgSatisfaction.toFixed(1);
        }

        function updateCharts(data) {
            createRevenueChart(data);
            createCategoryChart(data);
        }

        function createRevenueChart(data) {
            const ctx = document.getElementById('revenueChart').getContext('2d');
            
            const dateGroups = {};
            data.forEach(item => {
                const date = item.date || new Date().toISOString().split('T')[0];
                if (!dateGroups[date]) dateGroups[date] = [];
                dateGroups[date].push(item.revenue || 0);
            });
            
            const chartData = Object.keys(dateGroups).sort().map(date => ({
                x: date,
                y: dateGroups[date].reduce((a, b) => a + b, 0)
            }));
            
            if (charts.revenue) charts.revenue.destroy();
            
            charts.revenue = new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Daily Revenue (from PostgreSQL)',
                        data: chartData,
                        borderColor: 'rgb(102, 126, 234)',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    },
                    scales: {
                        x: { 
                            type: 'time',
                            time: { unit: 'day' },
                            ticks: { color: '#8b949e' },
                            grid: { color: '#30363d' }
                        },
                        y: { 
                            ticks: { color: '#8b949e' },
                            grid: { color: '#30363d' }
                        }
                    }
                }
            });
        }

        function createCategoryChart(data) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            
            const categories = {};
            data.forEach(item => {
                const cat = item.category || 'Other';
                categories[cat] = (categories[cat] || 0) + (item.revenue || 0);
            });
            
            if (charts.category) charts.category.destroy();
            
            charts.category = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(categories),
                    datasets: [{
                        label: 'Revenue by Category',
                        data: Object.values(categories),
                        backgroundColor: [
                            '#667eea', '#764ba2', '#f093fb', '#f5576c',
                            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            labels: { color: '#fff' },
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        function updateTable(data) {
            const table = document.getElementById('dataTable');
            if (data.length === 0) {
                const thead = table.querySelector('thead tr');
                thead.innerHTML = '<th>No data in database</th>';
                const tbody = table.querySelector('tbody');
                tbody.innerHTML = '<tr><td>Upload some data to get started</td></tr>';
                return;
            }
            
            const recentData = data.slice(0, 10);
            const keys = ['id', 'date', 'revenue', 'category', 'region', 'status', 'data_source'];
            
            const thead = table.querySelector('thead tr');
            thead.innerHTML = keys.map(key => `<th>${key.replace('_', ' ').toUpperCase()}</th>`).join('');
            
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = recentData.map(row => 
                '<tr>' + keys.map(key => {
                    let value = row[key] || '';
                    if (key === 'revenue' && value) value = '$' + parseFloat(value).toFixed(2);
                    return `<td>${String(value).substring(0, 20)}</td>`;
                }).join('') + '</tr>'
            ).join('');
        }

        function updateLastUpdated() {
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
        }

        function showUpload() {
            document.getElementById('upload-section').style.display = 'block';
        }

        function hideUpload() {
            document.getElementById('upload-section').style.display = 'none';
        }

        function updateStatus(type, message, indicator) {
            const status = document.getElementById('status');
            const statusClasses = {
                'success': 'alert-success',
                'danger': 'alert-danger',
                'loading': 'alert-warning',
                'info': 'alert-info'
            };
            
            const indicatorClasses = {
                'connected': 'status-connected',
                'loading': 'status-loading',
                'error': 'status-error'
            };
            
            status.className = `alert ${statusClasses[type]} text-center`;
            status.innerHTML = `<span class="status-indicator ${indicatorClasses[indicator]}"></span>${message}`;
        }

        // File upload handling
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                
                updateStatus('loading', 'Uploading file to database...', 'loading');

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('success', data.message + ' - Data saved to PostgreSQL', 'connected');
                        hideUpload();
                        refreshData();
                        loadDatabaseStats();
                    } else {
                        updateStatus('danger', 'Upload failed: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    updateStatus('danger', 'Upload error: ' + error, 'error');
                });
            }
        });

        // Initialize dashboard
        window.addEventListener('load', function() {
            refreshData();
            loadDatabaseStats();
        });

        // Auto-refresh every 30 seconds
        setInterval(() => {
            refreshData();
            loadDatabaseStats();
        }, 30000);
    </script>
</body>
</html>
    '''

@app.route('/api/sample')
def load_sample():
    """Load sample data and save to database"""
    try:
        sample_data = create_enhanced_sample_data()
        records_saved = save_data_to_db(sample_data, source='sample_generation')
        
        return jsonify({
            'success': True,
            'message': 'Sample data generated and saved to database',
            'records': records_saved
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data')
def get_data():
    """Get data from database"""
    try:
        data = get_data_from_db()
        return jsonify({
            'data': data,
            'total_records': len(data),
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get database analytics"""
    try:
        analytics = get_db_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def clear_database():
    """Clear all data from database"""
    try:
        db = SessionLocal()
        db.query(DataRecord).delete()
        db.commit()
        db.close()
        
        return jsonify({'success': True, 'message': 'Database cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and save to database"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(str(file.filename))
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Process the file
            data = process_file(filepath)
            records_saved = save_data_to_db(data, source=f'file_upload_{filename}')
            
            # Clean up uploaded file
            os.remove(filepath)
            
            return jsonify({
                'success': True,
                'message': f'File {filename} uploaded and {records_saved} records saved to database',
                'records': records_saved
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def simulate_real_time_data():
    """Background thread to simulate real-time data and save to database"""
    time.sleep(15)  # Wait for server to start
    
    counter = 0
    while True:
        try:
            # Generate new realistic data point
            revenue = round(np.random.lognormal(6, 0.5), 2)
            cost = round(np.random.lognormal(5, 0.4), 2)
            
            new_record = {
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'revenue': revenue,
                'cost': cost,
                'profit': round(revenue - cost, 2),
                'category': np.random.choice(['Electronics', 'Clothing', 'Books']),
                'region': np.random.choice(['North America', 'Europe', 'Asia Pacific']),
                'status': np.random.choice(['Active', 'Pending', 'Completed']),
                'conversion_rate': round(np.random.uniform(1, 15), 2),
                'customer_satisfaction': round(np.random.uniform(3.0, 5.0), 1),
                'units_sold': np.random.randint(1, 50),
                'priority': np.random.choice(['High', 'Medium', 'Low']),
                'roi': round(((revenue - cost) / cost) * 100, 1) if cost > 0 else 0
            }
            
            # Save to database
            save_data_to_db([new_record], source='real_time_simulation')
            counter += 1
            time.sleep(30)  # Add new data every 30 seconds
            
        except Exception as e:
            print(f"Real-time simulation error: {e}")
            time.sleep(120)

if __name__ == '__main__':
    print("🚀 Starting Database-Enhanced Real-Time Dashboard")
    print("🗄️ PostgreSQL Database Integration")
    print("📊 Persistent Data Storage & Analytics")
    print("🌐 Access at: http://localhost:5000")
    print("✨ Features: Database persistence, real-time analytics, data management")
    print("-" * 70)
    
    # Start background real-time simulation
    simulation_thread = threading.Thread(target=simulate_real_time_data, daemon=True)
    simulation_thread.start()
    
    # Run the database-enhanced app
    app.run(host='0.0.0.0', port=5000, debug=False)