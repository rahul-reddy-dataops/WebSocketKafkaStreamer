#!/usr/bin/env python3
"""
WebSocket Server Runner

This script starts the main Flask application with WebSocket support
for real-time data streaming and file upload functionality.
"""

import os
import sys
import logging
import threading
import time
from app import app, socketio
from websocket_server import WebSocketServer

def main():
    """Main function to run the WebSocket server application"""
    
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration from environment
        host = os.getenv('WEBSOCKET_HOST', '0.0.0.0')
        port = int(os.getenv('WEBSOCKET_PORT', '5000'))
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        enable_simulation = os.getenv('ENABLE_SIMULATION', 'true').lower() == 'true'
        
        logger.info(f"Starting WebSocket Server Application")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug Mode: {debug}")
        logger.info(f"Data Simulation: {enable_simulation}")
        
        # Ensure required directories exist
        os.makedirs('uploads', exist_ok=True)
        os.makedirs('config', exist_ok=True)
        os.makedirs('sample_data', exist_ok=True)
        
        logger.info("Required directories verified")
        
        # Start data simulation if enabled
        if enable_simulation:
            def start_simulation():
                """Start background data simulation"""
                try:
                    time.sleep(2)  # Wait for server to start
                    logger.info("Starting background data simulation")
                    
                    # Create standalone WebSocket server for simulation
                    sim_server = WebSocketServer()
                    sim_server.load_sample_data()
                    sim_server.start_simulation()
                    
                    logger.info("Background data simulation started")
                    
                except Exception as e:
                    logger.error(f"Error starting data simulation: {str(e)}")
            
            # Start simulation in background thread
            simulation_thread = threading.Thread(target=start_simulation, daemon=True)
            simulation_thread.start()
        
        logger.info("WebSocket server starting...")
        logger.info(f"Main interface available at: http://{host}:{port}")
        logger.info(f"Upload page available at: http://{host}:{port}/upload")
        logger.info("Make sure to start the dashboard application separately with: python run_dashboard.py")
        
        # Run the Flask-SocketIO server
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=debug,
            allow_unsafe_werkzeug=True  # For development only
        )
        
    except KeyboardInterrupt:
        logger.info("WebSocket server stopped by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {str(e)}")
        logger.error("Common issues:")
        logger.error("1. Port 5000 might be in use - try setting WEBSOCKET_PORT to a different port")
        logger.error("2. Check if all dependencies are installed: pip install -r requirements.txt")
        logger.error("3. Ensure you have proper write permissions for uploads directory")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are available"""
    required_modules = [
        'flask', 'flask_socketio', 'pandas', 'plotly', 
        'yaml', 'socketio', 'werkzeug'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("ERROR: Missing required dependencies:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install missing dependencies with:")
        print("pip install -r requirements.txt")
        sys.exit(1)

def show_startup_info():
    """Display startup information and instructions"""
    print("="*60)
    print("Real-Time Data Dashboard - WebSocket Server")
    print("="*60)
    print()
    print("This is the main WebSocket server that handles:")
    print("• File uploads (JSON/CSV)")
    print("• Real-time data streaming")
    print("• Web interface")
    print()
    print("After starting this server, run the dashboard with:")
    print("python run_dashboard.py")
    print()
    print("Then access:")
    print("• Main interface: http://localhost:5000")
    print("• Dashboard: http://localhost:8000")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*60)
    print()

if __name__ == '__main__':
    # Check dependencies first
    check_dependencies()
    
    # Show startup information
    show_startup_info()
    
    # Start the server
    main()
