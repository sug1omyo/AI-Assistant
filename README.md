<div align="center">

<!-- Header Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=180&section=header&text=AI-Assistant&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=32&desc=Nền%20Tảng%20Tích%20Hợp%20Đa%20Dịch%20Vụ%20AI&descAlignY=52&descSize=18"/>

<!-- Typing Animation -->
<a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=3000&pause=1000&color=6366F1&center=true&vCenter=true&multiline=true&repeat=true&width=600&height=80&lines=%F0%9F%A4%96+Multi-Model+AI+Chat;%F0%9F%8E%A8+Image+Generation+%7C+%F0%9F%8E%99%EF%B8%8F+Speech+Recognition;%F0%9F%93%84+Document+OCR+%7C+%F0%9F%93%8A+Text+to+SQL" alt="Typing SVG" />
</a>

<div>

    <!-- Badges Row 1 -->
<p>
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white"/>
<img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
<img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white"/>
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
</p>

</div>

<!-- Badges Row 2 -->
<p>
<a href="https://github.com/SkastVnT/AI-Assistant/stargazers"><img src="https://img.shields.io/github/stars/SkastVnT/AI-Assistant?style=for-the-badge&logo=github&color=f4c542&labelColor=1a1a2e"/></a>
<a href="https://github.com/SkastVnT/AI-Assistant/releases"><img src="https://img.shields.io/github/v/release/SkastVnT/AI-Assistant?style=for-the-badge&logo=semantic-release&color=6366f1&labelColor=1a1a2e"/></a>
<a href="https://github.com/SkastVnT/AI-Assistant/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge&labelColor=1a1a2e"/></a>
<a href="https://github.com/SkastVnT/AI-Assistant/actions"><img src="https://img.shields.io/github/actions/workflow/status/SkastVnT/AI-Assistant/tests.yml?style=for-the-badge&logo=github-actions&logoColor=white&label=CI&labelColor=1a1a2e"/></a>
</p>

<!-- Navigation -->
<p>
<a href="#-features"><img src="https://img.shields.io/badge/✨_Features-6366f1?style=flat-square"/></a>
<a href="#-quick-start"><img src="https://img.shields.io/badge/⚡_Quick_Start-10b981?style=flat-square"/></a>
<a href="#-services"><img src="https://img.shields.io/badge/🎯_Services-f59e0b?style=flat-square"/></a>
<a href="#-documentation"><img src="https://img.shields.io/badge/📚_Docs-ef4444?style=flat-square"/></a>
</p>

</div>

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 💬 Multi-Model AI Chat
> GPT-4, GROK, DeepSeek, Qwen, Gemini  
> ✅ Streaming response  
> ✅ Code execution sandbox  
> ✅ MongoDB conversation storage

</td>
<td width="50%">

### 🎙️ Speech Recognition  
> Nhận dạng tiếng Việt chính xác  
> ✅ Speaker Diarization  
> ✅ Real-time transcription  
> ✅ Batch processing

</td>
</tr>
<tr>
<td width="50%">

### 📄 Document Intelligence
> PaddleOCR + AI Analysis  
> ✅ Table extraction  
> ✅ Multi-language OCR  
> ✅ PDF/Image support

</td>
<td width="50%">

### 🎨 Image Generation
> ComfyUI Node Workflows  
> ✅ Text-to-Image  
> ✅ Image-to-Image  
> ✅ LoRA fine-tuning

</td>
</tr>
<tr>
<td width="50%">

### 📊 Text to SQL
> Natural Language → SQL Query  
> ✅ MySQL/PostgreSQL  
> ✅ Vietnamese support  
> ✅ Auto-complete

</td>
<td width="50%">

### 🖼️ Image Upscale
> RealESRGAN Enhancement  
> ✅ 4x upscaling  
> ✅ Batch processing  
> ✅ GIF animation support

</td>
</tr>
</table>

---

## ⚡ Quick Start

```bash
# Clone & Run
git clone https://github.com/SkastVnT/AI-Assistant.git && cd AI-Assistant

# 🖥️ Windows - Interactive Menu
menu.bat

# 🐧 Linux/Mac
./menu.sh

# 🐳 Docker (Recommended)
docker-compose up -d
```

<details>
<summary>📦 <b>Start Individual Services</b></summary>

```bash
scripts\start-chatbot.bat          # 🤖 ChatBot      → localhost:5001
scripts\start-hub-gateway.bat      # 🎯 API Gateway  → localhost:3000
scripts\start-speech2text.bat      # 🎙️ Speech2Text  → localhost:7860
scripts\start-document-intelligence.bat  # 📄 OCR    → localhost:5003
scripts\start-text2sql.bat         # 📊 Text2SQL    → localhost:5002
```

</details>

---

## 🎯 Services

<div align="center">

| Service | Port | Description |
|:-------:|:----:|:------------|
| 🤖 **ChatBot** | `5001` | Multi-model AI • MongoDB storage • Code sandbox |
| 🎯 **Hub Gateway** | `3000` | API orchestration • Rate limiting • Auth |
| 📄 **Doc Intelligence** | `5003` | Vietnamese OCR • Table extraction • AI analysis |
| 🎙️ **Speech2Text** | `7860` | Whisper • Speaker diarization • Real-time |
| 📊 **Text2SQL** | `5002` | NL→SQL • MySQL/PostgreSQL • Vietnamese |
| 🎨 **ComfyUI** | `8188` | Node workflows • Custom nodes • LoRA |
| 🖼️ **Image Upscale** | `CLI` | RealESRGAN 4x • Batch • GIF support |
| ✨ **LoRA Training** | `CLI` | SD fine-tuning • Dataset prep |
| 🔌 **MCP Server** | `CLI` | Claude Desktop integration |

</div>

---

## 📁 Architecture

```mermaid
graph LR
    A[🌐 Client] --> B[🎯 Hub Gateway :3000]
    B --> C[🤖 ChatBot :5001]
    B --> D[📄 Document OCR :5003]
    B --> E[🎙️ Speech2Text :7860]
    B --> F[📊 Text2SQL :5002]
    C --> G[(MongoDB)]
    C --> H[(Redis Cache)]
```

<details>
<summary>📂 <b>Project Structure</b></summary>

```
AI-Assistant/
├── 📦 services/           # Microservices
│   ├── chatbot/           # Flask + MongoDB + Multi-model
│   ├── hub-gateway/       # API Gateway + Auth
│   ├── speech2text/       # Whisper + Pyannote
│   ├── document-intelligence/
│   ├── text2sql/
│   ├── image-upscale/
│   ├── lora-training/
│   └── mcp-server/
├── 🎨 ComfyUI/            # Image Generation
├── 🔧 src/                # Shared modules
├── ⚙️ config/             # Configurations
├── 📜 scripts/            # 50+ automation scripts
├── 🧪 tests/              # Test suites
└── 🐳 docker/             # Docker configs
```

</details>

---

## 🐳 Docker

```bash
# Full stack
docker-compose up -d

# CPU-only (no GPU)
docker-compose -f docker-compose.light.yml up -d

# Health check
curl http://localhost:5001/health/detailed
```

---

## 🔧 Configuration

```env
# 🔑 Required
MONGODB_URI=mongodb://localhost:27017
GROK_API_KEY=your_key          # hoặc OPENAI_API_KEY

# 📦 Optional  
REDIS_HOST=localhost
FIREBASE_PROJECT_ID=your_project
```

> 💡 Copy `.env.example` → `.env`

---

## 📚 Documentation

<div align="center">

| 📖 Document | 📝 Description |
|:-----------:|:---------------|
| [SCRIPTS_GUIDE](SCRIPTS_GUIDE.md) | 50+ automation scripts guide |
| [SECURITY](SECURITY.md) | Security policy & audit report |
| [Requirements](requirements/) | Chunked dependency management |

</div>

---

## 👥 Contributors

<div align="center">

<a href="https://github.com/SkastVnT">
  <img src="https://github.com/SkastVnT.png" width="100" style="border-radius: 50%"/>
  <br/><b>SkastVnT</b>
  <br/><sub>🚀 Lead Developer</sub>
</a>
&nbsp;&nbsp;&nbsp;&nbsp;
<a href="https://github.com/sug1omyo">
  <img src="https://github.com/sug1omyo.png" width="100" style="border-radius: 50%"/>
  <br/><b>sug1omyo</b>
  <br/><sub>💻 Contributor</sub>
</a>

</div>

---

<div align="center">

## 📄 License

**MIT License** — [View License](LICENSE)

---

<a href="https://github.com/SkastVnT/AI-Assistant/stargazers">
  <img src="https://img.shields.io/badge/⭐_Star_this_repo-f4c542?style=for-the-badge"/>
</a>
<a href="https://discord.gg/d3K8Ck9NeR">
  <img src="https://img.shields.io/badge/💬_Join_Discord-5865F2?style=for-the-badge"/>
</a>

<!-- Footer Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer"/>

</div>
