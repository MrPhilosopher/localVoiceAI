// Configuration
const API_URL = 'http://localhost:8000/api/v1';
let currentUser = null;
let currentTenant = null;
let authToken = null;

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Auth forms
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const logoutBtn = document.getElementById('logout-btn');
    
    // Sections
    const authSection = document.getElementById('auth-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const tenantDetails = document.getElementById('tenant-details');
    
    // Tenant management
    const addTenantBtn = document.getElementById('add-tenant-btn');
    const newTenantName = document.getElementById('new-tenant-name');
    const tenantsList = document.getElementById('tenants-list');
    
    // Document management
    const uploadDocumentBtn = document.getElementById('upload-document-btn');
    const documentUpload = document.getElementById('document-upload');
    const documentsList = document.getElementById('documents-list');
    
    // Chat widget
    const chatWidgetCode = document.getElementById('chat-widget-code');
    const copyWidgetCodeBtn = document.getElementById('copy-widget-code-btn');
    const conversationsList = document.getElementById('conversations-list');
    
    // Chat widget demo
    const chatWidgetDemo = document.getElementById('chat-widget-demo');
    const chatWidgetToggle = document.getElementById('chat-widget-toggle');
    const chatWidgetTitle = document.getElementById('chat-widget-title');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    
    // Check for existing session
    const storedToken = localStorage.getItem('authToken');
    const storedUser = localStorage.getItem('currentUser');
    
    if (storedToken && storedUser) {
        authToken = storedToken;
        currentUser = JSON.parse(storedUser);
        showDashboard();
        loadTenants();
    }
    
    // Event Listeners
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);
    logoutBtn.addEventListener('click', handleLogout);
    
    addTenantBtn.addEventListener('click', handleAddTenant);
    uploadDocumentBtn.addEventListener('click', handleUploadDocument);
    copyWidgetCodeBtn.addEventListener('click', handleCopyWidgetCode);
    
    chatWidgetToggle.addEventListener('click', toggleChatWidget);
    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Functions
    async function handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            const response = await fetch(`${API_URL}/auth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': email,
                    'password': password,
                }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                authToken = data.access_token;
                localStorage.setItem('authToken', authToken);
                
                // Get user details
                const userResponse = await fetch(`${API_URL}/auth/me`, {
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                    },
                });
                
                if (userResponse.ok) {
                    currentUser = await userResponse.json();
                    localStorage.setItem('currentUser', JSON.stringify(currentUser));
                    showDashboard();
                    loadTenants();
                }
            } else {
                alert(`Login failed: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Login failed. Please try again.');
        }
    }
    
    async function handleRegister(e) {
        e.preventDefault();
        const email = document.getElementById('register-email').value;
        const fullName = document.getElementById('register-full-name').value;
        const companyName = document.getElementById('register-company-name').value;
        const password = document.getElementById('register-password').value;
        
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    full_name: fullName,
                    company_name: companyName,
                    password,
                }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert('Registration successful! You can now log in.');
                document.getElementById('login-email').value = email;
                document.getElementById('register-form').reset();
            } else {
                alert(`Registration failed: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Registration failed. Please try again.');
        }
    }
    
    function handleLogout() {
        authToken = null;
        currentUser = null;
        currentTenant = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        showAuthSection();
    }
    
    function showDashboard() {
        authSection.classList.add('hidden');
        dashboardSection.classList.remove('hidden');
    }
    
    function showAuthSection() {
        dashboardSection.classList.add('hidden');
        tenantDetails.classList.add('hidden');
        authSection.classList.remove('hidden');
    }
    
    async function loadTenants() {
        try {
            const response = await fetch(`${API_URL}/tenants/`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                const tenants = await response.json();
                renderTenants(tenants);
            }
        } catch (error) {
            console.error('Error loading tenants:', error);
        }
    }
    
    function renderTenants(tenants) {
        tenantsList.innerHTML = '';
        
        if (tenants.length === 0) {
            tenantsList.innerHTML = '<div class="neo-container p-6 text-center"><p class="text-xl">No agents found. Create your first agent above.</p></div>';
            return;
        }
        
        tenants.forEach(tenant => {
            const tenantElement = document.createElement('div');
            tenantElement.className = 'neo-container p-6';
            tenantElement.innerHTML = `
                <div class="flex justify-between items-center">
                    <h4 class="text-xl font-bold" style="color: var(--secondary);">${tenant.name}</h4>
                    <button class="view-tenant-btn neo-btn neo-secondary py-2 px-4 font-bold" data-id="${tenant.id}">
                        Manage Agent
                    </button>
                </div>
                <p class="mt-2">${tenant.description || 'AI Agent powered by LocalVoiceAI'}</p>
                <div class="mt-3 pt-3 border-t border-black flex justify-between">
                    <span class="text-sm font-medium">API Key: <span class="text-gray-600">${tenant.api_key.substring(0, 2)}${'•'.repeat(20)}${tenant.api_key.substring(tenant.api_key.length - 2)}</span></span>
                    <span class="text-sm font-medium">Created: <span class="text-gray-600">${new Date(tenant.created_at).toLocaleDateString()}</span></span>
                </div>
            `;
            
            tenantsList.appendChild(tenantElement);
            
            const viewBtn = tenantElement.querySelector('.view-tenant-btn');
            viewBtn.addEventListener('click', () => loadTenantDetails(tenant.id));
        });
    }
    
    async function handleAddTenant() {
        const name = newTenantName.value.trim();
        
        if (!name) {
            alert('Please enter a tenant name');
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/tenants/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    description: '',
                    owner_id: currentUser.id,
                    chat_widget_config: {
                        theme_color: '#4f46e5',
                        position: 'right',
                        welcome_message: 'Hello! How can I help you today?'
                    }
                }),
            });
            
            if (response.ok) {
                newTenantName.value = '';
                loadTenants();
            } else {
                const data = await response.json();
                alert(`Failed to create tenant: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error creating tenant:', error);
            alert('Failed to create tenant. Please try again.');
        }
    }
    
    async function loadTenantDetails(tenantId) {
        try {
            const response = await fetch(`${API_URL}/tenants/${tenantId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                currentTenant = await response.json();
                tenantDetails.classList.remove('hidden');
                
                // Update chat widget code
                updateChatWidgetCode();
                
                // Load documents
                loadDocuments(tenantId);
                
                // Load conversations
                loadConversations(tenantId);
                
                // Update chat widget demo
                chatWidgetTitle.textContent = `${currentTenant.name} Support`;
            }
        } catch (error) {
            console.error('Error loading tenant details:', error);
        }
    }
    
    function updateChatWidgetCode() {
        const code = `<script>
    (function() {
        var script = document.createElement('script');
        script.src = '${window.location.origin}/chat-widget.js';
        script.onload = function() {
            initChatWidget({
                tenantId: '${currentTenant.id}',
                position: '${currentTenant.chat_widget_config.position || 'right'}',
                themeColor: '${currentTenant.chat_widget_config.theme_color || '#4f46e5'}'
            });
        };
        document.head.appendChild(script);
    })();
</script>`;

        // Also store the API key in sessionStorage for the widget test page
        sessionStorage.setItem('currentTenantApiKey', currentTenant.api_key);
        
        chatWidgetCode.textContent = code;
    }
    
    async function loadDocuments(tenantId) {
        try {
            const response = await fetch(`${API_URL}/documents/${tenantId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                const documents = await response.json();
                renderDocuments(documents);
            }
        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }
    
    function renderDocuments(documents) {
        documentsList.innerHTML = '';
        
        if (documents.length === 0) {
            documentsList.innerHTML = '<div class="text-center p-6"><p>No documents uploaded yet.</p></div>';
            return;
        }
        
        documents.forEach(doc => {
            const docElement = document.createElement('div');
            docElement.className = 'neo-container p-3 flex justify-between items-center';
            
            let statusBadge = '';
            if (doc.is_processed) {
                statusBadge = '<span class="text-xs py-1 px-2 font-bold" style="background-color: var(--accent); color: white;">Processed</span>';
            } else if (doc.embedding_status === 'processing') {
                statusBadge = '<span class="text-xs py-1 px-2 font-bold" style="background-color: #f0c44d; color: black;">Processing</span>';
            } else if (doc.embedding_status.startsWith('failed')) {
                statusBadge = '<span class="text-xs py-1 px-2 font-bold" style="background-color: var(--error); color: white;">Failed</span>';
            } else {
                statusBadge = '<span class="text-xs py-1 px-2 font-bold" style="background-color: #c7d2fe; color: black;">Pending</span>';
            }
            
            // Add reprocess button if document processing failed
            let actionButtons = '';
            if (doc.embedding_status.startsWith('failed')) {
                actionButtons = `
                    <div class="flex space-x-2">
                        <button class="process-doc-btn neo-btn px-2 py-1" style="background-color: var(--accent); color: white;" data-id="${doc.id}">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
                            </svg>
                        </button>
                        <button class="delete-doc-btn neo-btn px-2 py-1" style="background-color: var(--error); color: white;" data-id="${doc.id}">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                `;
            } else {
                actionButtons = `
                    <button class="delete-doc-btn neo-btn px-2 py-1" style="background-color: var(--error); color: white;" data-id="${doc.id}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                        </svg>
                    </button>
                `;
            }
            
            docElement.innerHTML = `
                <div>
                    <p class="font-bold">${doc.title}</p>
                    <div class="flex items-center mt-1">
                        <span class="text-xs font-medium mr-2">${doc.document_type.toUpperCase()}</span>
                        ${statusBadge}
                    </div>
                </div>
                ${actionButtons}
            `;
            
            documentsList.appendChild(docElement);
            
            const deleteBtn = docElement.querySelector('.delete-doc-btn');
            deleteBtn.addEventListener('click', () => deleteDocument(doc.id));
            
            // Add event listener to process button if it exists
            const processBtn = docElement.querySelector('.process-doc-btn');
            if (processBtn) {
                processBtn.addEventListener('click', () => processDocument(doc.id));
            }
        });
    }
    
    async function handleUploadDocument() {
        if (!currentTenant) {
            alert('Please select a tenant first');
            return;
        }
        
        const fileInput = document.getElementById('document-upload');
        
        if (!fileInput.files.length) {
            alert('Please select a file to upload');
            return;
        }
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        formData.append('tenant_id', currentTenant.id);
        formData.append('title', file.name);
        formData.append('description', '');
        
        try {
            const response = await fetch(`${API_URL}/documents/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
                body: formData,
            });
            
            if (response.ok) {
                fileInput.value = '';
                loadDocuments(currentTenant.id);
            } else {
                const data = await response.json();
                alert(`Failed to upload document: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert('Failed to upload document. Please try again.');
        }
    }
    
    async function processDocument(documentId) {
        try {
            const response = await fetch(`${API_URL}/documents/${documentId}/process`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json',
                },
            });
            
            if (response.ok) {
                alert('Document processing started. This may take a moment.');
                loadDocuments(currentTenant.id);
            } else {
                const data = await response.json();
                alert(`Failed to process document: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error processing document:', error);
            alert('Failed to process document. Please try again.');
        }
    }
    
    async function deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) {
            return;
        }
        
        try {
            const response = await fetch(`${API_URL}/documents/${documentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                loadDocuments(currentTenant.id);
            } else {
                const data = await response.json();
                alert(`Failed to delete document: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error deleting document:', error);
            alert('Failed to delete document. Please try again.');
        }
    }
    
    async function loadConversations(tenantId) {
        try {
            const response = await fetch(`${API_URL}/chat/conversations/${tenantId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                const conversations = await response.json();
                renderConversations(conversations);
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
        }
    }
    
    function renderConversations(conversations) {
        conversationsList.innerHTML = '';
        
        if (conversations.length === 0) {
            conversationsList.innerHTML = '<div class="text-center p-6"><p>No conversations yet.</p></div>';
            return;
        }
        
        conversations.forEach(conversation => {
            const convElement = document.createElement('div');
            convElement.className = 'neo-container p-4';
            
            // Get the last message if available
            const lastMessage = conversation.messages.length 
                ? conversation.messages[conversation.messages.length - 1].content.substring(0, 70) + (conversation.messages[conversation.messages.length - 1].content.length > 70 ? '...' : '')
                : 'No messages';
            
            // Get message count
            const messageCount = conversation.messages.length;
            
            // Format date
            const date = new Date(conversation.created_at);
            const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            
            convElement.innerHTML = `
                <div class="flex justify-between items-center mb-2">
                    <p class="font-bold" style="color: var(--secondary);">Session: ${conversation.session_id.substring(0, 12)}...</p>
                    <span class="text-xs font-medium px-2 py-1" style="background-color: var(--background); border: 1px solid black;">${messageCount} messages</span>
                </div>
                <p class="text-sm mb-3">${lastMessage}</p>
                <div class="flex justify-between items-center border-t border-black pt-2">
                    <span class="text-xs">${formattedDate}</span>
                    <button class="view-conv-btn neo-btn neo-secondary px-3 py-1 text-xs font-bold" data-id="${conversation.id}">
                        View Details
                    </button>
                </div>
            `;
            
            conversationsList.appendChild(convElement);
            
            const viewBtn = convElement.querySelector('.view-conv-btn');
            viewBtn.addEventListener('click', () => viewConversation(conversation.id));
        });
    }
    
    async function viewConversation(conversationId) {
        try {
            const response = await fetch(`${API_URL}/chat/conversation/${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                },
            });
            
            if (response.ok) {
                const conversation = await response.json();
                
                // Create a modal to display the conversation
                const modal = document.createElement('div');
                modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
                
                const modalContent = document.createElement('div');
                modalContent.className = 'bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-auto';
                
                // Format date
                const date = new Date(conversation.created_at);
                const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                
                let messagesHTML = '';
                conversation.messages.forEach(msg => {
                    const msgClass = msg.role === 'user' 
                        ? 'bg-indigo-100 ml-auto' 
                        : 'bg-gray-100';
                    
                    const msgTime = new Date(msg.timestamp).toLocaleTimeString();
                    
                    messagesHTML += `
                        <div class="flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} mb-4">
                            <div class="${msgClass} rounded-lg p-3 max-w-[80%]">
                                <p>${msg.content}</p>
                            </div>
                            <span class="text-xs text-gray-500 mt-1">${msg.role} - ${msgTime}</span>
                        </div>
                    `;
                });
                
                modalContent.innerHTML = `
                    <div class="flex justify-between items-center mb-4">
                        <h3 class="text-lg font-medium">Conversation Details</h3>
                        <button class="close-modal-btn text-gray-500 hover:text-gray-700">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div class="mb-4">
                        <p><strong>Session ID:</strong> ${conversation.session_id}</p>
                        <p><strong>Customer ID:</strong> ${conversation.customer_identifier || 'Anonymous'}</p>
                        <p><strong>Started:</strong> ${formattedDate}</p>
                    </div>
                    <div class="border-t pt-4">
                        <h4 class="font-medium mb-2">Messages</h4>
                        <div class="space-y-2">
                            ${messagesHTML || '<p class="text-gray-500">No messages in this conversation.</p>'}
                        </div>
                    </div>
                `;
                
                modal.appendChild(modalContent);
                document.body.appendChild(modal);
                
                const closeBtn = modalContent.querySelector('.close-modal-btn');
                closeBtn.addEventListener('click', () => {
                    document.body.removeChild(modal);
                });
                
                // Close modal when clicking outside
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        document.body.removeChild(modal);
                    }
                });
            }
        } catch (error) {
            console.error('Error loading conversation details:', error);
        }
    }
    
    function handleCopyWidgetCode() {
        const code = chatWidgetCode.textContent;
        navigator.clipboard.writeText(code)
            .then(() => {
                alert('Widget code copied to clipboard!');
            })
            .catch(err => {
                console.error('Error copying text: ', err);
                alert('Failed to copy code. Please select and copy it manually.');
            });
    }
    
    // Chat Widget Demo
    let chatWidgetOpen = true;
    
    function toggleChatWidget() {
        if (chatWidgetOpen) {
            chatWidgetDemo.style.height = '46px';
            chatWidgetToggle.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
            `;
        } else {
            chatWidgetDemo.style.height = 'auto';
            chatWidgetToggle.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd" />
                </svg>
            `;
        }
        chatWidgetOpen = !chatWidgetOpen;
    }
    
    function sendChatMessage() {
        const message = chatInput.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        addChatMessage(message, 'user');
        chatInput.value = '';
        
        // Demo response (in a real app, this would call the API)
        setTimeout(() => {
            addChatMessage("I'm sorry, this is just a demo. The actual chat widget will be available on your website after integration.", 'assistant');
        }, 1000);
    }
    
    function addChatMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.className = role === 'user' 
            ? 'flex items-end justify-end' 
            : 'flex items-start';
        
        const bubbleClass = role === 'user' 
            ? 'bg-indigo-600 text-white' 
            : 'bg-indigo-100';
        
        messageElement.innerHTML = `
            <div class="${bubbleClass} rounded-lg p-2 max-w-[80%]">
                <p class="text-sm">${content}</p>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

// Function to open widget tester with the current tenant's API key
function openWidgetTester() {
    // Get the API key from session storage
    const apiKey = sessionStorage.getItem('currentTenantApiKey');
    
    if (apiKey) {
        // Store the API key in session storage and open widget test page
        // Without exposing the API key in the URL
        sessionStorage.setItem('currentTenantApiKey', apiKey);
        window.open('widget-test.html', '_blank');
    } else {
        // If no API key is available, open the widget test page without a parameter
        window.open('widget-test.html', '_blank');
    }
}