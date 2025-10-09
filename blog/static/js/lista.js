// Inicializar AOS (Animate On Scroll)
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });

        // Navbar scroll effect
        window.addEventListener('scroll', function() {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });

        // Back to top button
        const backToTopButton = document.querySelector('.back-to-top');
        
        window.addEventListener('scroll', function() {
            if (window.scrollY > 300) {
                backToTopButton.classList.add('active');
            } else {
                backToTopButton.classList.remove('active');
            }
        });

        backToTopButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Sistema de estrelas interativo
        document.addEventListener('DOMContentLoaded', function() {
            const stars = document.querySelectorAll('.star-rating input[type="radio"]');
            stars.forEach(star => {
                star.addEventListener('change', function() {
                    const labels = this.parentElement.querySelectorAll('label');
                    labels.forEach(label => label.style.color = '#ddd');
                    
                    let current = this;
                    while (current = current.previousElementSibling) {
                        current.checked = true;
                    }
                    
                    this.checked = true;
                    const checkedStars = this.parentElement.querySelectorAll('input[type="radio"]:checked');
                    checkedStars.forEach(star => {
                        star.nextElementSibling.style.color = '#ffc107';
                    });
                });
            });
        });

        // Hero background animation
        const heroBackground = document.querySelector('.hero-background img');
        if (heroBackground) {
            setInterval(() => {
                heroBackground.style.animation = 'none';
                setTimeout(() => {
                    heroBackground.style.animation = 'kenburns 20s infinite alternate';
                }, 10);
            }, 20000);
        }