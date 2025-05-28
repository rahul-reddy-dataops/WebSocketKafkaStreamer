import os
import json
import logging
import threading
import time
import pandas as pd
from flask import Flask
from flask_socketio import SocketIO
from data_processor import DataProcessor
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self):
        """Initialize WebSocket server for real-time data streaming"""
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get("SESSION_SECRET", "websocket-secret-key")
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.config = Config()
        self.data_processor = DataProcessor()
        self.payload_list = []
        self.is_running = False
        
        self.setup_routes()
        
    def setup_routes(self):
        """Setup WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to WebSocket server')
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from WebSocket server')
            
        @self.socketio.on('request_data')
        def handle_data_request():
            """Send current data to requesting client"""
            if self.payload_list:
                try:
                    df = pd.DataFrame(self.payload_list)
                    self.socketio.emit('new_data', {
                        'data': df.to_dict('records'),
                        'source': 'current_data'
                    })
                except Exception as e:
                    logger.error(f"Error sending data to client: {str(e)}")
    
    def add_data(self, data):
        """Add new data and broadcast to all clients"""
        try:
            if isinstance(data, dict):
                self.payload_list.append(data)
            elif isinstance(data, list):
                self.payload_list.extend(data)
            else:
                logger.warning(f"Unsupported data type: {type(data)}")
                return
            
            # Keep only last 1000 records to prevent memory issues
            if len(self.payload_list) > 1000:
                self.payload_list = self.payload_list[-1000:]
            
            # Create DataFrame and emit to clients
            df = pd.DataFrame(self.payload_list)
            self.socketio.emit('new_data', {
                'data': df.to_dict('records'),
                'source': 'real_time',
                'timestamp': time.time()
            })
            
            logger.info(f"Broadcasted data update to clients. Total records: {len(self.payload_list)}")
            
        except Exception as e:
            logger.error(f"Error adding and broadcasting data: {str(e)}")
    
    def simulate_data_stream(self):
        """Simulate real-time data streaming for demonstration"""
        logger.info("Starting data simulation thread")
        counter = 0
        
        while self.is_running:
            try:
                # Generate sample data point
                sample_data = {
                    'id': counter,
                    'timestamp': time.time(),
                    'value': 100 + (counter % 50),
                    'category': f'Category_{counter % 5}',
                    'status': 'active' if counter % 2 == 0 else 'inactive',
                    'metric_1': (counter * 1.5) % 100,
                    'metric_2': (counter * 2.3) % 200,
                    'region': ['North', 'South', 'East', 'West'][counter % 4]
                }
                
                self.add_data(sample_data)
                counter += 1
                
                # Wait before next data point
                time.sleep(self.config.get_simulation_interval())
                
            except Exception as e:
                logger.error(f"Error in data simulation: {str(e)}")
                time.sleep(5)  # Wait before retrying
    
    def load_sample_data(self):
        """Load initial sample data"""
        try:
            sample_file = 'sample_data/sample_data.json'
            if os.path.exists(sample_file):
                with open(sample_file, 'r') as f:
                    sample_data = json.load(f)
                
                if isinstance(sample_data, list):
                    self.payload_list.extend(sample_data)
                else:
                    self.payload_list.append(sample_data)
                
                logger.info(f"Loaded {len(sample_data)} sample records")
        except Exception as e:
            logger.error(f"Error loading sample data: {str(e)}")
    
    def start_simulation(self):
        """Start data simulation in background thread"""
        if not self.is_running:
            self.is_running = True
            simulation_thread = threading.Thread(target=self.simulate_data_stream, daemon=True)
            simulation_thread.start()
            logger.info("Data simulation started")
    
    def stop_simulation(self):
        """Stop data simulation"""
        self.is_running = False
        logger.info("Data simulation stopped")
    
    def run(self, host='0.0.0.0', port=8000):
        """Run the WebSocket server"""
        logger.info(f"Starting WebSocket server on {host}:{port}")
        
        # Load initial sample data
        self.load_sample_data()
        
        # Start data simulation if enabled
        if self.config.get_enable_simulation():
            self.start_simulation()
        
        # Run the server
        self.socketio.run(self.app, host=host, port=port, debug=False)

if __name__ == '__main__':
    server = WebSocketServer()
    server.run()
