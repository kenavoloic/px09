document.addEventListener('DOMContentLoaded', function() {
    const photoCoverField = document.querySelector('.field-photo_couverture_id');
    
    if (!photoCoverField) {
        return;
    }
    
    // Get the gallery ID from the current URL
    const urlParts = window.location.pathname.split('/');
    const galerieId = urlParts[urlParts.indexOf('galerie') + 1];
    
    if (!galerieId || galerieId === 'add') {
        return;
    }
    
    // Enhance the radio buttons with thumbnails
    const radioButtons = photoCoverField.querySelectorAll('input[type="radio"]');
    
    radioButtons.forEach(function(radio) {
        const label = radio.closest('label');
        const photoId = radio.value;
        
        if (!photoId) {
            // Special handling for "no cover" option
            return;
        }
        
        // Create enhanced label structure
        const thumbnail = document.createElement('div');
        thumbnail.className = 'photo-thumbnail';
        
        const photoInfo = document.createElement('div');
        photoInfo.className = 'photo-info';
        
        const originalText = label.textContent.trim();
        const parts = originalText.match(/^(.*?)\s*(\([^)]+\))?\s*$/);
        
        if (parts) {
            const titleDiv = document.createElement('div');
            titleDiv.className = 'photo-title';
            titleDiv.textContent = parts[1] || `Photo ${photoId}`;
            
            const collectionDiv = document.createElement('div');
            collectionDiv.className = 'photo-collection';
            collectionDiv.textContent = parts[2] || '';
            
            photoInfo.appendChild(titleDiv);
            if (parts[2]) {
                photoInfo.appendChild(collectionDiv);
            }
        }
        
        // Clear label and rebuild
        label.innerHTML = '';
        label.appendChild(radio);
        label.appendChild(thumbnail);
        label.appendChild(photoInfo);
        
        // Try to load thumbnail
        if (photoId) {
            fetch(`/admin/galeries/api/photo/${photoId}/thumbnail/`)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('No thumbnail');
                })
                .then(data => {
                    if (data.thumbnail_url) {
                        const img = document.createElement('img');
                        img.src = data.thumbnail_url;
                        img.alt = data.title || 'Photo';
                        thumbnail.innerHTML = '';
                        thumbnail.appendChild(img);
                    } else {
                        thumbnail.textContent = '📷';
                    }
                })
                .catch(() => {
                    thumbnail.textContent = '📷';
                });
        }
    });
    
    // Add click handlers for better UX
    photoCoverField.addEventListener('click', function(e) {
        if (e.target.closest('li') && !e.target.matches('input[type="radio"]')) {
            const radio = e.target.closest('li').querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                radio.dispatchEvent(new Event('change'));
            }
        }
    });
    
    // Add visual feedback on form submission
    const form = document.querySelector('#galerie_form');
    if (form) {
        form.addEventListener('submit', function() {
            const selectedRadio = photoCoverField.querySelector('input[type="radio"]:checked');
            if (selectedRadio) {
                console.log('Submitting with cover photo ID:', selectedRadio.value);
            }
        });
    }
});