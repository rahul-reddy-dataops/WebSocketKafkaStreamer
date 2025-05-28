#!/usr/bin/env python3
"""
Dashboard Application Runner

This script starts the Dash dashboard application that provides
interactive visualizations and real-time data updates.
"""

import os
import sys
import logging
from dashboard import DashboardApp

def main():
    """Main function to run the dashboard application"""
    
    # Configure logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Get configuration from environment
        host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
        port = int(os.getenv('DASHBOARD_PORT', '8000'))
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        
        logger.info(f"Starting Dashboard Application")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug Mode: {debug}")
        
        # Create and run dashboard
        dashboard = DashboardApp()
        
        logger.info("Dashboard application started successfully")
        logger.info(f"Access the dashboard at: http://{host}:{port}")
        
        # Run the dashboard
        dashboard.run(host=host, port=port)
        
    except KeyboardInterrupt:
        logger.info("Dashboard application stopped by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Failed to start dashboard application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
