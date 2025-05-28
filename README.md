# Generic Real-Time Data Dashboard

A comprehensive, production-ready real-time data dashboard system that combines WebSocket streaming, interactive visualizations, and file upload capabilities. This system is designed to be generic, configurable, and suitable for public hosting on platforms like GitHub, Replit, or cloud services.

## 🚀 Features

### Core Functionality
- **Real-time data streaming** via WebSocket connections
- **File upload support** for JSON and CSV files  
- **Interactive visualizations** using Plotly and Dash
- **Configurable KPIs** and metrics display
- **Responsive design** optimized for all devices
- **Live data updates** with automatic refresh
- **Background data simulation** for demonstration

### Visualization Types
- **Line charts** for time-series analysis
- **Bar charts** for categorical data
- **Pie charts** for distribution analysis  
- **Scatter plots** for correlation analysis
- **Heatmaps** for correlation matrices
- **Data tables** with recent records display

### Data Sources Supported
- **File uploads** (JSON/CSV format)
- **Real-time streaming** data
- **Sample data generation** for testing
- **Configurable data processing** pipeline

## 🏗️ System Architecture

The dashboard consists of two integrated applications:

### 1. Flask WebSocket Server
- Handles file uploads and data processing
- Provides WebSocket endpoints for real-time streaming
- Serves the main web interface
- Manages data storage and broadcasting

### 2. Dash Visualization App  
- Interactive dashboard with multiple chart types
- Real-time updates via WebSocket client
- Configurable KPIs and metrics
- Responsive layout with tabbed interface

## 📋 What Both Original Repositories Do

### Repository 1: Kafka WebSocket Server
The first code example (`cat_kafka_websocket_server.py`) demonstrates:
- **Kafka message consumption** using EefConsumer SDK
- **Real-time data processing** with commit/rollback handlers
- **WebSocket broadcasting** to connected clients
- **Flask-SocketIO integration** for web interface
- **Event-driven architecture** for handling streaming data

### Repository 2: Dash WebSocket Client  
The second code example (`python-dash_cat-dash-poc_cat_dash_websocket_client.py`) shows:
- **Interactive Dash dashboard** with multiple visualization tabs
- **S3 data integration** for loading historical data
- **Real-time WebSocket client** for live updates
- **KPI calculations** and metrics display
- **Multiple chart types** including heatmaps and trend analysis

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Modern web browser with WebSocket support
- At least 512MB RAM for basic usage

### Quick Installation
```bash
# Clone the repository
git clone https://github.com/your-username/generic-realtime-dashboard.git
cd generic-realtime-dashboard

# Install dependencies
pip install flask flask-socketio dash dash-bootstrap-components plotly pandas numpy python-socketio

# Create required directories
mkdir -p uploads sample_data

# Run the application
python generic_dashboard.py
```

### Using Requirements File
```bash
# Install all dependencies
pip install -r requirements.txt

# Run the dashboard
python generic_dashboard.py
```

## 🚀 Quick Start Guide

### Option 1: All-in-One Application (Recommended)
```bash
python generic_dashboard.py
```

Then access:
- **Main interface**: http://localhost:5000
- **Interactive dashboard**: http://localhost:5000/dashboard/
- **Upload page**: http://localhost:5000/upload

### Option 2: Separate Components
```bash
# Terminal 1 - Start WebSocket server
python run_websocket.py

# Terminal 2 - Start dashboard  
python run_dashboard.py
```

## 📊 Usage Instructions

### 1. Upload Your Data
1. Navigate to the upload page
2. Select a JSON or CSV file (max 16MB)
3. Click "Upload" to process the file
4. Data will appear in real-time on the dashboard

### 2. Load Sample Data
1. Click "Load Sample Data" on the main page
2. Demonstration data will be generated automatically
3. View the visualizations on the dashboard

### 3. View Real-Time Dashboard
1. Access the dashboard interface
2. Monitor KPIs and interactive charts
3. Switch between different visualization tabs
4. Data updates automatically every 5 seconds

## 📁 Supported Data Formats

### JSON Files
```json
[
  {
    "id": 1,
    "timestamp": "2024-01-15T10:00:00Z",
    "value": 125.50,
    "category": "Electronics",
    "status": "active",
    "region": "North"
  },
  {
    "id": 2,
    "timestamp": "2024-01-15T11:00:00Z", 
    "value": 200.75,
    "category": "Clothing",
    "status": "pending",
    "region": "South"
  }
]
```

### CSV Files  
```csv
id,timestamp,value,category,status,region
1,2024-01-15T10:00:00Z,125.50,Electronics,active,North
2,2024-01-15T11:00:00Z,200.75,Clothing,pending,South
3,2024-01-15T12:00:00Z,89.25,Books,active,East
```

### Requirements
- **File size**: Maximum 16MB
- **Encoding**: UTF-8 preferred (Latin-1 supported)
- **Structure**: Tabular data format
- **Headers**: Required for CSV files

## ⚙️ Configuration

### Environment Variables
```bash
# Server configuration
SESSION_SECRET=your-secret-key-here
HOST=0.0.0.0
PORT=5000

# Data settings  
MAX_RECORDS=1000
ENABLE_SIMULATION=true

# Upload settings
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=16777216
```

### Dashboard Customization
- Modify KPI calculations in `_create_kpi_cards()`
- Add new chart types in the chart creation methods
- Customize styling via Bootstrap themes
- Configure data processing in `_process_file()`

## 🌐 Public Hosting

### Replit Deployment
1. Fork this repository on Replit
2. Set environment variables in Replit secrets
3. Run the application
4. Access via your Replit URL

### GitHub Pages + External Hosting
1. Host the Flask app on services like Railway, Render, or Heroku  
2. Update WebSocket URLs in the frontend
3. Configure CORS settings for your domain
4. Set production environment variables

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "generic_dashboard.py"]
```

## 📈 Performance & Scalability

### Memory Management
- Automatic data rotation (keeps last 1000 records)
- Efficient DataFrame operations
- Background thread management

### Network Optimization  
- WebSocket compression enabled
- Minimal data payloads
- Efficient JSON serialization

### Recommended Limits
- **Concurrent users**: Up to 100 (single instance)
- **Data points**: Up to 1000 active records
- **File uploads**: 16MB maximum size
- **Update frequency**: 5-second intervals

## 🔧 Customization Examples

### Adding New Chart Types
```python
def _create_custom_chart(self, df):
    """Create a custom visualization"""
    try:
        # Your custom chart logic here
        fig = px.your_chart_type(df, ...)
        fig.update_layout(template="plotly_dark", height=400)
        return fig
    except Exception:
        return go.Figure().update_layout(template="plotly_dark", height=400)
```

### Custom KPI Calculations
```python
def _create_custom_kpi(self, df):
    """Calculate custom business metrics"""
    custom_metric = df['your_column'].custom_calculation()
    return custom_metric
```

## 🐛 Troubleshooting

### Common Issues
1. **Port already in use**: Change PORT environment variable
2. **WebSocket connection failed**: Check firewall settings
3. **File upload errors**: Verify file format and size
4. **No data displayed**: Check browser console for errors

### Debug Mode
```bash
# Run with debug enabled
python generic_dashboard.py --debug
```

### Logs Location
- Application logs: Console output
- Error logs: Check terminal for stack traces
- Upload logs: Verify uploads directory permissions

## 🤝 Contributing

### Development Setup
```bash
# Clone for development
git clone https://github.com/your-username/generic-realtime-dashboard.git
cd generic-realtime-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies  
pip install -r requirements-dev.txt
```

### Code Structure
```
generic-realtime-dashboard/
├── generic_dashboard.py     # Main application file
├── app.py                  # Flask WebSocket server
├── dashboard.py            # Dash visualization app
├── data_processor.py       # Data processing utilities
├── config.py              # Configuration management
├── templates/              # HTML templates
├── static/                 # CSS/JS assets
├── sample_data/           # Sample datasets
├── uploads/               # User uploaded files
└── requirements.txt       # Python dependencies
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

This dashboard system combines patterns and techniques from:
- Kafka streaming architectures
- Real-time web applications  
- Interactive data visualization
- Modern web development practices

---

**Ready to visualize your data in real-time?** Upload your files or load sample data to get started immediately!