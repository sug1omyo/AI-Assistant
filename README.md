<div align="center">

# 🤖 AI-Assistant

**Nền tảng tích hợp đa dịch vụ AI - Multi-Model Chat, Image Generation, Speech Recognition**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Ready-green?logo=mongodb&logoColor=white)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-success)](LICENSE)

[![GitHub Stars](https://img.shields.io/github/stars/SkastVnT/AI-Assistant?style=social)](https://github.com/SkastVnT/AI-Assistant/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/SkastVnT/AI-Assistant?style=social)](https://github.com/SkastVnT/AI-Assistant/network/members)

</div>

---

## 🚀 Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| 💬 **Multi-Model Chat** | Chat với GPT-4, GROK, DeepSeek, Qwen, Gemini - streaming response, code execution |
| 🎙️ **Speech2Text** | Nhận dạng tiếng Việt, phân biệt người nói (Speaker Diarization) |
| 📄 **Document OCR** | Trích xuất text từ ảnh/PDF với PaddleOCR + AI phân tích |
| 🎨 **Image Generation** | ComfyUI workflows - Text2Image, Img2Img, LoRA fine-tuning |
| 📊 **Text2SQL** | Chuyển câu hỏi tiếng Việt thành SQL query |
| 🖼️ **Image Upscale** | RealESRGAN nâng cấp ảnh 4x, hỗ trợ GIF |

---

## ⚡ Quick Start

```bash
# Clone
git clone https://github.com/SkastVnT/AI-Assistant.git
cd AI-Assistant

# Chạy menu tương tác
menu.bat          # Windows
./menu.sh         # Linux/Mac

# Hoặc Docker
docker-compose up -d
```

---

## 🎯 Services

| Service | Port | Mô tả |
|---------|:----:|-------|
| 🤖 ChatBot | 5001 | Multi-model AI chat + MongoDB + Code sandbox |
| 🎯 Hub Gateway | 3000 | API Gateway + Rate limiting + Auth |
| 📄 Document Intelligence | 5003 | OCR tiếng Việt + AI phân tích |
| 🎙️ Speech2Text | 7860 | Whisper + Speaker diarization |
| 📊 Text2SQL | 5002 | Natural Language → SQL |
| 🎨 ComfyUI | 8188 | Node-based image workflows |
| 🖼️ Image Upscale | CLI | RealESRGAN 4x |
| ✨ LoRA Training | CLI | Fine-tune SD models |
| 🔌 MCP Server | CLI | Claude Desktop integration |

---

## 📁 Cấu trúc

```
AI-Assistant/
├── services/          # 9 Microservices
├── ComfyUI/           # Image Generation
├── src/               # Shared modules
├── config/            # Configurations
├── scripts/           # 50+ scripts
├── tests/             # Test suites
└── docker/            # Docker configs
```

---

## 🐳 Docker

```bash
docker-compose up -d                              # Full stack
docker-compose -f docker-compose.light.yml up -d  # CPU-only
curl http://localhost:5001/health/detailed        # Health check
```

---

## ⚙️ Configuration

```env
# Required
MONGODB_URI=mongodb://localhost:27017
GROK_API_KEY=your_key        # hoặc OPENAI_API_KEY, GOOGLE_API_KEY

# Optional
REDIS_HOST=localhost
```

> Copy `.env.example` → `.env` và điền API keys

---

## 📚 Documentation

- [SCRIPTS_GUIDE.md](SCRIPTS_GUIDE.md) - Hướng dẫn scripts
- [SECURITY.md](SECURITY.md) - Security policy
- [requirements/](requirements/) - Dependency management

---

## 👥 Contributors

<a href="https://github.com/SkastVnT"><img src="https://github.com/SkastVnT.png" width="60" alt="SkastVnT"/></a>
<a href="https://github.com/sug1omyo"><img src="https://github.com/sug1omyo.png" width="60" alt="sug1omyo"/></a>

---

## 📄 License

MIT License - [LICENSE](LICENSE)

---

<div align="center">

**[⭐ Star](https://github.com/SkastVnT/AI-Assistant)** this repo if you find it useful!

[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?logo=discord&logoColor=white)](https://discord.gg/d3K8Ck9NeR)

</div>
