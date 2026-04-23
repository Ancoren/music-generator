# Music Generator - 项目规格

## 概述
基于 MiniMax music-2.6 API 的歌词转音乐生成工具，支持手动填词和 AI 自动写词两种模式，提供 Web 界面。

## 技术栈
- **后端**: FastAPI + uvicorn（异步任务）
- **前端**: 原生 HTML/CSS/JS（无框架）
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx

## 架构
```
用户浏览器
    │
    ▼
Nginx :80
  ├─ /          → 静态文件
  └─ /api/*     → 反向代理 → FastAPI :8000
           │
           ├─ POST /v1/lyrics_generation  (AI写词)
           └─ POST /v1/music_generation   (生成音乐)
```

## 双模式设计

### 模式一：手动填词
1. 用户输入风格描述 + 歌词
2. 直接调用 music_generation
3. 约 60-90 秒生成完成

### 模式二：AI 自动写词
1. 用户输入风格描述 + 歌曲主题
2. **阶段一**：调用 lyrics_generation API 生成完整歌词
3. 歌词展示在页面（可编辑修改）
4. **阶段二**：用修改后歌词调用 music_generation
5. 约 2 分钟完成

## API 设计

### POST /api/generate
**Request:**
```json
{
  "prompt": "风格描述",
  "lyrics": "歌词（手动模式）",
  "auto_lyrics": false,
  "theme": "歌曲主题（自动模式）",
  "model": "music-2.6"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing",
  "phase": "lyrics|music|done"
}
```

### GET /api/status/{task_id}
**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing|completed|failed",
  "phase": "music|done",
  "audio_url": "/api/downloads/xxx.mp3",
  "generated_lyrics": "AI生成的歌词...",
  "error": null
}
```

### GET /api/downloads/{filename}
下载生成的 MP3 文件。

## 环境变量
- `MINIMAX_API_KEY` - MiniMax API Key
- `API_BASE_URL` - MiniMax API 地址（默认：https://api.minimax.chat）

## 目录结构
```
music-generator/
├── SPEC.md
├── README.md
├── .env.example
├── docker-compose.yml
├── nginx.conf
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # 异步任务：写词 + 音乐
│   └── downloads/            # 生成的 MP3
└── frontend/
    ├── index.html           # 双模式切换页面
    ├── style.css
    └── app.js
```
