#!/usr/bin/env python3
"""
Simple Generic Real-Time Data Dashboard
Based on your Kafka WebSocket Server and Dash Client examples
"""

import os
import json
import time
import threading
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Create Flask app
app = Flask(__name__)
app.secret_key = "generic-dashboard-secret-key"

# Global data storage
current_data = []
data_lock = threading.Lock()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'json', 'csv'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('templates', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_sample_data():
    """Generate sample data similar to your examples"""
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Automotive']
    regions = ['North', 'South', 'East', 'West']
    statuses = ['active', 'inactive', 'pending']
    
    data = []
    for i in range(50):
        record = {
            'id': i + 1,
            'timestamp': datetime.now().isoformat(),
            'value': round(np.random.normal(100, 25), 2),
            'category': np.random.choice(categories),
            'region': np.random.choice(regions),
            'status': np.random.choice(statuses),
            'score': round(np.random.uniform(0, 100), 1),
            'amount': round(np.random.exponential(200), 2),
            'KPI': np.random.choice(['TUMBLE_COUNT_DISTINCT_CLAIMANT', 'HIGH_RISK_CLAIM_COUNT', 'SUM_TOTAL_CLM_AMT_PAID']),
            'window_start': datetime.now().isoformat()
        }
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
    """Main dashboard page"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generic Real-Time Data Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #1a1a1a; color: #fff; }
        .card { background: #2d2d2d; border: 1px solid #444; }
        .btn-primary { background: #0d6efd; border-color: #0d6efd; }
        .alert-info { background: #0f4c75; border-color: #3282b8; color: #fff; }
        .kpi-card { transition: transform 0.2s; }
        .kpi-card:hover { transform: translateY(-5px); }
    </style>
</head>
<body>
    <div class="container py-4">
        <!-- Header -->
        <div class="row mb-4">
            <div class="col-12 text-center">
                <h1 class="display-4 mb-3">
                    <i class="fas fa-chart-line me-3 text-primary"></i>
                    Generic Real-Time Data Dashboard
                </h1>
                <p class="lead">Based on Kafka WebSocket Server + Dash Client Architecture</p>
            </div>
        </div>

        <!-- Action Buttons -->
        <div class="row mb-4">
            <div class="col-12 text-center">
                <div class="btn-group" role="group">
                    <button onclick="loadSample()" class="btn btn-success btn-lg">
                        <i class="fas fa-play me-2"></i>Load Sample Data
                    </button>
                    <button onclick="showUpload()" class="btn btn-primary btn-lg">
                        <i class="fas fa-upload me-2"></i>Upload Data
                    </button>
                    <button onclick="refreshData()" class="btn btn-info btn-lg">
                        <i class="fas fa-sync me-2"></i>Refresh
                    </button>
                </div>
            </div>
        </div>

        <!-- Status -->
        <div class="row mb-4">
            <div class="col-12">
                <div id="status" class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>
                    Ready to receive data - Click "Load Sample Data" to start
                </div>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="row mb-4" id="kpi-section" style="display: none;">
            <div class="col-md-3 mb-3">
                <div class="card kpi-card text-center">
                    <div class="card-body">
                        <i class="fas fa-database fa-2x text-primary mb-2"></i>
                        <h5>Total Records</h5>
                        <h2 id="total-records" class="text-success">0</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card kpi-card text-center">
                    <div class="card-body">
                        <i class="fas fa-chart-bar fa-2x text-info mb-2"></i>
                        <h5>Avg Value</h5>
                        <h2 id="avg-value" class="text-info">0</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card kpi-card text-center">
                    <div class="card-body">
                        <i class="fas fa-arrow-up fa-2x text-warning mb-2"></i>
                        <h5>Max Amount</h5>
                        <h2 id="max-amount" class="text-warning">0</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card kpi-card text-center">
                    <div class="card-body">
                        <i class="fas fa-tags fa-2x text-danger mb-2"></i>
                        <h5>Categories</h5>
                        <h2 id="categories" class="text-danger">0</h2>
                    </div>
                </div>
            </div>
        </div>

        <!-- Upload Form -->
        <div class="row mb-4" id="upload-section" style="display: none;">
            <div class="col-md-8 mx-auto">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-upload me-2"></i>Upload Your Data</h5>
                    </div>
                    <div class="card-body">
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <input type="file" class="form-control" id="fileInput" accept=".json,.csv" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-upload me-2"></i>Upload
                            </button>
                            <button type="button" onclick="hideUpload()" class="btn btn-secondary ms-2">Cancel</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- Data Table -->
        <div class="row" id="data-section" style="display: none;">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-table me-2"></i>Data Preview (Last 10 Records)</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-dark table-striped" id="dataTable">
                                <thead><tr><th>Loading...</th></tr></thead>
                                <tbody></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function loadSample() {
            fetch('/api/sample')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('success', data.message + ' - ' + data.records + ' records loaded');
                        refreshData();
                    } else {
                        updateStatus('danger', 'Error: ' + data.error);
                    }
                })
                .catch(error => {
                    updateStatus('danger', 'Network error: ' + error);
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
                document.getElementById('data-section').style.display = 'block';
                
                // Update KPIs
                document.getElementById('total-records').textContent = data.length;
                
                const values = data.map(d => d.value || 0).filter(v => !isNaN(v));
                const amounts = data.map(d => d.amount || 0).filter(a => !isNaN(a));
                const categories = [...new Set(data.map(d => d.category).filter(c => c))];
                
                document.getElementById('avg-value').textContent = values.length > 0 ? 
                    (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : '0';
                document.getElementById('max-amount').textContent = amounts.length > 0 ? 
                    Math.max(...amounts).toFixed(2) : '0';
                document.getElementById('categories').textContent = categories.length;
                
                // Update table
                updateTable(data);
            }
        }

        function updateTable(data) {
            const table = document.getElementById('dataTable');
            if (data.length === 0) return;
            
            // Get last 10 records
            const recentData = data.slice(-10);
            const keys = Object.keys(recentData[0]);
            
            // Create header
            const thead = table.querySelector('thead tr');
            thead.innerHTML = keys.map(key => `<th>${key}</th>`).join('');
            
            // Create body
            const tbody = table.querySelector('tbody');
            tbody.innerHTML = recentData.map(row => 
                '<tr>' + keys.map(key => `<td>${String(row[key] || '').substring(0, 50)}</td>`).join('') + '</tr>'
            ).join('');
        }

        function showUpload() {
            document.getElementById('upload-section').style.display = 'block';
        }

        function hideUpload() {
            document.getElementById('upload-section').style.display = 'none';
        }

        function updateStatus(type, message) {
            const status = document.getElementById('status');
            status.className = `alert alert-${type} text-center`;
            status.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : type === 'danger' ? 'exclamation-triangle' : 'info'}-circle me-2"></i>${message}`;
        }

        // Upload form handler
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const fileInput = document.getElementById('fileInput');
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateStatus('success', data.message);
                    hideUpload();
                    refreshData();
                } else {
                    updateStatus('danger', 'Upload failed: ' + data.error);
                }
            })
            .catch(error => {
                updateStatus('danger', 'Upload error: ' + error);
            });
        });

        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
    '''

@app.route('/api/sample')
def load_sample():
    """Load sample data"""
    try:
        sample_data = create_sample_data()
        add_data_to_stream(sample_data)
        return jsonify({
            'success': True,
            'message': 'Sample data loaded successfully',
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

def simulate_data():
    """Background thread to simulate real-time data like your Kafka example"""
    time.sleep(5)  # Wait for server to start
    
    counter = 0
    while True:
        try:
            # Generate new data point similar to your examples
            new_record = {
                'id': 1000 + counter,
                'timestamp': datetime.now().isoformat(),
                'value': round(np.random.normal(100, 25), 2),
                'category': np.random.choice(['Electronics', 'Clothing', 'Books']),
                'region': np.random.choice(['North', 'South', 'East', 'West']),
                'status': np.random.choice(['active', 'inactive', 'pending']),
                'score': round(np.random.uniform(0, 100), 1),
                'amount': round(np.random.exponential(200), 2),
                'KPI': 'REAL_TIME_STREAM',
                'window_start': datetime.now().isoformat()
            }
            
            add_data_to_stream([new_record])
            counter += 1
            time.sleep(10)  # Add new data every 10 seconds
            
        except Exception as e:
            print(f"Simulation error: {e}")
            time.sleep(30)

if __name__ == '__main__':
    print("🚀 Starting Generic Real-Time Data Dashboard")
    print("📊 Based on your Kafka WebSocket Server + Dash Client examples")
    print("🌐 Access at: http://localhost:5000")
    print("📁 Upload JSON/CSV files or load sample data")
    print("-" * 50)
    
    # Start background simulation
    simulation_thread = threading.Thread(target=simulate_data, daemon=True)
    simulation_thread.start()
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=False)