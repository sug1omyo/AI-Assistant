/**
 * Message Renderer Module
 * Handles message rendering, markdown parsing, code highlighting
 */

export class MessageRenderer {
    constructor() {
        this.modelNames = {
            'gemini': 'Gemini 2.0 Flash',
            'grok': 'Grok-3',
            'openai': 'GPT-4o-mini',
            'deepseek': 'DeepSeek Chat',
            'deepseek-reasoner': '🧠 DeepSeek R1',
            'qwen': 'Qwen Turbo',
            'bloomvn': 'BloomVN-8B',
            'step-flash': 'Step-3.5 Flash',
            'stepfun': 'StepFun Direct',
            'bloomvn-local': 'BloomVN-8B Local',
            'qwen1.5-local': 'Qwen1.5 Local',
            'qwen2.5-local': 'Qwen2.5-14B Local'
        };
        
        this.modelIcons = {
            'grok': '🤖',
            'deepseek-reasoner': '🧪',
            'openai': '🧠',
            'deepseek': '🔍',
            'gemini': '💎',
            'step-flash': '⚡',
            'bloomvn': '🌸',
            'qwen': '🌙',
            'stepfun': '🚀'
        };
        
        this.contextNames = {
            'casual': '💬 Casual Chat',
            'psychological': '🧘 Psychology',
            'lifestyle': '🌟 Lifestyle',
            'programming': '💻 Programming',
            'creative': '🎨 Creative',
            'research': '🔬 Research'
        };

        this.messageHistory = new Map(); // Store message edit history
        this.initMarked();
        this.bindGlobalEditDelegation();
    }

    bindGlobalEditDelegation() {
        if (window.__editDelegationBound) return;
        window.__editDelegationBound = true;

        document.addEventListener('click', (e) => {
            const editBtn = e.target.closest('.edit-btn, .edit-message-btn');
            if (!editBtn) return;

            const messageDiv = editBtn.closest('.message.user');
            if (!messageDiv) return;

            e.preventDefault();
            e.stopPropagation();

            const textContent = messageDiv.querySelector('.message-text')?.textContent || '';
            this.showEditChatTool(messageDiv, textContent);
        });
    }

    /**
     * Initialize marked.js configuration
     */
    initMarked() {
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                breaks: true,
                gfm: true,
                highlight: function(code, lang) {
                    if (typeof hljs !== 'undefined') {
                        if (lang && hljs.getLanguage(lang)) {
                            return hljs.highlight(code, { language: lang }).value;
                        }
                        return hljs.highlightAuto(code).value;
                    }
                    return code;
                }
            });
        }
    }

    /**
     * Create and add message to chat
     */
    addMessage(chatContainer, content, isUser, model, context, timestamp, thinkingProcess = null, customPromptUsed = false, agentConfig = null) {
        // Hide welcome screen when adding messages
        const welcomeScreen = document.getElementById('welcomeScreen');
        if (welcomeScreen) welcomeScreen.style.display = 'none';

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        messageDiv.dataset.timestamp = timestamp;
        messageDiv.dataset.model = model || '';
        messageDiv.dataset.context = context || '';
        
        // Assign unique message ID for user messages (for history tracking)
        if (isUser) {
            messageDiv.dataset.messageId = `msg_${Date.now()}_${Math.random()}`;
        }

        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message__avatar';
        if (isUser) {
            avatarDiv.textContent = '👤';
        } else {
            avatarDiv.textContent = this.modelIcons[model] || '🤖';
        }
        messageDiv.appendChild(avatarDiv);

        // Body wrapper
        const bodyDiv = document.createElement('div');
        bodyDiv.className = 'message__body';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Add thinking process if provided (for assistant with deep thinking)
        if (!isUser && thinkingProcess) {
            const thinkingDiv = this.createThinkingSection(thinkingProcess);
            contentDiv.appendChild(thinkingDiv);
        }
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        if (isUser) {
            textDiv.textContent = content;
        } else {
            // Parse markdown for assistant messages
            if (typeof marked !== 'undefined') {
                const rawHtml = marked.parse(content);
                textDiv.innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawHtml) : rawHtml;
                
                // Highlight code blocks
                if (typeof hljs !== 'undefined') {
                    textDiv.querySelectorAll('pre code').forEach((block) => {
                        hljs.highlightElement(block);
                    });
                }
                
                // Add copy button for tables
                textDiv.querySelectorAll('table').forEach((table) => {
                    const copyBtn = document.createElement('button');
                    copyBtn.className = 'copy-table-btn';
                    copyBtn.textContent = '📋 Copy bảng';
                    copyBtn.onclick = () => this.copyTableToClipboard(table, copyBtn);
                    table.parentNode.insertBefore(copyBtn, table.nextSibling);
                });
            } else {
                textDiv.textContent = content;
            }
        }
        
        contentDiv.appendChild(textDiv);
        
        // Add model/context info for assistant
        if (!isUser && model && context) {
            const infoDiv = document.createElement('div');
            infoDiv.className = 'message-info';
            
            // Determine prompt/config type indicator
            let configIndicator = '📝 Base Prompt';
            let configDetails = '';
            
            if (agentConfig && agentConfig.enabled) {
                const thinkingMode = agentConfig.thinkingBudget || 'off';
                const temp = agentConfig.temperature || 0.7;
                
                if (thinkingMode === 'advanced') {
                    configIndicator = '🚀 Config Agent (Advanced)';
                    configDetails = ` • T:${temp}`;
                } else if (thinkingMode === 'on') {
                    configIndicator = '⚡ Config Agent (Thinking)';
                    configDetails = ` • T:${temp}`;
                } else {
                    configIndicator = '⚡ Config Agent';
                    configDetails = ` • T:${temp}`;
                }
            } else if (customPromptUsed) {
                configIndicator = '🛠️ Custom Prompt';
            }
            
            infoDiv.textContent = `${this.modelNames[model] || model} • ${this.contextNames[context] || context} • ${configIndicator}${configDetails}`;
            contentDiv.appendChild(infoDiv);
        }
        
        // Add timestamp with version counter for assistant messages
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        
        if (!isUser) {
            // Add version counter badge
            const versionBadge = document.createElement('span');
            versionBadge.className = 'message-version-badge';
            versionBadge.textContent = '1/1';
            timestampDiv.appendChild(versionBadge);
            
            const separator = document.createElement('span');
            separator.textContent = ' • ';
            timestampDiv.appendChild(separator);
        }
        
        const timeSpan = document.createElement('span');
        timeSpan.textContent = timestamp;
        timestampDiv.appendChild(timeSpan);
        
        contentDiv.appendChild(timestampDiv);
        
        // Add action buttons
        this.addMessageButtons(contentDiv, content, isUser, messageDiv);
        
        bodyDiv.appendChild(contentDiv);
        messageDiv.appendChild(bodyDiv);
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageDiv;
    }

    /**
     * Add file attachment message to chat
     */
    addFileMessage(chatContainer, files, timestamp) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message file-message user';
        messageDiv.dataset.timestamp = timestamp;

        // Avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message__avatar';
        avatarDiv.textContent = '👤';
        messageDiv.appendChild(avatarDiv);

        // Body wrapper
        const bodyDiv = document.createElement('div');
        bodyDiv.className = 'message__body';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'file-message-header';
        headerDiv.innerHTML = `📎 <strong>Đã tải lên ${files.length} file${files.length > 1 ? 's' : ''}</strong>`;
        contentDiv.appendChild(headerDiv);
        
        // Create file cards grid
        const filesGrid = document.createElement('div');
        filesGrid.className = 'file-message-grid';
        
        files.forEach((file, index) => {
            const fileCard = document.createElement('div');
            fileCard.className = 'file-message-card';
            
            // Icon or preview
            if (file.preview) {
                fileCard.innerHTML = `
                    <div class="file-message-preview">
                        <img src="${file.preview}" alt="${this.escapeHtml(file.name)}">
                    </div>
                `;
            } else {
                const icon = this.getFileIcon(file.type, file.name);
                fileCard.innerHTML = `
                    <div class="file-message-icon">${icon}</div>
                `;
            }
            
            // File info
            const infoDiv = document.createElement('div');
            infoDiv.className = 'file-message-info';
            infoDiv.innerHTML = `
                <div class="file-message-name" title="${this.escapeHtml(file.name)}">${this.escapeHtml(file.name)}</div>
                <div class="file-message-meta">${this.formatFileSize(file.size)}</div>
            `;
            fileCard.appendChild(infoDiv);
            
            filesGrid.appendChild(fileCard);
        });
        
        contentDiv.appendChild(filesGrid);
        
        // Add timestamp
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'message-timestamp';
        timestampDiv.textContent = timestamp;
        contentDiv.appendChild(timestampDiv);
        
        bodyDiv.appendChild(contentDiv);
        messageDiv.appendChild(bodyDiv);
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return messageDiv;
    }

    /**
     * Get file icon emoji
     */
    getFileIcon(type, name) {
        if (type.startsWith('image/')) return '🖼️';
        if (type.startsWith('video/')) return '🎥';
        if (type.startsWith('audio/')) return '🎵';
        if (type === 'application/pdf') return '📕';
        if (type === 'application/msword' || type.includes('wordprocessing')) return '📘';
        if (type.includes('spreadsheet') || name.endsWith('.xlsx')) return '📊';
        if (type === 'application/json') return '📋';
        if (name.endsWith('.py')) return '🐍';
        if (name.endsWith('.js')) return '📜';
        if (name.endsWith('.html')) return '🌐';
        if (name.endsWith('.css')) return '🎨';
        if (type.startsWith('text/')) return '📄';
        return '📎';
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Create thinking process section (collapsible)
     */
    createThinkingSection(thinkingProcess, isLoading = false) {
        const container = document.createElement('div');
        container.className = 'thinking-container';
        if (isLoading) {
            container.dataset.loading = 'true';
        }
        
        const header = document.createElement('div');
        header.className = 'thinking-header';
        
        const icon = document.createElement('span');
        icon.className = 'thinking-icon';
        icon.textContent = isLoading ? '⏳' : '🧠';
        
        const title = document.createElement('span');
        title.className = 'thinking-title';
        title.textContent = isLoading ? 'Thinking...' : 'Thought Process';
        
        const badge = document.createElement('span');
        badge.className = 'thinking-badge';
        badge.textContent = isLoading ? 'Analyzing' : 'Complete';
        badge.style.cssText = `
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 10px;
            background: ${isLoading ? 'rgba(102, 126, 234, 0.2)' : 'rgba(16, 185, 129, 0.2)'};
            color: ${isLoading ? '#667eea' : '#10b981'};
            font-weight: 600;
            margin-left: 8px;
        `;
        
        const toggle = document.createElement('span');
        toggle.className = 'thinking-toggle';
        toggle.textContent = '▼';
        
        header.appendChild(icon);
        header.appendChild(title);
        header.appendChild(badge);
        header.appendChild(toggle);
        
        const content = document.createElement('div');
        content.className = 'thinking-content';
        
        if (isLoading) {
            content.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px; color: #667eea;">
                    <span style="animation: pulse 1.5s infinite;">🔍</span>
                    <span>Analyzing the problem and generating response...</span>
                </div>
                <div style="margin-top: 8px; font-size: 12px; color: #888;">
                    The AI is thinking deeply about your request. This may take a moment for complex queries.
                </div>
            `;
        } else if (thinkingProcess) {
            // Parse thinking process
            if (typeof thinkingProcess === 'string') {
                content.textContent = thinkingProcess;
            } else {
                content.textContent = JSON.stringify(thinkingProcess, null, 2);
            }
        }
        
        // Toggle functionality
        header.addEventListener('click', () => {
            header.classList.toggle('collapsed');
            content.classList.toggle('collapsed');
        });
        
        container.appendChild(header);
        container.appendChild(content);
        
        return container;
    }
    
    /**
     * Update thinking process content
     */
    updateThinkingContent(container, thinkingProcess) {
        const content = container.querySelector('.thinking-content');
        const header = container.querySelector('.thinking-header');
        const title = header.querySelector('.thinking-title');
        const icon = header.querySelector('.thinking-icon');
        const badge = header.querySelector('.thinking-badge');
        
        if (content && title) {
            // Update icon and title
            if (icon) icon.textContent = '🧠';
            title.textContent = 'Thought Process';
            
            // Update badge
            if (badge) {
                badge.textContent = 'Complete';
                badge.style.background = 'rgba(16, 185, 129, 0.2)';
                badge.style.color = '#10b981';
            }
            
            // Update content
            if (typeof thinkingProcess === 'string') {
                // Format thinking process nicely
                const formatted = thinkingProcess
                    .split('\n')
                    .map(line => {
                        if (line.trim().startsWith('Step') || line.trim().startsWith('Analysis')) {
                            return `<strong style="color: #667eea;">${line}</strong>`;
                        }
                        return line;
                    })
                    .join('\n');
                content.innerHTML = `<pre style="white-space: pre-wrap; margin: 0; font-family: inherit;">${thinkingProcess}</pre>`;
            } else {
                content.textContent = JSON.stringify(thinkingProcess, null, 2);
            }
            
            // Remove loading state
            container.removeAttribute('data-loading');
            container.style.animation = 'none';
        }
    }

    /**
     * Add action buttons to message
     */
    addMessageButtons(contentDiv, content, isUser, messageDiv) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        if (!isUser) {
            // Copy button (Lucide icon)
            const copyBtn = this.createActionButton('copy-btn', 'clipboard', 'Copy');
            copyBtn.onclick = () => this.copyMessageToClipboard(content, copyBtn);
            actionsDiv.appendChild(copyBtn);
            
            // Like button
            const likeBtn = this.createActionButton('like-btn', 'thumbs-up', 'Good response');
            likeBtn.onclick = () => this.toggleFeedback(likeBtn, 'like', messageDiv);
            actionsDiv.appendChild(likeBtn);
            
            // Dislike button
            const dislikeBtn = this.createActionButton('dislike-btn', 'thumbs-down', 'Bad response');
            dislikeBtn.onclick = () => this.toggleFeedback(dislikeBtn, 'dislike', messageDiv);
            actionsDiv.appendChild(dislikeBtn);
            
            // Regenerate button
            const regenBtn = this.createActionButton('regenerate-btn', 'refresh-cw', 'Regenerate');
            regenBtn.onclick = () => this.regenerateResponse(messageDiv);
            actionsDiv.appendChild(regenBtn);
            
            // More options button
            const moreBtn = this.createActionButton('more-btn', 'ellipsis', 'More');
            moreBtn.onclick = () => this.showMoreOptions(messageDiv, moreBtn);
            actionsDiv.appendChild(moreBtn);
        } else {
            // Edit button for user messages
            const editBtn = this.createActionButton('edit-btn', 'pencil', 'Edit');
            editBtn.onclick = () => this.showEditChatTool(messageDiv, content);
            actionsDiv.appendChild(editBtn);
            
            // More options button
            const moreBtn = this.createActionButton('more-btn', 'ellipsis', 'More');
            moreBtn.onclick = () => this.showMoreOptions(messageDiv, moreBtn);
            actionsDiv.appendChild(moreBtn);
        }
        
        contentDiv.appendChild(actionsDiv);
    }

    /**
     * Open Edit Chat tool
     */
    showEditChatTool(messageDiv, originalContent) {
        this.showEditForm(messageDiv, originalContent, true);
    }

    /**
     * Create action button — uses Lucide icons for iOS bubble look
     */
    createActionButton(className, iconName, title) {
        const button = document.createElement('button');
        button.className = `message-action-btn ${className}`;
        button.innerHTML = `<i data-lucide="${iconName}" class="lucide"></i>`;
        button.title = title;
        // Initialize Lucide icon
        requestAnimationFrame(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons({ nodes: [button] });
            }
        });
        return button;
    }
    
    /**
     * Toggle feedback (like/dislike)
     */
    toggleFeedback(button, type, messageDiv) {
        const actionsDiv = button.parentElement;
        const likeBtn = actionsDiv.querySelector('.like-btn');
        const dislikeBtn = actionsDiv.querySelector('.dislike-btn');
        
        if (button.classList.contains('active')) {
            button.classList.remove('active');
            delete messageDiv.dataset.feedback;
        } else {
            likeBtn.classList.remove('active');
            dislikeBtn.classList.remove('active');
            button.classList.add('active');
            messageDiv.dataset.feedback = type;
        }
    }
    
    /**
     * Regenerate response
     */
    regenerateResponse(messageDiv) {
        // Find the user message before this assistant message
        let prevMessage = messageDiv.previousElementSibling;
        while (prevMessage && !prevMessage.classList.contains('user')) {
            prevMessage = prevMessage.previousElementSibling;
        }
        
        if (!prevMessage || !window.chatApp) return;
        
        const userText = prevMessage.querySelector('.message-text')?.textContent;
        if (!userText) return;
        
        // Store current response as version
        const currentResponse = messageDiv.querySelector('.message-text')?.innerHTML;
        const messageId = prevMessage.dataset.messageId || `msg_${Date.now()}_${Math.random()}`;
        prevMessage.dataset.messageId = messageId;
        
        // Save current version before regenerating (user message + current response)
        if (!this.messageHistory.has(messageId)) {
            this.messageHistory.set(messageId, []);
            // Save initial version
            this.addMessageVersion(messageId, userText, currentResponse, new Date().toISOString());
            if (window.chatManager) {
                window.chatManager.saveMessageVersion(messageId, userText, currentResponse, new Date().toISOString());
            }
        }
        
        // Add new empty version that will be filled when response arrives
        this.addMessageVersion(messageId, userText, '', new Date().toISOString());
        if (window.chatManager) {
            window.chatManager.saveMessageVersion(messageId, userText, '', new Date().toISOString());
        }
        
        // Update version indicator
        const history = this.getMessageHistory(messageId);
        prevMessage.dataset.currentVersion = (history.length - 1).toString();
        this.updateVersionIndicator(prevMessage);
        
        // Remove current assistant message
        messageDiv.remove();
        
        // Show loading indicator
        const chatContainer = prevMessage.parentElement;
        if (window.chatApp && window.chatApp.uiUtils) {
            window.chatApp.uiUtils.showLoading();
        }
        
        // Get current form values
        const formValues = window.chatApp.uiUtils.getFormValues();
        
        // Build conversation history
        const history_context = window.chatApp.buildConversationHistory();
        
        // Get selected memories
        const selectedMemories = window.chatApp.memoryManager.getSelectedMemories();
        
        // Create new AbortController
        window.chatApp.currentAbortController = new AbortController();
        
        // Send API request
        window.chatApp.apiService.sendMessage(
            userText,
            formValues.model,
            formValues.context,
            Array.from(window.chatApp.activeTools),
            formValues.deepThinking,
            history_context,
            [],
            selectedMemories,
            window.chatApp.currentAbortController.signal
        ).then(data => {
            // Hide loading
            window.chatApp.uiUtils.hideLoading();
            
            // Add response
            const responseTimestamp = window.chatApp.uiUtils.formatTimestamp(new Date());
            const responseContent = data.error ? `❌ **Lỗi:** ${data.error}` : data.response;
            
            window.chatApp.messageRenderer.addMessage(
                chatContainer,
                responseContent,
                false,
                formValues.model,
                formValues.context,
                responseTimestamp
            );
            
            // Update version history with the new response
            const historyVersions = this.getMessageHistory(messageId);
            if (historyVersions.length > 0) {
                historyVersions[historyVersions.length - 1].assistantResponse = responseContent;
                
                // Save to chatManager
                if (window.chatManager) {
                    const session = window.chatManager.getCurrentSession();
                    if (session && session.messageVersions && session.messageVersions[messageId]) {
                        const versions = session.messageVersions[messageId];
                        if (versions.length > 0) {
                            versions[versions.length - 1].assistantResponse = responseContent;
                            window.chatManager.saveSessions();
                        }
                    }
                }
            }
            
            // Save session
            window.chatApp.saveCurrentSession(true);
            
            // Make images clickable
            setTimeout(() => {
                window.chatApp.messageRenderer.makeImagesClickable((img) => window.chatApp.openImagePreview(img));
            }, 100);
            
        }).catch(error => {
            window.chatApp.uiUtils.hideLoading();
            
            if (error.name === 'AbortError') {
                console.log('[Regenerate] Request aborted by user');
            } else {
                console.error('[Regenerate] Error:', error);
                const errorMsg = window.chatApp.messageRenderer.addMessage(
                    chatContainer,
                    `❌ **Lỗi:** ${error.message || 'Không thể tạo lại response'}`,
                    false,
                    formValues.model,
                    formValues.context,
                    window.chatApp.uiUtils.formatTimestamp(new Date())
                );
            }
        });
    }
    
    /**
     * Show more options menu
     */
    showMoreOptions(messageDiv, button) {
        const isUser = messageDiv.classList.contains('user');
        const content = messageDiv.querySelector('.message-text')?.textContent || '';
        
        // Remove existing popup before opening a new one
        document.querySelectorAll('.message-options-menu').forEach(el => el.remove());

        const menu = document.createElement('div');
        menu.className = 'message-options-menu message-more-popup';
        const lang = localStorage.getItem('chatbot_language') || 'vi';
        menu.innerHTML = `
            <button class="option-item" data-action="copy">
                <span>📋</span> Copy message
            </button>
            ${!isUser ? `
            <button class="option-item" data-action="export">
                <span>📤</span> Export to file
            </button>
            ` : ''}
            <button class="option-item" data-action="fork">
                <span>🔀</span> ${lang === 'vi' ? 'Tách nhánh từ đây' : 'Fork from here'}
            </button>
            <button class="option-item" data-action="delete">
                <span>🗑️</span> Delete message
            </button>
        `;

        // Position menu (below button, clamp within viewport)
        menu.style.position = 'fixed';
        menu.style.visibility = 'hidden';
        document.body.appendChild(menu);

        const rect = button.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        const margin = 10;

        let top = rect.bottom + 8;
        let left = rect.right - menuRect.width;

        if (left < margin) left = margin;
        if (left + menuRect.width > window.innerWidth - margin) {
            left = window.innerWidth - menuRect.width - margin;
        }
        if (top + menuRect.height > window.innerHeight - margin) {
            top = rect.top - menuRect.height - 8;
        }
        if (top < margin) {
            top = margin;
        }

        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;
        menu.style.visibility = 'visible';
        
        // Add event listeners
        menu.querySelectorAll('.option-item').forEach(item => {
            item.addEventListener('click', () => {
                const action = item.dataset.action;
                this.handleMenuAction(action, messageDiv, content);
                menu.remove();
            });
        });
        
        // Close on click outside
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!menu.contains(e.target)) {
                    menu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            });
        }, 10);
    }
    
    /**
     * Handle menu action
     */
    handleMenuAction(action, messageDiv, content) {
        switch(action) {
            case 'copy':
                this.copyMessageToClipboard(content, null);
                break;
            case 'export':
                this.exportMessageToFile(content);
                break;
            case 'fork':
                if (typeof window.chatApp?.handleForkSession === 'function') {
                    window.chatApp.handleForkSession(messageDiv);
                }
                break;
            case 'delete':
                if (confirm('Delete this message?')) {
                    messageDiv.remove();
                }
                break;
        }
    }
    
    /**
     * Export message to file
     */
    exportMessageToFile(content) {
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `message_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    /**
     * Copy message to clipboard
     */
    async copyMessageToClipboard(content, button) {
        const plainText = content.replace(/<[^>]*>/g, '').trim();
        
        try {
            await navigator.clipboard.writeText(plainText);
            
            if (button) {
                const originalHTML = button.innerHTML;
                button.innerHTML = '✅';
                button.classList.add('copied');
                
                setTimeout(() => {
                    button.innerHTML = originalHTML;
                    button.classList.remove('copied');
                }, 2000);
            } else {
                // Show temporary notification
                const notification = document.createElement('div');
                notification.className = 'copy-notification';
                notification.textContent = '✅ Copied to clipboard!';
                document.body.appendChild(notification);
                setTimeout(() => notification.remove(), 2000);
            }
        } catch (err) {
            console.error('Failed to copy:', err);
            alert('Không thể copy. Vui lòng thử lại!');
        }
    }

    /**
     * Copy table to clipboard
     */
    async copyTableToClipboard(table, button) {
        // Convert table to TSV (Tab-separated values) for Excel compatibility
        let tsv = '';
        const rows = table.querySelectorAll('tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('th, td');
            const rowData = [];
            cells.forEach(cell => {
                rowData.push(cell.textContent.trim());
            });
            tsv += rowData.join('\t') + '\n';
        });
        
        try {
            await navigator.clipboard.writeText(tsv);
            const originalText = button.textContent;
            button.textContent = '✅ Đã copy!';
            button.classList.add('copied');
            
            setTimeout(() => {
                button.textContent = originalText;
                button.classList.remove('copied');
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            alert('Không thể copy bảng. Vui lòng thử lại.');
        }
    }

    /**
     * Show edit form for user message
     */
    showEditForm(messageDiv, originalContent, asTool = false) {
        // Check if edit form already exists
        const existingForm = messageDiv.querySelector('.edit-form');
        if (existingForm) {
            existingForm.style.display = '';
            const existingTextarea = existingForm.querySelector('textarea');
            if (existingTextarea) {
                existingTextarea.focus();
                existingTextarea.setSelectionRange(existingTextarea.value.length, existingTextarea.value.length);
            }
            existingForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            return;
        }
        
        // Save current content to history before editing (if not already saved)
        const messageId = messageDiv.dataset.messageId || `msg_${Date.now()}_${Math.random()}`;
        messageDiv.dataset.messageId = messageId;
        
        // Initialize current version index
        if (!messageDiv.dataset.currentVersion) {
            messageDiv.dataset.currentVersion = '0';
        }
        
        // Get corresponding assistant response
        let assistantMsg = messageDiv.nextElementSibling;
        while (assistantMsg && !assistantMsg.classList.contains('assistant')) {
            assistantMsg = assistantMsg.nextElementSibling;
        }
        const assistantResponse = assistantMsg ? assistantMsg.querySelector('.message-text')?.innerHTML : '';
        
        // Only save to history if this is the first edit
        if (!this.messageHistory.has(messageId)) {
            this.addMessageVersion(messageId, originalContent, assistantResponse, new Date().toISOString());
            // Also save to chatManager for persistence
            if (window.chatManager) {
                window.chatManager.saveMessageVersion(messageId, originalContent, assistantResponse, new Date().toISOString());
            }
        }
        
        // Create edit form
        const editForm = document.createElement('div');
        editForm.className = `edit-form ${asTool ? 'edit-chat-tool' : ''}`;

        const modelSelectSource = document.getElementById('modelSelect');
        const contextSelectSource = document.getElementById('contextSelect');

        const toolHeader = document.createElement('div');
        toolHeader.className = 'edit-chat-tool__header';
        toolHeader.innerHTML = '<span class="edit-chat-tool__title">Edit Chat Tool</span>';

        const toolSettings = document.createElement('div');
        toolSettings.className = 'edit-chat-tool__settings';

        const modelWrap = document.createElement('label');
        modelWrap.className = 'edit-chat-tool__field';
        modelWrap.innerHTML = '<span>Model chat</span>';
        const modelSelect = document.createElement('select');
        modelSelect.className = 'edit-chat-tool__select';

        if (modelSelectSource) {
            modelSelect.innerHTML = modelSelectSource.innerHTML;
            modelSelect.value = messageDiv.dataset.model || modelSelectSource.value || 'grok';
        }
        modelWrap.appendChild(modelSelect);

        // ── Rich Agent dropdown (thinkingMode-style) ──
        const agentMeta = [
            { value: 'casual',        icon: 'message-circle', label: 'Casual Chat',  desc: 'Trò chuyện tự nhiên', emoji: '💬' },
            { value: 'programming',   icon: 'code-2',         label: 'Programming',  desc: 'Hỗ trợ lập trình',    emoji: '💻' },
            { value: 'creative',      icon: 'palette',        label: 'Creative',     desc: 'Sáng tạo nội dung',   emoji: '🎨' },
            { value: 'research',      icon: 'search',         label: 'Research',     desc: 'Nghiên cứu chuyên sâu',emoji: '🔬' },
            { value: 'psychological', icon: 'heart-handshake',label: 'Psychology',   desc: 'Tâm lý & tư vấn',     emoji: '🧘' },
            { value: 'lifestyle',     icon: 'sparkles',       label: 'Lifestyle',    desc: 'Phong cách sống',      emoji: '🌟' },
        ];

        const currentAgent = messageDiv.dataset.context || (contextSelectSource ? contextSelectSource.value : 'casual');
        const currentMeta = agentMeta.find(a => a.value === currentAgent) || agentMeta[0];

        const agentWrap = document.createElement('div');
        agentWrap.className = 'edit-chat-tool__field edit-chat-tool__agent-field';
        agentWrap.innerHTML = '<span>Agent chat</span>';

        // Hidden select stays for form value
        const agentSelect = document.createElement('select');
        agentSelect.className = 'edit-chat-tool__select';
        agentSelect.style.display = 'none';
        if (contextSelectSource) {
            agentSelect.innerHTML = contextSelectSource.innerHTML;
            agentSelect.value = currentAgent;
        }

        // Trigger button
        const agentBtn = document.createElement('button');
        agentBtn.type = 'button';
        agentBtn.className = 'edit-chat-tool__agent-btn';
        agentBtn.innerHTML = `<span class="edit-agent-icon"><i data-lucide="${currentMeta.icon}" class="lucide"></i></span>`
            + `<span class="edit-agent-label">${currentMeta.label}</span>`
            + `<i data-lucide="chevron-down" class="lucide edit-agent-chevron"></i>`;

        // Dropdown panel
        const agentDrop = document.createElement('div');
        agentDrop.className = 'edit-agent-dropdown model-dropdown hidden';
        const groupDiv = document.createElement('div');
        groupDiv.className = 'model-dropdown__group';
        groupDiv.innerHTML = '<div class="model-dropdown__group-label">Agent</div>';

        agentMeta.forEach(m => {
            const item = document.createElement('div');
            item.className = `model-dropdown__item edit-agent-option${m.value === currentAgent ? ' active' : ''}`;
            item.dataset.value = m.value;
            item.innerHTML =
                `<span class="model-dropdown__item-icon"><i data-lucide="${m.icon}" class="lucide"></i></span>`
                + `<div class="model-dropdown__item-info">`
                +   `<div class="model-dropdown__item-name">${m.emoji} ${m.label}</div>`
                +   `<div class="model-dropdown__item-desc">${m.desc}</div>`
                + `</div>`;
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                agentSelect.value = m.value;
                agentBtn.querySelector('.edit-agent-icon').innerHTML = `<i data-lucide="${m.icon}" class="lucide"></i>`;
                agentBtn.querySelector('.edit-agent-label').textContent = m.label;
                agentDrop.querySelectorAll('.edit-agent-option').forEach(o => o.classList.remove('active'));
                item.classList.add('active');
                agentDrop.classList.add('hidden');
                agentDrop.classList.remove('open');
                if (window.lucide) lucide.createIcons({ nodes: [agentBtn] });
            });
            groupDiv.appendChild(item);
        });
        agentDrop.appendChild(groupDiv);

        // Toggle dropdown
        agentBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = !agentDrop.classList.contains('hidden');
            agentDrop.classList.toggle('hidden', isOpen);
            agentDrop.classList.toggle('open', !isOpen);
        });

        // Close on outside click
        const closeAgent = (e) => {
            if (!agentWrap.contains(e.target)) {
                agentDrop.classList.add('hidden');
                agentDrop.classList.remove('open');
            }
        };
        document.addEventListener('click', closeAgent);
        // Cleanup when form removed
        const agentObserver = new MutationObserver(() => {
            if (!document.contains(agentWrap)) {
                document.removeEventListener('click', closeAgent);
                agentObserver.disconnect();
            }
        });
        agentObserver.observe(messageDiv, { childList: true, subtree: true });

        agentWrap.appendChild(agentSelect);
        agentWrap.appendChild(agentBtn);
        agentWrap.appendChild(agentDrop);

        toolSettings.appendChild(modelWrap);
        toolSettings.appendChild(agentWrap);

        // Initialize lucide icons after DOM ready
        requestAnimationFrame(() => {
            if (window.lucide) lucide.createIcons({ nodes: [agentWrap] });
        });
        
        const textarea = document.createElement('textarea');
        textarea.className = 'edit-chat-tool__textarea';
        textarea.value = originalContent;
        textarea.placeholder = 'Chỉnh sửa tin nhắn...';
        
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'edit-form-buttons';
        
        const saveBtn = document.createElement('button');
        saveBtn.className = 'edit-save-btn';
        saveBtn.textContent = '💾 Lưu & Tạo lại response';
        saveBtn.onclick = () => {
            const newContent = textarea.value.trim();
            console.log('[Edit] Save clicked', {
                messageId,
                currentVersion: messageDiv.dataset.currentVersion,
                hasCallback: !!this.onEditSave,
                hasChatAppFallback: !!(window.chatApp && typeof window.chatApp.handleEditSave === 'function')
            });

            // Apply selected model/agent globally for next regeneration
            if (modelSelectSource && modelSelect.value) {
                modelSelectSource.value = modelSelect.value;
                modelSelectSource.dispatchEvent(new Event('change'));

                const modelLabel = document.getElementById('modelSelectorLabel');
                if (modelLabel) {
                    const selectedOption = modelSelect.options[modelSelect.selectedIndex];
                    modelLabel.textContent = selectedOption ? selectedOption.textContent : modelSelect.value;
                }
            }

            if (contextSelectSource && agentSelect.value) {
                contextSelectSource.value = agentSelect.value;
                contextSelectSource.dispatchEvent(new Event('change'));
            }

            // Persist chosen model/agent on this message
            if (modelSelect.value) messageDiv.dataset.model = modelSelect.value;
            if (agentSelect.value) messageDiv.dataset.context = agentSelect.value;

            if (newContent && newContent !== originalContent) {
                const previousVersion = parseInt(messageDiv.dataset.currentVersion || '0', 10);
                if (window.chatApp && typeof window.chatApp.syncConversationBranches === 'function' && !Number.isNaN(previousVersion)) {
                    // Capture current downstream branch before creating a new version.
                    window.chatApp.syncConversationBranches();
                }

                // Find and save old assistant response before removing
                let nextMsg = messageDiv.nextElementSibling;
                while (nextMsg && !nextMsg.classList.contains('assistant')) {
                    nextMsg = nextMsg.nextElementSibling;
                }
                const oldResponse = nextMsg ? nextMsg.querySelector('.message-text')?.innerHTML : '';
                
                // Save new version with empty response (will be filled after regeneration)
                this.addMessageVersion(messageId, newContent, '', new Date().toISOString());
                if (window.chatManager) {
                    window.chatManager.saveMessageVersion(messageId, newContent, '', new Date().toISOString());
                }
                
                // Update message content
                const textDiv = messageDiv.querySelector('.message-text');
                textDiv.textContent = newContent;
                
                // Update version indicator
                const history = this.getMessageHistory(messageId);
                const currentIdx = history.length - 1;
                messageDiv.dataset.currentVersion = currentIdx.toString();
                this.updateVersionIndicator(messageDiv);
                
                // Remove edit form
                editForm.remove();
                
                // Find and remove subsequent assistant message
                if (nextMsg) {
                    nextMsg.remove();
                }
                
                // Regenerate response with edited message
                if (this.onEditSave) {
                    this.onEditSave(messageDiv, newContent, originalContent);
                } else if (window.chatApp && typeof window.chatApp.handleEditSave === 'function') {
                    // Fallback for edge cases where callback binding is missing on restored sessions
                    window.chatApp.handleEditSave(messageDiv, newContent, originalContent);
                } else {
                    // Avoid silent failure: user can see that regenerate did not run
                    console.error('[Edit] Missing onEditSave callback and fallback handler.');
                    if (window.chatApp?.uiUtils?.showAlert) {
                        window.chatApp.uiUtils.showAlert('Khong the tao lai response: callback Edit chua duoc khoi tao. Hay reload trang.');
                    }
                }
            }
        };
        
        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'edit-cancel-btn';
        cancelBtn.textContent = '❌ Hủy';
        cancelBtn.onclick = () => editForm.remove();
        
        buttonsDiv.appendChild(saveBtn);
        buttonsDiv.appendChild(cancelBtn);
        editForm.appendChild(toolHeader);
        editForm.appendChild(toolSettings);
        editForm.appendChild(textarea);
        editForm.appendChild(buttonsDiv);
        
        messageDiv.querySelector('.message-content').appendChild(editForm);
        textarea.focus();
    }

    /**
     * Add message version to history
     */
    addMessageVersion(messageId, userContent, assistantResponse, timestamp) {
        if (!this.messageHistory.has(messageId)) {
            this.messageHistory.set(messageId, []);
        }
        
        this.messageHistory.get(messageId).push({
            userContent: userContent,
            assistantResponse: assistantResponse,
            timestamp: timestamp
        });
    }
    
    /**
     * Update version indicator with navigation buttons
     */
    updateVersionIndicator(messageDiv) {
        const messageId = messageDiv.dataset.messageId;
        if (!messageId) return;
        
        const history = this.getMessageHistory(messageId);
        if (history.length <= 1) return;
        
        const currentIdx = parseInt(messageDiv.dataset.currentVersion || '0');
        const total = history.length;
        
        // Find or create version badge in timestamp
        const timestampDiv = messageDiv.querySelector('.message-timestamp');
        if (!timestampDiv) return;
        
        let versionBadge = timestampDiv.querySelector('.message-version-badge');
        if (!versionBadge) {
            versionBadge = document.createElement('span');
            versionBadge.className = 'message-version-badge';
            timestampDiv.insertBefore(versionBadge, timestampDiv.firstChild);
            
            const separator = document.createElement('span');
            separator.textContent = ' • ';
            timestampDiv.insertBefore(separator, versionBadge.nextSibling);
        }
        
        // Create navigation controls
        const navContainer = document.createElement('span');
        navContainer.className = 'version-navigation';
        
        // Back button
        const backBtn = document.createElement('button');
        backBtn.className = 'version-nav-btn';
        backBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>';
        backBtn.title = 'Previous version';
        backBtn.disabled = currentIdx === 0;
        backBtn.onclick = () => this.navigateVersion(messageDiv, currentIdx - 1);
        
        // Version counter
        const counter = document.createElement('span');
        counter.className = 'version-counter';
        counter.textContent = `${currentIdx + 1}/${total}`;
        
        // Forward button
        const forwardBtn = document.createElement('button');
        forwardBtn.className = 'version-nav-btn';
        forwardBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>';
        forwardBtn.title = 'Next version';
        forwardBtn.disabled = currentIdx === total - 1;
        forwardBtn.onclick = () => this.navigateVersion(messageDiv, currentIdx + 1);
        
        navContainer.appendChild(backBtn);
        navContainer.appendChild(counter);
        navContainer.appendChild(forwardBtn);
        
        versionBadge.innerHTML = '';
        versionBadge.appendChild(navContainer);
    }
    
    /**
     * Navigate to specific version
     */
    navigateVersion(messageDiv, newIndex) {
        const messageId = messageDiv.dataset.messageId;
        const history = this.getMessageHistory(messageId);
        
        if (newIndex < 0 || newIndex >= history.length) return;

        const oldIndex = parseInt(messageDiv.dataset.currentVersion || '0');
        const direction = newIndex > oldIndex ? 1 : -1; // 1 = forward, -1 = back
        
        // ── Smooth user-message crossfade ──
        const textDiv = messageDiv.querySelector('.message-text');
        if (textDiv) {
            textDiv.style.transition = 'none';
            textDiv.style.opacity = '1';
            textDiv.style.transform = 'translateX(0)';
            // Force reflow
            void textDiv.offsetWidth;
            textDiv.style.transition = 'opacity .22s ease, transform .22s ease';
            textDiv.style.opacity = '0';
            textDiv.style.transform = `translateX(${direction * -18}px)`;

            setTimeout(() => {
                textDiv.textContent = history[newIndex].userContent;
                textDiv.style.transform = `translateX(${direction * 18}px)`;
                // Force reflow
                void textDiv.offsetWidth;
                textDiv.style.opacity = '1';
                textDiv.style.transform = 'translateX(0)';
            }, 200);
        }
        
        // ── Smooth assistant-message crossfade ──
        let assistantMsg = messageDiv.nextElementSibling;
        while (assistantMsg && !assistantMsg.classList.contains('assistant')) {
            assistantMsg = assistantMsg.nextElementSibling;
        }
        
        const hasResponse = history[newIndex].assistantResponse && history[newIndex].assistantResponse.trim() !== '';
        
        if (hasResponse && assistantMsg) {
            const assistantTextDiv = assistantMsg.querySelector('.message-text');
            if (assistantTextDiv) {
                assistantTextDiv.style.transition = 'none';
                assistantTextDiv.style.opacity = '1';
                assistantTextDiv.style.transform = 'translateX(0)';
                void assistantTextDiv.offsetWidth;
                assistantTextDiv.style.transition = 'opacity .22s ease, transform .22s ease';
                assistantTextDiv.style.opacity = '0';
                assistantTextDiv.style.transform = `translateX(${direction * -18}px)`;

                setTimeout(() => {
                    assistantTextDiv.innerHTML = history[newIndex].assistantResponse;
                    if (typeof hljs !== 'undefined') {
                        assistantTextDiv.querySelectorAll('pre code').forEach(b => hljs.highlightElement(b));
                    }
                    assistantTextDiv.style.transform = `translateX(${direction * 18}px)`;
                    void assistantTextDiv.offsetWidth;
                    assistantTextDiv.style.opacity = '1';
                    assistantTextDiv.style.transform = 'translateX(0)';
                }, 200);
            }
        } else if (hasResponse && !assistantMsg) {
            const chatContainer = messageDiv.parentElement;
            const model = messageDiv.dataset.model || 'gemini';
            const context = messageDiv.dataset.context || 'casual';
            const timestamp = messageDiv.dataset.timestamp || new Date().toLocaleTimeString('vi-VN');
            
            const tempContainer = document.createElement('div');
            this.addMessage(tempContainer, history[newIndex].assistantResponse, false, model, context, timestamp);
            const newAssistantMsg = tempContainer.firstChild;
            newAssistantMsg.style.opacity = '0';
            newAssistantMsg.style.transform = `translateX(${direction * 18}px)`;
            messageDiv.parentNode.insertBefore(newAssistantMsg, messageDiv.nextSibling);
            void newAssistantMsg.offsetWidth;
            newAssistantMsg.style.transition = 'opacity .28s ease, transform .28s ease';
            newAssistantMsg.style.opacity = '1';
            newAssistantMsg.style.transform = 'translateX(0)';
        }
        
        // Update current version
        messageDiv.dataset.currentVersion = newIndex.toString();

        // Restore downstream conversation branch for selected version (Grok-like branching).
        if (window.chatApp && typeof window.chatApp.applyVersionBranch === 'function') {
            window.chatApp.applyVersionBranch(messageDiv, newIndex);
        }
        
        // Refresh version indicator
        this.updateVersionIndicator(messageDiv);
    }

    /**
     * Get message history
     */
    getMessageHistory(messageId) {
        return this.messageHistory.get(messageId) || [];
    }

    /**
     * Make images clickable for preview
     */
    makeImagesClickable(onImageClick) {
        // Query for images in message content and generated preview images
        const images = document.querySelectorAll('.message-content img, .message-text img, .generated-preview, img[alt="Generated Image"]');
        console.log(`[Image Preview] Found ${images.length} images`);
        
        images.forEach(img => {
            if (!img.hasAttribute('data-clickable')) {
                img.setAttribute('data-clickable', 'true');
                img.style.cursor = 'zoom-in';
                img.addEventListener('click', function(e) {
                    e.stopPropagation();
                    console.log('[Image Preview] Image clicked:', this.src?.substring(0, 100));
                    if (onImageClick) {
                        onImageClick(this);
                    }
                });
                console.log('[Image Preview] Made clickable:', img.alt || img.src?.substring(0, 50));
            }
        });
    }

    /**
     * Re-attach event listeners after loading chat
     */
    reattachEventListeners(chatContainer, onEditSave, onCopy, onImageClick) {
        // Re-attach all message action buttons
        chatContainer.querySelectorAll('.message').forEach(messageDiv => {
            const isUser = messageDiv.classList.contains('user');
            const content = messageDiv.querySelector('.message-text')?.textContent || '';
            const contentHTML = messageDiv.querySelector('.message-text')?.innerHTML || '';
            
            // Find action buttons container
            const actionsDiv = messageDiv.querySelector('.message-actions');
            if (!actionsDiv) return;
            
            if (!isUser) {
                // Assistant message actions
                const copyBtn = actionsDiv.querySelector('.copy-btn');
                if (copyBtn) {
                    copyBtn.onclick = () => this.copyMessageToClipboard(contentHTML, copyBtn);
                }
                
                const likeBtn = actionsDiv.querySelector('.like-btn');
                if (likeBtn) {
                    likeBtn.onclick = () => this.toggleFeedback(likeBtn, 'like', messageDiv);
                }
                
                const dislikeBtn = actionsDiv.querySelector('.dislike-btn');
                if (dislikeBtn) {
                    dislikeBtn.onclick = () => this.toggleFeedback(dislikeBtn, 'dislike', messageDiv);
                }
                
                const regenBtn = actionsDiv.querySelector('.regenerate-btn');
                if (regenBtn) {
                    regenBtn.onclick = () => this.regenerateResponse(messageDiv);
                }
                
                const moreBtn = actionsDiv.querySelector('.more-btn');
                if (moreBtn) {
                    moreBtn.onclick = () => this.showMoreOptions(messageDiv, moreBtn);
                }
            } else {
                // User message actions
                const editBtn = actionsDiv.querySelector('.edit-btn');
                if (editBtn) {
                    editBtn.onclick = () => this.showEditChatTool(messageDiv, content);
                }
                
                const moreBtn = actionsDiv.querySelector('.more-btn');
                if (moreBtn) {
                    moreBtn.onclick = () => this.showMoreOptions(messageDiv, moreBtn);
                }
            }
        });
        
        // Re-attach version navigation buttons
        chatContainer.querySelectorAll('.version-nav-btn').forEach(btn => {
            const messageDiv = btn.closest('.message');
            if (!messageDiv) return;
            
            const currentVersion = parseInt(messageDiv.dataset.currentVersion || '0');
            const isBack = (btn.title || '').toLowerCase().includes('previous');
            const newIndex = isBack ? currentVersion - 1 : currentVersion + 1;
            
            btn.onclick = () => this.navigateVersion(messageDiv, newIndex);
        });
        
        // Legacy buttons (old style - keep for compatibility)
        chatContainer.querySelectorAll('.edit-message-btn').forEach(btn => {
            const messageDiv = btn.closest('.message');
            const textContent = messageDiv.querySelector('.message-text')?.textContent || '';
            btn.onclick = () => this.showEditChatTool(messageDiv, textContent);
        });
        
        chatContainer.querySelectorAll('.copy-message-btn').forEach(btn => {
            const messageDiv = btn.closest('.message');
            const textContent = messageDiv.querySelector('.message-text')?.textContent || '';
            btn.onclick = () => this.copyMessageToClipboard(textContent, btn);
        });
        
        // Table copy buttons
        chatContainer.querySelectorAll('.copy-table-btn').forEach(btn => {
            const table = btn.previousElementSibling;
            if (table && table.tagName === 'TABLE') {
                btn.onclick = () => this.copyTableToClipboard(table, btn);
            }
        });
        
        // Make images clickable
        if (onImageClick) {
            this.makeImagesClickable(onImageClick);
        }
    }

    /**
     * Set edit save callback
     */
    setEditSaveCallback(callback) {
        this.onEditSave = callback;
    }
    
    /**
     * Open image preview modal
     */
    openImagePreview(imgElement) {
        const modal = document.getElementById('imagePreviewModal');
        const previewImg = document.getElementById('imagePreviewContent');
        const previewInfo = document.getElementById('imagePreviewInfo');
        
        if (modal && previewImg) {
            if (window.resetPreviewZoom) window.resetPreviewZoom();
            previewImg.src = imgElement.src;
            previewImg.dataset.downloadUrl = imgElement.src;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            
            if (previewInfo) {
                const img = new Image();
                img.onload = () => {
                    previewInfo.innerHTML = `
                        <div class="lightbox__meta-grid">
                            <div class="lightbox__meta-item"><span class="lightbox__meta-label">Dimensions</span><span class="lightbox__meta-value">${img.width} × ${img.height}</span></div>
                        </div>
                    `;
                };
                img.src = imgElement.src;
            }
        }
    }
    
    closeImagePreview() {
        const modal = document.getElementById('imagePreviewModal');
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    downloadPreviewImage() {
        const previewImg = document.getElementById('imagePreviewContent');
        if (previewImg && previewImg.src) {
            const link = document.createElement('a');
            link.href = previewImg.dataset.downloadUrl || previewImg.src;
            link.download = `image_${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }
}
