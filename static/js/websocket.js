// WebSocket Client for Real-Time Data Dashboard

class DashboardWebSocket {
    constructor() {
        this.socket = null;
        this.connectionStatus = null;
        this.retryAttempts = 0;
        this.maxRetries = 5;
        this.retryDelay = 2000;
        this.isConnected = false;
        
        this.initialize();
    }
    
    initialize() {
        // Get connection status element
        this.connectionStatus = document.getElementById('connectionStatus');
        
        // Connect to WebSocket
        this.connect();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    connect() {
        try {
            // Initialize Socket.IO client
            this.socket = io('http://localhost:5000', {
                autoConnect: true,
                reconnection: true,
                reconnectionAttempts: this.maxRetries,
                reconnectionDelay: this.retryDelay,
                timeout: 10000
            });
            
            this.setupSocketEvents();
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('error', 'Failed to connect to WebSocket server');
        }
    }
    
    setupSocketEvents() {
        // Connection successful
        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            this.isConnected = true;
            this.retryAttempts = 0;
            this.updateConnectionStatus('success', 'Connected to real-time data stream');
            
            // Request current data
            this.socket.emit('request_data');
        });
        
        // Connection error
        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.isConnected = false;
            this.updateConnectionStatus('error', 'Connection failed - retrying...');
        });
        
        // Disconnection
        this.socket.on('disconnect', (reason) => {
            console.log('Disconnected from WebSocket server:', reason);
            this.isConnected = false;
            this.updateConnectionStatus('warning', 'Disconnected from server');
        });
        
        // Reconnection attempt
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnection attempt ${attemptNumber}`);
            this.updateConnectionStatus('info', `Reconnecting... (attempt ${attemptNumber})`);
        });
        
        // Successful reconnection
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`Reconnected after ${attemptNumber} attempts`);
            this.isConnected = true;
            this.updateConnectionStatus('success', 'Reconnected to real-time data stream');
        });
        
        // Failed to reconnect
        this.socket.on('reconnect_failed', () => {
            console.error('Failed to reconnect to WebSocket server');
            this.isConnected = false;
            this.updateConnectionStatus('error', 'Could not reconnect to server');
        });
        
        // New data received
        this.socket.on('new_data', (data) => {
            console.log('Received new data:', data);
            this.handleNewData(data);
        });
        
        // Custom events
        this.socket.on('data_update', (data) => {
            console.log('Data update received:', data);
            this.handleDataUpdate(data);
        });
        
        this.socket.on('status_update', (status) => {
            console.log('Status update:', status);
            this.handleStatusUpdate(status);
        });
    }
    
    setupEventListeners() {
        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && !this.isConnected) {
                console.log('Page became visible, attempting to reconnect...');
                this.reconnect();
            }
        });
        
        // Window focus/blur
        window.addEventListener('focus', () => {
            if (!this.isConnected) {
                this.reconnect();
            }
        });
        
        // Before page unload
        window.addEventListener('beforeunload', () => {
            if (this.socket) {
                this.socket.disconnect();
            }
        });
    }
    
    updateConnectionStatus(type, message) {
        if (!this.connectionStatus) return;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            loading: 'fas fa-spinner fa-spin'
        };
        
        const colorMap = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info',
            loading: 'alert-info'
        };
        
        this.connectionStatus.className = `alert ${colorMap[type] || 'alert-info'}`;
        this.connectionStatus.innerHTML = `
            <i class="${iconMap[type] || 'fas fa-info-circle'} me-2"></i>
            ${message}
        `;
    }
    
    handleNewData(data) {
        // Dispatch custom event for other components to listen to
        const event = new CustomEvent('websocket-data', {
            detail: {
                data: data.data || [],
                source: data.source || 'unknown',
                timestamp: data.timestamp || Date.now(),
                filename: data.filename || null
            }
        });
        
        document.dispatchEvent(event);
        
        // Update UI elements
        this.updateDataInfo(data);
        
        // Add to recent activity if on main page
        if (typeof addActivityItem === 'function') {
            const recordCount = Array.isArray(data.data) ? data.data.length : 0;
            addActivityItem(
                `New data received`,
                `${recordCount} records from ${data.source || 'unknown source'}`
            );
        }
    }
    
    handleDataUpdate(data) {
        console.log('Handling data update:', data);
        
        // Dispatch custom event
        const event = new CustomEvent('websocket-update', {
            detail: data
        });
        
        document.dispatchEvent(event);
    }
    
    handleStatusUpdate(status) {
        console.log('Handling status update:', status);
        
        if (status.type && status.message) {
            this.updateConnectionStatus(status.type, status.message);
        }
        
        // Dispatch custom event
        const event = new CustomEvent('websocket-status', {
            detail: status
        });
        
        document.dispatchEvent(event);
    }
    
    updateDataInfo(data) {
        // Update any data info displays on the page
        const dataInfoElements = document.querySelectorAll('[data-websocket-info]');
        
        dataInfoElements.forEach(element => {
            const infoType = element.getAttribute('data-websocket-info');
            
            switch (infoType) {
                case 'record-count':
                    element.textContent = Array.isArray(data.data) ? data.data.length : 0;
                    break;
                case 'last-update':
                    element.textContent = new Date().toLocaleTimeString();
                    break;
                case 'source':
                    element.textContent = data.source || 'Unknown';
                    break;
            }
        });
    }
    
    // Public methods
    reconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
        
        setTimeout(() => {
            this.connect();
        }, 1000);
    }
    
    sendMessage(event, data) {
        if (this.socket && this.isConnected) {
            this.socket.emit(event, data);
            return true;
        } else {
            console.warn('Cannot send message: WebSocket not connected');
            return false;
        }
    }
    
    requestData() {
        return this.sendMessage('request_data');
    }
    
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            socket: this.socket ? this.socket.connected : false
        };
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
    }
}

// Initialize WebSocket connection when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're not on the dashboard page
    // (dashboard has its own WebSocket handling)
    if (!window.location.href.includes(':8000')) {
        window.dashboardWebSocket = new DashboardWebSocket();
        
        // Make it globally available
        window.wsConnect = () => window.dashboardWebSocket.connect();
        window.wsDisconnect = () => window.dashboardWebSocket.disconnect();
        window.wsReconnect = () => window.dashboardWebSocket.reconnect();
        window.wsStatus = () => window.dashboardWebSocket.getConnectionStatus();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardWebSocket;
}
