// Inicializar AOS (Animate On Scroll)
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });

        // Navbar scroll effect
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                document.querySelector('.navbar').classList.add('scrolled');
            } else {
                document.querySelector('.navbar').classList.remove('scrolled');
            }
            
            // Back to top button
            if (window.scrollY > 300) {
                document.querySelector('.back-to-top').classList.add('active');
            } else {
                document.querySelector('.back-to-top').classList.remove('active');
            }
        });

        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });

        // Hero background animation
        const heroBackground = document.querySelector('.page-hero-background img');
        if (heroBackground) {
            setInterval(() => {
                heroBackground.style.animation = 'none';
                setTimeout(() => {
                    heroBackground.style.animation = 'kenburns 20s infinite alternate';
                }, 10);
            }, 20000);
        }

        // Adicionar efeitos aos campos do formulário
        document.addEventListener('DOMContentLoaded', function() {
            const formControls = document.querySelectorAll('.form-control');
            formControls.forEach(control => {
                control.addEventListener('focus', function() {
                    this.parentElement.classList.add('focused');
                });
                control.addEventListener('blur', function() {
                    if (this.value === '') {
                        this.parentElement.classList.remove('focused');
                    }
                });
            });

            // Detectar largura da viewport para responsividade
            function updateViewportWidth() {
                document.documentElement.style.setProperty('--viewport-width', window.innerWidth + 'px');
            }
            
            updateViewportWidth();
            window.addEventListener('resize', updateViewportWidth);
        });

        // Back to Top Simplificado - Coloque no final do seu arquivo JS
const backToTop = document.querySelector('.back-to-top');

if (backToTop) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.classList.add('active');
        } else {
            backToTop.classList.remove('active');
        }
    });
    
    backToTop.addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}