# Music Generator - 项目规格

## 概述
基于 MiniMax music-2.6 API 的歌词转音乐生成工具，提供 Web 界面。

## 技术栈
- **后端**: FastAPI + uvicorn
- **前端**: 原生 HTML/CSS/JS（无框架）
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx（前端 + API 统一端口）

## 架构
```
用户浏览器
    │
    ▼
Nginx :80
  ├─ /          → 静态文件（frontend/）
  └─ /api/*     → 反向代理 → FastAPI :8000
           │
           ▼
      MiniMax API
```

## API 设计

### POST /api/generate
生成音乐任务。

**Request:**
```json
{
  "prompt": "风格描述",
  "lyrics": "歌词（带\\n分隔）",
  "model": "music-2.6"
}
```

**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing"
}
```

### GET /api/status/{task_id}
查询任务状态。

**Response:**
```json
{
  "task_id": "uuid",
  "status": "processing|completed|failed",
  "audio_url": "/downloads/xxx.mp3",
  "error": null
}
```

### GET /api/downloads/{filename}
下载生成的 MP3 文件。

## 功能
1. 输入歌词（带结构标记：[主歌]、[副歌] 等）
2. 输入风格描述（中文/英文均可）
3. 提交生成，后端轮询 MiniMax 直到完成
4. 在线播放 + 下载 MP3
5. 生成历史记录（当前会话内）

## 环境变量
- `MINIMAX_API_KEY` - MiniMax API Key
- `API_BASE_URL` - MiniMax API 地址（默认：https://api.minimax.chat）

## 目录结构
```
music-generator/
├── SPEC.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── downloads/          (gitkeep)
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```
