#!/usr/bin/env python3
"""
Generic Real-Time Data Dashboard

A comprehensive dashboard system that combines features from both Kafka streaming 
and WebSocket real-time data visualization. This system supports:
- File uploads (JSON/CSV)
- Real-time data streaming via WebSocket
- Interactive Plotly/Dash visualizations
- Configurable KPIs and metrics
- Public hosting capabilities
"""

import os
import json
import logging
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import socketio as sio_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenericDataDashboard:
    def __init__(self):
        """Initialize the generic data dashboard"""
        # Flask app setup
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get("SESSION_SECRET", "generic-dashboard-key")
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_proto=1, x_host=1)
        
        # SocketIO setup
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            async_mode='threading'
        )
        
        # Data storage
        self.current_data = []
        self.data_lock = threading.Lock()
        
        # Configuration
        self.upload_folder = 'uploads'
        self.allowed_extensions = {'json', 'csv'}
        self.max_records = 1000
        
        # Create directories
        for directory in [self.upload_folder, 'sample_data']:
            os.makedirs(directory, exist_ok=True)
        
        # Setup routes
        self._setup_flask_routes()
        self._setup_socketio_events()
        
        # Dash app
        self.dash_app = None
        self._setup_dash_app()
    
    def _setup_flask_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return render_template('dashboard_index.html')
        
        @self.app.route('/upload', methods=['GET', 'POST'])
        def upload():
            if request.method == 'GET':
                return render_template('upload.html')
            
            # Handle file upload
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file selected'}), 400
                
                file = request.files['file']
                if not file.filename:
                    return jsonify({'error': 'No file selected'}), 400
                
                if self._allowed_file(file.filename):
                    filename = secure_filename(str(file.filename))
                    filepath = os.path.join(self.upload_folder, filename)
                    file.save(filepath)
                    
                    # Process and add data
                    data = self._process_file(filepath)
                    self._add_data_to_stream(data)
                    
                    return jsonify({
                        'success': True,
                        'message': f'File {filename} uploaded successfully',
                        'records': len(data)
                    })
                else:
                    return jsonify({'error': 'Invalid file type'}), 400
                    
            except Exception as e:
                logger.error(f"Upload error: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/data')
        def get_data():
            """Get current data"""
            with self.data_lock:
                return jsonify({
                    'data': self.current_data,
                    'total_records': len(self.current_data),
                    'timestamp': time.time()
                })
        
        @self.app.route('/api/sample')
        def load_sample():
            """Load sample data"""
            sample_data = self._generate_sample_data()
            self._add_data_to_stream(sample_data)
            return jsonify({
                'success': True,
                'message': 'Sample data loaded',
                'records': len(sample_data)
            })
    
    def _setup_socketio_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected')
            # Send current data to new client
            with self.data_lock:
                emit('new_data', {
                    'data': self.current_data,
                    'total_records': len(self.current_data),
                    'timestamp': time.time()
                })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected')
        
        @self.socketio.on('request_data')
        def handle_data_request():
            """Handle data request from client"""
            with self.data_lock:
                emit('new_data', {
                    'data': self.current_data,
                    'total_records': len(self.current_data),
                    'timestamp': time.time()
                })
    
    def _setup_dash_app(self):
        """Setup Dash application for visualizations"""
        # Initialize Dash app
        self.dash_app = dash.Dash(
            __name__,
            server=self.app,
            url_base_pathname='/dashboard/',
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css",
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
            ]
        )
        
        # Dash layout
        self.dash_app.layout = dbc.Container([
            dcc.Store(id='data-store'),
            dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
            
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1([
                        html.I(className="fas fa-chart-line me-3"),
                        "Generic Real-Time Dashboard"
                    ], className="text-center mb-4")
                ])
            ]),
            
            # Connection status
            dbc.Row([
                dbc.Col([
                    dbc.Alert(
                        id="connection-status",
                        children="Connecting to data stream...",
                        color="info",
                        className="mb-3"
                    )
                ])
            ]),
            
            # KPI Cards
            dbc.Row(id="kpi-cards", className="mb-4"),
            
            # Charts
            dbc.Tabs([
                dbc.Tab(label='Overview', tab_id='tab-overview', children=[
                    dbc.Row([
                        dbc.Col([dcc.Graph(id='overview-chart')], width=6),
                        dbc.Col([dcc.Graph(id='distribution-chart')], width=6)
                    ])
                ]),
                dbc.Tab(label='Time Series', tab_id='tab-timeseries', children=[
                    dbc.Row([
                        dbc.Col([dcc.Graph(id='timeseries-chart')], width=12)
                    ])
                ]),
                dbc.Tab(label='Analytics', tab_id='tab-analytics', children=[
                    dbc.Row([
                        dbc.Col([dcc.Graph(id='correlation-chart')], width=6),
                        dbc.Col([dcc.Graph(id='scatter-chart')], width=6)
                    ])
                ])
            ], id='tabs', active_tab='tab-overview'),
            
            # Data table
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H4("Recent Data"),
                    html.Div(id="data-table")
                ])
            ])
        ], fluid=True)
        
        # Setup callbacks
        self._setup_dash_callbacks()
    
    def _setup_dash_callbacks(self):
        """Setup Dash callbacks"""
        
        @self.dash_app.callback(
            [
                Output('data-store', 'data'),
                Output('connection-status', 'children'),
                Output('connection-status', 'color')
            ],
            [Input('interval-component', 'n_intervals')]
        )
        def update_data_store(n_intervals):
            try:
                # Get current data
                with self.data_lock:
                    data = self.current_data.copy()
                
                if data:
                    status_msg = f"Connected - {len(data)} records (last update: {datetime.now().strftime('%H:%M:%S')})"
                    status_color = "success"
                else:
                    status_msg = f"Waiting for data... (refresh #{n_intervals})"
                    status_color = "warning"
                
                return data, status_msg, status_color
                
            except Exception as e:
                logger.error(f"Error updating data store: {str(e)}")
                return [], f"Error: {str(e)}", "danger"
        
        @self.dash_app.callback(
            [
                Output('kpi-cards', 'children'),
                Output('overview-chart', 'figure'),
                Output('distribution-chart', 'figure'),
                Output('timeseries-chart', 'figure'),
                Output('correlation-chart', 'figure'),
                Output('scatter-chart', 'figure'),
                Output('data-table', 'children')
            ],
            [
                Input('data-store', 'data'),
                Input('tabs', 'active_tab')
            ]
        )
        def update_dashboard(data, active_tab):
            if not data:
                empty_fig = go.Figure().add_annotation(
                    text="No data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )
                empty_fig.update_layout(template="plotly_dark", height=400)
                
                return (
                    [dbc.Col([dbc.Card([dbc.CardBody([html.H5("No Data"), html.H2("0")])])], width=3)],
                    empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                    html.P("No data to display")
                )
            
            df = pd.DataFrame(data)
            
            # KPI Cards
            kpi_cards = self._create_kpi_cards(df)
            
            # Charts
            overview_fig = self._create_overview_chart(df)
            distribution_fig = self._create_distribution_chart(df)
            timeseries_fig = self._create_timeseries_chart(df)
            correlation_fig = self._create_correlation_chart(df)
            scatter_fig = self._create_scatter_chart(df)
            
            # Data table
            data_table = self._create_data_table(df)
            
            return (
                kpi_cards, overview_fig, distribution_fig, 
                timeseries_fig, correlation_fig, scatter_fig, data_table
            )
    
    def _allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _process_file(self, filepath):
        """Process uploaded file"""
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
            logger.error(f"Error processing file {filepath}: {str(e)}")
            raise
    
    def _add_data_to_stream(self, new_data):
        """Add data to the stream and broadcast"""
        with self.data_lock:
            if isinstance(new_data, list):
                self.current_data.extend(new_data)
            else:
                self.current_data.append(new_data)
            
            # Keep only recent records
            if len(self.current_data) > self.max_records:
                self.current_data = self.current_data[-self.max_records:]
        
        # Broadcast to all clients
        self.socketio.emit('new_data', {
            'data': self.current_data,
            'total_records': len(self.current_data),
            'timestamp': time.time()
        })
    
    def _generate_sample_data(self, num_records=50):
        """Generate sample data for demonstration"""
        np.random.seed(42)
        
        categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
        regions = ['North', 'South', 'East', 'West']
        statuses = ['active', 'inactive', 'pending']
        
        data = []
        for i in range(num_records):
            record = {
                'id': i + 1,
                'timestamp': (datetime.now().timestamp() - (num_records - i) * 3600),
                'value': round(np.random.normal(100, 25), 2),
                'category': np.random.choice(categories),
                'region': np.random.choice(regions),
                'status': np.random.choice(statuses),
                'score': round(np.random.uniform(0, 100), 1),
                'amount': round(np.random.exponential(200), 2)
            }
            data.append(record)
        
        return data
    
    def _create_kpi_cards(self, df):
        """Create KPI cards"""
        cards = []
        
        # Total Records
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Total Records"),
                        html.H2(f"{len(df):,}", className="text-primary")
                    ])
                ])
            ], width=3)
        )
        
        # Numeric columns KPIs
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"Avg {col.title()}"),
                            html.H2(f"{df[col].mean():.2f}", className="text-success")
                        ])
                    ])
                ], width=3)
            )
        
        if len(numeric_cols) > 1:
            col = numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0]
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"Max {col.title()}"),
                            html.H2(f"{df[col].max():.2f}", className="text-info")
                        ])
                    ])
                ], width=3)
            )
        
        # Categorical column
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            col = categorical_cols[0]
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(f"Unique {col.title()}"),
                            html.H2(f"{df[col].nunique()}", className="text-warning")
                        ])
                    ])
                ], width=3)
            )
        
        return cards[:4]
    
    def _create_overview_chart(self, df):
        """Create overview chart"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                fig = px.line(df.head(50), y=col, title=f"{col.title()} Trend")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception:
            pass
        
        return go.Figure().update_layout(template="plotly_dark", height=400)
    
    def _create_distribution_chart(self, df):
        """Create distribution chart"""
        try:
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                col = categorical_cols[0]
                value_counts = df[col].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index, 
                           title=f"Distribution of {col.title()}")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception:
            pass
        
        return go.Figure().update_layout(template="plotly_dark", height=400)
    
    def _create_timeseries_chart(self, df):
        """Create time series chart"""
        try:
            # Look for timestamp column
            timestamp_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            if timestamp_cols and len(numeric_cols) > 0:
                time_col = timestamp_cols[0]
                value_col = numeric_cols[0]
                
                # Convert timestamp if needed
                if pd.api.types.is_numeric_dtype(df[time_col]):
                    df[time_col] = pd.to_datetime(df[time_col], unit='s')
                else:
                    df[time_col] = pd.to_datetime(df[time_col])
                
                fig = px.line(df, x=time_col, y=value_col, title="Time Series Analysis")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception:
            pass
        
        return go.Figure().update_layout(template="plotly_dark", height=400)
    
    def _create_correlation_chart(self, df):
        """Create correlation heatmap"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(corr_matrix, text_auto=True, title="Correlation Matrix")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception:
            pass
        
        return go.Figure().update_layout(template="plotly_dark", height=400)
    
    def _create_scatter_chart(self, df):
        """Create scatter plot"""
        try:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                               title=f"{numeric_cols[0]} vs {numeric_cols[1]}")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception:
            pass
        
        return go.Figure().update_layout(template="plotly_dark", height=400)
    
    def _create_data_table(self, df):
        """Create data table"""
        try:
            recent_data = df.tail(10)
            
            if recent_data.empty:
                return html.P("No data available")
            
            # Create table
            table_header = [html.Thead([html.Tr([html.Th(col) for col in recent_data.columns])])]
            table_rows = []
            
            for _, row in recent_data.iterrows():
                table_rows.append(html.Tr([html.Td(str(val)[:50]) for val in row]))
            
            table_body = [html.Tbody(table_rows)]
            
            return dbc.Table(
                table_header + table_body,
                bordered=True,
                dark=True,
                hover=True,
                responsive=True,
                striped=True
            )
        except Exception:
            return html.P("Error displaying table")
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the dashboard application"""
        logger.info(f"Starting Generic Data Dashboard on {host}:{port}")
        logger.info(f"Main interface: http://{host}:{port}")
        logger.info(f"Dashboard: http://{host}:{port}/dashboard/")
        
        # Start data simulation in background
        self._start_simulation()
        
        self.socketio.run(self.app, host=host, port=port, debug=debug)
    
    def _start_simulation(self):
        """Start background data simulation"""
        def simulate_data():
            time.sleep(3)  # Wait for server to start
            
            # Load initial sample data
            sample_data = self._generate_sample_data(20)
            self._add_data_to_stream(sample_data)
            
            # Continuous simulation
            counter = 0
            while True:
                try:
                    # Generate new data point every 5 seconds
                    new_record = {
                        'id': 1000 + counter,
                        'timestamp': time.time(),
                        'value': round(np.random.normal(100, 25), 2),
                        'category': np.random.choice(['Electronics', 'Clothing', 'Books']),
                        'region': np.random.choice(['North', 'South', 'East', 'West']),
                        'status': np.random.choice(['active', 'inactive', 'pending']),
                        'score': round(np.random.uniform(0, 100), 1),
                        'amount': round(np.random.exponential(200), 2)
                    }
                    
                    self._add_data_to_stream([new_record])
                    counter += 1
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Simulation error: {str(e)}")
                    time.sleep(10)
        
        simulation_thread = threading.Thread(target=simulate_data, daemon=True)
        simulation_thread.start()
        logger.info("Background data simulation started")

# Create HTML templates
def create_templates():
    """Create necessary HTML templates"""
    os.makedirs('templates', exist_ok=True)
    
    # Main index template
    index_html = '''<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generic Real-Time Data Dashboard</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-4">
        <div class="row mb-4">
            <div class="col-12 text-center">
                <h1 class="display-4 mb-3">
                    <i class="fas fa-chart-line me-3"></i>
                    Generic Real-Time Data Dashboard
                </h1>
                <p class="lead">Upload your data and visualize it in real-time</p>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-12 text-center">
                <div class="btn-group" role="group">
                    <a href="/upload" class="btn btn-primary btn-lg">
                        <i class="fas fa-upload me-2"></i>Upload Data
                    </a>
                    <a href="/api/sample" class="btn btn-success btn-lg" onclick="loadSample(event)">
                        <i class="fas fa-play me-2"></i>Load Sample Data
                    </a>
                    <a href="/dashboard/" class="btn btn-info btn-lg">
                        <i class="fas fa-chart-bar me-2"></i>Open Dashboard
                    </a>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-12">
                <div id="status" class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Ready to receive data
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script>
        function loadSample(event) {
            event.preventDefault();
            fetch('/api/sample')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('status').innerHTML = 
                            '<i class="fas fa-check me-2"></i>' + data.message;
                        document.getElementById('status').className = 'alert alert-success';
                    }
                });
        }
        
        // WebSocket connection
        const socket = io();
        socket.on('new_data', function(data) {
            document.getElementById('status').innerHTML = 
                '<i class="fas fa-database me-2"></i>Data updated: ' + 
                data.total_records + ' records';
            document.getElementById('status').className = 'alert alert-success';
        });
    </script>
</body>
</html>'''
    
    with open('templates/dashboard_index.html', 'w') as f:
        f.write(index_html)
    
    # Upload template
    upload_html = '''<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Data</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="container py-4">
        <div class="row mb-4">
            <div class="col-12">
                <a href="/" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Home
                </a>
                <h2 class="mt-3">Upload Your Data</h2>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-body">
                        <form id="uploadForm" enctype="multipart/form-data">
                            <div class="mb-3">
                                <label for="file" class="form-label">Choose file (JSON or CSV)</label>
                                <input type="file" class="form-control" id="file" name="file" 
                                       accept=".json,.csv" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-upload me-2"></i>Upload
                            </button>
                        </form>
                        
                        <div id="result" class="mt-3"></div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Supported Formats</h5>
                    </div>
                    <div class="card-body">
                        <h6>JSON:</h6>
                        <pre><code>[{"id": 1, "value": 100}]</code></pre>
                        
                        <h6>CSV:</h6>
                        <pre><code>id,value
1,100
2,200</code></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        document.getElementById('uploadForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            const fileInput = document.getElementById('file');
            formData.append('file', fileInput.files[0]);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById('result');
                if (data.success) {
                    result.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    setTimeout(() => {
                        window.location.href = '/dashboard/';
                    }, 2000);
                } else {
                    result.innerHTML = '<div class="alert alert-danger">' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('result').innerHTML = 
                    '<div class="alert alert-danger">Upload failed: ' + error + '</div>';
            });
        });
    </script>
</body>
</html>'''
    
    with open('templates/upload.html', 'w') as f:
        f.write(upload_html)

if __name__ == '__main__':
    # Create templates
    create_templates()
    
    # Create and run dashboard
    dashboard = GenericDataDashboard()
    dashboard.run(debug=True)