import os
import yaml
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Config:
    def __init__(self, config_path='config/config.yaml'):
        """Initialize configuration manager"""
        self.config_path = config_path
        self.config_data = self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file with environment variable overrides"""
        try:
            # Default configuration
            default_config = {
                'websocket': {
                    'host': '0.0.0.0',
                    'port': 5000,
                    'url': 'http://localhost:5000'
                },
                'dashboard': {
                    'host': '0.0.0.0',
                    'port': 8000,
                    'auto_refresh_interval': 5000,
                    'theme': 'dark'
                },
                'data': {
                    'max_records': 1000,
                    'enable_simulation': True,
                    'simulation_interval': 2,
                    'upload_folder': 'uploads',
                    'allowed_extensions': ['json', 'csv']
                },
                'kpis': {
                    'total_records': {
                        'name': 'Total Records',
                        'icon': 'fas fa-database',
                        'color': 'primary'
                    },
                    'average_value': {
                        'name': 'Average Value',
                        'icon': 'fas fa-chart-bar',
                        'color': 'success'
                    },
                    'max_value': {
                        'name': 'Maximum Value',
                        'icon': 'fas fa-arrow-up',
                        'color': 'info'
                    },
                    'unique_categories': {
                        'name': 'Unique Categories',
                        'icon': 'fas fa-tags',
                        'color': 'warning'
                    }
                },
                'charts': {
                    'overview': {
                        'type': 'line',
                        'title': 'Data Overview'
                    },
                    'distribution': {
                        'type': 'bar',
                        'title': 'Data Distribution'
                    },
                    'correlation': {
                        'type': 'heatmap',
                        'title': 'Correlation Matrix'
                    }
                }
            }
            
            # Try to load from file
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        default_config.update(file_config)
            
            # Override with environment variables
            self._apply_env_overrides(default_config)
            
            return default_config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return self._get_minimal_config()
    
    def _apply_env_overrides(self, config):
        """Apply environment variable overrides"""
        # WebSocket configuration
        if os.getenv('WEBSOCKET_HOST'):
            config['websocket']['host'] = os.getenv('WEBSOCKET_HOST')
        if os.getenv('WEBSOCKET_PORT'):
            config['websocket']['port'] = int(os.getenv('WEBSOCKET_PORT'))
        if os.getenv('WEBSOCKET_URL'):
            config['websocket']['url'] = os.getenv('WEBSOCKET_URL')
        
        # Dashboard configuration
        if os.getenv('DASHBOARD_HOST'):
            config['dashboard']['host'] = os.getenv('DASHBOARD_HOST')
        if os.getenv('DASHBOARD_PORT'):
            config['dashboard']['port'] = int(os.getenv('DASHBOARD_PORT'))
        
        # Data configuration
        if os.getenv('ENABLE_SIMULATION'):
            config['data']['enable_simulation'] = os.getenv('ENABLE_SIMULATION').lower() == 'true'
        if os.getenv('SIMULATION_INTERVAL'):
            config['data']['simulation_interval'] = float(os.getenv('SIMULATION_INTERVAL'))
        if os.getenv('MAX_RECORDS'):
            config['data']['max_records'] = int(os.getenv('MAX_RECORDS'))
    
    def _get_minimal_config(self):
        """Get minimal configuration for fallback"""
        return {
            'websocket': {
                'host': '0.0.0.0',
                'port': 5000,
                'url': 'http://localhost:5000'
            },
            'dashboard': {
                'host': '0.0.0.0',
                'port': 8000,
                'auto_refresh_interval': 5000
            },
            'data': {
                'max_records': 1000,
                'enable_simulation': True,
                'simulation_interval': 2
            }
        }
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation"""
        try:
            keys = key_path.split('.')
            value = self.config_data
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def get_websocket_config(self):
        """Get WebSocket configuration"""
        return self.config_data.get('websocket', {})
    
    def get_dashboard_config(self):
        """Get dashboard configuration"""
        return self.config_data.get('dashboard', {})
    
    def get_data_config(self):
        """Get data processing configuration"""
        return self.config_data.get('data', {})
    
    def get_websocket_url(self):
        """Get WebSocket URL"""
        return self.get('websocket.url', 'http://localhost:5000')
    
    def get_enable_simulation(self):
        """Check if data simulation is enabled"""
        return self.get('data.enable_simulation', True)
    
    def get_simulation_interval(self):
        """Get data simulation interval in seconds"""
        return self.get('data.simulation_interval', 2)
    
    def get_max_records(self):
        """Get maximum records to keep in memory"""
        return self.get('data.max_records', 1000)
    
    def get_kpi_config(self):
        """Get KPI configuration"""
        return self.config_data.get('kpis', {})
    
    def get_chart_config(self):
        """Get chart configuration"""
        return self.config_data.get('charts', {})
    
    def save_config(self, config_data=None):
        """Save configuration to file"""
        try:
            config_to_save = config_data or self.config_data
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        try:
            def deep_update(original, updates):
                for key, value in updates.items():
                    if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                        deep_update(original[key], value)
                    else:
                        original[key] = value
            
            deep_update(self.config_data, updates)
            self.save_config()
            
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
