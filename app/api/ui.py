"""Minimal HTML chat UI - single page, no frameworks."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def chat_ui():
    """Serve minimal HTML chat UI."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Intelligence Agent</title>
    <style>
        /* Design Tokens - iOS 26 Inspired */
        :root {
            /* Colors */
            --color-primary: #007AFF;
            --color-primary-hover: #0051D5;
            --color-surface: rgba(255, 255, 255, 0.7);
            --color-surface-elevated: rgba(255, 255, 255, 0.85);
            --color-background: linear-gradient(135deg, #F5F7FA 0%, #E8ECF1 100%);
            --color-text-primary: rgba(0, 0, 0, 0.85);
            --color-text-secondary: rgba(0, 0, 0, 0.6);
            --color-text-tertiary: rgba(0, 0, 0, 0.4);
            --color-border: rgba(0, 0, 0, 0.08);
            --color-shadow: rgba(0, 0, 0, 0.08);
            --color-shadow-elevated: rgba(0, 0, 0, 0.12);
            
            /* Spacing */
            --spacing-xs: 4px;
            --spacing-sm: 8px;
            --spacing-md: 16px;
            --spacing-lg: 24px;
            --spacing-xl: 32px;
            --spacing-2xl: 48px;
            --spacing-3xl: 64px;
            
            /* Typography */
            --font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
            --font-size-xs: 11px;
            --font-size-sm: 13px;
            --font-size-base: 15px;
            --font-size-lg: 17px;
            --font-size-xl: 20px;
            --font-size-2xl: 28px;
            --font-weight-regular: 400;
            --font-weight-medium: 500;
            --font-weight-semibold: 600;
            
            /* Elevation */
            --blur-sm: 10px;
            --blur-md: 20px;
            --blur-lg: 30px;
            --shadow-sm: 0 1px 3px var(--color-shadow);
            --shadow-md: 0 4px 12px var(--color-shadow);
            --shadow-lg: 0 8px 24px var(--color-shadow-elevated);
            
            /* Motion */
            --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: 250ms cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--font-family);
            background: var(--color-background);
            background-attachment: fixed;
            height: 100vh;
            display: flex;
            flex-direction: column;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            color: var(--color-text-primary);
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        /* Glassmorphic Header */
        .header {
            background: var(--color-surface-elevated);
            backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            border-bottom: 0.5px solid var(--color-border);
            padding: var(--spacing-xl) var(--spacing-lg);
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: var(--shadow-sm);
        }
        
        .header h1 {
            font-size: var(--font-size-2xl);
            font-weight: var(--font-weight-semibold);
            letter-spacing: -0.5px;
            color: var(--color-text-primary);
            margin: 0;
        }
        
        /* Messages Container */
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--spacing-xl) var(--spacing-lg);
            display: flex;
            flex-direction: column;
            gap: var(--spacing-md);
            scroll-behavior: smooth;
        }
        
        .messages::-webkit-scrollbar {
            width: 4px;
        }
        
        .messages::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .messages::-webkit-scrollbar-thumb {
            background: var(--color-border);
            border-radius: 2px;
        }
        
        .messages::-webkit-scrollbar-thumb:hover {
            background: var(--color-text-tertiary);
        }
        
        /* Message Bubbles */
        .message {
            padding: var(--spacing-md) var(--spacing-lg);
            border-radius: 20px;
            max-width: 75%;
            word-wrap: break-word;
            white-space: pre-wrap;
            font-size: var(--font-size-base);
            line-height: 1.5;
            transition: transform var(--transition-base), opacity var(--transition-base);
            animation: messageSlideIn var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        @keyframes messageSlideIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            background: var(--color-primary);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 6px;
            box-shadow: var(--shadow-md);
        }
        
        .message.user:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-lg);
        }
        
        .message.agent {
            background: var(--color-surface);
            backdrop-filter: blur(var(--blur-md)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-md)) saturate(180%);
            color: var(--color-text-primary);
            align-self: flex-start;
            border-bottom-left-radius: 6px;
            box-shadow: var(--shadow-sm);
            border: 0.5px solid var(--color-border);
        }
        
        .message.agent:hover {
            background: var(--color-surface-elevated);
            transform: translateY(-1px);
        }
        
        .message.loading {
            color: var(--color-text-secondary);
            font-style: normal;
            opacity: 0.7;
        }
        
        /* Input Area - Glassmorphic */
        .input-area {
            padding: var(--spacing-lg);
            background: var(--color-surface-elevated);
            backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            border-top: 0.5px solid var(--color-border);
            display: flex;
            gap: var(--spacing-md);
            align-items: center;
            position: sticky;
            bottom: 0;
            z-index: 100;
            box-shadow: 0 -2px 12px var(--color-shadow);
        }
        
        .input-area input {
            flex: 1;
            padding: var(--spacing-md) var(--spacing-lg);
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(var(--blur-sm));
            -webkit-backdrop-filter: blur(var(--blur-sm));
            border: 0.5px solid var(--color-border);
            border-radius: 20px;
            font-size: var(--font-size-base);
            font-family: var(--font-family);
            color: var(--color-text-primary);
            transition: all var(--transition-base);
            outline: none;
        }
        
        .input-area input::placeholder {
            color: var(--color-text-tertiary);
        }
        
        .input-area input:focus {
            background: rgba(255, 255, 255, 0.8);
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
            transform: translateY(-1px);
        }
        
        .input-area input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Button - iOS Style */
        .input-area button {
            padding: var(--spacing-md) var(--spacing-xl);
            background: var(--color-primary);
            color: white;
            border: none;
            border-radius: 20px;
            font-size: var(--font-size-base);
            font-weight: var(--font-weight-medium);
            font-family: var(--font-family);
            cursor: pointer;
            transition: all var(--transition-base);
            box-shadow: var(--shadow-sm);
            min-width: 80px;
        }
        
        .input-area button:hover:not(:disabled) {
            background: var(--color-primary-hover);
            transform: translateY(-1px) scale(1.02);
            box-shadow: var(--shadow-md);
        }
        
        .input-area button:active:not(:disabled) {
            transform: translateY(0) scale(0.98);
        }
        
        .input-area button:disabled {
            background: rgba(0, 0, 0, 0.1);
            color: var(--color-text-tertiary);
            cursor: not-allowed;
            box-shadow: none;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                padding: var(--spacing-lg) var(--spacing-md);
            }
            
            .header h1 {
                font-size: var(--font-size-xl);
            }
            
            .messages {
                padding: var(--spacing-lg) var(--spacing-md);
            }
            
            .message {
                max-width: 85%;
                font-size: var(--font-size-sm);
            }
            
            .input-area {
                padding: var(--spacing-md);
            }
        }
        
        /* Loading Animation */
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .message.loading {
            animation: pulse 1.5s ease-in-out infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Meeting Intelligence</h1>
        </div>
        <div class="messages" id="messages">
            <div class="message agent">
                Hello! I can help you summarize meetings. Try asking: "Summarize my last meeting with [client name]"
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    </div>
    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Disable input with smooth transition
            messageInput.disabled = true;
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';
            
            // Add user message
            addMessage(message, 'user');
            messageInput.value = '';
            
            // Add loading indicator
            const loadingId = addMessage('Thinking...', 'agent', 'loading');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                if (!response.ok) {
                    throw new Error('Server error');
                }
                
                const data = await response.json();
                
                // Remove loading with fade-out
                if (loadingId) {
                    loadingId.style.transition = 'opacity 150ms cubic-bezier(0.4, 0, 0.2, 1), transform 150ms cubic-bezier(0.4, 0, 0.2, 1)';
                    loadingId.style.opacity = '0';
                    loadingId.style.transform = 'translateY(-8px)';
                    setTimeout(() => removeMessage(loadingId), 150);
                }
                
                // Add response with slight delay for smooth transition
                setTimeout(() => {
                    addMessage(data.message, 'agent');
                }, 100);
            } catch (error) {
                if (loadingId) {
                    loadingId.style.transition = 'opacity 150ms cubic-bezier(0.4, 0, 0.2, 1)';
                    loadingId.style.opacity = '0';
                    setTimeout(() => removeMessage(loadingId), 150);
                }
                setTimeout(() => {
                    addMessage('Sorry, an error occurred. Please try again.', 'agent');
                }, 100);
            } finally {
                // Re-enable input
                setTimeout(() => {
                    messageInput.disabled = false;
                    sendButton.disabled = false;
                    sendButton.textContent = 'Send';
                    messageInput.focus();
                }, 200);
            }
        }
        
        function addMessage(text, type, className = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type} ${className}`;
            
            // Handle markdown-style formatting for better readability
            if (type === 'agent' && text.includes('**')) {
                // Simple markdown parsing for bold text
                const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                messageDiv.innerHTML = formattedText;
            } else {
                messageDiv.textContent = text;
            }
            
            // Add with fade-in animation
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateY(8px)';
            messagesDiv.appendChild(messageDiv);
            
            // Trigger animation
            requestAnimationFrame(() => {
                messageDiv.style.transition = 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1), transform 200ms cubic-bezier(0.4, 0, 0.2, 1)';
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0)';
            });
            
            // Smooth scroll to bottom
            setTimeout(() => {
                messagesDiv.scrollTo({
                    top: messagesDiv.scrollHeight,
                    behavior: 'smooth'
                });
            }, 50);
            
            return messageDiv;
        }
        
        function removeMessage(element) {
            if (typeof element === 'string') {
                // If ID passed, find by ID
                const el = document.getElementById(element);
                if (el) el.remove();
            } else {
                element.remove();
            }
        }
        
        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
