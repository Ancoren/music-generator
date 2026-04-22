# AI Music Generator

基于 MiniMax music-2.6 的歌词转音乐 Web 应用，支持一键生成 + 在线播放 + 下载。

## 快速部署

### 1. 准备 API Key

在国内版 [MiniMax Token Plan](https://platform.minimax.io) 申请 API Key。

### 2. 启动服务

```bash
# 克隆 / 进入目录
cd /root/projects/music-generator

# 配置 Key（复制示例文件）
cp .env.example .env
vim .env  # 填入你的 MINIMAX_API_KEY

# 启动
docker-compose up -d --build

# 查看状态
docker-compose logs -f backend
```

### 3. 访问

打开 `http://你的服务器IP`

---

## 目录结构

```
music-generator/
├── docker-compose.yml   # 服务编排
├── nginx.conf           # Nginx 配置
├── .env                 # 环境变量（需要手动创建）
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py          # FastAPI 服务
│   └── downloads/       # 生成的音乐文件
└── frontend/
    ├── index.html       # 主页面
    ├── style.css        # 样式
    └── app.js           # 前端逻辑
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /api/generate` | 提交生成任务 | 返回 task_id |
| `GET /api/status/{task_id}` | 查询状态 | 返回音频URL |
| `GET /api/downloads/{file}` | 下载MP3 | 通过后端提供 |

## 歌词格式示例

```
[前奏]
钢琴轻柔 弦乐铺底

[主歌1]
歌词内容...

[副歌]
高潮部分...

[说唱]
节奏说唱...

[尾声]
渐弱消失
```

结构标记帮助 AI 理解歌曲段落，可用中文（主歌、副歌）或英文（Verse、Chorus、Rap、Bridge）。
