// Add this to your main.js file

// Chat functionality
document.getElementById('chat-input-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    input.value = '';

    try {
        // Show loading state
        const loadingMessage = addMessageToChat('Thinking...', 'bot');
        
        // Call your backend API
        const response = await fetch('http://localhost:8000/gemini_call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: message })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        // Remove loading message
        loadingMessage.remove();
        
        // Add bot response to chat
        addMessageToChat(data.response, 'bot');

    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
    }
});

function addMessageToChat(message, type) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${type}-message`);
    
    // Message content
    messageElement.textContent = message;
    
    // Add timestamp
    const timeElement = document.createElement('div');
    timeElement.classList.add('message-time');
    timeElement.textContent = new Date().toLocaleTimeString();
    messageElement.appendChild(timeElement);
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageElement;
}