#!/usr/bin/env python3
"""
Enhanced Generic Real-Time Data Dashboard
Beautiful visualizations with interactive charts and animated KPIs
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

# Create Flask app
app = Flask(__name__)
app.secret_key = "enhanced-dashboard-secret-key"

# Global data storage
current_data = []
data_lock = threading.Lock()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'csv'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_enhanced_sample_data():
    """Generate rich sample data with multiple metrics for enhanced visualizations"""
    np.random.seed(42)
    
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Automotive', 'Health', 'Beauty']
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America']
    statuses = ['Active', 'Pending', 'Completed', 'Cancelled']
    priorities = ['High', 'Medium', 'Low']
    
    # Generate data for the last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    data = []
    for i in range(200):  # More data points for better charts
        date = base_date + timedelta(days=np.random.randint(0, 30), 
                                   hours=np.random.randint(0, 24),
                                   minutes=np.random.randint(0, 60))
        
        record = {
            'id': i + 1,
            'timestamp': date.isoformat(),
            'date': date.strftime('%Y-%m-%d'),
            'month': date.strftime('%B'),
            'day_of_week': date.strftime('%A'),
            'hour': date.hour,
            
            # Financial metrics
            'revenue': round(np.random.lognormal(6, 0.5), 2),
            'cost': round(np.random.lognormal(5, 0.4), 2),
            'profit_margin': round(np.random.uniform(10, 40), 1),
            
            # Performance metrics
            'conversion_rate': round(np.random.uniform(1, 15), 2),
            'customer_satisfaction': round(np.random.uniform(3.0, 5.0), 1),
            'response_time': round(np.random.exponential(200), 0),
            
            # Business metrics
            'units_sold': np.random.randint(1, 100),
            'page_views': np.random.randint(100, 10000),
            'bounce_rate': round(np.random.uniform(20, 80), 1),
            
            # Categorical data
            'category': np.random.choice(categories),
            'region': np.random.choice(regions),
            'status': np.random.choice(statuses),
            'priority': np.random.choice(priorities),
            
            # Customer data
            'customer_type': np.random.choice(['New', 'Returning', 'VIP']),
            'acquisition_channel': np.random.choice(['Organic', 'Paid Search', 'Social Media', 'Email', 'Direct']),
            
            # Additional metrics
            'rating': round(np.random.uniform(1, 5), 1),
            'inventory_level': np.random.randint(0, 1000),
            'temperature': round(np.random.normal(22, 5), 1),  # For IoT-style data
        }
        
        # Calculate derived metrics
        record['profit'] = round(record['revenue'] - record['cost'], 2)
        record['roi'] = round((record['profit'] / record['cost']) * 100, 1) if record['cost'] > 0 else 0
        
        data.append(record)
    
    return data

def add_data_to_stream(new_data):
    """Add data to global stream"""
    global current_data
    with data_lock:
        if isinstance(new_data, list):
            current_data.extend(new_data)
        else:
            current_data.append(new_data)
        
        # Keep only last 1000 records
        if len(current_data) > 1000:
            current_data = current_data[-1000:]

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
    """Enhanced dashboard with beautiful charts and animations"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Real-Time Data Dashboard</title>
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
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #ffffff;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
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
    </style>
</head>
<body>
    <div class="dashboard-header">
        <div class="container">
            <div class="row">
                <div class="col-12 text-center">
                    <h1 class="display-4 mb-3">
                        <i class="fas fa-chart-line me-3"></i>
                        Enhanced Real-Time Dashboard
                    </h1>
                    <p class="lead mb-0">Interactive Data Visualization with Live Charts & KPIs</p>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- Control Panel -->
        <div class="row mb-4">
            <div class="col-12 text-center">
                <button onclick="loadSample()" class="btn btn-gradient btn-lg me-3">
                    <i class="fas fa-play me-2"></i>Load Sample Data
                </button>
                <button onclick="showUpload()" class="btn btn-gradient btn-lg me-3">
                    <i class="fas fa-upload me-2"></i>Upload Data
                </button>
                <button onclick="refreshData()" class="btn btn-gradient btn-lg">
                    <i class="fas fa-sync me-2"></i>Refresh
                </button>
            </div>
        </div>

        <!-- Status Bar -->
        <div class="row mb-4">
            <div class="col-12">
                <div id="status" class="alert alert-info text-center">
                    <span class="status-indicator status-loading"></span>
                    Ready to receive data - Click "Load Sample Data" to start
                </div>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="row" id="kpi-section" style="display: none;">
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-database kpi-icon text-primary"></i>
                    <div class="kpi-label">Total Records</div>
                    <div class="kpi-value" id="total-records">0</div>
                    <div class="metric-trend trend-up" id="records-trend">
                        <i class="fas fa-arrow-up"></i> +12% from last period
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-dollar-sign kpi-icon text-success"></i>
                    <div class="kpi-label">Total Revenue</div>
                    <div class="kpi-value" id="total-revenue">$0</div>
                    <div class="metric-trend trend-up" id="revenue-trend">
                        <i class="fas fa-arrow-up"></i> +8.3% from last month
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-percentage kpi-icon text-warning"></i>
                    <div class="kpi-label">Avg Conversion Rate</div>
                    <div class="kpi-value" id="conversion-rate">0%</div>
                    <div class="metric-trend trend-up" id="conversion-trend">
                        <i class="fas fa-arrow-up"></i> +2.1% improvement
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6">
                <div class="kpi-card">
                    <i class="fas fa-star kpi-icon text-info"></i>
                    <div class="kpi-label">Avg Satisfaction</div>
                    <div class="kpi-value" id="satisfaction">0.0</div>
                    <div class="metric-trend trend-up" id="satisfaction-trend">
                        <i class="fas fa-arrow-up"></i> +0.3 rating increase
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Section -->
        <div class="row" id="charts-section" style="display: none;">
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-line me-2"></i>Revenue Trend</h5>
                    <canvas id="revenueChart"></canvas>
                </div>
            </div>
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-pie me-2"></i>Sales by Category</h5>
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-bar me-2"></i>Regional Performance</h5>
                    <canvas id="regionChart"></canvas>
                </div>
            </div>
            <div class="col-lg-6 col-md-12">
                <div class="chart-container">
                    <h5 class="mb-3"><i class="fas fa-chart-area me-2"></i>Conversion Funnel</h5>
                    <canvas id="funnelChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Upload Section -->
        <div class="row" id="upload-section" style="display: none;">
            <div class="col-md-8 mx-auto">
                <div class="upload-zone" id="uploadZone">
                    <i class="fas fa-cloud-upload-alt fa-3x mb-3 text-muted"></i>
                    <h5>Drag & Drop your files here</h5>
                    <p class="text-muted">or click to browse (JSON, CSV files supported)</p>
                    <input type="file" id="fileInput" accept=".json,.csv" style="display: none;">
                    <button onclick="document.getElementById('fileInput').click()" class="btn btn-gradient mt-2">
                        <i class="fas fa-folder-open me-2"></i>Choose File
                    </button>
                    <button onclick="hideUpload()" class="btn btn-secondary mt-2 ms-2">Cancel</button>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="row mt-4" id="data-section" style="display: none;">
            <div class="col-12">
                <div class="data-table-container">
                    <div class="p-3 border-bottom">
                        <h5 class="mb-0"><i class="fas fa-table me-2"></i>Recent Data Records</h5>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-dark table-hover mb-0" id="dataTable">
                            <thead><tr><th>Loading...</th></tr></thead>
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
            updateStatus('loading', 'Loading sample data...', 'loading');
            
            fetch('/api/sample')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('success', `${data.message} - ${data.records} records loaded`, 'connected');
                        refreshData();
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
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                });
        }

        function updateDashboard(data) {
            if (data && data.length > 0) {
                document.getElementById('kpi-section').style.display = 'block';
                document.getElementById('charts-section').style.display = 'block';
                document.getElementById('data-section').style.display = 'block';
                
                updateKPIs(data);
                updateCharts(data);
                updateTable(data);
            }
        }

        function updateKPIs(data) {
            // Total Records
            document.getElementById('total-records').textContent = data.length.toLocaleString();
            
            // Total Revenue
            const revenues = data.map(d => d.revenue || 0).filter(r => !isNaN(r));
            const totalRevenue = revenues.reduce((a, b) => a + b, 0);
            document.getElementById('total-revenue').textContent = '$' + totalRevenue.toLocaleString();
            
            // Average Conversion Rate
            const conversions = data.map(d => d.conversion_rate || 0).filter(c => !isNaN(c));
            const avgConversion = conversions.length > 0 ? 
                (conversions.reduce((a, b) => a + b, 0) / conversions.length) : 0;
            document.getElementById('conversion-rate').textContent = avgConversion.toFixed(1) + '%';
            
            // Average Satisfaction
            const satisfactions = data.map(d => d.customer_satisfaction || 0).filter(s => !isNaN(s));
            const avgSatisfaction = satisfactions.length > 0 ? 
                (satisfactions.reduce((a, b) => a + b, 0) / satisfactions.length) : 0;
            document.getElementById('satisfaction').textContent = avgSatisfaction.toFixed(1);
        }

        function updateCharts(data) {
            // Revenue Trend Chart
            createRevenueChart(data);
            
            // Category Pie Chart
            createCategoryChart(data);
            
            // Regional Bar Chart
            createRegionChart(data);
            
            // Funnel Chart
            createFunnelChart(data);
        }

        function createRevenueChart(data) {
            const ctx = document.getElementById('revenueChart').getContext('2d');
            
            // Group by date
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
                        label: 'Daily Revenue',
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

        function createRegionChart(data) {
            const ctx = document.getElementById('regionChart').getContext('2d');
            
            const regions = {};
            data.forEach(item => {
                const region = item.region || 'Unknown';
                regions[region] = (regions[region] || 0) + (item.revenue || 0);
            });
            
            if (charts.region) charts.region.destroy();
            
            charts.region = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(regions),
                    datasets: [{
                        label: 'Revenue by Region',
                        data: Object.values(regions),
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgb(102, 126, 234)',
                        borderWidth: 1
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

        function createFunnelChart(data) {
            const ctx = document.getElementById('funnelChart').getContext('2d');
            
            const statuses = {};
            data.forEach(item => {
                const status = item.status || 'Unknown';
                statuses[status] = (statuses[status] || 0) + 1;
            });
            
            if (charts.funnel) charts.funnel.destroy();
            
            charts.funnel = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(statuses),
                    datasets: [{
                        label: 'Records by Status',
                        data: Object.values(statuses),
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(220, 53, 69, 0.8)',
                            'rgba(23, 162, 184, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { labels: { color: '#fff' } }
                    },
                    scales: {
                        x: { 
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

        function updateTable(data) {
            const table = document.getElementById('dataTable');
            if (data.length === 0) return;
            
            const recentData = data.slice(-10);
            const keys = ['id', 'timestamp', 'revenue', 'category', 'region', 'status', 'conversion_rate'];
            
            const thead = table.querySelector('thead tr');
            thead.innerHTML = keys.map(key => `<th>${key.replace('_', ' ').toUpperCase()}</th>`).join('');
            
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = recentData.map(row => 
                '<tr>' + keys.map(key => {
                    let value = row[key] || '';
                    if (key === 'revenue' && value) value = '$' + parseFloat(value).toFixed(2);
                    if (key === 'conversion_rate' && value) value = parseFloat(value).toFixed(1) + '%';
                    if (key === 'timestamp' && value) value = new Date(value).toLocaleDateString();
                    return `<td>${String(value).substring(0, 20)}</td>`;
                }).join('') + '</tr>'
            ).join('');
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
                
                updateStatus('loading', 'Uploading file...', 'loading');

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('success', data.message, 'connected');
                        hideUpload();
                        refreshData();
                    } else {
                        updateStatus('danger', 'Upload failed: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    updateStatus('danger', 'Upload error: ' + error, 'error');
                });
            }
        });

        // Drag and drop functionality
        const uploadZone = document.getElementById('uploadZone');
        
        uploadZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#667eea';
            uploadZone.style.background = 'rgba(102, 126, 234, 0.1)';
        });
        
        uploadZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#30363d';
            uploadZone.style.background = '#161b22';
        });
        
        uploadZone.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadZone.style.borderColor = '#30363d';
            uploadZone.style.background = '#161b22';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
                document.getElementById('fileInput').dispatchEvent(new Event('change'));
            }
        });

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
    '''

@app.route('/api/sample')
def load_sample():
    """Load enhanced sample data"""
    try:
        sample_data = create_enhanced_sample_data()
        add_data_to_stream(sample_data)
        return jsonify({
            'success': True,
            'message': 'Enhanced sample data loaded successfully',
            'records': len(sample_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data')
def get_data():
    """Get current data"""
    with data_lock:
        return jsonify({
            'data': current_data,
            'total_records': len(current_data),
            'timestamp': time.time()
        })

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
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
            add_data_to_stream(data)
            
            return jsonify({
                'success': True,
                'message': f'File {filename} uploaded successfully',
                'records': len(data)
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def simulate_real_time_data():
    """Background thread to simulate real-time data updates"""
    time.sleep(10)  # Wait for server to start
    
    counter = 0
    while True:
        try:
            # Generate new realistic data point
            new_record = {
                'id': 10000 + counter,
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'revenue': round(np.random.lognormal(6, 0.5), 2),
                'cost': round(np.random.lognormal(5, 0.4), 2),
                'category': np.random.choice(['Electronics', 'Clothing', 'Books']),
                'region': np.random.choice(['North America', 'Europe', 'Asia Pacific']),
                'status': np.random.choice(['Active', 'Pending', 'Completed']),
                'conversion_rate': round(np.random.uniform(1, 15), 2),
                'customer_satisfaction': round(np.random.uniform(3.0, 5.0), 1),
                'units_sold': np.random.randint(1, 50),
                'priority': np.random.choice(['High', 'Medium', 'Low']),
            }
            
            # Calculate derived metrics
            new_record['profit'] = round(new_record['revenue'] - new_record['cost'], 2)
            
            add_data_to_stream([new_record])
            counter += 1
            time.sleep(15)  # Add new data every 15 seconds
            
        except Exception as e:
            print(f"Real-time simulation error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    print("🚀 Starting Enhanced Real-Time Data Dashboard")
    print("📊 Beautiful Charts, Animated KPIs & Interactive Visualizations")
    print("🌐 Access at: http://localhost:5000")
    print("✨ Features: Revenue trends, Category analysis, Regional performance")
    print("-" * 60)
    
    # Start background real-time simulation
    simulation_thread = threading.Thread(target=simulate_real_time_data, daemon=True)
    simulation_thread.start()
    
    # Run the enhanced app
    app.run(host='0.0.0.0', port=5000, debug=False)