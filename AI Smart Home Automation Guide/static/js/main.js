// Wait for the DOM to load
document.addEventListener('DOMContentLoaded', function() {
    // Add initial bot message
    addBotMessage("Hello! How can I help you with your smart home today?");
    
    // Add enter key listener
    document.getElementById('user-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (message) {
        addUserMessage(message);
        input.value = '';
        
        updateChatStatus('processing');
        
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            updateChatStatus('');
            
            // Check for color command
            const colorMatch = data.device_update?.state.match(/on_(red|blue|green|yellow|purple|white)/);
            if (colorMatch) {
                const color = colorMatch[1];
                updateChatColor(color);
                addBotMessage(data.response, 'success', color);
            } else {
                updateChatColor(null);
                addBotMessage(data.response, data.device_update ? 'success' : 'normal');
            }
            
            if (data.device_update) {
                updateDevice(data.device_update);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            updateChatStatus('error');
            updateChatColor(null);
            addBotMessage("Sorry, there was an error processing your request.", 'error');
        });
    }
}

function addUserMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = message;
    messageDiv.appendChild(messageContent);
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestamp);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addBotMessage(message, status = 'normal', color = null) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message bot-message status-${status}`;
    
    if (color) {
        messageDiv.classList.add(`color-${color}`);
    }
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Add color indicator if color is specified
    if (color) {
        const colorDot = document.createElement('span');
        colorDot.className = `color-indicator ${color}`;
        messageContent.appendChild(colorDot);
    }
    
    messageContent.appendChild(document.createTextNode(message));
    messageDiv.appendChild(messageContent);
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestamp);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function updateChatStatus(status) {
    const chatSection = document.querySelector('.chat-section');
    // Remove all status classes
    chatSection.classList.remove('listening', 'processing', 'error');
    
    if (status) {
        chatSection.classList.add(status);
    }
}

function updateChatColor(color) {
    const chatSection = document.querySelector('.chat-section');
    // Remove all color classes
    chatSection.classList.remove('color-red', 'color-blue', 'color-green', 'color-yellow', 'color-purple', 'color-white');
    
    if (color) {
        chatSection.classList.add(`color-${color}`);
    }
}

function updateSpeakerDevice(deviceUpdate) {
    const deviceCard = document.querySelector(`[data-device-id="${deviceUpdate.device_id}"]`);
    if (!deviceCard || deviceCard.dataset.deviceType !== 'speaker') return;

    // Update device state classes
    deviceCard.classList.remove('active', 'state-muted', 'playing');
    
    // Update volume bar if volume is included in the update
    if (deviceUpdate.volume !== undefined) {
        const volumeBar = deviceCard.querySelector('.volume-bar-fill');
        const volumeLevel = deviceCard.querySelector('.volume-level');
        if (volumeBar && volumeLevel) {
            volumeBar.style.width = `${deviceUpdate.volume}%`;
            volumeLevel.textContent = `Volume: ${deviceUpdate.volume}%`;
            
            // Animate volume change
            volumeBar.style.transition = 'width 0.3s ease';
            deviceCard.style.animation = 'speakerPulse 0.5s ease';
        }
    }

    // Update state-specific animations
    switch(deviceUpdate.state) {
        case 'on':
            deviceCard.classList.add('active');
            break;
        case 'playing':
            deviceCard.classList.add('active', 'playing');
            break;
        case 'muted':
            deviceCard.classList.add('state-muted');
            break;
    }

    // Update status text
    const statusElement = deviceCard.querySelector('.device-status');
    if (statusElement) {
        statusElement.textContent = `Status: ${deviceUpdate.state}`;
    }

    // Reset animation
    setTimeout(() => {
        deviceCard.style.animation = '';
    }, 500);
}

function updateDevice(deviceUpdate) {
    const deviceCard = document.querySelector(`[data-device-id="${deviceUpdate.device_id}"]`);
    if (deviceCard) {
        // Add state change animation
        deviceCard.classList.add('state-changing');
        setTimeout(() => {
            deviceCard.classList.remove('state-changing');
        }, 300);

        const statusElement = deviceCard.querySelector('.device-status');
        if (statusElement) {
            statusElement.textContent = `Status: ${deviceUpdate.state}`;
            
            // Remove all existing status and color classes
            deviceCard.classList.remove('active', 'status-on', 'status-off', 
                'color-red', 'color-blue', 'color-green', 'color-yellow', 
                'color-purple', 'color-white');
            
            // Check for color states
            const colorMatch = deviceUpdate.state.match(/on_(red|blue|green|yellow|purple|white)/);
            if (colorMatch) {
                const color = colorMatch[1];
                deviceCard.classList.add(`color-${color}`, 'active');
            }
            // Check for other active states
            else if (deviceUpdate.state === 'on' || 
                    deviceUpdate.state === 'playing' || 
                    deviceUpdate.state === 'unlocked' ||
                    deviceUpdate.state.startsWith('on_')) {
                deviceCard.classList.add('active');
            }
        }
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add event listener for manual scrolling
document.getElementById('chat-messages').addEventListener('scroll', function(e) {
    // You can add logic here to load more messages when scrolling to top
    if (e.target.scrollTop === 0) {
        // Optional: Load previous messages when scrolled to top
        // loadPreviousMessages();
    }
});

// Optional: Function to load previous messages
function loadPreviousMessages() {
    // Add your logic to fetch and display previous messages
    // Example:
    fetch('/api/previous-messages')
        .then(response => response.json())
        .then(data => {
            data.messages.reverse().forEach(message => {
                const chatMessages = document.getElementById('chat-messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${message.type}-message`;
                
                const messageContent = document.createElement('div');
                messageContent.className = 'message-content';
                messageContent.textContent = message.content;
                messageDiv.appendChild(messageContent);
                
                const timestamp = document.createElement('div');
                timestamp.className = 'message-timestamp';
                timestamp.textContent = new Date(message.timestamp).toLocaleTimeString();
                messageDiv.appendChild(timestamp);
                
                chatMessages.insertBefore(messageDiv, chatMessages.firstChild);
            });
        });
}

// Ensure the chat container is scrolled to bottom when page loads
document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom();
});

// Add input focus effect
document.getElementById('user-input').addEventListener('focus', () => {
    updateChatStatus('listening');
});

document.getElementById('user-input').addEventListener('blur', () => {
    updateChatStatus('');
});
