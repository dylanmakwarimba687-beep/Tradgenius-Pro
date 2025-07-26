// TradeGenius Pro - Main JavaScript
// Copyright 2024 - All Rights Reserved

'use strict';

// Global Configuration
const CONFIG = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 30000, // 30 seconds
    CHART_UPDATE_INTERVAL: 60000, // 1 minute
    PREMIUM_ACCURACY_BOOST: 15,
    MAX_SIGNALS_FREE: 10,
    MAX_SIGNALS_PREMIUM: 50
};

// Global State Management
class AppState {
    constructor() {
        this.user = null;
        this.signals = [];
        this.selectedMarket = 'all';
        this.isLoading = false;
        this.lastUpdate = null;
        this.websocket = null;
        this.notifications = [];
    }
    
    setUser(user) {
        this.user = user;
        this.saveToStorage('user', user);
    }
    
    getUser() {
        if (!this.user) {
            this.user = this.loadFromStorage('user');
        }
        return this.user;
    }
    
    saveToStorage(key, data) {
        try {
            localStorage.setItem(`tradegenius_${key}`, JSON.stringify(data));
        } catch (e) {
            console.warn('Failed to save to localStorage:', e);
        }
    }
    
    loadFromStorage(key) {
        try {
            const data = localStorage.getItem(`tradegenius_${key}`);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.warn('Failed to load from localStorage:', e);
            return null;
        }
    }
    
    clearStorage() {
        Object.keys(localStorage).forEach(key => {
            if (key.startsWith('tradegenius_')) {
                localStorage.removeItem(key);
            }
        });
    }
}

// Initialize global state
const appState = new AppState();

// API Service
class APIService {
    static async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const token = localStorage.getItem('access_token');
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Token expired, redirect to login
                    window.location.href = '/login';
                    return;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    static async getSignals(market = 'all') {
        return this.request(`/signals?market=${market}`);
    }
    
    static async getPremiumSignals() {
        return this.request('/premium-signals');
    }
    
    static async getMarketAnalysis(symbol, market) {
        return this.request(`/market-analysis?symbol=${symbol}&market=${market}`);
    }
    
    static async getPortfolio() {
        return this.request('/portfolio');
    }
    
    static async upgradeToPremium() {
        return this.request('/upgrade-premium', { method: 'POST' });
    }
}

// Signal Manager
class SignalManager {
    constructor() {
        this.signals = [];
        this.filters = {
            market: 'all',
            accuracy: 0,
            signalType: 'all'
        };
    }
    
    async loadSignals() {
        try {
            appState.isLoading = true;
            this.updateLoadingState(true);
            
            const user = appState.getUser();
            let signals;
            
            if (user && user.is_premium) {
                signals = await APIService.getPremiumSignals();
            } else {
                signals = await APIService.getSignals(this.filters.market);
            }
            
            this.signals = signals || [];
            this.renderSignals();
            appState.lastUpdate = new Date();
            
        } catch (error) {
            console.error('Failed to load signals:', error);
            this.showError('Failed to load signals. Please try again.');
        } finally {
            appState.isLoading = false;
            this.updateLoadingState(false);
        }
    }
    
    renderSignals() {
        const container = document.getElementById('signalsContainer');
        if (!container) return;
        
        if (this.signals.length === 0) {
            container.innerHTML = this.getEmptyState();
            return;
        }
        
        const filteredSignals = this.filterSignals();
        const signalsHTML = filteredSignals.map(signal => this.createSignalCard(signal)).join('');
        
        container.innerHTML = signalsHTML;
        this.attachSignalEventListeners();
    }
    
    filterSignals() {
        return this.signals.filter(signal => {
            if (this.filters.market !== 'all' && signal.market_type !== this.filters.market) {
                return false;
            }
            
            if (signal.accuracy < this.filters.accuracy) {
                return false;
            }
            
            if (this.filters.signalType !== 'all') {
                const signalType = signal.signal.toLowerCase();
                if (this.filters.signalType === 'buy' && !signalType.includes('buy')) {
                    return false;
                }
                if (this.filters.signalType === 'sell' && !signalType.includes('sell')) {
                    return false;
                }
            }
            
            return true;
        });
    }
    
    createSignalCard(signal) {
        const signalClass = this.getSignalClass(signal.signal);
        const signalColor = this.getSignalColor(signal.signal);
        const timeAgo = this.getTimeAgo(signal.timestamp);
        const isPremium = signal.is_premium || false;
        
        return `
            <div class="signal-card ${signalClass} card mb-3" data-signal-id="${signal.symbol}">
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <div class="d-flex align-items-center">
                                <div class="signal-icon me-3">
                                    <i class="fas fa-${this.getMarketIcon(signal.market_type)} fa-2x text-${signalColor}"></i>
                                </div>
                                <div>
                                    <h5 class="mb-0 fw-bold">${signal.symbol}</h5>
                                    <small class="text-muted text-uppercase">${signal.market_type}</small>
                                    ${isPremium ? '<span class="badge bg-warning text-dark ms-2">PREMIUM</span>' : ''}
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-2">
                            <span class="badge bg-${signalColor} fs-6 px-3 py-2">${signal.signal}</span>
                        </div>
                        
                        <div class="col-md-2 text-center">
                            <div class="accuracy-display">
                                <div class="h5 mb-0 text-${signalColor}">${signal.accuracy.toFixed(1)}%</div>
                                <small class="text-muted">Accuracy</small>
                            </div>
                        </div>
                        
                        <div class="col-md-2 text-center">
                            <div class="price-display">
                                <div class="h6 mb-0">$${this.formatPrice(signal.entry_price)}</div>
                                <small class="text-muted">Entry Price</small>
                            </div>
                        </div>
                        
                        <div class="col-md-2 text-center">
                            <div class="target-display">
                                <div class="h6 mb-0 text-success">$${this.formatPrice(signal.take_profit)}</div>
                                <small class="text-muted">Target</small>
                            </div>
                        </div>
                        
                        <div class="col-md-1 text-center">
                            <small class="text-muted">${timeAgo}</small>
                            <div class="mt-1">
                                <button class="btn btn-sm btn-outline-primary" onclick="viewSignalDetails('${signal.symbol}')">
                                    <i class="fas fa-eye"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-12">
                            <div class="signal-metrics d-flex justify-content-between">
                                <div class="metric">
                                    <small class="text-muted">Sentiment:</small>
                                    <span class="badge bg-${this.getSentimentColor(signal.sentiment)} ms-1">
                                        ${this.getSentimentLabel(signal.sentiment)}
                                    </span>
                                </div>
                                <div class="metric">
                                    <small class="text-muted">Risk/Reward:</small>
                                    <span class="fw-bold ms-1">${signal.risk_reward}:1</span>
                                </div>
                                <div class="metric">
                                    <small class="text-muted">Stop Loss:</small>
                                    <span class="text-danger fw-bold ms-1">$${this.formatPrice(signal.stop_loss)}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getSignalClass(signal) {
        if (signal.toLowerCase().includes('buy')) return 'buy';
        if (signal.toLowerCase().includes('sell')) return 'sell';
        return 'hold';
    }
    
    getSignalColor(signal) {
        if (signal.toLowerCase().includes('buy')) return 'success';
        if (signal.toLowerCase().includes('sell')) return 'danger';
        return 'warning';
    }
    
    getMarketIcon(marketType) {
        const icons = {
            'forex': 'exchange-alt',
            'crypto': 'bitcoin',
            'stocks': 'chart-line',
            'futures': 'industry',
            'commodities': 'coins'
        };
        return icons[marketType] || 'chart-line';
    }
    
    getSentimentColor(sentiment) {
        if (sentiment > 0.3) return 'success';
        if (sentiment < -0.3) return 'danger';
        return 'warning';
    }
    
    getSentimentLabel(sentiment) {
        if (sentiment > 0.3) return 'Bullish';
        if (sentiment < -0.3) return 'Bearish';
        return 'Neutral';
    }
    
    formatPrice(price) {
        if (price >= 1000) {
            return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        }
        return price.toFixed(4);
    }
    
    getTimeAgo(timestamp) {
        const now = new Date();
        const signalTime = new Date(timestamp);
        const diffMs = now - signalTime;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    }
    
    getEmptyState() {
        return `
            <div class="text-center py-5">
                <i class="fas fa-chart-line fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No signals available</h5>
                <p class="text-muted">Try adjusting your filters or check back later.</p>
                <button class="btn btn-primary" onclick="signalManager.loadSignals()">
                    <i class="fas fa-refresh me-2"></i>Refresh
                </button>
            </div>
        `;
    }
    
    showError(message) {
        const container = document.getElementById('signalsContainer');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger text-center">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                    <button class="btn btn-outline-danger btn-sm ms-3" onclick="signalManager.loadSignals()">
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    updateLoadingState(isLoading) {
        const loadingElements = document.querySelectorAll('.loading-indicator');
        loadingElements.forEach(el => {
            el.style.display = isLoading ? 'block' : 'none';
        });
    }
    
    attachSignalEventListeners() {
        // Add click handlers for signal cards
        document.querySelectorAll('.signal-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('button')) {
                    const signalId = card.dataset.signalId;
                    this.showSignalModal(signalId);
                }
            });
        });
    }
    
    showSignalModal(signalId) {
        const signal = this.signals.find(s => s.symbol === signalId);
        if (!signal) return;
        
        // Create and show modal with signal details
        const modalHTML = this.createSignalModal(signal);
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        const modal = new bootstrap.Modal(document.getElementById('signalModal'));
        modal.show();
        
        // Remove modal from DOM when hidden
        document.getElementById('signalModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
    }
    
    createSignalModal(signal) {
        return `
            <div class="modal fade" id="signalModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-${this.getMarketIcon(signal.market_type)} me-2"></i>
                                ${signal.symbol} Signal Details
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>Signal Information</h6>
                                    <table class="table table-sm">
                                        <tr>
                                            <td>Signal Type:</td>
                                            <td><span class="badge bg-${this.getSignalColor(signal.signal)}">${signal.signal}</span></td>
                                        </tr>
                                        <tr>
                                            <td>Accuracy:</td>
                                            <td class="fw-bold">${signal.accuracy.toFixed(1)}%</td>
                                        </tr>
                                        <tr>
                                            <td>Entry Price:</td>
                                            <td class="fw-bold">$${this.formatPrice(signal.entry_price)}</td>
                                        </tr>
                                        <tr>
                                            <td>Take Profit:</td>
                                            <td class="text-success fw-bold">$${this.formatPrice(signal.take_profit)}</td>
                                        </tr>
                                        <tr>
                                            <td>Stop Loss:</td>
                                            <td class="text-danger fw-bold">$${this.formatPrice(signal.stop_loss)}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h6>Analysis</h6>
                                    <table class="table table-sm">
                                        <tr>
                                            <td>Sentiment:</td>
                                            <td><span class="badge bg-${this.getSentimentColor(signal.sentiment)}">${this.getSentimentLabel(signal.sentiment)}</span></td>
                                        </tr>
                                        <tr>
                                            <td>Risk/Reward:</td>
                                            <td class="fw-bold">${signal.risk_reward}:1</td>
                                        </tr>
                                        <tr>
                                            <td>Market:</td>
                                            <td class="text-uppercase">${signal.market_type}</td>
                                        </tr>
                                        <tr>
                                            <td>Generated:</td>
                                            <td>${this.getTimeAgo(signal.timestamp)}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="copySignal('${signal.symbol}')">
                                <i class="fas fa-copy me-2"></i>Copy Signal
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Chart Manager
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Price'
                    }
                }
            }
        };
    }
    
    createChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;
        
        const config = {
            type: 'line',
            data: data,
            options: { ...this.defaultOptions, ...options }
        };
        
        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        return chart;
    }
    
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }
    
    destroyChart(canvasId) {
        const chart = this.charts.get(canvasId);
        if (chart) {
            chart.destroy();
            this.charts.delete(canvasId);
        }
    }
}

// Notification Manager
class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }
    
    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.className = 'notification-container position-fixed top-0 end-0 p-3';
        this.container.style.zIndex = '9999';
        document.body.appendChild(this.container);
    }
    
    show(message, type = 'info', duration = 5000) {
        const notification = this.createNotification(message, type);
        this.container.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            this.remove(notification);
        }, duration);
        
        return notification;
    }
    
    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="notificationManager.remove(this.parentElement)"></button>
        `;
        
        // Add animation
        notification.style.transform = 'translateX(100%)';
        notification.style.transition = 'transform 0.3s ease';
        
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        return notification;
    }
    
    remove(notification) {
        if (notification && notification.parentElement) {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }
    }
    
    success(message) {
        return this.show(message, 'success');
    }
    
    error(message) {
        return this.show(message, 'danger');
    }
    
    warning(message) {
        return this.show(message, 'warning');
    }
    
    info(message) {
        return this.show(message, 'info');
    }
}

// Initialize managers
const signalManager = new SignalManager();
const chartManager = new ChartManager();
const notificationManager = new NotificationManager();

// Global Functions
function viewSignalDetails(symbol) {
    signalManager.showSignalModal(symbol);
}

function copySignal(symbol) {
    const signal = signalManager.signals.find(s => s.symbol === symbol);
    if (signal) {
        const signalText = `
${signal.symbol} - ${signal.signal}
Entry: $${signalManager.formatPrice(signal.entry_price)}
Target: $${signalManager.formatPrice(signal.take_profit)}
Stop Loss: $${signalManager.formatPrice(signal.stop_loss)}
Accuracy: ${signal.accuracy.toFixed(1)}%
        `.trim();
        
        navigator.clipboard.writeText(signalText).then(() => {
            notificationManager.success('Signal copied to clipboard!');
        }).catch(() => {
            notificationManager.error('Failed to copy signal');
        });
    }
}

function refreshDashboard() {
    signalManager.loadSignals();
    notificationManager.info('Dashboard refreshed');
}

// Auto-refresh functionality
function startAutoRefresh() {
    setInterval(() => {
        if (!document.hidden) {
            signalManager.loadSignals();
        }
    }, CONFIG.REFRESH_INTERVAL);
}

// Page visibility handling
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        // Page became visible, refresh data
        signalManager.loadSignals();
    }
});

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize signal manager
    if (document.getElementById('signalsContainer')) {
        signalManager.loadSignals();
        startAutoRefresh();
    }
    
    // Add market filter listeners
    document.querySelectorAll('input[name="marketFilter"]').forEach(radio => {
        radio.addEventListener('change', function() {
            signalManager.filters.market = this.value;
            signalManager.loadSignals();
        });
    });
    
    // Add accuracy filter listener
    const accuracyFilter = document.getElementById('accuracyFilter');
    if (accuracyFilter) {
        accuracyFilter.addEventListener('change', function() {
            signalManager.filters.accuracy = parseInt(this.value);
            signalManager.renderSignals();
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    notificationManager.error('An unexpected error occurred. Please refresh the page.');
});

// Unhandled promise rejection handling
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    notificationManager.error('A network error occurred. Please check your connection.');
});

// Export for global access
window.TradeGenius = {
    signalManager,
    chartManager,
    notificationManager,
    appState,
    APIService
};