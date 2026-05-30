/**
 * LIGHTBOX.JS — Lightbox moderne pour galeries photo
 * Navigation clavier, tactile, zoom, préchargement
 */

class ModernLightbox {
  constructor() {
    this.currentIndex = 0;
    this.photos = [];
    this.isOpen = false;
    this.isZoomed = false;
    this.showInfo = false;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.lastTap = 0;
    this.preloadedImages = new Set();
    this.isDragging = false;
    this.dragStartX = 0;
    this.dragStartY = 0;
    
    this.init();
  }
  
  init() {
    this.createLightboxHTML();
    this.bindEvents();
    this.findPhotoLinks();
  }
  
  createLightboxHTML() {
    const lightboxHTML = `
      <div class="lightbox" id="lightbox">
        <div class="lightbox-container">
          <div class="lightbox-loader" id="lightbox-loader"></div>
          <img class="lightbox-image" id="lightbox-image" alt="">
          
          <button class="lightbox-close" id="lightbox-close" title="Fermer (Escape)">×</button>
          
          <div class="lightbox-counter" id="lightbox-counter"></div>
          
          <button class="lightbox-nav lightbox-prev" id="lightbox-prev" title="Photo précédente (←)">‹</button>
          <button class="lightbox-nav lightbox-next" id="lightbox-next" title="Photo suivante (→)">›</button>
          
          <button class="lightbox-zoom" id="lightbox-zoom" title="Zoom (Z)">⊕</button>
        </div>
        
        <!-- Conteneur pour précharger les images -->
        <div class="lightbox-preload" id="lightbox-preload"></div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', lightboxHTML);
    
    // Références aux éléments
    this.lightbox = document.getElementById('lightbox');
    this.image = document.getElementById('lightbox-image');
    this.loader = document.getElementById('lightbox-loader');
    this.counter = document.getElementById('lightbox-counter');
    this.prevBtn = document.getElementById('lightbox-prev');
    this.nextBtn = document.getElementById('lightbox-next');
    this.closeBtn = document.getElementById('lightbox-close');
    this.zoomBtn = document.getElementById('lightbox-zoom');
    this.preloadContainer = document.getElementById('lightbox-preload');
  }
  
  findPhotoLinks() {
    // Trouve tous les liens vers des photos dans les galeries
    const photoLinks = document.querySelectorAll('.photo-link, a[href*="/photo/"]');
    
    console.log('Lightbox: Found', photoLinks.length, 'photo links');
    console.log('Lightbox: First link href:', photoLinks[0]?.href);
    console.log('Lightbox: Photo links:', Array.from(photoLinks).map(l => l.href));
    
    this.photos = Array.from(photoLinks).map((link, originalIndex) => {
      const img = link.querySelector('img');
      console.log('Lightbox: Processing link', originalIndex, link.href);
      return {
        href: link.href,
        thumbnail: img ? img.src : null,
        title: link.title || img?.alt || '',
        alt: img?.alt || '',
        element: link
      };
    });
    
    // Attache les événements de clic avec debugging
    photoLinks.forEach((link, index) => {
      console.log('Lightbox: Attaching click event to link', index, link.href);
      
      link.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Lightbox: CLICK DETECTED on photo', index, 'URL:', link.href);
        this.open(index);
      });
      
      // Test si le link est cliquable
      link.style.cursor = 'pointer';
      link.style.position = 'relative';
      link.style.zIndex = '1';
    });
    
    if (photoLinks.length === 0) {
      console.warn('Lightbox: No photo links found! Check selectors: .photo-link, a[href*="/photo/"]');
    }
  }
  
  bindEvents() {
    // Fermeture
    this.closeBtn.addEventListener('click', (e) => {
      console.log('Lightbox: Close button clicked');
      e.preventDefault();
      e.stopPropagation();
      this.close();
    });
    this.lightbox.addEventListener('click', (e) => {
      if (e.target === this.lightbox) this.close();
    });
    
    // Navigation
    this.prevBtn.addEventListener('click', () => this.prev());
    this.nextBtn.addEventListener('click', () => this.next());
    
    // Zoom
    this.zoomBtn.addEventListener('click', () => this.toggleZoom());
    
    // Click sur desktop, double-tap sur mobile
    this.image.addEventListener('click', (e) => {
      if (this.isMobileDevice()) {
        // Sur mobile, on ignore le clic simple - seul le double-tap fonctionne
        return;
      } else {
        // Sur desktop, clic simple pour zoom avec position de souris
        this.toggleZoom(e);
      }
    });
    
    
    // Clavier
    document.addEventListener('keydown', (e) => this.handleKeydown(e));
    
    // Touch events pour mobile
    this.image.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    this.image.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    
    // Events pour le drag de l'image zoomée
    this.image.addEventListener('mousedown', (e) => this.handleDragStart(e));
    this.image.addEventListener('mousemove', (e) => this.handleDragMove(e));
    this.image.addEventListener('mouseup', (e) => this.handleDragEnd(e));
    this.image.addEventListener('mouseleave', (e) => this.handleDragEnd(e));
    
    // Gestion du redimensionnement
    window.addEventListener('resize', () => this.handleResize());
  }
  
  async open(index) {
    console.log('Lightbox: Opening photo at index', index);
    console.log('Lightbox: this.lightbox element:', this.lightbox);
    console.log('Lightbox: document.body:', document.body);
    
    this.currentIndex = index;
    this.isOpen = true;
    
    if (!this.lightbox) {
      console.error('Lightbox: No lightbox element found!');
      return;
    }
    
    console.log('Lightbox: Adding classes...');
    document.body.classList.add('lightbox-open');
    this.lightbox.classList.add('active');
    
    // Force styles pour debug
    this.lightbox.style.display = 'flex';
    this.lightbox.style.opacity = '1';
    this.lightbox.style.visibility = 'visible';
    this.lightbox.style.zIndex = '99999';
    this.lightbox.style.position = 'fixed';
    this.lightbox.style.top = '0';
    this.lightbox.style.left = '0';
    this.lightbox.style.width = '100%';
    this.lightbox.style.height = '100%';
    this.lightbox.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    
    console.log('Lightbox: Styles forcés:', {
      display: this.lightbox.style.display,
      opacity: this.lightbox.style.opacity,
      visibility: this.lightbox.style.visibility,
      zIndex: this.lightbox.style.zIndex
    });
    
    // Force les boutons de navigation à être au premier plan
    if (this.prevBtn) {
      this.prevBtn.style.zIndex = '100000';
      this.prevBtn.style.position = 'absolute';
      this.prevBtn.style.pointerEvents = 'auto';
      console.log('Lightbox: Prev button z-index forced');
    }
    
    if (this.nextBtn) {
      this.nextBtn.style.zIndex = '100000'; 
      this.nextBtn.style.position = 'absolute';
      this.nextBtn.style.pointerEvents = 'auto';
      console.log('Lightbox: Next button z-index forced');
    }
    
    if (this.closeBtn) {
      this.closeBtn.style.zIndex = '100000';
      this.closeBtn.style.position = 'absolute'; 
      this.closeBtn.style.pointerEvents = 'auto';
      console.log('Lightbox: Close button z-index forced');
    }
    
    console.log('Lightbox: Loading photo...');
    await this.loadPhoto(index);
    
    console.log('Lightbox: Updating navigation and counter...');
    this.updateNavigation();
    this.updateCounter();
    this.preloadAdjacent();
    
    console.log('Lightbox: Should be open now!');
  }
  
  close() {
    console.log('Lightbox: close() method called');
    
    if (!this.isOpen) {
      console.log('Lightbox: Already closed, ignoring close request');
      return;
    }
    
    console.log('Lightbox: Closing lightbox...');
    this.lightbox.classList.add('closing');
    
    setTimeout(() => {
      console.log('Lightbox: Removing classes and resetting state');
      this.isOpen = false;
      this.isZoomed = false;
      this.showInfo = false;
      
      document.body.classList.remove('lightbox-open');
      this.lightbox.classList.remove('active', 'closing');
      this.image.classList.remove('zoomed');
      
      // Reset forced styles
      this.lightbox.style.display = '';
      this.lightbox.style.opacity = '';
      this.lightbox.style.visibility = '';
      
      console.log('Lightbox: Closed successfully');
    }, 300);
  }
  
  async loadPhoto(index) {
    console.log('Lightbox: loadPhoto called with index', index);
    
    if (index < 0 || index >= this.photos.length) {
      console.error('Lightbox: Invalid photo index', index, 'Total photos:', this.photos.length);
      return;
    }
    
    const photo = this.photos[index];
    console.log('Lightbox: Loading photo:', photo);
    
    if (!this.loader || !this.image) {
      console.error('Lightbox: Missing loader or image elements', {loader: this.loader, image: this.image});
      return;
    }
    
    this.loader.style.display = 'block';
    this.image.style.opacity = '0';
    
    try {
      console.log('Lightbox: Getting image URL for:', photo.href);
      // Si c'est un lien vers une page photo, on doit extraire l'URL de l'image
      const imageUrl = await this.getPhotoImageUrl(photo.href);
      console.log('Lightbox: Got image URL:', imageUrl);
      
      const img = new Image();
      img.onload = () => {
        console.log('Lightbox: Image loaded successfully');
        this.image.src = imageUrl;
        this.image.alt = photo.alt;
        this.image.style.opacity = '1';
        this.loader.style.display = 'none';
      };
      img.onerror = () => {
        console.error('Lightbox: Erreur de chargement de l\'image:', imageUrl);
        this.loader.style.display = 'none';
        this.image.src = photo.thumbnail || '';
        this.image.style.opacity = '0.5';
      };
      img.src = imageUrl;
      
    } catch (error) {
      console.error('Lightbox: Erreur dans loadPhoto:', error);
      this.loader.style.display = 'none';
      this.image.src = photo.thumbnail || '';
      this.image.style.opacity = '0.5';
    }
  }
  
  async getPhotoImageUrl(photoPageUrl) {
    // Si c'est déjà une URL d'image directe
    if (photoPageUrl.match(/\.(jpg|jpeg|png|gif|webp|avif)$/i)) {
      return photoPageUrl;
    }
    
    try {
      const response = await fetch(photoPageUrl);
      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');
      
      // Cherche l'image principale dans la page photo
      const mainImage = doc.querySelector('.main-image, .photo-main img, .lightbox-image');
      if (mainImage && mainImage.src) {
        return mainImage.src;
      }
      
      // Fallback : cherche toute image dans le contenu
      const anyImage = doc.querySelector('img[src*="media"], img[src*="photos"]');
      if (anyImage && anyImage.src) {
        return anyImage.src;
      }
      
      throw new Error('Image non trouvée dans la page');
    } catch (error) {
      console.error('Erreur lors de l\'extraction de l\'image:', error);
      throw error;
    }
  }
  
  
  updateNavigation() {
    this.prevBtn.disabled = this.currentIndex === 0;
    this.nextBtn.disabled = this.currentIndex === this.photos.length - 1;
  }
  
  updateCounter() {
    this.counter.textContent = `${this.currentIndex + 1} / ${this.photos.length}`;
  }
  
  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.loadPhoto(this.currentIndex);
      this.updateNavigation();
      this.updateCounter();
      this.preloadAdjacent();
    }
  }
  
  next() {
    if (this.currentIndex < this.photos.length - 1) {
      this.currentIndex++;
      this.loadPhoto(this.currentIndex);
      this.updateNavigation();
      this.updateCounter();
      this.preloadAdjacent();
    }
  }
  
  toggleZoom(event = null) {
    this.isZoomed = !this.isZoomed;
    
    if (this.isZoomed && event) {
      // Calcul de la position de la souris relative à l'image
      const imageRect = this.image.getBoundingClientRect();
      const mouseX = event.clientX - imageRect.left;
      const mouseY = event.clientY - imageRect.top;
      
      // Position relative en pourcentage
      const originX = (mouseX / imageRect.width) * 100;
      const originY = (mouseY / imageRect.height) * 100;
      
      // Application du transform-origin
      this.image.style.transformOrigin = `${originX}% ${originY}%`;
      
      // Reset de la translation lors du zoom
      this.image.style.transform = '';
    } else {
      // Reset au centre pour le dézoom ou zoom par bouton
      this.image.style.transformOrigin = 'center';
      this.image.style.transform = '';
    }
    
    this.image.classList.toggle('zoomed', this.isZoomed);
    this.zoomBtn.textContent = this.isZoomed ? '⊖' : '⊕';
    
    // Reset du curseur
    this.image.style.cursor = this.isZoomed ? 'zoom-out' : 'zoom-in';
  }
  
  
  async preloadAdjacent() {
    const preloadIndexes = [this.currentIndex - 1, this.currentIndex + 1];
    
    for (const index of preloadIndexes) {
      if (index >= 0 && index < this.photos.length && !this.preloadedImages.has(index)) {
        try {
          const photo = this.photos[index];
          const imageUrl = await this.getPhotoImageUrl(photo.href);
          
          const preloadImg = new Image();
          preloadImg.src = imageUrl;
          preloadImg.style.display = 'none';
          this.preloadContainer.appendChild(preloadImg);
          
          this.preloadedImages.add(index);
        } catch (error) {
          console.error('Erreur de préchargement pour l\'index', index, error);
        }
      }
    }
  }
  
  handleKeydown(e) {
    if (!this.isOpen) return;
    
    switch (e.key) {
      case 'Escape':
        e.preventDefault();
        this.close();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        this.prev();
        break;
      case 'ArrowRight':
        e.preventDefault();
        this.next();
        break;
      case 'z':
      case 'Z':
        e.preventDefault();
        this.toggleZoom();
        break;
      case ' ':
        e.preventDefault();
        // Espace pour basculer zoom
        this.toggleZoom();
        break;
    }
  }
  
  handleTouchStart(e) {
    if (e.touches.length === 1) {
      this.touchStartX = e.touches[0].clientX;
      this.touchStartY = e.touches[0].clientY;
    }
  }
  
  handleTouchEnd(e) {
    if (!this.touchStartX || !this.touchStartY) return;
    
    const touchEndX = e.changedTouches[0].clientX;
    const touchEndY = e.changedTouches[0].clientY;
    
    const deltaX = this.touchStartX - touchEndX;
    const deltaY = this.touchStartY - touchEndY;
    
    const minSwipeDistance = 50;
    
    // Détection du double-tap
    const currentTime = new Date().getTime();
    const tapLength = currentTime - this.lastTap;
    
    if (tapLength < 500 && tapLength > 0 && Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10) {
      // Double-tap détecté (pas de mouvement significatif)
      // Pour mobile, utiliser la position du touch comme origine
      const touchEvent = {
        clientX: e.changedTouches[0].clientX,
        clientY: e.changedTouches[0].clientY
      };
      this.toggleZoom(touchEvent);
      e.preventDefault();
      this.lastTap = 0; // Reset pour éviter les triple-taps
      this.touchStartX = 0;
      this.touchStartY = 0;
      return;
    }
    
    this.lastTap = currentTime;
    
    // Logique de swipe (seulement si pas de double-tap)
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // Swipe horizontal
      if (Math.abs(deltaX) > minSwipeDistance) {
        if (deltaX > 0) {
          this.next(); // Swipe vers la gauche = photo suivante
        } else {
          this.prev(); // Swipe vers la droite = photo précédente
        }
      }
    } else {
      // Swipe vertical
      if (Math.abs(deltaY) > minSwipeDistance && deltaY > 0) {
        // Swipe vers le haut = fermer
        this.close();
      }
    }
    
    this.touchStartX = 0;
    this.touchStartY = 0;
  }
  
  handleResize() {
    if (this.isZoomed) {
      this.isZoomed = false;
      this.image.classList.remove('zoomed');
      this.zoomBtn.textContent = '⊕';
    }
  }
  
  handleDragStart(e) {
    if (!this.isZoomed) return;
    
    this.isDragging = true;
    this.dragStartX = e.clientX;
    this.dragStartY = e.clientY;
    
    // Changer le curseur
    this.image.style.cursor = 'grabbing';
    e.preventDefault();
  }
  
  handleDragMove(e) {
    if (!this.isDragging || !this.isZoomed) return;
    
    const deltaX = e.clientX - this.dragStartX;
    const deltaY = e.clientY - this.dragStartY;
    
    // Appliquer la translation en plus du scale
    const currentTransform = this.image.style.transform || '';
    const scaleMatch = currentTransform.match(/scale\([^)]+\)/);
    const scale = scaleMatch ? scaleMatch[0] : 'scale(2.5)';
    
    this.image.style.transform = `${scale} translate(${deltaX}px, ${deltaY}px)`;
    
    e.preventDefault();
  }
  
  handleDragEnd(e) {
    if (!this.isDragging) return;
    
    this.isDragging = false;
    this.image.style.cursor = this.isZoomed ? 'zoom-out' : 'zoom-in';
  }

  isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
           || window.innerWidth <= 768;
  }
}

// Initialisation automatique quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  console.log('Lightbox: DOM loaded, initializing...');
  
  // Délai pour laisser masonry s'exécuter d'abord
  setTimeout(() => {
    try {
      new ModernLightbox();
    } catch (error) {
      console.error('Lightbox: Erreur d\'initialisation:', error);
    }
  }, 500);
});

// Export pour utilisation module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernLightbox;
}
