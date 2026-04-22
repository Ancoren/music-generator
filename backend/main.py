"""
MiniMax Music Generator - FastAPI Backend
基于 music-2.6 API 的歌词转音乐生成服务
"""

import os
import uuid
import asyncio
import httpx
import urllib.parse
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


# ============ 配置 ============
API_KEY = os.getenv("MINIMAX_API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.minimax.chat")
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


# ============ 数据模型 ============
class GenerateRequest(BaseModel):
    prompt: str
    lyrics: str
    model: str = "music-2.6"


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    audio_url: str | None = None
    error: str | None = None


# ============ 任务状态存储 ============
# 简单内存存储，生产环境可用 Redis
tasks: dict[str, dict] = {}


# ============ 辅助函数 ============
def parse_lyrics(lyrics_text: str) -> str:
    """确保歌词格式正确：\n 分隔"""
    lines = []
    for line in lyrics_text.strip().split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)


async def download_audio(audio_url: str, filename: Path) -> bool:
    """下载音频文件到本地"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(audio_url)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
    except Exception as e:
        print(f"Download failed: {e}")
    return False


async def generate_music_task(task_id: str, prompt: str, lyrics: str, model: str):
    """异步生成音乐任务"""
    tasks[task_id] = {"status": "processing", "audio_url": None, "error": None}

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "lyrics": parse_lyrics(lyrics),
                "output_format": "url"
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            print(f"[{task_id}] Starting generation...")
            response = await client.post(
                f"{API_BASE_URL}/v1/music_generation",
                json=payload,
                headers=headers
            )

            if response.status_code != 200:
                error_msg = response.text
                tasks[task_id] = {"status": "failed", "error": f"API error {response.status_code}: {error_msg}"}
                return

            data = response.json()
            audio_url = data.get("data", {}).get("audio")

            if not audio_url:
                tasks[task_id] = {"status": "failed", "error": "No audio URL in response"}
                return

            # 下载音频
            filename = DOWNLOAD_DIR / f"{task_id}.mp3"
            success = await download_audio(audio_url, filename)

            if success:
                tasks[task_id] = {
                    "status": "completed",
                    "audio_url": f"/api/downloads/{task_id}.mp3",
                    "duration": data.get("extra_info", {}).get("music_duration", 0)
                }
                print(f"[{task_id}] Generation completed: {filename}")
            else:
                tasks[task_id] = {"status": "failed", "error": "Failed to download audio"}

    except asyncio.TimeoutError:
        tasks[task_id] = {"status": "failed", "error": "Generation timeout (>5min)"}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}


# ============ FastAPI 应用 ============
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Music Generator started. API: {API_BASE_URL}")
    yield
    print("Music Generator stopped.")


app = FastAPI(title="Music Generator", lifespan=lifespan)


# ---------- API 路由 ----------

@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """提交音乐生成任务"""
    if not API_KEY:
        raise HTTPException(status_code=500, detail="MINIMAX_API_KEY not configured")

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    if not request.lyrics.strip():
        raise HTTPException(status_code=400, detail="lyrics is required")

    task_id = str(uuid.uuid4())

    # 启动异步生成任务（不阻塞响应）
    asyncio.create_task(generate_music_task(task_id, request.prompt, request.lyrics, request.model))

    return GenerateResponse(task_id=task_id, status="processing")


@app.get("/api/status/{task_id}", response_model=GenerateResponse)
async def get_status(task_id: str):
    """查询任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    return GenerateResponse(
        task_id=task_id,
        status=task["status"],
        audio_url=task.get("audio_url"),
        error=task.get("error")
    )


@app.get("/api/downloads/{filename}")
async def download_file(filename: str):
    """下载生成的音频文件"""
    # 安全检查：只允许 .mp3
    if not filename.endswith('.mp3'):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_path = DOWNLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务（调试用）"""
    return {
        task_id: {
            "status": t["status"],
            "audio_url": t.get("audio_url"),
            "error": t.get("error")
        }
        for task_id, t in tasks.items()
    }


# ---------- 前端静态文件（开发用） ----------
# 生产环境由 Nginx 提供
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend"), name="static")


@app.get("/")
async def serve_index():
    """Serve 前端页面"""
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    return FileResponse(index_path)
