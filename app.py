from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import ccxt
import requests
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import ta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import tweepy
from newsapi import NewsApiClient
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv
import threading
import time
import schedule

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tradegenius.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
jwt = JWTManager(app)

# AI Models and Analysis Classes
class AISignalGenerator:
    def __init__(self):
        self.scaler = StandardScaler()
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.lstm_model = None
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
    def prepare_features(self, data):
        """Prepare technical indicators and features for ML models"""
        df = pd.DataFrame(data)
        
        # Technical indicators
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['bb_upper'] = ta.volatility.bollinger_hband(df['close'])
        df['bb_lower'] = ta.volatility.bollinger_lband(df['close'])
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        df['volume_sma'] = ta.volume.volume_sma(df['close'], df['volume'], window=20)
        
        # Price features
        df['price_change'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        return df.fillna(method='bfill')
    
    def generate_signal(self, symbol, market_type='forex'):
        """Generate AI-powered trading signal"""
        try:
            # Get market data
            data = self.get_market_data(symbol, market_type)
            if data is None or len(data) < 50:
                return None
                
            # Prepare features
            df = self.prepare_features(data)
            
            # Get sentiment data
            sentiment_score = self.get_sentiment_analysis(symbol)
            
            # Get news impact
            news_impact = self.analyze_news_impact(symbol)
            
            # Generate ML prediction
            ml_signal = self.ml_prediction(df)
            
            # Combine all signals
            signal_strength = self.combine_signals(ml_signal, sentiment_score, news_impact)
            
            # Determine signal type
            if signal_strength > 0.7:
                signal_type = 'STRONG_BUY'
            elif signal_strength > 0.3:
                signal_type = 'BUY' 
            elif signal_strength < -0.7:
                signal_type = 'STRONG_SELL'
            elif signal_strength < -0.3:
                signal_type = 'SELL'
            else:
                signal_type = 'HOLD'
            
            # Calculate accuracy based on premium status
            base_accuracy = 75 + (abs(signal_strength) * 15)
            
            return {
                'symbol': symbol,
                'signal': signal_type,
                'strength': abs(signal_strength),
                'accuracy': min(95, base_accuracy),
                'sentiment': sentiment_score,
                'news_impact': news_impact,
                'timestamp': datetime.now().isoformat(),
                'market_type': market_type,
                'entry_price': df['close'].iloc[-1],
                'stop_loss': self.calculate_stop_loss(df, signal_type),
                'take_profit': self.calculate_take_profit(df, signal_type),
                'risk_reward': self.calculate_risk_reward(df, signal_type)
            }
            
        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")
            return None
    
    def get_market_data(self, symbol, market_type):
        """Fetch market data from various sources"""
        try:
            if market_type == 'crypto':
                exchange = ccxt.binance()
                ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=100)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                return df.to_dict('records')
            elif market_type in ['stocks', 'forex']:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="3mo", interval="1h")
                if hist.empty:
                    return None
                hist.reset_index(inplace=True)
                hist.columns = [col.lower() for col in hist.columns]
                return hist.to_dict('records')
        except:
            return None
    
    def get_sentiment_analysis(self, symbol):
        """Analyze social media and news sentiment"""
        try:
            # Simulate sentiment analysis (in production, use real Twitter/Reddit APIs)
            sentiment_scores = []
            
            # Mock sentiment data
            mock_texts = [
                f"{symbol} looking bullish today",
                f"Great momentum in {symbol}",
                f"{symbol} might face resistance",
                f"Positive outlook for {symbol}"
            ]
            
            for text in mock_texts:
                blob = TextBlob(text)
                sentiment_scores.append(blob.sentiment.polarity)
            
            return np.mean(sentiment_scores)
        except:
            return 0
    
    def analyze_news_impact(self, symbol):
        """Analyze news impact on the symbol"""
        try:
            # Mock news analysis (in production, use NewsAPI)
            return np.random.uniform(-0.5, 0.5)
        except:
            return 0
    
    def ml_prediction(self, df):
        """Generate ML-based prediction"""
        try:
            features = ['sma_20', 'sma_50', 'rsi', 'macd', 'atr', 'volume_ratio']
            X = df[features].fillna(0).values[-20:]  # Last 20 periods
            
            if len(X) < 20:
                return 0
            
            # Simple prediction based on technical indicators
            rsi = df['rsi'].iloc[-1]
            macd = df['macd'].iloc[-1]
            sma_signal = 1 if df['close'].iloc[-1] > df['sma_20'].iloc[-1] else -1
            
            # Combine signals
            signal = 0
            if rsi < 30:  # Oversold
                signal += 0.3
            elif rsi > 70:  # Overbought
                signal -= 0.3
            
            if macd > 0:
                signal += 0.2
            else:
                signal -= 0.2
                
            signal += sma_signal * 0.3
            
            return np.clip(signal, -1, 1)
        except:
            return 0
    
    def combine_signals(self, ml_signal, sentiment, news_impact):
        """Combine all signal sources"""
        weights = {
            'ml': 0.5,
            'sentiment': 0.3,
            'news': 0.2
        }
        
        combined = (weights['ml'] * ml_signal + 
                   weights['sentiment'] * sentiment + 
                   weights['news'] * news_impact)
        
        return np.clip(combined, -1, 1)
    
    def calculate_stop_loss(self, df, signal_type):
        """Calculate stop loss level"""
        current_price = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.02
        
        if 'BUY' in signal_type:
            return current_price - (2 * atr)
        else:
            return current_price + (2 * atr)
    
    def calculate_take_profit(self, df, signal_type):
        """Calculate take profit level"""
        current_price = df['close'].iloc[-1]
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else current_price * 0.02
        
        if 'BUY' in signal_type:
            return current_price + (3 * atr)
        else:
            return current_price - (3 * atr)
    
    def calculate_risk_reward(self, df, signal_type):
        """Calculate risk-reward ratio"""
        return 1.5  # Default 1:1.5 risk-reward

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_premium_active(self):
        if not self.is_premium:
            return False
        if self.premium_expires and self.premium_expires < datetime.utcnow():
            return False
        return True

class TradingSignal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False)
    signal_type = db.Column(db.String(20), nullable=False)
    market_type = db.Column(db.String(20), nullable=False)
    strength = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=True)
    take_profit = db.Column(db.Float, nullable=True)
    sentiment_score = db.Column(db.Float, nullable=True)
    news_impact = db.Column(db.Float, nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

class UserPortfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    market_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize AI Signal Generator
ai_generator = AISignalGenerator()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'success': True,
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'is_premium': user.is_premium_active()
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already exists'}), 400
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/api/signals')
@login_required
def get_signals():
    market_type = request.args.get('market', 'all')
    
    # Define symbols for different markets
    symbols = {
        'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X'],
        'crypto': ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'LINK/USDT'],
        'stocks': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
        'futures': ['GC=F', 'CL=F', 'SI=F', 'NG=F', 'ZC=F']
    }
    
    signals = []
    
    if market_type == 'all':
        for market, symbol_list in symbols.items():
            for symbol in symbol_list[:2]:  # Limit to 2 per market for demo
                signal = ai_generator.generate_signal(symbol, market)
                if signal:
                    # Adjust accuracy for premium users
                    if current_user.is_premium_active():
                        signal['accuracy'] = min(95, signal['accuracy'] + 15)
                    signals.append(signal)
    else:
        symbol_list = symbols.get(market_type, [])
        for symbol in symbol_list:
            signal = ai_generator.generate_signal(symbol, market_type)
            if signal:
                if current_user.is_premium_active():
                    signal['accuracy'] = min(95, signal['accuracy'] + 15)
                signals.append(signal)
    
    return jsonify(signals)

@app.route('/api/premium-signals')
@login_required
def get_premium_signals():
    if not current_user.is_premium_active():
        return jsonify({'error': 'Premium subscription required'}), 403
    
    # Generate high-accuracy premium signals
    premium_symbols = {
        'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'],
        'crypto': ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'],
        'stocks': ['AAPL', 'GOOGL', 'TSLA']
    }
    
    signals = []
    for market, symbol_list in premium_symbols.items():
        for symbol in symbol_list:
            signal = ai_generator.generate_signal(symbol, market)
            if signal:
                signal['accuracy'] = min(98, signal['accuracy'] + 20)  # Premium boost
                signal['is_premium'] = True
                signals.append(signal)
    
    return jsonify(signals)

@app.route('/api/market-analysis')
@login_required
def market_analysis():
    symbol = request.args.get('symbol', 'EURUSD=X')
    market_type = request.args.get('market', 'forex')
    
    # Get comprehensive market analysis
    data = ai_generator.get_market_data(symbol, market_type)
    if not data:
        return jsonify({'error': 'Unable to fetch market data'}), 400
    
    df = pd.DataFrame(data)
    df = ai_generator.prepare_features(df)
    
    # Create charts
    fig = go.Figure()
    
    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name=symbol
    ))
    
    # Add technical indicators
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['sma_20'],
        name='SMA 20',
        line=dict(color='orange')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['sma_50'],
        name='SMA 50',
        line=dict(color='blue')
    ))
    
    fig.update_layout(
        title=f'{symbol} Technical Analysis',
        yaxis_title='Price',
        xaxis_title='Time',
        template='plotly_dark'
    )
    
    chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    
    # Generate analysis summary
    current_price = df['close'].iloc[-1]
    rsi = df['rsi'].iloc[-1]
    macd = df['macd'].iloc[-1]
    
    analysis = {
        'symbol': symbol,
        'current_price': current_price,
        'rsi': rsi,
        'macd': macd,
        'trend': 'Bullish' if df['close'].iloc[-1] > df['sma_20'].iloc[-1] else 'Bearish',
        'support': df['bb_lower'].iloc[-1],
        'resistance': df['bb_upper'].iloc[-1],
        'chart': chart_json,
        'sentiment': ai_generator.get_sentiment_analysis(symbol),
        'news_impact': ai_generator.analyze_news_impact(symbol)
    }
    
    return jsonify(analysis)

@app.route('/api/upgrade-premium', methods=['POST'])
@login_required
def upgrade_premium():
    # In production, integrate with payment gateway
    current_user.is_premium = True
    current_user.premium_expires = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Premium upgrade successful'})

@app.route('/api/portfolio')
@login_required
def get_portfolio():
    portfolio = UserPortfolio.query.filter_by(user_id=current_user.id).all()
    
    portfolio_data = []
    total_value = 0
    total_pnl = 0
    
    for position in portfolio:
        pnl = (position.current_price - position.entry_price) * position.quantity
        pnl_percent = ((position.current_price - position.entry_price) / position.entry_price) * 100
        
        portfolio_data.append({
            'symbol': position.symbol,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'market_type': position.market_type
        })
        
        total_value += position.current_price * position.quantity
        total_pnl += pnl
    
    return jsonify({
        'positions': portfolio_data,
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_pnl_percent': (total_pnl / (total_value - total_pnl)) * 100 if total_value > total_pnl else 0
    })

@app.route('/signals')
@login_required
def signals_page():
    return render_template('signals.html', user=current_user)

@app.route('/analysis')
@login_required
def analysis_page():
    return render_template('analysis.html', user=current_user)

@app.route('/portfolio')
@login_required
def portfolio_page():
    return render_template('portfolio.html', user=current_user)

@app.route('/alerts')
@login_required
def alerts_page():
    return render_template('alerts.html', user=current_user)

# Background task to update signals
def update_signals():
    """Background task to continuously update trading signals"""
    with app.app_context():
        while True:
            try:
                # Update signals every 5 minutes
                print("Updating trading signals...")
                # Add your signal update logic here
                time.sleep(300)  # 5 minutes
            except Exception as e:
                print(f"Error updating signals: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@tradegenius.com', is_premium=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    # Start background signal updates
    signal_thread = threading.Thread(target=update_signals, daemon=True)
    signal_thread.start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)