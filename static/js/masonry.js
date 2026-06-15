// Masonry layout pour les grilles de photos adaptatives
document.addEventListener('DOMContentLoaded', function() {
    const grids = document.querySelectorAll('.photos-grid.adaptive');
    
    grids.forEach(grid => {
        const items = grid.querySelectorAll('.photo-item');
        
        function resizeGridItems() {
            const rowGap = parseInt(window.getComputedStyle(grid).getPropertyValue('gap'));
            const rowHeight = parseInt(window.getComputedStyle(grid).getPropertyValue('grid-auto-rows'));
            
            items.forEach(item => {
                const img = item.querySelector('img');
                if (!img) return;
                
                // Attendre que l'image soit chargée
                if (img.complete) {
                    updateGridItem(item, img, rowHeight, rowGap);
                } else {
                    img.addEventListener('load', () => {
                        updateGridItem(item, img, rowHeight, rowGap);
                    });
                }
            });
        }
        
        function updateGridItem(item, img, rowHeight, rowGap) {
            const content = item.querySelector('.photo-link');
            const contentHeight = content.getBoundingClientRect().height;
            const rowSpan = Math.ceil((contentHeight + rowGap) / (rowHeight + rowGap));
            
            item.style.setProperty('--grid-rows', rowSpan);
        }
        
        // Initialiser
        resizeGridItems();
        
        // Réajuster lors du redimensionnement
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(resizeGridItems, 150);
        });
    });
});