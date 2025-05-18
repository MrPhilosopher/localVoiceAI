/**
 * AI Chat Agent Widget
 * 
 * This script creates a chat widget that can be embedded on customer websites.
 * It connects to the AI chat agent API to process messages.
 */

function initChatWidget(config) {
    const API_URL = 'http://localhost:8000/api/v1';
    let conversationId = null;
    
    // Create widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.id = 'ai-chat-widget';
    widgetContainer.style.position = 'fixed';
    widgetContainer.style.bottom = '20px';
    widgetContainer.style.right = config.position === 'left' ? 'auto' : '20px';
    widgetContainer.style.left = config.position === 'left' ? '20px' : 'auto';
    widgetContainer.style.zIndex = '9999';
    widgetContainer.style.width = '320px';
    widgetContainer.style.border = '2px solid black';
    widgetContainer.style.boxShadow = '4px 4px 0px rgba(0, 0, 0, 0.8)';
    widgetContainer.style.overflow = 'hidden';
    widgetContainer.style.backgroundColor = '#ffffff';
    widgetContainer.style.fontFamily = "'Space Grotesk', sans-serif";
    
    // Add fonts if not already added
    if (!document.getElementById('widget-fonts')) {
        const fontLink = document.createElement('link');
        fontLink.id = 'widget-fonts';
        fontLink.rel = 'stylesheet';
        fontLink.href = 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap';
        document.head.appendChild(fontLink);
    }
    
    // Create widget header
    const widgetHeader = document.createElement('div');
    widgetHeader.style.backgroundColor = config.themeColor || '#2e294e';
    widgetHeader.style.borderBottom = '2px solid black';
    widgetHeader.style.color = '#ffffff';
    widgetHeader.style.padding = '12px 16px';
    widgetHeader.style.display = 'flex';
    widgetHeader.style.justifyContent = 'space-between';
    widgetHeader.style.alignItems = 'center';
    
    // Add company name to header
    const companyName = document.createElement('h3');
    companyName.textContent = 'LocalVoiceAI';
    companyName.style.margin = '0';
    companyName.style.fontSize = '15px';
    companyName.style.fontWeight = '700';
    
    // Add toggle button to header
    const toggleButton = document.createElement('button');
    toggleButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
    </svg>`;
    toggleButton.style.background = 'transparent';
    toggleButton.style.border = 'none';
    toggleButton.style.color = '#ffffff';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.padding = '0';
    
    widgetHeader.appendChild(companyName);
    widgetHeader.appendChild(toggleButton);
    
    // Create messages container
    const messagesContainer = document.createElement('div');
    messagesContainer.style.height = '300px';
    messagesContainer.style.overflowY = 'auto';
    messagesContainer.style.padding = '16px';
    messagesContainer.style.display = 'flex';
    messagesContainer.style.flexDirection = 'column';
    messagesContainer.style.gap = '12px';
    messagesContainer.style.backgroundColor = '#f7fff7';
    
    // Create input area
    const inputContainer = document.createElement('div');
    inputContainer.style.borderTop = '2px solid black';
    inputContainer.style.padding = '12px';
    inputContainer.style.display = 'flex';
    inputContainer.style.gap = '8px';
    inputContainer.style.backgroundColor = 'white';
    
    const messageInput = document.createElement('input');
    messageInput.type = 'text';
    messageInput.placeholder = 'Type your message...';
    messageInput.style.flexGrow = '1';
    messageInput.style.padding = '8px 12px';
    messageInput.style.border = '2px solid black';
    messageInput.style.borderRadius = '0';
    messageInput.style.fontSize = '14px';
    messageInput.style.fontFamily = "'Space Grotesk', sans-serif";
    
    const sendButton = document.createElement('button');
    sendButton.textContent = 'Send';
    sendButton.style.backgroundColor = config.themeColor || '#2e294e';
    sendButton.style.color = '#ffffff';
    sendButton.style.border = '2px solid black';
    sendButton.style.boxShadow = '2px 2px 0px rgba(0, 0, 0, 0.8)';
    sendButton.style.borderRadius = '0';
    sendButton.style.padding = '8px 12px';
    sendButton.style.cursor = 'pointer';
    sendButton.style.fontSize = '14px';
    sendButton.style.fontWeight = 'bold';
    sendButton.style.fontFamily = "'Space Grotesk', sans-serif";
    
    // Add hover effect to send button
    sendButton.onmouseover = function() {
        this.style.transform = 'translate(1px, 1px)';
        this.style.boxShadow = '1px 1px 0px rgba(0, 0, 0, 0.8)';
    };
    sendButton.onmouseout = function() {
        this.style.transform = 'none';
        this.style.boxShadow = '2px 2px 0px rgba(0, 0, 0, 0.8)';
    };
    
    inputContainer.appendChild(messageInput);
    inputContainer.appendChild(sendButton);
    
    // Assemble widget
    widgetContainer.appendChild(widgetHeader);
    widgetContainer.appendChild(messagesContainer);
    widgetContainer.appendChild(inputContainer);
    
    // Add widget to page
    document.body.appendChild(widgetContainer);
    
    // Widget state
    let isOpen = true;
    
    // Add welcome message
    addMessage('Hello! How can I help you today?', 'assistant');
    
    // Event listeners
    toggleButton.addEventListener('click', () => {
        if (isOpen) {
            messagesContainer.style.display = 'none';
            inputContainer.style.display = 'none';
            toggleButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>`;
        } else {
            messagesContainer.style.display = 'flex';
            inputContainer.style.display = 'flex';
            toggleButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>`;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        isOpen = !isOpen;
    });
    
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Helper functions
    function addMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.style.display = 'flex';
        messageElement.style.flexDirection = 'column';
        messageElement.style.alignItems = role === 'user' ? 'flex-end' : 'flex-start';
        messageElement.style.marginBottom = '8px';
        
        const bubble = document.createElement('div');
        bubble.textContent = content;
        bubble.style.maxWidth = '85%';
        bubble.style.padding = '10px 14px';
        bubble.style.border = '2px solid black';
        bubble.style.boxShadow = '2px 2px 0px rgba(0, 0, 0, 0.8)';
        bubble.style.fontSize = '14px';
        bubble.style.fontFamily = "'Space Grotesk', sans-serif";
        
        if (role === 'user') {
            bubble.style.backgroundColor = config.themeColor || '#2e294e';
            bubble.style.color = '#ffffff';
        } else {
            bubble.style.backgroundColor = '#ffffff';
            bubble.style.color = '#1a1a1a';
        }
        
        // Add a small label indicating who sent the message
        const label = document.createElement('div');
        label.textContent = role === 'user' ? 'You' : 'AI';
        label.style.fontSize = '10px';
        label.style.marginTop = '4px';
        label.style.marginLeft = role === 'user' ? '0' : '4px';
        label.style.marginRight = role === 'user' ? '4px' : '0';
        label.style.opacity = '0.7';
        
        messageElement.appendChild(bubble);
        messageElement.appendChild(label);
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    async function createConversation() {
        try {
            const sessionId = generateSessionId();
            
            const response = await fetch(`${API_URL}/chat/conversation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tenant_id: config.tenantId,
                    session_id: sessionId,
                    customer_identifier: getCookieValue('customer_id') || null
                }),
            });
            
            if (response.ok) {
                const data = await response.json();
                conversationId = data.id;
                return true;
            } else {
                console.error('Failed to create conversation');
                return false;
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            return false;
        }
    }
    
    async function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        // Add message to UI immediately
        addMessage(message, 'user');
        messageInput.value = '';
        
        // Ensure we have a conversation
        if (!conversationId) {
            const success = await createConversation();
            if (!success) {
                addMessage('Sorry, I cannot connect to the support system right now. Please try again later.', 'assistant');
                return;
            }
        }
        
        try {
            const response = await fetch(`${API_URL}/chat/message/${conversationId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: message
                }),
            });
            
            if (response.ok) {
                const data = await response.json();
                addMessage(data.content, 'assistant');
            } else {
                console.error('Failed to send message');
                addMessage('Sorry, there was an error processing your message. Please try again.', 'assistant');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Sorry, there was an error processing your message. Please try again.', 'assistant');
        }
    }
    
    function generateSessionId() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    
    function getCookieValue(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : null;
    }
}

// If the script is loaded directly (not through the snippet)
if (typeof window !== 'undefined' && window.aiChatWidgetConfig) {
    console.log("Initializing widget with config:", window.aiChatWidgetConfig);
    try {
        initChatWidget(window.aiChatWidgetConfig);
    } catch (e) {
        console.error("Error initializing chat widget:", e);
    }
}