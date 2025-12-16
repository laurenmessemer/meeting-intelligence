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
    <title>Meeting Assistant</title>
    <link rel="icon" href="/static/meeting_assistant_logo_br.png" type="image/png">
    <link rel="apple-touch-icon" href="/static/meeting_assistant_logo_br.png">
    <style>
        /* Design Tokens */
        :root {
            /* Colors */
            --color-primary: rgba(255, 149, 0, 0.9); /* vibrant orange */;
            --color-primary-hover: rgba(235, 132, 0, 0.9); 
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
            max-width: none;
            margin: 0 auto;
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .header-logo {
            height: 35px; /* matches previous H1 visual weight */
            width: auto;
            display: inline-block;
            object-fit: contain;
            filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.08));
        }

        /* Glassmorphic Header */
        .header {
            padding: var(--spacing-md) var(--spacing-lg);
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            max-width: none;
            margin-left: auto;
            margin-right: auto;
            background: transparent;
            border-bottom: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }
        
        .header::before {
            content: '';
            position: absolute;
            left: calc(-50vw + 50%);
            right: calc(-50vw + 50%);
            top: 0;
            bottom: 0;
            background: var(--color-surface-elevated);
            backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            border-bottom: 0.5px solid var(--color-border);
            box-shadow: var(--shadow-sm);
            z-index: -1;
        }
        
        .header h1 {
            font-size: var(--font-size-2xl);
            font-weight: var(--font-weight-semibold);
            letter-spacing: -0.5px;
            line-height: 1.2;
            color: var(--color-text-primary);
            margin: 0;
        }
        
        /* Messages Container */
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--spacing-sm) var(--spacing-lg);
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
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
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: 20px;
            max-width: 65%;
            word-wrap: break-word;
            white-space: pre-line;
            font-size: var(--font-size-base);
            line-height: 1.4;
            transition: transform var(--transition-base), opacity var(--transition-base);
            animation: messageSlideIn var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Typography reset inside message bubbles */
        .message,
        .message-agent-welcome {
            /* Reset all text elements to remove default browser indentation */
        }
        
        .message p,
        .message h1,
        .message h2,
        .message h3,
        .message h4,
        .message h5,
        .message h6,
        .message ul,
        .message ol,
        .message li,
        .message-agent-welcome p,
        .message-agent-welcome h1,
        .message-agent-welcome h2,
        .message-agent-welcome h3,
        .message-agent-welcome h4,
        .message-agent-welcome h5,
        .message-agent-welcome h6,
        .message-agent-welcome ul,
        .message-agent-welcome ol,
        .message-agent-welcome li {
            margin: 0;
            padding: 0;
            text-align: left;
        }
        
        /* Remove default list indentation */
        .message ul,
        .message ol,
        .message-agent-welcome ul,
        .message-agent-welcome ol {
            padding-left: 0;
            list-style-position: outside;
        }
        
        /* Controlled vertical spacing between paragraphs */
        .message p + p,
        .message-agent-welcome p + p {
            margin-top: var(--spacing-xs);
        }
        
        /* Controlled spacing for headers */
        .message h1 + p,
        .message h2 + p,
        .message h3 + p,
        .message h4 + p,
        .message h5 + p,
        .message h6 + p,
        .message p + h1,
        .message p + h2,
        .message p + h3,
        .message p + h4,
        .message p + h5,
        .message p + h6,
        .message-agent-welcome h1 + p,
        .message-agent-welcome h2 + p,
        .message-agent-welcome h3 + p,
        .message-agent-welcome h4 + p,
        .message-agent-welcome h5 + p,
        .message-agent-welcome h6 + p,
        .message-agent-welcome p + h1,
        .message-agent-welcome p + h2,
        .message-agent-welcome p + h3,
        .message-agent-welcome p + h4,
        .message-agent-welcome p + h5,
        .message-agent-welcome p + h6 {
            margin-top: var(--spacing-xs);
        }
        
        /* Controlled spacing for list items */
        .message li + li,
        .message-agent-welcome li + li {
            margin-top: var(--spacing-xs);
        }
        
        /* Spacing before lists */
        .message p + ul,
        .message p + ol,
        .message h1 + ul,
        .message h2 + ul,
        .message h3 + ul,
        .message h4 + ul,
        .message h5 + ul,
        .message h6 + ul,
        .message h1 + ol,
        .message h2 + ol,
        .message h3 + ol,
        .message h4 + ol,
        .message h5 + ol,
        .message h6 + ol,
        .message-agent-welcome p + ul,
        .message-agent-welcome p + ol,
        .message-agent-welcome h1 + ul,
        .message-agent-welcome h2 + ul,
        .message-agent-welcome h3 + ul,
        .message-agent-welcome h4 + ul,
        .message-agent-welcome h5 + ul,
        .message-agent-welcome h6 + ul,
        .message-agent-welcome h1 + ol,
        .message-agent-welcome h2 + ol,
        .message-agent-welcome h3 + ol,
        .message-agent-welcome h4 + ol,
        .message-agent-welcome h5 + ol,
        .message-agent-welcome h6 + ol {
            margin-top: var(--spacing-xs);
        }
        
        /* Spacing after lists */
        .message ul + p,
        .message ol + p,
        .message ul + h1,
        .message ul + h2,
        .message ul + h3,
        .message ul + h4,
        .message ul + h5,
        .message ul + h6,
        .message ol + h1,
        .message ol + h2,
        .message ol + h3,
        .message ol + h4,
        .message ol + h5,
        .message ol + h6,
        .message-agent-welcome ul + p,
        .message-agent-welcome ol + p,
        .message-agent-welcome ul + h1,
        .message-agent-welcome ul + h2,
        .message-agent-welcome ul + h3,
        .message-agent-welcome ul + h4,
        .message-agent-welcome ul + h5,
        .message-agent-welcome ul + h6,
        .message-agent-welcome ol + h1,
        .message-agent-welcome ol + h2,
        .message-agent-welcome ol + h3,
        .message-agent-welcome ol + h4,
        .message-agent-welcome ol + h5,
        .message-agent-welcome ol + h6 {
            margin-top: var(--spacing-xs);
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
        
        /* Input Area */
        .input-area {
            padding: var(--spacing-md) var(--spacing-lg);
            display: flex;
            gap: var(--spacing-sm);
            align-items: center;
            position: sticky;
            bottom: 0;
            z-index: 100;
            box-sizing: border-box;
            width: 100%;
            max-width: clamp(700px, 90vw, 1400px);
            margin-left: auto;
            margin-right: auto;
            background: transparent;
            border-top: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
        }
        
        .input-area::before {
            content: '';
            position: absolute;
            left: calc(-50vw + 50%);
            right: calc(-50vw + 50%);
            top: 0;
            bottom: 0;
            background: var(--color-surface-elevated);
            backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-lg)) saturate(180%);
            border-top: 0.5px solid var(--color-border);
            box-shadow: 0 -2px 12px var(--color-shadow);
            z-index: -1;
        }
        
        .input-area input {
            flex: 1;
            padding: var(--spacing-sm) var(--spacing-md);
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(var(--blur-sm));
            -webkit-backdrop-filter: blur(var(--blur-sm));
            border: 0.5px solid var(--color-border);
            border-radius: 20px;
            font-size: var(--font-size-base);
            font-family: var(--font-family);
            line-height: 1.4;
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
            box-shadow: 0 0 0 3px rgba(255, 149, 0, 0.1);
            transform: translateY(-1px);
        }
        
        .input-area input:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        /* Button */
        .input-area button {
            padding: var(--spacing-sm) var(--spacing-md);
            background: var(--color-primary);
            color: white;
            border: none;
            border-radius: 20px;
            font-size: var(--font-size-base);
            font-weight: var(--font-weight-medium);
            font-family: var(--font-family);
            line-height: 1.4;
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

            .header-logo {
                height: 28px;
            }
            .header {
                padding: var(--spacing-sm) var(--spacing-md);
            }
            
            .header h1 {
                font-size: var(--font-size-xl);
                line-height: 1.2;
            }
            
            .messages {
                padding: var(--spacing-xs) var(--spacing-md);
            }
            
            .message {
                max-width: 85%;
                font-size: var(--font-size-sm);
                line-height: 1.4;
            }
            
            .input-area {
                max-width: 100%;
                padding: var(--spacing-sm) var(--spacing-sm);
            }
        }
        
        /* Action Items (HubSpot Approval) */
        .action-items {
            margin-top: var(--spacing-sm);
        }

        .action-items strong {
            display: block;
            margin-bottom: var(--spacing-xs);
            font-weight: var(--font-weight-semibold);
            line-height: 1.4;
            text-align: left;
        }

        .action-items-list {
            list-style: none;
            padding: var(--spacing-md);
            margin: var(--spacing-sm) var(--spacing-sm);
        }

        .action-item {
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-xs);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.45);
            backdrop-filter: blur(var(--blur-sm));
            -webkit-backdrop-filter: blur(var(--blur-sm));
            border: 0.5px solid var(--color-border);
            font-size: var(--font-size-sm);
            line-height: 1.8;
            color: var(--color-text-primary);
        }
        
        .action-item:last-child {
            margin-bottom: 0;
        }

        .action-button {
            align-self: flex-start;
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: 16px;
            border: none;
            font-family: var(--font-family);
            font-size: var(--font-size-sm);
            font-weight: var(--font-weight-medium);
            line-height: 1.4;
            cursor: pointer;
            background: rgba(255, 149, 0, 0.9); /* vibrant orange */
            color: white;
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-base);
            margin-top: var(--spacing-xs);
        }

        .action-button:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .action-button:active {
            transform: scale(0.97);
        }

        /* Welcome Message Styling */
        .message-agent-welcome {
            padding: var(--spacing-xs) var(--spacing-md);
            border-radius: 20px;
            max-width: 65%;
            align-self: flex-start;
            background: var(--color-surface);
            backdrop-filter: blur(var(--blur-md)) saturate(180%);
            -webkit-backdrop-filter: blur(var(--blur-md)) saturate(180%);
            color: var(--color-text-primary);
            border-bottom-left-radius: 6px;
            box-shadow: var(--shadow-sm);
            border: 0.5px solid var(--color-border);
            font-size: var(--font-size-base);
            line-height: 1.4;
            word-wrap: break-word;
            white-space: pre-line;
        }

        .welcome-text {
            font-size: var(--font-size-base);
            line-height: 1.4;
            font-weight: var(--font-weight-regular);
            color: var(--color-text-primary);
            margin: 0;
            padding: 0;
            max-width: 100%;
            text-align: left;
        }

        .welcome-buttons {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-xs);
            margin-top: var(--spacing-xs);
        }

        .quick-start-button {
            width: 100%;
            text-align: center;
            padding: var(--spacing-sm) var(--spacing-md);
            border-radius: 12px;
            border: 0.5px solid rgba(255, 149, 0, 0.3);
            font-family: var(--font-family);
            font-size: var(--font-size-sm);
            font-weight: var(--font-weight-medium);
            line-height: 1.4;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(var(--blur-sm));
            -webkit-backdrop-filter: blur(var(--blur-sm));
            color: var(--color-text-primary);
            box-shadow: 0 1px 3px var(--color-shadow), 0 0 0 0.5px rgba(255, 149, 0, 0.1);
            transition: all var(--transition-base);
            margin: 0;
        }

        .quick-start-button:hover {
            background: rgba(255, 255, 255, 0.7);
            transform: translateY(-1px);
            border-color: rgba(255, 149, 0, 0.6);
            box-shadow: 0 4px 12px var(--color-shadow), 0 0 0 1px rgba(255, 149, 0, 0.2);
        }

        .quick-start-button:focus {
            outline: none;
            border-color: rgba(255, 149, 0, 0.6);
            box-shadow: 0 4px 12px var(--color-shadow), 0 0 0 1px rgba(255, 149, 0, 0.2);
        }

        .quick-start-button:active {
            transform: scale(0.97) translateY(0);
            border-color: rgba(255, 149, 0, 0.5);
            box-shadow: 0 1px 3px var(--color-shadow), 0 0 0 0.5px rgba(255, 149, 0, 0.15);
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
            <img
                src="/static/meeting_assistant_logo_br.png"
                alt="Meeting Assistant"
                class="header-logo"
            />
        </div>
        <div class="messages" id="messages">
            <div class="message-agent-welcome">
                <p class="welcome-text">Welcome! I can help you summarize meetings, brief you on upcoming meetings, and generate follow-up emails.</p>
                <p class="welcome-text">To get started try something like...</p>
                <div class="welcome-buttons">
                    <button class="quick-start-button" onclick="sendMessage('Summarize my last meeting')">Summarize my last meeting</button>
                    <button class="quick-start-button" onclick="sendMessage('Brief me on my next meeting')">Brief me on my next meeting</button>
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');

        let lastMetadata = null;

        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage(textOverride = null) {
            const message = textOverride ?? messageInput.value.trim();
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
                lastMetadata = data.metadata || null;

                
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
                    if (data.metadata?.requires_hubspot_approval) {
                        renderHubSpotApproval(data.metadata.proposed_hubspot_tasks || []);
                    }
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
        
        function sendApprovalMessage() {
            sendMessageWithText("approve hubspot tasks");
        }

        async function sendMessageWithText(text) {
            if (!text) return;

            // Disable input
            messageInput.disabled = true;
            sendButton.disabled = true;

            // Add user message to UI
            addMessage(text, 'user');

            // Add loading indicator
            const loadingId = addMessage('Adding tasks to HubSpot...', 'agent', 'loading');

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                if (!response.ok) throw new Error('Server error');

                const data = await response.json();

                removeMessage(loadingId);
                addMessage(data.message, 'agent');

            } catch (error) {
                removeMessage(loadingId);
                addMessage('Failed to add tasks to HubSpot.', 'agent');
            } finally {
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();
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
        
        function renderHubSpotApproval(tasks) {
            const container = document.createElement('div');
            container.className = 'message agent action-items';

            const title = document.createElement('strong');
            title.textContent = `I found ${tasks.length} action item(s).`;
            container.appendChild(title);

            const list = document.createElement('ul');
            list.className = 'action-items-list';

            tasks.forEach(task => {
                const li = document.createElement('li');
                li.className = 'action-item';
                li.textContent = task.text;
                list.appendChild(li);
            });

            container.appendChild(list);

            const button = document.createElement('button');
            button.className = 'action-button';
            button.textContent = 'Add to HubSpot';

            button.onclick = () => {
                sendApprovalMessage();
            };

            container.appendChild(button);
            messagesDiv.appendChild(container);

            messagesDiv.scrollTo({
                top: messagesDiv.scrollHeight,
                behavior: 'smooth'
            });
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
        
        function prefillInput(text) {
            messageInput.value = text;
            messageInput.focus();
            // Scroll input into view if needed
            messageInput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
