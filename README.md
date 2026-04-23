# AI Music Generator

基于 MiniMax music-2.6 的歌词转音乐 Web 应用，支持**手动填词**和**AI 自动写词**两种模式，一键生成 + 在线播放 + 下载。

## 功能

- ✍️ **手动填词** — 输入歌词 + 风格描述，直接生成音乐
- 🤖 **AI 自动写词** — 输入歌曲主题，AI 生成歌词（可编辑）后再生成音乐
- 🎵 在线播放 + MP3 下载
- 🎨 深色主题 Web 界面

---

## 快速部署

## 部署方式

| 方式 | 适用场景 | 难度 |
|------|---------|------|
| [Docker Compose](./docs/bt-panel-deploy.md#方式一宝塔终端最快推荐) | 服务器有 SSH 终端 | ⭐ |
| [宝塔面板 Docker](./docs/bt-panel-deploy.md) | 习惯用宝塔图形化 | ⭐⭐ |
| [Docker Compose + Traefik](./docs/bt-panel-deploy.md#方式三docker-compose--traefik自动https) | 有域名 + 要 HTTPS | ⭐⭐ |

---

### Docker Compose（推荐，5 分钟搞定）

```bash
# 1. 克隆项目
git clone https://github.com/Ancoren/music-generator.git
cd music-generator

# 2. 配置 API Key
cp .env.example .env
vim .env
# 填入你的 MINIMAX_API_KEY
# MINIMAX_API_KEY=sk-cp-xxxxx

# 3. 启动服务
docker-compose up -d --build

# 4. 查看状态
docker-compose logs -f backend

# 5. 访问
open http://你的服务器IP
```

服务自动在 **80 端口** 启动，无需额外配置 Nginx。

---

### 方式二：手动 Docker 命令

```bash
cd music-generator

# 构建镜像
docker build -t music-generator ./backend

# 运行后端
docker run -d -p 8000:8000 \
  --name music-backend \
  -e MINIMAX_API_KEY=sk-cp-xxxxx \
  -e API_BASE_URL=https://api.minimax.chat \
  -v $(pwd)/backend/downloads:/app/downloads \
  music-generator

# 运行 Nginx
docker run -d -p 80:80 \
  --name music-nginx \
  -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v $(pwd)/frontend:/usr/share/nginx/html:ro \
  --link music-backend \
  nginx:alpine
```

---

### 方式三：Docker Compose + Traefik（自动 HTTPS）

需要域名 + Traefik 已运行：

```yaml
# docker-compose.traefik.yml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    environment:
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
      - API_BASE_URL=${API_BASE_URL:-https://api.minimax.chat}
    volumes:
      - ./backend/downloads:/app/downloads
    labels:
      - "traefik.enable=true"
      - "traefik.http.rulers.music-backend.rule=Host(`music.yourdomain.com`)"
      - "traefik.http.rulers.music-backend.entrypoints=websecure"
      - "traefik.http.rulers.music-backend.tls.certResolver=letsencrypt"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - backend
    labels:
      - "traefik.enable=true"
      - "traefik.http.rulers.music-nginx.rule=Host(`music.yourdomain.com`)"
      - "traefik.http.rulers.music-nginx.entrypoints=websecure"
      - "traefik.http.rulers.music-nginx.tls.certResolver=letsencrypt"
```

```bash
docker-compose -f docker-compose.traefik.yml up -d
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MINIMAX_API_KEY` | **必须填写** | MiniMax API Key |
| `API_BASE_URL` | `https://api.minimax.chat` | 国内版地址 |

### 获取 API Key

1. 注册 [MiniMax Token Plan](https://platform.minimax.io)
2. 进入 API Keys → 创建新的 Secret Key
3. Key 格式：`sk-cp-xxxxx`

---

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/generate` | 提交生成任务 | 见下方请求格式 |
| `GET /api/status/{task_id}` | 查询状态 | 返回音频URL + 生成歌词 |
| `GET /api/downloads/{file}` | 下载MP3 | 通过后端提供 |
| `GET /api/tasks` | 所有任务状态 | 调试用 |

### /api/generate 请求格式

**手动填词：**
```json
{
  "prompt": "华语流行抒情，钢琴主导，弦乐烘托，温暖治愈氛围",
  "lyrics": "[前奏]\n钢琴轻柔...",
  "auto_lyrics": false
}
```

**AI 自动写词：**
```json
{
  "prompt": "华语流行抒情，钢琴主导，弦乐烘托，温暖治愈",
  "theme": "一个人在深夜思念远方的恋人",
  "auto_lyrics": true
}
```

---

## 歌词格式说明

```
[前奏]        → 开场音乐无人声
[主歌1/2]     → Verse
[预副歌]      → Pre-Chorus
[副歌]        → Chorus（高潮）
[说唱]        → Rap
[桥段]        → Bridge
[尾声]        → Outro
```

结构标记帮助 AI 理解歌曲段落，可用中文或英文标记。

---

## 目录结构

```
music-generator/
├── docker-compose.yml      # 推荐部署配置
├── docker-compose.traefik.yml  # HTTPS 部署配置
├── nginx.conf              # Nginx 反向代理
├── .env.example            # 环境变量模板
├── README.md
├── SPEC.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py              # FastAPI 异步服务
│   └── downloads/           # 生成的 MP3 文件
└── frontend/
    ├── index.html           # 主页面
    ├── style.css            # 样式
    └── app.js               # 前端逻辑
```

---

## 故障排查

**502 Bad Gateway**
```bash
# 检查 backend 是否启动
docker-compose logs backend
# 重启
docker-compose restart backend
```

**生成失败 / 超时**
- MiniMax API 偶发超时，重试即可
- 检查 `MINIMAX_API_KEY` 是否正确

**端口被占用**
```bash
# 改端口（nginx.conf 改 80 为其他端口）
# 同时改 docker-compose.yml 的 ports
```
