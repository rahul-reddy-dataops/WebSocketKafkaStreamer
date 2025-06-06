import os
import logging
import threading
import time
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
from data_processor import DataProcessor
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "generic-dashboard-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize SocketIO with CORS support for public hosting
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    async_mode='threading'
)

# Configuration
config = Config()
data_processor = DataProcessor()

# Global data storage
current_data = []
data_lock = threading.Lock()

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure required directories exist
for directory in [UPLOAD_FOLDER, 'config', 'sample_data']:
    os.makedirs(directory, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main page with dashboard overview and file upload"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """File upload page"""
    return render_template('upload.html')

def add_data_to_stream(data_list):
    """Add data to the global stream and broadcast to clients"""
    global current_data
    with data_lock:
        if isinstance(data_list, list):
            current_data.extend(data_list)
        else:
            current_data.append(data_list)
        
        # Keep only the last 1000 records to prevent memory issues
        if len(current_data) > 1000:
            current_data = current_data[-1000:]
    
    # Broadcast to all connected clients
    socketio.emit('new_data', {
        'data': current_data,
        'total_records': len(current_data),
        'timestamp': time.time()
    })

@app.route('/upload_data', methods=['POST'])
def upload_data():
    """Handle file upload and process data"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(str(file.filename))
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the uploaded data
            try:
                processed_data = data_processor.process_file(filepath)
                data_records = processed_data.to_dict('records')
                
                # Add to global data stream
                add_data_to_stream(data_records)
                
                logger.info(f"Successfully processed and broadcasted data from {filename}")
                return jsonify({
                    'success': True, 
                    'message': f'File {filename} uploaded and processed successfully',
                    'records': len(processed_data)
                })
                
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        else:
            return jsonify({'error': 'Invalid file type. Please upload JSON or CSV files.'}), 400
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed'}), 500

@app.route('/api/config')
def get_config():
    """Get dashboard configuration"""
    try:
        return jsonify({
            'kpis': config.get_kpi_config(),
            'charts': config.get_chart_config(),
            'websocket_url': config.get_websocket_url()
        })
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return jsonify({'error': 'Configuration error'}), 500

@app.route('/api/sample_data')
def load_sample_data():
    """Load sample data for demonstration"""
    try:
        sample_file = 'sample_data/sample_data.json'
        if os.path.exists(sample_file):
            processed_data = data_processor.process_file(sample_file)
            
            # Emit sample data to all connected clients
            socketio.emit('new_data', {
                'data': processed_data.to_dict('records'),
                'source': 'sample_data',
                'filename': 'sample_data.json'
            }, broadcast=True)
            
            return jsonify({
                'success': True,
                'message': 'Sample data loaded successfully',
                'records': len(processed_data)
            })
        else:
            return jsonify({'error': 'Sample data not found'}), 404
            
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        return jsonify({'error': 'Failed to load sample data'}), 500

@app.route('/dashboard')
def dashboard():
    """Redirect to dashboard application"""
    dashboard_url = f"http://localhost:8000"
    return redirect(dashboard_url)

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info('Client connected to WebSocket')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info('Client disconnected from WebSocket')

@socketio.on('request_data')
def handle_data_request():
    """Handle client request for current data"""
    try:
        # Send any cached data if available
        if hasattr(data_processor, 'last_processed_data') and data_processor.last_processed_data is not None:
            socketio.emit('new_data', {
                'data': data_processor.last_processed_data.to_dict('records'),
                'source': 'cached_data'
            })
    except Exception as e:
        logger.error(f"Error handling data request: {str(e)}")

if __name__ == '__main__':
    # Run the WebSocket server to run application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
