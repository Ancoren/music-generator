/**
 * AI Music Generator - Frontend JS
 * 支持手动填词 / AI自动写词双模式
 */

let currentTaskId = null;
let pollInterval = null;
let currentMode = 'manual';

// ============ 模式切换 ============

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.mode === mode);
    });
    document.getElementById('manualSection').style.display = mode === 'manual' ? 'block' : 'none';
    document.getElementById('autoSection').style.display = mode === 'auto' ? 'block' : 'none';
    document.getElementById('generatedLyricsArea').style.display = 'none';
    hideResult();
}

function hideResult() {
    document.getElementById('resultCard').style.display = 'none';
}

// ============ 主函数 ============

async function generateMusic() {
    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) { alert('请输入风格描述'); return; }

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = currentMode === 'auto' ? '🤖 写词中...' : '🎵 生成中...';

    showResult();
    hideError();
    hidePlayer();

    try {
        let payload;
        if (currentMode === 'manual') {
            const lyrics = document.getElementById('lyrics').value.trim();
            if (!lyrics) { alert('请输入歌词'); resetBtn(); return; }
            payload = { prompt, lyrics, auto_lyrics: false };
        } else {
            const theme = document.getElementById('theme').value.trim();
            if (!theme) { alert('请输入歌曲主题'); resetBtn(); return; }
            payload = { prompt, theme, auto_lyrics: true };
        }

        setStatus('提交任务...', true);
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || '提交失败');

        currentTaskId = data.task_id;
        setPhase(data.phase === 'lyrics' ? 'lyrics' : 'music');
        startPolling();

    } catch (err) {
        showError(err.message);
        resetBtn();
    }
}

// ============ 轮询 ============

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollStatus, 3000);
}

function stopPolling() {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
}

async function pollStatus() {
    if (!currentTaskId) return;
    try {
        const response = await fetch(`/api/status/${currentTaskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
            stopPolling();
            setPhase('done');
            if (data.generated_lyrics) {
                document.getElementById('generatedLyrics').value = data.generated_lyrics;
            }
            showPlayer(data.audio_url, data.generated_lyrics);
            resetBtn();

        } else if (data.status === 'failed') {
            stopPolling();
            showError(data.error || '生成失败');
            resetBtn();

        } else {
            // processing
            if (data.phase === 'lyrics') {
                setPhase('lyrics');
            } else {
                setPhase('music');
            }
        }
    } catch (err) {
        console.error('Poll error:', err);
    }
}

// ============ UI ============

function setPhase(phase) {
    const spinner = document.getElementById('spinner');
    const lyricsStage = document.getElementById('lyricsStage');
    const progressFill = document.getElementById('progressFill');

    if (phase === 'lyrics') {
        setStatus('🤖 AI 正在生成歌词...', true);
        lyricsStage.style.display = 'block';
        progressFill.style.animation = 'progress-indeterminate 1.8s ease-in-out infinite';
    } else if (phase === 'music') {
        setStatus('🎵 正在生成音乐（约需 60-90 秒）...', true);
        lyricsStage.style.display = 'none';
        progressFill.style.animation = 'progress-indeterminate 1.8s ease-in-out infinite';
    } else {
        setStatus('✅ 完成！', false);
        lyricsStage.style.display = 'none';
        progressFill.style.animation = 'none';
        progressFill.style.width = '100%';
    }
}

function setStatus(text, spinning) {
    document.getElementById('statusText').textContent = text;
    document.getElementById('spinner').style.display = spinning ? 'inline-block' : 'none';
}

function showResult() {
    document.getElementById('resultCard').style.display = 'block';
    document.getElementById('lyricsStage').style.display = 'none';
    document.getElementById('playerArea').style.display = 'none';
    document.getElementById('errorMsg').style.display = 'none';
    const progressFill = document.getElementById('progressFill');
    progressFill.style.animation = 'none';
    progressFill.style.width = '0%';
}

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = '❌ ' + msg;
    el.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}

function showPlayer(audioUrl, generatedLyrics) {
    const playerArea = document.getElementById('playerArea');
    playerArea.style.display = 'block';
    document.getElementById('audioPlayer').src = audioUrl;

    // 显示歌词
    const lyricsEl = document.getElementById('finalLyrics');
    if (generatedLyrics) {
        const displayLyrics = generatedLyrics
            .replace(/\[([^\]]+)\]/g, '<span class="lyric-section">[$1]</span>')
            .replace(/\n/g, '<br>');
        lyricsEl.innerHTML = `<div class="lyrics-display"><strong>📋 歌词：</strong><br>${displayLyrics}</div>`;
        lyricsEl.style.display = 'block';
    } else {
        lyricsEl.style.display = 'none';
    }
}

function hidePlayer() {
    document.getElementById('playerArea').style.display = 'none';
    document.getElementById('finalLyrics').style.display = 'none';
}

function resetBtn() {
    const btn = document.getElementById('generateBtn');
    btn.disabled = false;
    btn.textContent = '🎵 生成音乐';
}

function downloadTrack() {
    const src = document.getElementById('audioPlayer').src;
    if (!src) return;
    const a = document.createElement('a');
    a.href = src;
    a.download = 'ai-music.mp3';
    a.click();
}
