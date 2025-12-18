# 🚀 AI Assistant Hub - Main Gateway

**Version**: 2.1.0  
**Updated**: 2025-12-18

## 📋 Overview

The AI Assistant Hub is the central gateway that provides a unified dashboard and API for accessing all AI services in the ecosystem. It serves as the main entry point for users to discover and navigate to various AI services.

## ✨ Features

- **Web Dashboard**: Beautiful, responsive UI for service discovery
- **RESTful API**: Complete API for service management and monitoring
- **Health Monitoring**: Real-time health checks with system metrics
- **Service Discovery**: Automatic service registration and listing
- **Rate Limiting**: Built-in request rate limiting for API endpoints
- **CORS Support**: Configurable cross-origin resource sharing
- **Error Handling**: Centralized error handling with detailed logging
- **System Metrics**: CPU, memory, and disk usage monitoring

## 🏗️ Architecture

```
hub-gateway/
├── hub.py                    # Main application entry point
├── handlers/
│   ├── error_handler.py      # Error handling & custom exceptions
│   └── __init__.py
├── utils/
│   ├── rate_limiter.py       # API rate limiting
│   ├── cache.py              # Response caching
│   ├── token_counter.py      # Token usage tracking
│   ├── google_drive_uploader.py
│   └── __init__.py
├── logs/                     # Application logs
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🚦 Getting Started

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- All dependencies from main project `requirements.txt`

### Installation

1. **Install dependencies** (from project root):
```bash
pip install -r requirements.txt
```

2. **Configure environment** (optional):
Create a `.env` file in the project root:
```env
# Hub Configuration
HUB_HOST=0.0.0.0
HUB_PORT=3000
DEBUG=True

# CORS Configuration
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

### Running the Hub

#### Method 1: Using the start script (Recommended)
```bash
# From project root
scripts\start-hub-gateway.bat
```

#### Method 2: Direct execution
```bash
# From hub-gateway directory
cd services/hub-gateway
python hub.py
```

#### Method 3: From project root
```bash
python services/hub-gateway/hub.py
```

## 🔌 API Endpoints

### Web Interface

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Hub dashboard (Web UI) |

### Service Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/services` | GET | List all available services |
| `/api/services/<name>` | GET | Get specific service details |

### Health & Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with system metrics |
| `/api/stats` | GET | Hub statistics and metrics |
| `/api/system` | GET | Detailed system information |
| `/api/version` | GET | Version information |

## 📊 API Examples

### Get All Services
```bash
curl http://localhost:3000/api/services
```

Response:
```json
{
  "chatbot": {
    "name": "AI ChatBot",
    "description": "Trợ lý AI thông minh với Gemini, GPT-3.5, DeepSeek",
    "icon": "🤖",
    "port": 5000,
    "url": "http://localhost:5000",
    "features": [...]
  },
  ...
}
```

### Health Check
```bash
curl http://localhost:3000/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "services_count": 3,
  "uptime_seconds": 3600.5,
  "system_metrics": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "memory_available_mb": 8192.5,
    "disk_percent": 65.3,
    "disk_free_gb": 150.2
  }
}
```

### Get System Info
```bash
curl http://localhost:3000/api/system
```

Response:
```json
{
  "cpu": {
    "count": 8,
    "percent": 12.5,
    "freq_mhz": 2400.0
  },
  "memory": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "percent_used": 46.9
  },
  "disk": {
    "total_gb": 500.0,
    "free_gb": 175.5,
    "percent_used": 64.9
  }
}
```

## ⚙️ Configuration

The hub uses configuration from `config/model_config.py`. Key configurations:

```python
class HubConfig:
    DEBUG = True/False
    HOST = "0.0.0.0"
    PORT = 3000
    CORS_ORIGINS = "*"
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/hub.log"
    ENABLE_CACHE = True
```

### Service Registration

Services are registered in `config/model_config.py`:

```python
SERVICES = {
    "chatbot": ServiceConfig(
        name="AI ChatBot",
        description="...",
        icon="🤖",
        port=5000,
        url="http://localhost:5000",
        color="from-blue-500 to-purple-600",
        features=[...]
    ),
    ...
}
```

## 🛡️ Error Handling

The hub implements centralized error handling with custom exceptions:

- `HubException`: Base exception for hub-specific errors
- `ServiceNotFoundError`: When requested service doesn't exist
- `ServiceUnavailableError`: When service is down
- `ConfigurationError`: Configuration-related errors

All errors return JSON responses with appropriate HTTP status codes.

## 📈 Rate Limiting

API endpoints are protected with rate limiting:

- `/api/services`: 100 requests per 60 seconds
- `/api/services/<name>`: 200 requests per 60 seconds

Rate limit configuration can be adjusted in the route decorators.

## 🔍 Logging

Logs are stored in `services/hub-gateway/logs/` directory:

- Application logs: `hub.log`
- Error logs: Included in main log file
- Log rotation: Automatic (configured in logging_config.py)

## 🚨 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 3000
netstat -ano | findstr :3000

# Kill the process (Windows)
taskkill /F /PID <PID>
```

### Template Not Found Error
Ensure the `services/templates/index.html` exists. If missing:
```bash
# Copy from resources
copy resources\templates\index.html services\templates\index.html
```

### Import Errors
Make sure you're running from the correct directory and the project root is in sys.path:
```bash
# From project root
python services/hub-gateway/hub.py
```

## 🔄 Recent Updates (v2.1.0)

- ✅ Fixed template path issue
- ✅ Enhanced health check with system metrics
- ✅ Added system information endpoint
- ✅ Improved CORS configuration
- ✅ Added version tracking
- ✅ Enhanced startup banner
- ✅ Better error messages
- ✅ Added uptime tracking

## 📝 Development

### Adding a New Service

1. Add service configuration in `config/model_config.py`:
```python
"new_service": ServiceConfig(
    name="New Service",
    description="Service description",
    icon="🎯",
    port=8080,
    url="http://localhost:8080",
    color="from-green-500 to-blue-600",
    features=["Feature 1", "Feature 2"]
)
```

2. Restart the hub - the new service will appear automatically in the dashboard.

### Custom Error Handling

Add custom exceptions in `handlers/error_handler.py`:
```python
class CustomError(HubException):
    status_code = 400
```

## 🤝 Contributing

When contributing to the hub gateway:

1. Follow the existing code structure
2. Add appropriate error handling
3. Update API documentation
4. Add logging for important operations
5. Test all endpoints before committing

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review logs in `logs/` directory
- Check main project documentation
- Open an issue on GitHub

## 📄 License

This service is part of the AI Assistant project. See LICENSE file in project root.

---

**Made with ❤ by AI Assistant Team**
