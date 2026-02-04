<div align="center">

# 🤖 AI-Assistant 
### *Nền Tảng Tích Hợp Đa Dịch Vụ AI*

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)

[![Stars](https://img.shields.io/github/stars/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=FFD700)](https://github.com/SkastVnT/AI-Assistant)
[![Release](https://img.shields.io/github/v/release/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=10B981)](https://github.com/SkastVnT/AI-Assistant/releases)

**🌟 11 AI Microservices | Multi-Model Chat | Image Generation | Speech Recognition 🚀**

[Features](#-features) • [Quick Start](#-quick-start) • [Services](#-services) • [Documentation](#-documentation)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Multi-Model Chat** | GPT-4, GROK, DeepSeek, Qwen, Gemini với streaming response |
| 🗣️ **Speech Recognition** | Nhận dạng tiếng Việt + phân biệt người nói (Speaker Diarization) |
| 📄 **Document OCR** | Trích xuất text từ ảnh/PDF với PaddleOCR + AI phân tích |
| 🎨 **Image Generation** | ComfyUI workflows cho Text-to-Image, Img2Img |
| 📊 **Text to SQL** | Chuyển câu hỏi tiếng Việt thành SQL query |
| 🖼️ **Image Upscale** | RealESRGAN nâng cấp ảnh 4x + hỗ trợ GIF |
| 🎯 **API Gateway** | Điều phối tất cả services qua 1 endpoint |
| 🔌 **MCP Server** | Kết nối Claude Desktop với các tools |

---

## ⚡ Quick Start

```bash
git clone https://github.com/SkastVnT/AI-Assistant.git && cd AI-Assistant

# Windows: Interactive Menu
menu.bat

# Or start specific service
scripts\start-chatbot.bat          # ChatBot      :5001
scripts\start-hub-gateway.bat      # API Gateway  :3000
scripts\start-speech2text.bat      # Speech2Text  :7860

# Docker
docker-compose up -d
```

---

## 🎯 Services

| Service | Port | Chức năng chính |
|---------|------|-----------------|
| 🤖 **ChatBot** | `5001` | Chat AI đa mô hình + MongoDB lưu trữ hội thoại + Code execution |
| 🎯 **Hub Gateway** | `3000` | API Gateway điều phối + Rate limiting + Authentication |
| 📄 **Document Intelligence** | `5003` | OCR tiếng Việt + trích xuất bảng + AI phân tích nội dung |
| 🎙️ **Speech2Text** | `7860` | Transcription tiếng Việt + phân biệt người nói + Real-time |
| 📊 **Text2SQL** | `5002` | NL→SQL + hỗ trợ MySQL/PostgreSQL + Auto-complete |
| 🎨 **ComfyUI** | `8188` | Node-based image workflows + Custom nodes + LoRA support |
| 🖼️ **Image Upscale** | CLI | RealESRGAN 4x + batch processing + GIF animation |
| ✨ **LoRA Training** | CLI | Fine-tune SD models + dataset preparation |
| 🔌 **MCP Server** | CLI | Claude Desktop integration + Custom tools |

---

## 📁 Project Structure

```
AI-Assistant/
├── services/          # 11 Microservices
│   ├── chatbot/       # Flask + MongoDB + Multi-model AI
│   ├── hub-gateway/   # API Gateway + Auth
│   ├── speech2text/   # Whisper + Pyannote
│   ├── document-intelligence/  # PaddleOCR + AI
│   └── ...
├── ComfyUI/           # Image Generation Workflows
├── src/               # Shared modules (cache, db, security)
├── config/            # Firebase, Rate limiter, Model configs
├── scripts/           # 50+ automation scripts
├── tests/             # Unit + Integration + E2E
└── docker/            # Docker configurations
```

---

## 🐳 Docker

```bash
docker-compose up -d                              # All services
docker-compose -f docker-compose.light.yml up -d  # CPU-only mode
docker-compose logs -f chatbot                    # View logs
curl http://localhost:5001/health/detailed        # Health check
```

---

## 🔧 Configuration

```env
# Required
MONGODB_URI=mongodb://localhost:27017
GROK_API_KEY=your_key        # Or OPENAI_API_KEY, GOOGLE_API_KEY

# Optional
REDIS_HOST=localhost
FIREBASE_PROJECT_ID=your_project
```

> 📄 Copy `.env.example` → `.env` và điền API keys

---

## 📚 Documentation

| Doc | Mô tả |
|-----|-------|
| [SCRIPTS_GUIDE.md](SCRIPTS_GUIDE.md) | Hướng dẫn 50+ scripts |
| [SECURITY.md](SECURITY.md) | Security policy + Audit report |
| [requirements/](requirements/) | Chunked dependencies |
| [tests/](tests/) | Testing guide |

---

## 👥 Team

<table>
<tr>
<td align="center">
<img src="https://github.com/SkastVnT.png" width="80" style="border-radius: 50%;" />
<br><b>SkastVnT</b><br>
<sub>Lead Developer</sub>
</td>
<td align="center">
<img src="https://github.com/sug1omyo.png" width="80" style="border-radius: 50%;" />
<br><b>sug1omyo</b><br>
<sub>Contributor</sub>
</td>
</tr>
</table>

---

## 📄 License

MIT License - [LICENSE](LICENSE)

<div align="center">

**⭐ Star us on GitHub!** • [![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord)](https://discord.gg/d3K8Ck9NeR)

</div>
