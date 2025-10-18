// responsive-engine.js
class ResponsiveEngine {
    constructor() {
        this.breakpoints = {
            xs: 0,
            sm: 576,
            md: 768,
            lg: 992,
            xl: 1200,
            xxl: 1400
        };
        
        this.currentBreakpoint = '';
        this.orientation = '';
        this.isTouchDevice = false;
        
        this.init();
    }
    
    init() {
        this.detectDeviceType();
        this.setupResizeObserver();
        this.setupMutationObserver();
        this.applyGlobalResponsiveRules();
        this.optimizeImages();
        this.setupTouchInteractions();
        this.setupOrientationHandler();
        
        console.log('🚀 Responsive Engine Iniciada');
    }
    
    // 1. Detecção de Dispositivo e Capacidades
    detectDeviceType() {
        // Detectar touch
        this.isTouchDevice = 'ontouchstart' in window || 
                           navigator.maxTouchPoints > 0 || 
                           navigator.msMaxTouchPoints > 0;
        
        document.body.classList.toggle('touch-device', this.isTouchDevice);
        document.body.classList.toggle('no-touch', !this.isTouchDevice);
        
        // Detectar conexão
        if (navigator.connection) {
            const connection = navigator.connection;
            document.body.classList.toggle('slow-connection', 
                connection.effectiveType === 'slow-2g' || 
                connection.effectiveType === '2g'
            );
        }
        
        this.updateBreakpoint();
    }
    
    // 2. Sistema de Breakpoints Dinâmico
    updateBreakpoint() {
        const width = window.innerWidth;
        let newBreakpoint = '';
        
        if (width >= this.breakpoints.xxl) newBreakpoint = 'xxl';
        else if (width >= this.breakpoints.xl) newBreakpoint = 'xl';
        else if (width >= this.breakpoints.lg) newBreakpoint = 'lg';
        else if (width >= this.breakpoints.md) newBreakpoint = 'md';
        else if (width >= this.breakpoints.sm) newBreakpoint = 'sm';
        else newBreakpoint = 'xs';
        
        if (newBreakpoint !== this.currentBreakpoint) {
            // Remover classe anterior
            if (this.currentBreakpoint) {
                document.body.classList.remove(`breakpoint-${this.currentBreakpoint}`);
            }
            
            // Adicionar nova classe
            this.currentBreakpoint = newBreakpoint;
            document.body.classList.add(`breakpoint-${this.currentBreakpoint}`);
            
            this.onBreakpointChange(newBreakpoint);
        }
    }
    
    onBreakpointChange(breakpoint) {
        console.log(`📱 Breakpoint alterado: ${breakpoint}`);
        
        // Ações específicas por breakpoint
        switch(breakpoint) {
            case 'xs':
                this.applyMobileOptimizations();
                break;
            case 'sm':
                this.applySmallMobileOptimizations();
                break;
            case 'md':
                this.applyTabletOptimizations();
                break;
            case 'lg':
                this.applyDesktopOptimizations();
                break;
            default:
                this.applyLargeScreenOptimizations();
        }
        
        // Disparar evento customizado
        window.dispatchEvent(new CustomEvent('breakpointChange', {
            detail: { breakpoint, width: window.innerWidth }
        }));
    }
    
    // 3. Observer para Redimensionamento
    setupResizeObserver() {
        let resizeTimeout;
        
        const handleResize = () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.updateBreakpoint();
                this.updateOrientation();
                this.optimizeLayout();
            }, 100);
        };
        
        window.addEventListener('resize', handleResize);
        
        // Observer para elementos específicos
        this.setupElementResizeObserver();
    }
    
    setupElementResizeObserver() {
        if ('ResizeObserver' in window) {
            this.resizeObserver = new ResizeObserver(entries => {
                entries.forEach(entry => {
                    this.adaptElementToContainer(entry.target);
                });
            });
        }
    }
    
    // 4. Observer para Mudanças no DOM
    setupMutationObserver() {
        this.mutationObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // Element node
                        this.makeElementResponsive(node);
                    }
                });
            });
        });
        
        this.mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // 5. Sistema de Orientação
    setupOrientationHandler() {
        this.updateOrientation();
        window.addEventListener('resize', this.updateOrientation.bind(this));
        
        // Suporte para eventos de orientação em dispositivos móveis
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.updateOrientation();
                this.updateBreakpoint();
            }, 300);
        });
    }
    
    updateOrientation() {
        const newOrientation = window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
        
        if (newOrientation !== this.orientation) {
            if (this.orientation) {
                document.body.classList.remove(`orientation-${this.orientation}`);
            }
            
            this.orientation = newOrientation;
            document.body.classList.add(`orientation-${this.orientation}`);
            
            this.onOrientationChange(newOrientation);
        }
    }
    
    onOrientationChange(orientation) {
        console.log(`🔄 Orientação alterada: ${orientation}`);
        
        if (orientation === 'landscape') {
            this.applyLandscapeOptimizations();
        } else {
            this.applyPortraitOptimizations();
        }
    }
    
    // 6. Otimizações Globais
    applyGlobalResponsiveRules() {
        this.injectResponsiveCSS();
        this.makeExistingContentResponsive();
        this.setupResponsiveTypography();
    }
    
    injectResponsiveCSS() {
        const style = document.createElement('style');
        style.textContent = `
            /* Regras responsivas base */
            .responsive-engine * {
                box-sizing: border-box;
            }
            
            /* Imagens responsivas */
            img:not(.no-responsive) {
                max-width: 100%;
                height: auto;
            }
            
            /* Vídeos responsivos */
            video:not(.no-responsive),
            iframe:not(.no-responsive) {
                max-width: 100%;
                height: auto;
            }
            
            /* Tables responsivas */
            .responsive-table {
                overflow-x: auto;
                display: block;
            }
            
            /* Touch optimizations */
            .touch-device .clickable {
                min-height: 44px;
                min-width: 44px;
            }
            
            /* Breakpoint classes */
            .breakpoint-xs .hide-xs { display: none !important; }
            .breakpoint-sm .hide-sm { display: none !important; }
            .breakpoint-md .hide-md { display: none !important; }
            .breakpoint-lg .hide-lg { display: none !important; }
            .breakpoint-xl .hide-xl { display: none !important; }
            
            /* Orientation helpers */
            .orientation-landscape .hide-landscape { display: none !important; }
            .orientation-portrait .hide-portrait { display: none !important; }
        `;
        
        document.head.appendChild(style);
    }
    
    // 7. Tornar Elementos Existentes Responsivos
    makeExistingContentResponsive() {
        // Imagens
        document.querySelectorAll('img:not([data-responsive-processed])').forEach(img => {
            this.makeImageResponsive(img);
        });
        
        // Tables
        document.querySelectorAll('table:not(.responsive-table)').forEach(table => {
            this.makeTableResponsive(table);
        });
        
        // Vídeos e iframes
        document.querySelectorAll('video, iframe').forEach(media => {
            this.makeMediaResponsive(media);
        });
        
        // Containers
        document.querySelectorAll('.container, [class*="col-"]').forEach(container => {
            this.adaptContainer(container);
        });
    }
    
    makeElementResponsive(element) {
        // Processar elemento e seus filhos
        if (element.tagName === 'IMG') {
            this.makeImageResponsive(element);
        } else if (element.tagName === 'TABLE') {
            this.makeTableResponsive(element);
        } else if (['VIDEO', 'IFRAME'].includes(element.tagName)) {
            this.makeMediaResponsive(element);
        }
        
        // Processar filhos recursivamente
        element.querySelectorAll('img, table, video, iframe').forEach(child => {
            this.makeElementResponsive(child);
        });
    }
    
    // 8. Otimizações Específicas por Elemento
    makeImageResponsive(img) {
        if (img.hasAttribute('data-responsive-processed')) return;
        
        img.setAttribute('data-responsive-processed', 'true');
        
        // Garantir atributos alt
        if (!img.hasAttribute('alt')) {
            img.setAttribute('alt', 'Imagem responsiva');
        }
        
        // Lazy loading
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
        
        // Adicionar fallback para erro
        img.addEventListener('error', function() {
            this.style.display = 'none';
        });
    }
    
    makeTableResponsive(table) {
        if (table.classList.contains('responsive-table')) return;
        
        const wrapper = document.createElement('div');
        wrapper.className = 'responsive-table';
        table.parentNode.insertBefore(wrapper, table);
        wrapper.appendChild(table);
    }
    
    makeMediaResponsive(media) {
        if (media.classList.contains('no-responsive')) return;
        
        media.style.maxWidth = '100%';
        media.style.height = 'auto';
        
        // Aspect ratio para iframes
        if (media.tagName === 'IFRAME') {
            media.style.aspectRatio = '16 / 9';
        }
    }
    
    // 9. Otimizações de Layout
    optimizeLayout() {
        this.optimizeTextContainers();
        this.optimizeNavigation();
        this.optimizeForms();
    }
    
    optimizeTextContainers() {
        document.querySelectorAll('p, h1, h2, h3, h4, h5, h6').forEach(textElement => {
            const containerWidth = textElement.offsetWidth;
            
            if (containerWidth < 300) {
                textElement.style.wordWrap = 'break-word';
                textElement.style.overflowWrap = 'break-word';
            }
        });
    }
    
    optimizeNavigation() {
        const navs = document.querySelectorAll('nav, .navbar, .menu');
        
        navs.forEach(nav => {
            if (window.innerWidth < 768) {
                nav.classList.add('mobile-nav');
            } else {
                nav.classList.remove('mobile-nav');
            }
        });
    }
    
    optimizeForms() {
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (this.isTouchDevice) {
                input.classList.add('touch-input');
                
                // Aumentar área de toque para mobile
                if (window.innerWidth < 768) {
                    input.style.minHeight = '44px';
                    input.style.fontSize = '16px'; // Prevenir zoom no iOS
                }
            }
        });
    }
    
    // 10. Otimizações de Imagens
    optimizeImages() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadOptimalImage(img);
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }
    
    loadOptimalImage(img) {
        const src = img.getAttribute('data-src');
        if (!src) return;
        
        const optimalSrc = this.getOptimalImageSize(src, window.innerWidth);
        img.src = optimalSrc;
        img.classList.remove('lazy');
    }
    
    getOptimalImageSize(baseSrc, viewportWidth) {
        // Lógica para escolher o tamanho ideal da imagem
        if (viewportWidth <= 768) {
            return baseSrc.replace('.jpg', '-mobile.jpg') || baseSrc;
        } else if (viewportWidth <= 1200) {
            return baseSrc.replace('.jpg', '-tablet.jpg') || baseSrc;
        } else {
            return baseSrc.replace('.jpg', '-desktop.jpg') || baseSrc;
        }
    }
    
    // 11. Otimizações Específicas por Breakpoint
    applyMobileOptimizations() {
        document.body.classList.add('mobile-optimized');
        this.increaseTouchTargets();
        this.simplifyAnimations();
    }
    
    applyTabletOptimizations() {
        document.body.classList.add('tablet-optimized');
    }
    
    applyDesktopOptimizations() {
        document.body.classList.add('desktop-optimized');
    }
    
    applyLandscapeOptimizations() {
        document.body.classList.add('landscape-optimized');
    }
    
    applyPortraitOptimizations() {
        document.body.classList.add('portrait-optimized');
    }
    
    // 12. Utilidades para Touch
    setupTouchInteractions() {
        if (this.isTouchDevice) {
            this.increaseTouchTargets();
            this.preventZoomOnInput();
        }
    }
    
    increaseTouchTargets() {
        const interactiveElements = document.querySelectorAll('button, a, [role="button"]');
        
        interactiveElements.forEach(el => {
            if (el.offsetWidth < 44 || el.offsetHeight < 44) {
                el.classList.add('small-touch-target');
            }
        });
    }
    
    preventZoomOnInput() {
        const inputs = document.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                // Adicionar timeout para garantir que o viewport está estável
                setTimeout(() => {
                    window.scrollTo(0, 0);
                }, 100);
            });
        });
    }
    
    simplifyAnimations() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
        }
    }
    
    // 13. Adaptação de Elementos a Containers
    adaptElementToContainer(element) {
        const containerWidth = element.offsetWidth;
        
        if (containerWidth < 200) {
            element.classList.add('very-narrow-container');
        } else if (containerWidth < 400) {
            element.classList.add('narrow-container');
        } else {
            element.classList.remove('very-narrow-container', 'narrow-container');
        }
    }
    
    adaptContainer(container) {
        const width = container.offsetWidth;
        
        // Remover classes antigas
        container.classList.remove('container-xs', 'container-sm', 'container-md', 'container-lg');
        
        // Adicionar classe baseada na largura
        if (width < 300) container.classList.add('container-xs');
        else if (width < 500) container.classList.add('container-sm');
        else if (width < 800) container.classList.add('container-md');
        else container.classList.add('container-lg');
    }
    
    // 14. Sistema de Tipografia Responsiva
    setupResponsiveTypography() {
        const baseSize = this.calculateOptimalFontSize();
        document.documentElement.style.setProperty('--responsive-font-size', `${baseSize}px`);
    }
    
    calculateOptimalFontSize() {
        const width = window.innerWidth;
        
        if (width <= 480) return 14;
        if (width <= 768) return 15;
        if (width <= 1024) return 16;
        if (width <= 1440) return 17;
        return 18;
    }
    
    // 15. Métodos Públicos
    getCurrentBreakpoint() {
        return this.currentBreakpoint;
    }
    
    getOrientation() {
        return this.orientation;
    }
    
    isMobile() {
        return this.currentBreakpoint === 'xs' || this.currentBreakpoint === 'sm';
    }
    
    isTablet() {
        return this.currentBreakpoint === 'md';
    }
    
    isDesktop() {
        return this.currentBreakpoint === 'lg' || this.currentBreakpoint === 'xl' || this.currentBreakpoint === 'xxl';
    }
    
    // Destruir instância (para SPA)
    destroy() {
        if (this.mutationObserver) {
            this.mutationObserver.disconnect();
        }
        
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('orientationchange', this.handleOrientationChange);
    }
}

// 16. Inicialização Automática
function initResponsiveEngine() {
    // Esperar DOM estar pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.ResponsiveEngine = new ResponsiveEngine();
        });
    } else {
        window.ResponsiveEngine = new ResponsiveEngine();
    }
}

// 17. Export para módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ResponsiveEngine, initResponsiveEngine };
} else {
    // Inicialização automática no browser
    initResponsiveEngine();
}

// 18. Polyfill para ResizeObserver (opcional)
if (!window.ResizeObserver) {
    console.warn('ResizeObserver não suportado. Algumas funcionalidades podem não funcionar.');
}