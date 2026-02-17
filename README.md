# 🐍 拜年助手 (Bainian Assistant)

> AI-powered Chinese New Year reply generator — upload WeChat screenshots, get personalized replies instantly.

**Live Demo**: https://bainian.aitist.ai

![Screenshot](docs/screenshot.png)

---

## ✨ Features

- **Batch upload** — drag & drop multiple screenshots at once
- **Parallel processing** — all images processed simultaneously, no waiting
- **Multiple AI models** — choose from Gemini Flash, Qwen VL, Claude Sonnet, or DeepSeek V3
- **3 reply styles** per image: formal, humorous, and concise
- **One-click copy** — tap to copy any reply to clipboard
- **Mobile-friendly** — works great on phone browser
- **Ctrl+V paste** — paste screenshots directly from clipboard
- **Customizable persona** — configure the AI to write in *your* voice

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/oyzh888/bainian-assistant.git
cd bainian-assistant
```

### 2. Install dependencies

```bash
pip install flask openai
```

> Requires Python 3.9+

### 3. Set up environment

```bash
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 4. Run

```bash
# Load env and start
export $(cat .env | xargs)
python app.py
```

Open http://localhost:3005 in your browser.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | — | Your OpenRouter API key |
| `PORT` | ❌ | `3005` | Server port |
| `DEFAULT_MODEL` | ❌ | `gemini-flash` | Default model key |
| `SYSTEM_PROMPT` | ❌ | Built-in | Override the AI system prompt |

### Personalizing the Reply Style

The app comes with a generic, friendly system prompt. To make replies sound **like you**, create a `config.json` in the project root:

```json
{
  "system_prompt": "你是在帮[你的名字]回复春节拜年消息。\n\n## 风格\n- [描述你的说话习惯]\n- [你常用的表达方式]\n- 回复长度：15-35字\n\n## 输出格式（严格JSON）\n{\n  \"recognized\": \"发送人和内容简述\",\n  \"replies\": [\n    {\"type\": \"formal\", \"label\": \"🎩 正式温馨\", \"text\": \"回复内容\"},\n    {\"type\": \"humor\",  \"label\": \"😄 幽默俏皮\", \"text\": \"回复内容\"},\n    {\"type\": \"short\",  \"label\": \"⚡ 简短精炼\", \"text\": \"回复内容\"}\n  ]\n}"
}
```

> `config.json` is in `.gitignore` — your personal prompt stays private.

---

## 🤖 Supported Models

All models accessed via [OpenRouter](https://openrouter.ai):

| Key | Model | Notes |
|---|---|---|
| `gemini-flash` | Google Gemini 2.0 Flash | ⚡ Fastest, great Chinese |
| `qwen-vl-72b` | Qwen 2.5 VL 72B | 🇨🇳 Strong Chinese + vision |
| `claude-sonnet` | Claude Sonnet 4.5 | 🤖 Best understanding |
| `deepseek` | DeepSeek Chat V3 | 🔥 Excellent Chinese writing |

### Estimated cost per screenshot

| Model | Cost |
|---|---|
| Gemini Flash | ~$0.001 |
| Qwen VL 72B | ~$0.003 |
| Claude Sonnet | ~$0.01 |
| DeepSeek V3 | ~$0.001 |

---

## 🌐 Deployment

### Simple (local)
```bash
python app.py
```

### With Gunicorn (production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:3005 "app:app"
```

### Docker
```bash
docker build -t bainian-assistant .
docker run -e OPENROUTER_API_KEY=your_key -p 3005:3005 bainian-assistant
```

### Expose via Cloudflare Tunnel
```bash
cloudflared tunnel --url http://localhost:3005
```

---

## 📁 Project Structure

```
bainian-assistant/
├── app.py              # Main Flask application
├── config.json         # (gitignored) Your personal system prompt
├── .env                # (gitignored) Your API keys
├── .env.example        # Template for environment variables
├── Dockerfile          # Container build file
├── requirements.txt    # Python dependencies
├── docs/
│   └── screenshot.png  # Demo screenshot
└── README.md
```

---

## 🛠️ How It Works

1. User uploads a screenshot (WeChat / SMS / any chat app)
2. Image is base64-encoded and sent to the selected AI model via OpenRouter
3. The model (with vision capability) reads the screenshot content
4. AI generates 3 reply options in JSON format
5. Frontend renders results with one-click copy

```
Screenshot → Base64 → OpenRouter API → AI Model → JSON Response → UI
```

---

## 🔒 Privacy

- Images are processed in memory and **never saved** to disk
- No user data is logged or stored
- API calls go directly to OpenRouter — the app is just a thin wrapper
- Your `config.json` and `.env` are gitignored

---

## 📝 License

MIT License — feel free to use, modify, and distribute.

---

## 🙏 Credits

Built with:
- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [OpenRouter](https://openrouter.ai/) — Multi-model AI API
- [Gemini](https://deepmind.google/technologies/gemini/) / [Qwen](https://qwenlm.github.io/) / [Claude](https://anthropic.com/) / [DeepSeek](https://www.deepseek.com/)
