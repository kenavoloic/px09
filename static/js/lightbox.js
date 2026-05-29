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
          
          <button class="lightbox-info-toggle" id="lightbox-info-toggle" title="Afficher/Masquer infos (I)">i</button>
          <button class="lightbox-zoom" id="lightbox-zoom" title="Zoom (Z)">⊕</button>
          
          <div class="lightbox-info" id="lightbox-info">
            <div class="lightbox-title" id="lightbox-title"></div>
            <div class="lightbox-meta" id="lightbox-meta"></div>
            <div class="lightbox-description" id="lightbox-description"></div>
          </div>
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
    this.infoToggle = document.getElementById('lightbox-info-toggle');
    this.zoomBtn = document.getElementById('lightbox-zoom');
    this.info = document.getElementById('lightbox-info');
    this.title = document.getElementById('lightbox-title');
    this.meta = document.getElementById('lightbox-meta');
    this.description = document.getElementById('lightbox-description');
    this.preloadContainer = document.getElementById('lightbox-preload');
  }
  
  findPhotoLinks() {
    // Trouve tous les liens vers des photos dans les galeries
    const photoLinks = document.querySelectorAll('.photo-link, a[href*="/photo/"]');
    
    this.photos = Array.from(photoLinks).map(link => {
      const img = link.querySelector('img');
      return {
        href: link.href,
        thumbnail: img ? img.src : null,
        title: link.title || img?.alt || '',
        alt: img?.alt || '',
        element: link
      };
    });
    
    // Attache les événements de clic
    photoLinks.forEach((link, index) => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.open(index);
      });
    });
  }
  
  bindEvents() {
    // Fermeture
    this.closeBtn.addEventListener('click', () => this.close());
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
        // Sur desktop, clic simple pour zoom
        this.toggleZoom();
      }
    });
    
    // Toggle info
    this.infoToggle.addEventListener('click', () => this.toggleInfo());
    
    // Clavier
    document.addEventListener('keydown', (e) => this.handleKeydown(e));
    
    // Touch events pour mobile
    this.image.addEventListener('touchstart', (e) => this.handleTouchStart(e));
    this.image.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    
    // Gestion du redimensionnement
    window.addEventListener('resize', () => this.handleResize());
  }
  
  async open(index) {
    this.currentIndex = index;
    this.isOpen = true;
    
    document.body.classList.add('lightbox-open');
    this.lightbox.classList.add('active');
    
    await this.loadPhoto(index);
    this.updateNavigation();
    this.updateCounter();
    this.preloadAdjacent();
  }
  
  close() {
    if (!this.isOpen) return;
    
    this.lightbox.classList.add('closing');
    
    setTimeout(() => {
      this.isOpen = false;
      this.isZoomed = false;
      this.showInfo = false;
      
      document.body.classList.remove('lightbox-open');
      this.lightbox.classList.remove('active', 'closing');
      this.image.classList.remove('zoomed');
      this.info.classList.remove('visible');
      this.infoToggle.classList.remove('active');
    }, 300);
  }
  
  async loadPhoto(index) {
    if (index < 0 || index >= this.photos.length) return;
    
    const photo = this.photos[index];
    
    this.loader.style.display = 'block';
    this.image.style.opacity = '0';
    
    try {
      // Si c'est un lien vers une page photo, on doit extraire l'URL de l'image
      const imageUrl = await this.getPhotoImageUrl(photo.href);
      
      const img = new Image();
      img.onload = () => {
        this.image.src = imageUrl;
        this.image.alt = photo.alt;
        this.image.style.opacity = '1';
        this.loader.style.display = 'none';
        
        // Mise à jour des infos
        this.updatePhotoInfo(photo);
      };
      img.onerror = () => {
        console.error('Erreur de chargement de l\'image:', imageUrl);
        this.loader.style.display = 'none';
        this.image.src = photo.thumbnail || '';
        this.image.style.opacity = '0.5';
      };
      img.src = imageUrl;
      
    } catch (error) {
      console.error('Erreur:', error);
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
  
  updatePhotoInfo(photo) {
    this.title.textContent = photo.title;
    this.meta.textContent = `Photo ${this.currentIndex + 1} sur ${this.photos.length}`;
    this.description.textContent = photo.alt;
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
  
  toggleZoom() {
    this.isZoomed = !this.isZoomed;
    this.image.classList.toggle('zoomed', this.isZoomed);
    this.zoomBtn.textContent = this.isZoomed ? '⊖' : '⊕';
  }
  
  toggleInfo() {
    this.showInfo = !this.showInfo;
    this.info.classList.toggle('visible', this.showInfo);
    this.infoToggle.classList.toggle('active', this.showInfo);
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
      case 'i':
      case 'I':
        e.preventDefault();
        this.toggleInfo();
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
      this.toggleZoom();
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
  
  isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) 
           || window.innerWidth <= 768;
  }
}

// Initialisation automatique quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new ModernLightbox();
});

// Export pour utilisation module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernLightbox;
}
