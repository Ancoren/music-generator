"""
MiniMax Music Generator - FastAPI Backend
支持两种模式：
1. 手动填词 -> 直接生成音乐
2. 主题 -> AI自动写词 -> 再生成音乐
"""

import os
import uuid
import asyncio
import httpx
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel


# ============ 配置 ============
API_KEY = os.getenv("MINIMAX_API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.minimax.chat")
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


# ============ 数据模型 ============
class GenerateRequest(BaseModel):
    prompt: str                          # 风格描述
    lyrics: str = ""                     # 歌词（手动模式填写）
    auto_lyrics: bool = False            # 是否自动生成歌词
    theme: str = ""                     # 主题（自动模式填写）
    model: str = "music-2.6"


class GenerateResponse(BaseModel):
    task_id: str
    status: str
    phase: str = ""                      # 当前阶段: lyrics|music|done
    audio_url: str | None = None
    generated_lyrics: str | None = None # AI生成的歌词
    error: str | None = None


# ============ 任务状态存储 ============
tasks: dict[str, dict] = {}


# ============ 辅助函数 ============
def parse_lyrics(lyrics_text: str) -> str:
    lines = []
    for line in lyrics_text.strip().split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    return '\n'.join(lines)


async def call_lyrics_generation(theme: str, style: str) -> str | None:
    """调用 lyrics_generation API 自动写词"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "mode": "write_full_song",
                "prompt": f"主题：{theme}，风格：{style}"
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            response = await client.post(
                f"{API_BASE_URL}/v1/lyrics_generation",
                json=payload,
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("lyrics") or data.get("lyrics")
    except Exception as e:
        print(f"Lyrics generation error: {e}")
    return None


async def call_music_generation(prompt: str, lyrics: str, model: str) -> dict | None:
    """调用 music_generation API 生成音乐"""
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
        response = await client.post(
            f"{API_BASE_URL}/v1/music_generation",
            json=payload,
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        raise Exception(f"Music API error {response.status_code}: {response.text}")


async def download_audio(audio_url: str, filename: Path) -> bool:
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


async def generate_music_task(task_id: str, prompt: str, lyrics: str,
                               auto_lyrics: bool, theme: str, model: str):
    """异步生成任务：支持自动写词 + 音乐生成"""
    tasks[task_id] = {
        "status": "processing",
        "phase": "lyrics" if auto_lyrics else "music",
        "audio_url": None,
        "generated_lyrics": None,
        "error": None
    }

    try:
        # ---- 阶段一：自动生成歌词 ----
        if auto_lyrics:
            print(f"[{task_id}] Phase 1: Generating lyrics for theme '{theme}'...")
            generated = await call_lyrics_generation(theme, prompt)
            if not generated:
                tasks[task_id] = {"status": "failed", "error": "Failed to generate lyrics"}
                return
            lyrics = generated
            tasks[task_id]["generated_lyrics"] = lyrics
            tasks[task_id]["phase"] = "music"
            print(f"[{task_id}] Lyrics generated: {len(lyrics)} chars")

        # ---- 阶段二：生成音乐 ----
        print(f"[{task_id}] Phase 2: Generating music...")
        data = await call_music_generation(prompt, lyrics, model)
        audio_url = data.get("data", {}).get("audio")
        if not audio_url:
            tasks[task_id] = {"status": "failed", "error": "No audio URL returned"}
            return

        # 下载音频
        filename = DOWNLOAD_DIR / f"{task_id}.mp3"
        success = await download_audio(audio_url, filename)
        if success:
            tasks[task_id].update({
                "status": "completed",
                "phase": "done",
                "audio_url": f"/api/downloads/{task_id}.mp3",
                "duration": data.get("extra_info", {}).get("music_duration", 0)
            })
            print(f"[{task_id}] Done: {filename}")
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
    if not API_KEY:
        raise HTTPException(status_code=500, detail="MINIMAX_API_KEY not configured")

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt is required")

    if not request.auto_lyrics and not request.lyrics.strip():
        raise HTTPException(status_code=400, detail="lyrics required when auto_lyrics is disabled")

    if request.auto_lyrics and not request.theme.strip():
        raise HTTPException(status_code=400, detail="theme required when auto_lyrics is enabled")

    task_id = str(uuid.uuid4())

    asyncio.create_task(generate_music_task(
        task_id,
        request.prompt,
        request.lyrics,
        request.auto_lyrics,
        request.theme,
        request.model
    ))

    return GenerateResponse(task_id=task_id, status="processing",
                            phase="lyrics" if request.auto_lyrics else "music")


@app.get("/api/status/{task_id}", response_model=GenerateResponse)
async def get_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    t = tasks[task_id]
    return GenerateResponse(
        task_id=task_id,
        status=t["status"],
        phase=t.get("phase", ""),
        audio_url=t.get("audio_url"),
        generated_lyrics=t.get("generated_lyrics"),
        error=t.get("error")
    )


@app.get("/api/downloads/{filename}")
async def download_file(filename: str):
    if not filename.endswith('.mp3'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    file_path = DOWNLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="audio/mpeg", filename=filename)


@app.get("/api/tasks")
async def list_tasks():
    return {
        task_id: {
            "status": t["status"],
            "phase": t.get("phase"),
            "audio_url": t.get("audio_url"),
            "error": t.get("error")
        }
        for task_id, t in tasks.items()
    }


# ---------- 前端静态文件 ----------
app.mount("/static", StaticFiles(directory=Path(__file__).parent.parent / "frontend"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(Path(__file__).parent.parent / "frontend" / "index.html")
