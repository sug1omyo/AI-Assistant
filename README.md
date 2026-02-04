<div align="center">

# 🤖 AI-Assistant 
### *Nền Tảng Tích Hợp Đa Dịch Vụ AI*

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&width=600&lines=ChatBot+%7C+Text2SQL+%7C+Speech2Text+%7C+Image+Gen;Document+Intelligence+%7C+Upscaling+%7C+LoRA+Training;ComfyUI+%7C+MCP+Server+%7C+Multi-Model+AI;Built+with+%E2%9D%A4%EF%B8%8F+by+SkastVnT" alt="Typing SVG" />

---

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![ComfyUI](https://img.shields.io/badge/ComfyUI-Integrated-FF6B6B?style=for-the-badge&logo=python&logoColor=white)
![Security](https://img.shields.io/badge/Security-Audited-green?style=for-the-badge&logo=security&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)

[![Stars](https://img.shields.io/github/stars/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=FFD700)](https://github.com/SkastVnT/AI-Assistant)
[![Forks](https://img.shields.io/github/forks/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=3B82F6)](https://github.com/SkastVnT/AI-Assistant)
[![Release](https://img.shields.io/github/v/release/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=10B981)](https://github.com/SkastVnT/AI-Assistant/releases)

**🌟 Nền tảng tích hợp 11 dịch vụ AI Microservices 🚀**

[📖 Features](#-services) • [⚡ Quick Start](#-quick-start) • [🎮 Scripts](#-scripts) • [📚 Docs](#-documentation) • [🔒 Security](#-security)

</div>

---

## ⚡ Quick Start

```bash
# Clone repository
git clone https://github.com/SkastVnT/AI-Assistant.git
cd AI-Assistant

# Option 1: Interactive Menu (Easiest!)
menu.bat                           # Windows
./menu.sh                          # Linux/Mac

# Option 2: Start Individual Service
scripts\start-chatbot.bat          # Port 5001 - AI ChatBot
scripts\start-text2sql.bat         # Port 5002 - Text2SQL
scripts\start-hub-gateway.bat      # Port 3000 - API Gateway
scripts\start-speech2text.bat      # Port 7860 - Speech2Text
scripts\start-document-intelligence.bat  # Port 5003 - OCR

# Option 3: Docker Compose
docker-compose up -d               # All services
docker-compose -f docker-compose.light.yml up -d  # Lightweight
```

### Dependencies
- **Full stack**: `pip install -r requirements.txt`
- **Selective install**: See [requirements/README.md](requirements/README.md) for chunked installs
- **Individual service**: Each service has its own `requirements.txt`

---

## 🎯 Services

| Service | Description | Port | Status |
|---------|-------------|------|--------|
| 🤖 **ChatBot** | Multi-model AI Chat (GROK, GPT-4, DeepSeek, Qwen) + MongoDB | `5001` | ✅ Production |
| 📊 **Text2SQL** | Natural Language → SQL Query | `5002` | ✅ Production |
| 📄 **Document Intelligence** | OCR + AI Document Analysis (PaddleOCR) | `5003` | ✅ Production |
| 🎙️ **Speech2Text** | Vietnamese Transcription + Speaker Diarization | `7860` | ✅ Production |
| 🎨 **ComfyUI** | Advanced AI Image Generation Workflows | `8188` | ✅ Integrated |
| ✨ **LoRA Training** | Fine-tune Stable Diffusion Models | N/A | ✅ Ready |
| 🖼️ **Image Upscale** | RealESRGAN Enhancement + GIF Support | N/A | ✅ Ready |
| 🎯 **Hub Gateway** | API Gateway & Service Orchestration | `3000` | ✅ Production |
| 🔌 **MCP Server** | Model Context Protocol for Claude Desktop | N/A | ✅ Ready |
| 📁 **Templates** | Shared UI Templates & Components | N/A | ✅ Ready |

> **Note:** Stable Diffusion & Edit-Image models (~3GB) archived to [Google Drive](https://drive.google.com) for repo size optimization.

---

## 🤖 ChatBot Highlights

**Database Migration Complete (MongoDB + Redis)**

- ✅ **MongoDB**: Conversations, Messages, Memory với Repository Pattern
- ✅ **Redis**: Caching với TTL và compression
- ✅ **Health Checks**: `/health`, `/health/live`, `/health/ready`, `/health/detailed`
- ✅ **Metrics**: Prometheus-compatible metrics
- ✅ **Multi-Model**: GROK, GPT-4, DeepSeek, Qwen, Google Gemini
- ✅ **Streaming**: Real-time token-by-token output
- ✅ **Code Execution**: Secure Python/JS sandbox
- ✅ **Firebase Integration**: Authentication & real-time sync
- ✅ **Session Gallery**: Private image gallery per session

---

## 🎮 Scripts

```bash
# Start Services
scripts\start-all.bat              # All services
scripts\start-chatbot.bat          # ChatBot (5001)
scripts\start-hub-gateway.bat      # Hub Gateway (3000)
scripts\start-speech2text.bat      # Speech2Text (7860)
scripts\start-document-intelligence.bat  # Document OCR (5003)
scripts\start-text2sql.bat         # Text2SQL (5002)
scripts\start-image-upscale.bat    # Image Upscale
scripts\start-lora-training.bat    # LoRA Training
scripts\start-mcp.bat              # MCP Server

# Management
scripts\stop-all.bat               # Stop all services
scripts\health-check-all.bat       # Health checks for all
scripts\deploy-chatbot.bat         # Deploy with backup
scripts\rollback-chatbot.bat       # Rollback if needed
scripts\cleanup.bat                # Cleanup temp files

# Setup & Configuration
scripts\setup-all.bat              # Setup all services
scripts\setup-venv.bat             # Create virtual environment
scripts\quick-start.bat            # Quick setup wizard

# Testing
scripts\test-all.bat               # Run all tests
scripts\test_mongodb.py            # Test MongoDB connection

# Deployment
scripts\expose-public.bat          # Expose via Cloudflare tunnels
scripts\deploy_public.py           # Public deployment
```

---

## 📁 Project Structure

```
AI-Assistant/
├── 📦 services/                   # Microservices (11 services)
│   ├── chatbot/                   # AI ChatBot (Flask + MongoDB)
│   ├── text2sql/                  # Natural Language to SQL
│   ├── document-intelligence/     # OCR & Document Analysis
│   ├── speech2text/               # Audio Transcription
│   ├── hub-gateway/               # API Gateway & Orchestration
│   ├── image-upscale/             # RealESRGAN Enhancement
│   ├── lora-training/             # LoRA Fine-tuning
│   ├── mcp-server/                # Model Context Protocol
│   └── templates/                 # Shared UI Components
│
├── 🎨 ComfyUI/                    # Advanced Image Generation Workflows
│
├── 🔧 src/                        # Core shared modules
│   ├── cache/                     # Caching utilities
│   ├── database/                  # Database connectors
│   ├── health/                    # Health check utilities
│   ├── security/                  # Security modules
│   └── utils/                     # Common utilities
│
├── ⚙️ config/                     # Global configuration
│   ├── firebase_config.py         # Firebase setup
│   ├── model_config.py            # AI model configurations
│   ├── rate_limiter.py            # Rate limiting
│   └── response_cache.py          # Response caching
│
├── 🧪 tests/                      # Test suites
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   └── e2e/                       # End-to-end tests
│
├── 📜 scripts/                    # Automation scripts (50+ scripts)
├── 📋 requirements/               # Chunked dependencies
├── 🐳 docker/                     # Docker configurations
├── 🔐 private/                    # Private submodule (docs, diagrams)
├── 📊 logs/                       # Application logs
├── 💾 local_data/                 # Local cache & data
└── 📁 resources/                  # Static resources & models
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SCRIPTS_GUIDE.md](SCRIPTS_GUIDE.md) | Complete scripts documentation |
| [SECURITY.md](SECURITY.md) | Security policy & guidelines |
| [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) | Full security audit report |
| [requirements/README.md](requirements/README.md) | Dependency management guide |
| [tests/README.md](tests/README.md) | Testing documentation |
| [services/chatbot/README.md](services/chatbot/README.md) | ChatBot service documentation |

> 📂 Additional docs (setup guides, API docs, architecture) available in `private/` submodule

---

## 🐳 Docker

```bash
# Start all services
docker-compose up -d

# Lightweight mode (no GPU services)
docker-compose -f docker-compose.light.yml up -d

# Start specific services
docker-compose up -d chatbot mongodb redis

# View logs
docker-compose logs -f chatbot

# Health check
curl http://localhost:5001/health/detailed

# Stop all
docker-compose down
```

### Available Containers
- `ai-chatbot` - ChatBot service (5001)
- `ai-hub-gateway` - API Gateway (3000)
- `ai-mongodb` - MongoDB database
- `ai-redis` - Redis cache
- `ai-speech2text` - Speech2Text (7860)
- `ai-document-intelligence` - Document OCR (5003)

---

## 🧪 Testing

```bash
# ChatBot tests (Repository Pattern)
cd services/chatbot
python -m pytest tests/ -v

# All services
scripts\test-all.bat
```

---

## 🔧 Environment Variables

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=chatbot

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# AI APIs
GROK_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
DEEPSEEK_API_KEY=your_key

# Firebase (Optional)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY=your_private_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret
```

> 📄 See `.env.example` for full configuration template

---

## 📊 Metrics & Monitoring

```bash
# Health endpoints
GET /health              # Basic health
GET /health/live         # Liveness probe (Kubernetes)
GET /health/ready        # Readiness probe (Kubernetes)
GET /health/detailed     # Full status with dependencies

# Metrics
GET /metrics             # Prometheus format
```

### CI/CD Workflows
- **tests.yml** - Automated testing on PR
- **codeql-analysis.yml** - Security code scanning
- **dependency-review.yml** - Dependency vulnerability check
- **security-scan.yml** - Security scanning

---
## Author & Collaborators
</div>

<table>
<tr>
<td align="center" width="50%">

<img src="https://github.com/SkastVnT.png" width="120" height="120" style="border-radius: 50%; border: 3px solid #6366F1;" />

### **SkastVnT**

[![GitHub](https://img.shields.io/badge/GitHub-SkastVnT-181717?style=for-the-badge&logo=github)](https://github.com/SkastVnT)
[![Email](https://img.shields.io/badge/Email-Contact-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:nguyvip007@gmail.com)

**Solo Developer • AI Enthusiast • Full-Stack Engineer**

*Developed with late nights, lots of coffee ☕, and a passion for AI* 

</td>
<td align="center" width="50%">

<img src="https://github.com/sug1omyo.png" width="120" height="120" style="border-radius: 50%; border: 3px solid #10B981;" />

### **sug1omyo**

[![GitHub](https://img.shields.io/badge/GitHub-sug1omyo-181717?style=for-the-badge&logo=github)](https://github.com/sug1omyo)
[![Email](https://img.shields.io/badge/Email-Contact-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:ngtuanhei2004@gmail.com)

**Fresher Software Engineer**

***Collaborator & Contributor***

*Atsui~*
*Atsukute hikarabisou*
*Ugoitenai no ni atsui yo~*


</td>
</tr>
</table>

<div align="center">

---

<div align="center">



## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

**Security:** Please review our [Security Policy](SECURITY.md) before contributing.

---

## 🔒 Security

We take security seriously. Please see our [Security Policy](SECURITY.md) for:
- Reporting vulnerabilities
- Security best practices
- Known security issues
- Security modules and tools

**Latest Security Audit:** February 2, 2026 - 120 findings identified and documented.

See detailed reports:
- [SECURITY_AUDIT_REPORT.md](SECURITY_AUDIT_REPORT.md) - Full audit report
- [SECURITY_FINDINGS_SUMMARY.txt](SECURITY_FINDINGS_SUMMARY.txt) - Findings summary

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Made with ❤️ by [SkastVnT](https://github.com/SkastVnT)**

[![GitHub](https://img.shields.io/badge/GitHub-SkastVnT-181717?style=flat-square&logo=github)](https://github.com/SkastVnT)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord)](https://discord.gg/d3K8Ck9NeR)

**⭐ Star us on GitHub if you find this useful!**

</div>
