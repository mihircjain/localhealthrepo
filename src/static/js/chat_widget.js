// Chat Widget Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Chat widget elements
    const chatWidgetToggle = document.getElementById('chat-widget-toggle');
    const chatWidgetPopup = document.getElementById('chat-widget-popup');
    const chatWidgetClose = document.getElementById('chat-widget-close');
    const chatWidgetInput = document.getElementById('chat-widget-input-field');
    const chatWidgetSendBtn = document.getElementById('chat-widget-send-btn');
    const chatWidgetMessages = document.getElementById('chat-widget-messages');
    
    // Toggle chat widget
    chatWidgetToggle.addEventListener('click', function() {
        chatWidgetPopup.classList.toggle('active');
        if (chatWidgetPopup.classList.contains('active')) {
            chatWidgetInput.focus();
        }
    });
    
    // Close chat widget
    chatWidgetClose.addEventListener('click', function() {
        chatWidgetPopup.classList.remove('active');
    });
    
    // Send message
    chatWidgetSendBtn.addEventListener('click', function() {
        sendChatMessage();
    });
    
    // Send message on Enter key
    chatWidgetInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    function sendChatMessage() {
        const message = chatWidgetInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Clear input
        chatWidgetInput.value = '';
        
        // Get current user ID (in a real app, this would be from auth)
        const userId = 1; // Placeholder
        
        // Send message to backend
        fetch('/api/chat/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId,
                query: message
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add response to chat
                addMessageToChat('system', data.response);
            } else {
                // Add error message
                addMessageToChat('system', 'Sorry, I encountered an error processing your request.');
                console.error('Chat error:', data.error);
            }
        })
        .catch(error => {
            // Add error message
            addMessageToChat('system', 'Sorry, I encountered an error processing your request.');
            console.error('Error sending chat message:', error);
        });
    }
    
    function addMessageToChat(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = `<p>${content}</p>`;
        
        messageDiv.appendChild(contentDiv);
        chatWidgetMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatWidgetMessages.scrollTop = chatWidgetMessages.scrollHeight;
    }
});
