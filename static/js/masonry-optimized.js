// Masonry layout optimisé qui réorganise les photos pour minimiser les espaces
document.addEventListener('DOMContentLoaded', function() {
    const grids = document.querySelectorAll('.photos-grid.adaptive');
    
    grids.forEach(grid => {
        const ordreManuel = grid.getAttribute('data-ordre-manuel') === 'true';
        const items = Array.from(grid.querySelectorAll('.photo-item'));
        
        function resizeGridItems() {
            const rowGap = parseInt(window.getComputedStyle(grid).getPropertyValue('gap'));
            const rowHeight = parseInt(window.getComputedStyle(grid).getPropertyValue('grid-auto-rows'));
            
            if (ordreManuel) {
                // Mode manuel : respecter l'ordre DOM
                items.forEach(item => {
                    const img = item.querySelector('img');
                    if (!img) return;
                    
                    if (img.complete) {
                        updateGridItem(item, img, rowHeight, rowGap);
                    } else {
                        img.addEventListener('load', () => {
                            updateGridItem(item, img, rowHeight, rowGap);
                        });
                    }
                });
            } else {
                // Mode optimisé : réorganiser pour minimiser les espaces
                optimizeMasonryLayout(items, rowHeight, rowGap);
            }
        }
        
        function updateGridItem(item, img, rowHeight, rowGap) {
            const content = item.querySelector('.photo-link');
            const contentHeight = content.getBoundingClientRect().height;
            const rowSpan = Math.ceil((contentHeight + rowGap) / (rowHeight + rowGap));
            
            item.style.setProperty('--grid-rows', rowSpan);
        }
        
        function optimizeMasonryLayout(items, rowHeight, rowGap) {
            const columns = getNumberOfColumns();
            const columnHeights = new Array(columns).fill(0);
            
            // Calculer les dimensions de chaque photo
            const itemsWithDimensions = items.map(item => {
                const img = item.querySelector('img');
                if (!img || !img.complete) return null;
                
                const content = item.querySelector('.photo-link');
                const contentHeight = content.getBoundingClientRect().height;
                const rowSpan = Math.ceil((contentHeight + rowGap) / (rowHeight + rowGap));
                
                return {
                    item,
                    rowSpan,
                    aspectRatio: img.naturalWidth / img.naturalHeight
                };
            }).filter(Boolean);
            
            // Trier par rapport d'aspect (portrait/paysage) pour un meilleur mix
            itemsWithDimensions.sort((a, b) => {
                const aIsPortrait = a.aspectRatio < 1;
                const bIsPortrait = b.aspectRatio < 1;
                
                if (aIsPortrait !== bIsPortrait) {
                    return aIsPortrait ? 1 : -1; // Paysage en premier
                }
                
                return b.aspectRatio - a.aspectRatio; // Plus large en premier
            });
            
            // Placer chaque photo dans la colonne la plus courte
            itemsWithDimensions.forEach(({item, rowSpan}, index) => {
                const shortestColumn = columnHeights.indexOf(Math.min(...columnHeights));
                const gridRowStart = columnHeights[shortestColumn] + 1;
                
                item.style.setProperty('--grid-rows', rowSpan);
                item.style.gridColumn = shortestColumn + 1;
                item.style.gridRowStart = gridRowStart;
                
                columnHeights[shortestColumn] += rowSpan;
                
                // Animation d'entrée échelonnée
                item.style.animationDelay = `${index * 50}ms`;
                item.classList.add('masonry-optimized');
            });
        }
        
        function getNumberOfColumns() {
            const gridStyle = window.getComputedStyle(grid);
            const columns = gridStyle.gridTemplateColumns.split(' ').length;
            return columns;
        }
        
        // Attendre que toutes les images soient chargées
        const images = grid.querySelectorAll('img');
        const imagePromises = Array.from(images).map(img => {
            return new Promise(resolve => {
                if (img.complete) {
                    resolve();
                } else {
                    img.addEventListener('load', resolve);
                    img.addEventListener('error', resolve);
                }
            });
        });
        
        Promise.all(imagePromises).then(() => {
            resizeGridItems();
        });
        
        // Réajuster lors du redimensionnement
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(resizeGridItems, 150);
        });
    });
});

// CSS pour l'animation d'entrée
const style = document.createElement('style');
style.textContent = `
.masonry-optimized {
    animation: fadeInUp 0.6s ease-out forwards;
    opacity: 0;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
`;
document.head.appendChild(style);