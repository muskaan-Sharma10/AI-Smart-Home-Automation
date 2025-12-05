// Get the modal
const modal = document.getElementById('editModal');
const closeBtn = document.getElementsByClassName('close')[0];

// Close modal when clicking the X
closeBtn.onclick = function() {
    modal.style.display = "none";
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

function editDevice(deviceId) {
    // Get the device card
    const deviceCard = document.querySelector(`[data-device-id="${deviceId}"]`);
    const name = deviceCard.querySelector('h3').textContent;
    const type = deviceCard.querySelector('p').textContent.split(': ')[1].toLowerCase();

    // Populate the edit form
    document.getElementById('editDeviceId').value = deviceId;
    document.getElementById('editName').value = name;
    document.getElementById('editType').value = type;

    // Show the modal
    modal.style.display = "block";
}

function deleteDevice(deviceId) {
    if (confirm('Are you sure you want to delete this device?')) {
        fetch(`/devices/${deviceId}`, {  // Removed /api prefix
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to delete device');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const deviceCard = document.querySelector(`[data-device-id="${deviceId}"]`);
                deviceCard.remove();
            } else {
                throw new Error('Server returned success: false');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(`Error deleting device: ${error.message}`);
        });
    }
}

// Handle edit form submission
document.getElementById('editForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const deviceId = document.getElementById('editDeviceId').value;
    const name = document.getElementById('editName').value;
    const type = document.getElementById('editType').value;

    fetch(`/api/devices/${deviceId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: name,
            type: type
        })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Failed to update device');
    })
    .then(data => {
        // Update the device card in the DOM
        const deviceCard = document.querySelector(`[data-device-id="${deviceId}"]`);
        deviceCard.querySelector('h3').textContent = data.name;
        deviceCard.querySelector('p').textContent = `Type: ${data.type.charAt(0).toUpperCase() + data.type.slice(1)}`;
        
        // Close the modal
        modal.style.display = "none";
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating device. Please try again.');
    });
});
