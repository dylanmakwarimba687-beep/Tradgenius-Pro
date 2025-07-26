#!/usr/bin/env python3
"""
TradeGenius Pro® - Production Startup Script
Copyright 2024 - All Rights Reserved

This script initializes and runs the TradeGenius Pro trading platform
with proper configuration, logging, and error handling.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Configure logging for the application"""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'tradegenius_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please copy .env.example to .env and configure the required variables.")
        return False
    
    return True

def check_dependencies():
    """Check if all required Python packages are installed"""
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'pandas',
        'numpy',
        'yfinance',
        'ccxt',
        'textblob',
        'scikit-learn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required Python packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Please run: pip install -r requirements.txt")
        return False
    
    return True

def initialize_database():
    """Initialize the database with required tables"""
    try:
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Check if admin user exists, create if not
            from app import User
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@tradegeniuspro.com',
                    is_premium=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created (admin/admin123)")
            
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def display_banner():
    """Display the application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ████████╗██████╗  █████╗ ██████╗ ███████╗ ██████╗ ███████╗███╗   ██╗██╗██╗  ║
║  ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝ ██╔════╝████╗  ██║██║██║  ║
║     ██║   ██████╔╝███████║██║  ██║█████╗  ██║  ███╗█████╗  ██╔██╗ ██║██║██║  ║
║     ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝  ██║   ██║██╔══╝  ██║╚██╗██║██║██║  ║
║     ██║   ██║  ██║██║  ██║██████╔╝███████╗╚██████╔╝███████╗██║ ╚████║██║██║  ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ║
║                                                                              ║
║                           ██████╗ ██████╗  ██████╗ ®                        ║
║                           ██╔══██╗██╔══██╗██╔═══██╗                         ║
║                           ██████╔╝██████╔╝██║   ██║                         ║
║                           ██╔═══╝ ██╔══██╗██║   ██║                         ║
║                           ██║     ██║  ██║╚██████╔╝                         ║
║                           ╚═╝     ╚═╝  ╚═╝ ╚═════╝                          ║
║                                                                              ║
║                      AI-Powered Trading Signals Platform                     ║
║                         © 2024 - All Rights Reserved                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def main():
    """Main application entry point"""
    # Display banner
    display_banner()
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting TradeGenius Pro platform...")
    
    # Load environment variables
    env_file = project_root / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
        logger.info("Environment variables loaded from .env file")
    else:
        logger.warning("No .env file found, using system environment variables")
    
    # Check environment
    print("🔍 Checking environment...")
    if not check_environment():
        sys.exit(1)
    print("✅ Environment check passed")
    
    # Check dependencies
    print("📦 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Dependencies check passed")
    
    # Initialize database
    print("🗄️  Initializing database...")
    if not initialize_database():
        sys.exit(1)
    print("✅ Database initialized")
    
    # Import and run the Flask app
    try:
        from app import app
        
        # Configuration
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        
        print(f"\n🚀 Starting TradeGenius Pro on http://{host}:{port}")
        print(f"🔧 Debug mode: {'ON' if debug else 'OFF'}")
        print(f"📊 Demo account: admin / admin123")
        print(f"💎 Premium features enabled for demo account")
        print("\n" + "="*80)
        
        logger.info(f"Application starting on {host}:{port}")
        
        # Start the Flask application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application shutdown requested by user")
        print("\n\n👋 TradeGenius Pro shutdown complete. Thank you for using our platform!")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"\n❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()