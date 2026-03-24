/**
 * Video Generation — Sora 2
 * Uses /api/video/* endpoints (OpenAI Videos API)
 *
 * Models: sora-2 ($0.10/s), sora-2-pro ($0.30/s)
 * Sizes:  1280x720, 720x1280, 1792x1024, 1024x1792
 * Durations: 4, 8, 12 seconds
 */

export class VideoGen {
    constructor() {
        this.isGenerating = false;
        this.pollTimer = null;
        this.currentJobId = null;
        this.selectedImage = null;  // File object for image-to-video
        this.mode = 'text';         // 'text' or 'image'
        this.COST_PER_SEC = { 'sora-2': 0.10, 'sora-2-pro': 0.30 };
    }

    // ── Modal Control ──────────────────────────────────────────────

    openModal() {
        const modal = document.getElementById('videoGenModal');
        if (modal) {
            modal.classList.add('active', 'open');
            modal.style.display = 'flex';
            this._updateCostEstimate();
            this._bindCostListeners();
            this._setupDragDrop();
        }
    }

    closeModal() {
        const modal = document.getElementById('videoGenModal');
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = 'none';
        }
        this._stopPolling();
    }

    switchTab(tab) {
        document.querySelectorAll('#videoGenModal .vg-tab-btn').forEach(btn => {
            const isActive = btn.dataset.tab === tab;
            btn.style.color = isActive ? 'var(--text-primary)' : 'var(--text-tertiary)';
            btn.style.borderBottomColor = isActive ? 'var(--accent)' : 'transparent';
            btn.classList.toggle('active', isActive);
        });
        document.querySelectorAll('#videoGenModal .vg-tab-panel').forEach(panel => {
            panel.style.display = panel.id === `vg-${tab}` ? 'block' : 'none';
        });
    }

    // ── Mode Toggle (text / image) ─────────────────────────────────

    switchMode(mode) {
        this.mode = mode;
        document.querySelectorAll('.vg-mode-btn').forEach(btn => {
            const isActive = btn.dataset.mode === mode;
            btn.style.background = isActive ? 'var(--accent)' : 'var(--bg-tertiary)';
            btn.style.color = isActive ? '#fff' : 'var(--text-secondary)';
        });
        const uploadZone = document.getElementById('vgImageUploadZone');
        if (uploadZone) uploadZone.style.display = mode === 'image' ? 'block' : 'none';
        const prompt = document.getElementById('vgPrompt');
        if (prompt) {
            prompt.placeholder = mode === 'image'
                ? 'Describe how to animate this image...'
                : 'Describe the video you want to create...';
        }
    }

    // ── Image Upload ───────────────────────────────────────────────

    _setupDragDrop() {
        if (this._dragBound) return;
        this._dragBound = true;
        const zone = document.getElementById('vgDropZone');
        if (!zone) return;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.style.borderColor = 'var(--accent)';
            zone.style.background = 'var(--accent-soft, rgba(99,102,241,0.08))';
        });
        zone.addEventListener('dragleave', () => {
            zone.style.borderColor = 'var(--border-primary)';
            zone.style.background = 'var(--bg-tertiary)';
        });
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.style.borderColor = 'var(--border-primary)';
            zone.style.background = 'var(--bg-tertiary)';
            const file = e.dataTransfer?.files?.[0];
            if (file && file.type.startsWith('image/')) {
                this._setImage(file);
            }
        });
    }

    handleImageSelect(input) {
        const file = input?.files?.[0];
        if (file) this._setImage(file);
    }

    _setImage(file) {
        const maxSize = 20 * 1024 * 1024;
        if (file.size > maxSize) {
            this._showStatus('Image too large (max 20 MB)', 'error');
            return;
        }
        this.selectedImage = file;
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.getElementById('vgPreviewImg');
            if (img) img.src = e.target.result;
            const name = document.getElementById('vgImageName');
            if (name) name.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`;
            const content = document.getElementById('vgDropContent');
            if (content) content.style.display = 'none';
            const preview = document.getElementById('vgImagePreview');
            if (preview) preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    clearImage() {
        this.selectedImage = null;
        const content = document.getElementById('vgDropContent');
        if (content) content.style.display = 'block';
        const preview = document.getElementById('vgImagePreview');
        if (preview) preview.style.display = 'none';
        const input = document.getElementById('vgImageInput');
        if (input) input.value = '';
    }

    // ── Cost Estimate ──────────────────────────────────────────────

    _bindCostListeners() {
        if (this._costBound) return;
        this._costBound = true;
        ['vgDuration', 'vgModel'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => this._updateCostEstimate());
        });
    }

    _updateCostEstimate() {
        const duration = parseInt(document.getElementById('vgDuration')?.value || '8');
        const model = document.getElementById('vgModel')?.value || 'sora-2';
        const rate = this.COST_PER_SEC[model] || 0.10;
        const cost = (duration * rate).toFixed(2);
        const costVal = document.getElementById('vgCostValue');
        if (costVal) costVal.textContent = `$${cost}`;
        const el = document.getElementById('vgCostEstimate');
        if (el) {
            const span = el.querySelector('span:first-child');
            if (span) span.textContent = `💰 ${duration}s × $${rate}/s`;
        }
    }

    // ── Generate ───────────────────────────────────────────────────

    async generate() {
        if (this.isGenerating) return;

        const prompt = document.getElementById('vgPrompt')?.value?.trim();
        if (!prompt) {
            this._showStatus('Please enter a prompt!', 'error');
            return;
        }

        const size = document.getElementById('vgResolution')?.value || '1280x720';
        const seconds = document.getElementById('vgDuration')?.value || '8';
        const model = document.getElementById('vgModel')?.value || 'sora-2';

        if (this.mode === 'image' && !this.selectedImage) {
            this._showStatus('Please upload an image first!', 'error');
            return;
        }

        // Confirmation dialog to prevent accidental spending
        const rate = this.COST_PER_SEC[model] || 0.10;
        const cost = (parseInt(seconds) * rate).toFixed(2);
        const modeLabel = this.mode === 'image' ? 'Image → Video' : 'Text → Video';
        const confirmed = confirm(
            `⚠️ Confirm Video Generation\n\n` +
            `Mode: ${modeLabel}\n` +
            `Model: ${model}\n` +
            `Duration: ${seconds}s | Resolution: ${size}\n` +
            `Estimated cost: $${cost}\n\n` +
            `Prompt: "${prompt.slice(0, 100)}${prompt.length > 100 ? '...' : ''}"\n\n` +
            `Proceed? (You can cancel the job after submitting)`
        );
        if (!confirmed) return;

        this.isGenerating = true;
        const btn = document.getElementById('vgGenerateBtn');
        if (btn) { btn.disabled = true; btn.innerHTML = '⏳ Submitting...'; }

        // Hide previous result, show progress
        this._hideResult();
        const modeLabel = this.mode === 'image' ? 'Image-to-Video' : 'Text-to-Video';
        this._showProgress(`Submitting ${modeLabel} to OpenAI...`, 0);

        try {
            let resp;
            if (this.mode === 'image' && this.selectedImage) {
                // Multipart form-data with image
                const formData = new FormData();
                formData.append('prompt', prompt);
                formData.append('size', size);
                formData.append('seconds', seconds);
                formData.append('model', model);
                formData.append('image', this.selectedImage);
                resp = await fetch('/api/video/generate', {
                    method: 'POST',
                    body: formData,
                });
            } else {
                // JSON body (text-to-video)
                resp = await fetch('/api/video/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, size, seconds, model }),
                });
            }
            const data = await resp.json();

            if (!resp.ok) {
                throw new Error(data.error || `HTTP ${resp.status}`);
            }

            this.currentJobId = data.id;
            this._showStatus(`Job submitted: ${data.id}`, 'info');
            this._showProgress('Queued — waiting for OpenAI...', 0);

            // Start polling
            this._startPolling(data.id);
        } catch (e) {
            this._showStatus(`Error: ${e.message}`, 'error');
            this._hideProgress();
        } finally {
            this.isGenerating = false;
            if (btn) { btn.disabled = false; btn.innerHTML = '🎬 Generate Video'; }
        }
    }

    // ── Polling ────────────────────────────────────────────────────

    _startPolling(jobId) {
        this._stopPolling();
        let interval = 2000;
        let elapsed = 0;

        const poll = async () => {
            try {
                const resp = await fetch(`/api/video/status/${jobId}`);
                const data = await resp.json();

                if (!resp.ok) throw new Error(data.error || 'Poll failed');

                const status = data.status;
                const progress = data.progress || 0;

                if (status === 'completed') {
                    this._stopPolling();
                    this._showProgress('Completed!', 100);
                    this._showVideo(jobId, data);
                    this._showStatus('Video ready!', 'success');
                    return;
                }

                if (status === 'failed') {
                    this._stopPolling();
                    this._showStatus(`Failed: ${data.error || 'Unknown error'}`, 'error');
                    this._hideProgress();
                    return;
                }

                // in_progress / queued
                const label = status === 'queued' ? 'Queued — waiting...' : `Generating... ${progress}%`;
                this._showProgress(label, progress);

                // Backoff: 2s for first 30s, then 5s
                elapsed += interval;
                if (elapsed > 30000 && interval < 5000) interval = 5000;

                this.pollTimer = setTimeout(poll, interval);
            } catch (e) {
                console.error('[VideoGen] Poll error:', e);
                // Keep polling on transient errors
                this.pollTimer = setTimeout(poll, 5000);
            }
        };

        this.pollTimer = setTimeout(poll, interval);
    }

    _stopPolling() {
        if (this.pollTimer) { clearTimeout(this.pollTimer); this.pollTimer = null; }
    }

    // ── UI Helpers ─────────────────────────────────────────────────

    _showStatus(msg, type = 'info') {
        const dot = document.getElementById('vgStatusDot');
        const text = document.getElementById('vgStatusText');
        if (!text) return;
        const colors = { error: '#ef4444', success: '#22c55e', info: 'var(--text-tertiary)', warn: '#f59e0b' };
        const dotColors = { error: '#ef4444', success: '#22c55e', info: 'var(--success, #22c55e)', warn: '#f59e0b' };
        text.style.color = colors[type] || colors.info;
        text.textContent = msg;
        if (dot) dot.style.background = dotColors[type] || dotColors.info;
    }

    _showProgress(label, pct) {
        const wrap = document.getElementById('vgProgress');
        if (wrap) wrap.style.display = 'block';
        const lbl = document.getElementById('vgProgressLabel');
        if (lbl) lbl.textContent = label;
        const pctEl = document.getElementById('vgProgressPct');
        if (pctEl) pctEl.textContent = pct > 0 ? `${pct}%` : '';
        const bar = document.getElementById('vgProgressBar');
        if (bar) bar.style.width = `${pct}%`;
    }

    _hideProgress() {
        const wrap = document.getElementById('vgProgress');
        if (wrap) wrap.style.display = 'none';
    }

    _showVideo(jobId, meta) {
        const wrap = document.getElementById('vgResult');
        if (wrap) wrap.style.display = 'block';
        const video = document.getElementById('vgVideo');
        if (video) {
            video.src = `/api/video/download/${jobId}`;
            video.load();
        }
        const metaEl = document.getElementById('vgResultMeta');
        if (metaEl) {
            const parts = [];
            if (meta.model) parts.push(`Model: ${meta.model}`);
            if (meta.size) parts.push(`Size: ${meta.size}`);
            if (meta.seconds) parts.push(`Duration: ${meta.seconds}s`);
            if (meta.cost_estimate) parts.push(`Cost: ${meta.cost_estimate}`);
            metaEl.textContent = parts.join(' • ');
        }
    }

    _hideResult() {
        const wrap = document.getElementById('vgResult');
        if (wrap) wrap.style.display = 'none';
    }

    downloadCurrent() {
        if (!this.currentJobId) return;
        const a = document.createElement('a');
        a.href = `/api/video/download/${this.currentJobId}`;
        a.download = `${this.currentJobId}.mp4`;
        a.click();
    }

    generateAnother() {
        this._hideResult();
        this._hideProgress();
        this._showStatus('Ready', 'info');
        this.currentJobId = null;
        this.clearImage();
    }

    // ── Cancel ─────────────────────────────────────────────────────

    async cancelCurrentJob() {
        if (!this.currentJobId) return;
        const jobId = this.currentJobId;
        const confirmed = confirm(`🛑 Cancel video job?\n\nJob ID: ${jobId}\n\nThis will attempt to stop the generation and may save you money if OpenAI hasn't finished processing.`);
        if (!confirmed) return;
        await this._doCancelJob(jobId);
    }

    async cancelJob(jobId) {
        const confirmed = confirm(`🛑 Cancel video job?\n\nJob ID: ${jobId}`);
        if (!confirmed) return;
        await this._doCancelJob(jobId);
        this.loadJobs();  // Refresh list
    }

    async _doCancelJob(jobId) {
        const cancelBtn = document.getElementById('vgCancelBtn');
        if (cancelBtn) { cancelBtn.disabled = true; cancelBtn.innerHTML = '⏳ Cancelling...'; }

        try {
            const resp = await fetch(`/api/video/cancel/${jobId}`, { method: 'POST' });
            const data = await resp.json();
            if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);

            this._stopPolling();
            this._hideProgress();
            this._showStatus(`Job ${jobId.slice(0, 12)}... cancelled`, 'warn');

            if (this.currentJobId === jobId) {
                this.currentJobId = null;
                this.isGenerating = false;
                const genBtn = document.getElementById('vgGenerateBtn');
                if (genBtn) { genBtn.disabled = false; genBtn.innerHTML = '🎬 Generate Video'; }
            }
        } catch (e) {
            this._showStatus(`Cancel failed: ${e.message}`, 'error');
        } finally {
            if (cancelBtn) { cancelBtn.disabled = false; cancelBtn.innerHTML = '🛑 Cancel Job — Stop Spending'; }
        }
    }

    // ── Jobs List ──────────────────────────────────────────────────

    async loadJobs() {
        const container = document.getElementById('vgJobsList');
        if (!container) return;
        container.innerHTML = '<p style="color: var(--text-tertiary); text-align: center; padding: 16px;">Loading...</p>';

        try {
            const resp = await fetch('/api/video/list?limit=20');
            const data = await resp.json();
            const jobs = data.videos || [];

            if (jobs.length === 0) {
                container.innerHTML = '<p style="color: var(--text-tertiary); text-align: center; padding: 24px;">No videos yet. Generate your first video!</p>';
                return;
            }

            container.innerHTML = jobs.map(job => {
                const statusIcon = { completed: '🟢', failed: '🔴', in_progress: '🟡', queued: '⚪', cancelled: '🟠' }[job.status] || '⚪';
                const statusLabel = { completed: 'Completed', failed: 'Failed', in_progress: 'In Progress', queued: 'Queued', cancelled: 'Cancelled' }[job.status] || job.status;
                const date = job.created_at ? new Date(job.created_at).toLocaleString() : '';
                const prompt = (job.prompt || '').slice(0, 100) + ((job.prompt || '').length > 100 ? '...' : '');
                const isReady = job.status === 'completed';
                const isActive = job.status === 'in_progress' || job.status === 'queued';
                return `
                    <div style="padding: 14px 16px; margin-bottom: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); border: 1px solid var(--border-primary); transition: all 0.2s;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 6px;">
                                ${statusIcon} ${statusLabel}
                                ${isActive ? '<span style="font-size: 11px; padding: 1px 6px; background: rgba(234,179,8,0.15); color: #eab308; border-radius: 8px;">LIVE</span>' : ''}
                            </span>
                            <span style="font-size: 11px; color: var(--text-tertiary);">${date}</span>
                        </div>
                        <p style="font-size: 13px; color: var(--text-secondary); margin: 6px 0; line-height: 1.4;">${this._escapeHtml(prompt)}</p>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                            <div style="display: flex; gap: 10px; font-size: 12px; color: var(--text-tertiary);">
                                <span>${job.model || ''}</span>
                                <span>${job.size || ''}</span>
                                <span>${job.seconds || ''}s</span>
                                <span style="font-weight: 600; color: var(--accent);">${job.cost_estimate || ''}</span>
                            </div>
                            <div style="display: flex; gap: 6px;">
                                ${isReady ? `<a href="/api/video/download/${job.id}" download style="font-size: 12px; padding: 4px 10px; background: var(--accent); color: #fff; border-radius: var(--radius-sm); text-decoration: none; font-weight: 600;">📥 Download</a>` : ''}
                                ${isActive ? `<button class="vg-job-cancel" onclick="window.videoGen?.cancelJob('${job.id}')" style="font-size: 12px; padding: 4px 10px; background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); border-radius: var(--radius-sm); cursor: pointer; font-weight: 600;">🛑 Cancel</button>` : ''}
                            </div>
                        </div>
                    </div>`;
            }).join('');
        } catch (e) {
            container.innerHTML = `<p style="color: var(--error, #ef4444); text-align: center; padding: 16px;">Error: ${e.message}</p>`;
        }
    }

    _escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}
