"""
AI Assistant Hub - Main Gateway (Refactored & Enhanced)
Professional structure following Generative AI template
Version: 2.1.0
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import sys
from pathlib import Path
from datetime import datetime
import psutil

# Add project root to path (go up 2 levels: hub-gateway -> services -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.model_config import HubConfig
from config.logging_config import setup_logging
from handlers.error_handler import (
    HubException, 
    handle_hub_exception, 
    handle_generic_exception,
    error_handler
)
from utils.rate_limiter import rate_limit

# Version Information
__version__ = "2.1.0"
__updated__ = "2025-12-18"

# Initialize Flask app
app = Flask(__name__, template_folder='../templates')
app.config.from_object(HubConfig)

# CORS Configuration with better control
CORS(app, 
     origins=HubConfig.CORS_ORIGINS,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Length", "X-JSON"],
     supports_credentials=True)

# Setup logging
logger = setup_logging(
    log_level=HubConfig.LOG_LEVEL,
    log_file=HubConfig.LOG_FILE
)

# Register error handlers
app.register_error_handler(HubException, handle_hub_exception)
app.register_error_handler(Exception, handle_generic_exception)

# Track startup time
startup_time = datetime.now()


@app.route('/')
@error_handler
def index():
    """Home page - Gateway dashboard"""
    logger.info("Serving hub gateway homepage")
    services = HubConfig.get_all_services()
    
    # Convert ServiceConfig objects to dicts for template
    services_dict = {
        key: {
            'name': service.name,
            'description': service.description,
            'icon': service.icon,
            'port': service.port,
            'url': service.url,
            'color': service.color,
            'features': service.features,
            'status': 'available'
        }
        for key, service in services.items()
    }
    
    return render_template('index.html', services=services_dict)


@app.route('/api/services')
@error_handler
@rate_limit(max_requests=100, window_seconds=60)
def get_services():
    """Get all services information"""
    logger.debug("API request: get_services")
    services = HubConfig.get_all_services()
    
    services_dict = {
        key: {
            'name': service.name,
            'description': service.description,
            'icon': service.icon,
            'port': service.port,
            'url': service.url,
            'features': service.features
        }
        for key, service in services.items()
    }
    
    return jsonify(services_dict)


@app.route('/api/services/<service_name>')
@error_handler
@rate_limit(max_requests=200, window_seconds=60)
def get_service(service_name):
    """Get specific service information"""
    logger.debug(f"API request: get_service - {service_name}")
    service = HubConfig.get_service_config(service_name)
    
    if not service:
        raise HubException(
            f"Service '{service_name}' not found",
            status_code=404
        )
    
    return jsonify({
        'name': service.name,
        'description': service.description,
        'icon': service.icon,
        'port': service.port,
        'url': service.url,
        'features': service.features
    })


@app.route('/api/health')
@error_handler
def health_check():
    """Enhanced health check endpoint with system metrics"""
    logger.debug("Health check requested")
    services = HubConfig.get_all_services()
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = (datetime.now() - startup_time).total_seconds()
    
    return jsonify({
        'status': 'healthy',
        'version': __version__,
        'updated': __updated__,
        'services_count': len(services),
        'services': list(services.keys()),
        'message': 'AI Assistant Hub is running smoothly',
        'uptime_seconds': round(uptime, 2),
        'system_metrics': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_mb': round(memory.available / 1024 / 1024, 2),
            'disk_percent': disk.percent,
            'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/stats')
@error_handler
def get_stats():
    """Get hub statistics and metrics"""
    services = HubConfig.get_all_services()
    uptime = (datetime.now() - startup_time).total_seconds()
    
    return jsonify({
        'total_services': len(services),
        'services_list': list(services.keys()),
        'cache_enabled': HubConfig.ENABLE_CACHE,
        'debug_mode': HubConfig.DEBUG,
        'version': __version__,
        'uptime_hours': round(uptime / 3600, 2),
        'host': HubConfig.HOST,
        'port': HubConfig.PORT,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/version')
@error_handler
def get_version():
    """Get version information"""
    return jsonify({
        'version': __version__,
        'updated': __updated__,
        'python_version': sys.version.split()[0],
        'flask_version': 'Latest'
    })


@app.route('/api/system')
@error_handler
def get_system_info():
    """Get detailed system information"""
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return jsonify({
        'cpu': {
            'count': cpu_count,
            'percent': psutil.cpu_percent(interval=0.1),
            'freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else None
        },
        'memory': {
            'total_gb': round(memory.total / 1024 / 1024 / 1024, 2),
            'available_gb': round(memory.available / 1024 / 1024 / 1024, 2),
            'percent_used': memory.percent
        },
        'disk': {
            'total_gb': round(disk.total / 1024 / 1024 / 1024, 2),
            'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
            'percent_used': disk.percent
        },
        'timestamp': datetime.now().isoformat()
    })


def print_banner():
    """Print enhanced startup banner"""
    services = HubConfig.get_all_services()
    
    print("\n" + "=" * 80)
    print("🚀 AI ASSISTANT HUB - MAIN GATEWAY v" + __version__)
    print("=" * 80)
    print(f"📅 Version Updated: {__updated__}")
    print(f"📍 Hub URL: http://{HubConfig.HOST}:{HubConfig.PORT}")
    print(f"🐛 Debug Mode: {HubConfig.DEBUG}")
    print(f"📊 Log Level: {HubConfig.LOG_LEVEL}")
    print(f"🔐 CORS Origins: {HubConfig.CORS_ORIGINS}")
    print(f"⏰ Started at: {startup_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "-" * 80)
    print(f"📦 Available Services ({len(services)}):")
    for key, service in services.items():
        print(f"   {service.icon} {service.name:25s} → {service.url:30s} [Port {service.port}]")
    print("\n" + "-" * 80)
    print("🔗 API Endpoints:")
    print("   📍 GET  /                    → Hub Dashboard (Web UI)")
    print("   📍 GET  /api/health          → Health Check with Metrics")
    print("   📍 GET  /api/services        → List All Services")
    print("   📍 GET  /api/services/<name> → Get Service Details")
    print("   📍 GET  /api/stats           → Hub Statistics")
    print("   📍 GET  /api/version         → Version Information")
    print("   📍 GET  /api/system          → System Information")
    print("\n" + "-" * 80)
    print("💡 Important Notes:")
    print("   • Each service runs independently on its designated port")
    print("   • Check service README for startup instructions")
    print("   • Use 'scripts/start-all.bat' to launch all services")
    print("   • Use 'scripts/stop-all.bat' to stop all services")
    print("   • Access the web dashboard at http://localhost:3000")
    print("=" * 80 + "\n")
    logger.info(f"AI Assistant Hub v{__version__} started successfully")


if __name__ == '__main__':
    print_banner()
    app.run(
        debug=HubConfig.DEBUG,
        host=HubConfig.HOST,
        port=HubConfig.PORT
    )
