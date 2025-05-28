import os
import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import socketio
import threading
import time
import json
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardApp:
    def __init__(self):
        """Initialize the Dashboard application"""
        self.config = Config()
        self.cached_data = pd.DataFrame()
        self.kpi_config = self.config.get_kpi_config()
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__, 
            external_stylesheets=[
                dbc.themes.BOOTSTRAP,
                "https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css",
                "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
            ],
            suppress_callback_exceptions=True
        )
        
        # Initialize WebSocket client
        self.sio = socketio.Client()
        self.setup_websocket()
        self.setup_layout()
        self.setup_callbacks()
        
    def setup_websocket(self):
        """Setup WebSocket client for real-time data"""
        
        @self.sio.event
        def connect():
            logger.info('Connected to WebSocket server')
            self.sio.emit('request_data')  # Request current data on connect
        
        @self.sio.event
        def disconnect():
            logger.info('Disconnected from WebSocket server')
        
        @self.sio.event
        def connect_error(data):
            logger.error(f'WebSocket connection error: {data}')
        
        @self.sio.on('new_data')
        def on_new_data(data):
            try:
                new_data = pd.DataFrame(data['data'])
                if not new_data.empty:
                    self.cached_data = new_data
                    logger.info(f"Received {len(new_data)} records from WebSocket")
            except Exception as e:
                logger.error(f"Error processing WebSocket data: {str(e)}")
    
    def start_websocket_client(self):
        """Start WebSocket client in background thread"""
        def connect_websocket():
            try:
                websocket_url = self.config.get_websocket_url()
                self.sio.connect(websocket_url)
                self.sio.wait()
            except Exception as e:
                logger.error(f"WebSocket connection failed: {str(e)}")
                # Retry connection after delay
                time.sleep(5)
                self.start_websocket_client()
        
        thread = threading.Thread(target=connect_websocket, daemon=True)
        thread.start()
    
    def setup_layout(self):
        """Setup the dashboard layout"""
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className="fas fa-chart-line me-2"),
                        html.H1("Real-Time Data Dashboard", className="d-inline")
                    ], className="text-center mb-4")
                ])
            ]),
            
            # Auto-refresh interval
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # Update every 5 seconds
                n_intervals=0
            ),
            
            # Connection status indicator
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
            
            html.Hr(),
            
            # Charts in tabs
            dbc.Tabs([
                dbc.Tab(label='Overview', tab_id='tab-overview', children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='overview-chart')
                        ], width=6),
                        dbc.Col([
                            dcc.Graph(id='trend-chart')
                        ], width=6)
                    ])
                ]),
                
                dbc.Tab(label='Detailed Analytics', tab_id='tab-analytics', children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='detailed-chart')
                        ], width=12)
                    ])
                ]),
                
                dbc.Tab(label='Data Distribution', tab_id='tab-distribution', children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(id='distribution-chart')
                        ], width=6),
                        dbc.Col([
                            dcc.Graph(id='heatmap-chart')
                        ], width=6)
                    ])
                ])
                
            ], id='tabs', active_tab='tab-overview'),
            
            # Data table
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    html.H4("Recent Data", className="mb-3"),
                    html.Div(id="data-table")
                ])
            ])
            
        ], fluid=True, className="py-3")
    
    def create_kpi_cards(self, df):
        """Create KPI cards based on data"""
        if df.empty:
            return [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("No Data", className="text-muted"),
                            html.H2("0", className="text-secondary")
                        ])
                    ])
                ], width=3)
            ]
        
        cards = []
        
        # Total Records
        cards.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-database me-2"),
                            html.H5("Total Records", className="d-inline")
                        ]),
                        html.H2(f"{len(df):,}", className="text-primary mt-2")
                    ])
                ], className="h-100")
            ], width=3)
        )
        
        # Numeric columns for additional KPIs
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            col = numeric_cols[0]
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-chart-bar me-2"),
                                html.H5(f"Avg {col.title()}", className="d-inline")
                            ]),
                            html.H2(f"{df[col].mean():.2f}", className="text-success mt-2")
                        ])
                    ], className="h-100")
                ], width=3)
            )
        
        if len(numeric_cols) > 1:
            col = numeric_cols[1]
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-arrow-up me-2"),
                                html.H5(f"Max {col.title()}", className="d-inline")
                            ]),
                            html.H2(f"{df[col].max():.2f}", className="text-info mt-2")
                        ])
                    ], className="h-100")
                ], width=3)
            )
        
        # Unique categories
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            col = categorical_cols[0]
            unique_count = df[col].nunique()
            cards.append(
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-tags me-2"),
                                html.H5(f"Unique {col.title()}", className="d-inline")
                            ]),
                            html.H2(f"{unique_count}", className="text-warning mt-2")
                        ])
                    ], className="h-100")
                ], width=3)
            )
        
        return cards[:4]  # Limit to 4 cards
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [
                Output('connection-status', 'children'),
                Output('connection-status', 'color'),
                Output('kpi-cards', 'children'),
                Output('overview-chart', 'figure'),
                Output('trend-chart', 'figure'),
                Output('detailed-chart', 'figure'),
                Output('distribution-chart', 'figure'),
                Output('heatmap-chart', 'figure'),
                Output('data-table', 'children')
            ],
            [
                Input('interval-component', 'n_intervals'),
                Input('tabs', 'active_tab')
            ]
        )
        def update_dashboard(n_intervals, active_tab):
            df = self.cached_data.copy()
            
            # Connection status
            if df.empty:
                status_msg = f"Waiting for data... (refresh #{n_intervals})"
                status_color = "warning"
            else:
                status_msg = f"Connected - {len(df)} records loaded (last update: {time.strftime('%H:%M:%S')})"
                status_color = "success"
            
            # KPI Cards
            kpi_cards = self.create_kpi_cards(df)
            
            # Default empty figures
            empty_fig = go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            empty_fig.update_layout(
                template="plotly_dark",
                height=400,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            
            if df.empty:
                return (
                    status_msg, status_color, kpi_cards,
                    empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                    html.P("No data to display", className="text-muted")
                )
            
            # Create charts
            overview_fig = self.create_overview_chart(df)
            trend_fig = self.create_trend_chart(df)
            detailed_fig = self.create_detailed_chart(df)
            distribution_fig = self.create_distribution_chart(df)
            heatmap_fig = self.create_heatmap_chart(df)
            
            # Data table
            data_table = self.create_data_table(df)
            
            return (
                status_msg, status_color, kpi_cards,
                overview_fig, trend_fig, detailed_fig, distribution_fig, heatmap_fig,
                data_table
            )
    
    def create_overview_chart(self, df):
        """Create overview chart"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                fig = px.line(df.head(50), y=col, title=f"{col.title()} Over Time")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
            else:
                categorical_cols = df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    col = categorical_cols[0]
                    value_counts = df[col].value_counts()
                    fig = px.bar(x=value_counts.index, y=value_counts.values, 
                               title=f"Distribution of {col.title()}")
                    fig.update_layout(template="plotly_dark", height=400)
                    return fig
        except Exception as e:
            logger.error(f"Error creating overview chart: {str(e)}")
        
        return go.Figure()
    
    def create_trend_chart(self, df):
        """Create trend chart"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                fig = px.scatter(df.head(100), x=numeric_cols[0], y=numeric_cols[1],
                               title=f"{numeric_cols[0].title()} vs {numeric_cols[1].title()}")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception as e:
            logger.error(f"Error creating trend chart: {str(e)}")
        
        return go.Figure()
    
    def create_detailed_chart(self, df):
        """Create detailed analytics chart"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                col = numeric_cols[0]
                fig = px.histogram(df, x=col, title=f"Distribution of {col.title()}")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception as e:
            logger.error(f"Error creating detailed chart: {str(e)}")
        
        return go.Figure()
    
    def create_distribution_chart(self, df):
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
        except Exception as e:
            logger.error(f"Error creating distribution chart: {str(e)}")
        
        return go.Figure()
    
    def create_heatmap_chart(self, df):
        """Create heatmap chart"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) >= 2:
                corr_matrix = df[numeric_cols].corr()
                fig = px.imshow(corr_matrix, text_auto=True, aspect="auto",
                              title="Correlation Heatmap")
                fig.update_layout(template="plotly_dark", height=400)
                return fig
        except Exception as e:
            logger.error(f"Error creating heatmap chart: {str(e)}")
        
        return go.Figure()
    
    def create_data_table(self, df):
        """Create data table"""
        try:
            # Show last 10 records
            recent_data = df.tail(10)
            
            if recent_data.empty:
                return html.P("No data available", className="text-muted")
            
            # Create table
            table_header = [html.Thead([html.Tr([html.Th(col) for col in recent_data.columns])])]
            table_rows = []
            
            for _, row in recent_data.iterrows():
                table_rows.append(html.Tr([html.Td(str(val)) for val in row]))
            
            table_body = [html.Tbody(table_rows)]
            
            return dbc.Table(
                table_header + table_body,
                bordered=True,
                dark=True,
                hover=True,
                responsive=True,
                striped=True,
                className="mt-3"
            )
            
        except Exception as e:
            logger.error(f"Error creating data table: {str(e)}")
            return html.P("Error displaying data table", className="text-danger")
    
    def run(self, host='0.0.0.0', port=8000):
        """Run the dashboard application"""
        # Start WebSocket client
        self.start_websocket_client()
        
        # Run Dash app
        self.app.run_server(
            host=host,
            port=port,
            debug=False,
            dev_tools_hot_reload=False
        )

if __name__ == '__main__':
    dashboard = DashboardApp()
    dashboard.run()
