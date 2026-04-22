/**
 * AI Music Generator - Frontend JS
 */

let currentTaskId = null;
let pollInterval = null;

// ============ 主函数 ============

async function generateMusic() {
    const prompt = document.getElementById('prompt').value.trim();
    const lyrics = document.getElementById('lyrics').value.trim();
    const btn = document.getElementById('generateBtn');

    if (!prompt) {
        alert('请输入风格描述');
        return;
    }
    if (!lyrics) {
        alert('请输入歌词');
        return;
    }

    // 禁用按钮
    btn.disabled = true;
    btn.textContent = '🎵 生成中...';

    // 显示结果区
    const resultCard = document.getElementById('resultCard');
    resultCard.style.display = 'block';
    setStatus('提交中...', true);
    hideError();
    hidePlayer();

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, lyrics })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '提交失败');
        }

        currentTaskId = data.task_id;
        setStatus('生成中（首次约需 60-90 秒）...', true);
        startPolling();

    } catch (err) {
        showError(err.message);
        resetButton();
    }
}

// ============ 轮询 ============

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollStatus, 3000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

async function pollStatus() {
    if (!currentTaskId) return;

    try {
        const response = await fetch(`/api/status/${currentTaskId}`);
        const data = await response.json();

        if (data.status === 'completed') {
            stopPolling();
            setStatus('✅ 生成完成！', false);
            showPlayer(data.audio_url);
            resetButton();
        } else if (data.status === 'failed') {
            stopPolling();
            showError(data.error || '生成失败');
            resetButton();
        } else {
            setStatus('生成中...（请耐心等待约 60-90 秒）', true);
        }
    } catch (err) {
        console.error('Poll error:', err);
    }
}

// ============ UI 辅助 ============

function setStatus(text, spinning) {
    document.getElementById('statusText').textContent = text;
    document.getElementById('spinner').style.display = spinning ? 'inline-block' : 'none';
    const progressFill = document.getElementById('progressFill');
    if (spinning) {
        progressFill.style.animation = 'progress-indeterminate 1.8s ease-in-out infinite';
    } else {
        progressFill.style.animation = 'none';
        progressFill.style.width = '100%';
    }
}

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = '❌ ' + msg;
    el.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}

function showPlayer(audioUrl) {
    const playerArea = document.getElementById('playerArea');
    playerArea.style.display = 'block';
    document.getElementById('audioPlayer').src = audioUrl;
}

function hidePlayer() {
    document.getElementById('playerArea').style.display = 'none';
}

function resetButton() {
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
