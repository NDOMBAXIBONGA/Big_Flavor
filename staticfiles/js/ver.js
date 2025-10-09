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

            // Back to top button
            const backToTop = document.querySelector('.back-to-top');
            if (window.scrollY > 300) {
                backToTop.classList.add('active');
            } else {
                backToTop.classList.remove('active');
            }
        });

        // Quantity control functions
        function incrementQuantity(button) {
            const input = button.parentElement.querySelector('input[type="number"]');
            if (parseInt(input.value) < parseInt(input.max)) {
                input.value = parseInt(input.value) + 1;
                input.form.submit();
            }
        }

        function decrementQuantity(button) {
            const input = button.parentElement.querySelector('input[type="number"]');
            if (parseInt(input.value) > parseInt(input.min)) {
                input.value = parseInt(input.value) - 1;
                input.form.submit();
            }
        }

        // Back to top functionality
        document.querySelector('.back-to-top').addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Add floating elements dynamically
        function createFloatingElements() {
            const container = document.querySelector('.cart-section');
            for (let i = 0; i < 5; i++) {
                const element = document.createElement('div');
                element.classList.add('floating-element');
                
                const size = Math.random() * 100 + 50;
                const top = Math.random() * 80 + 10;
                const left = Math.random() * 80 + 10;
                const duration = Math.random() * 20 + 10;
                const delay = Math.random() * 5;
                
                element.style.width = `${size}px`;
                element.style.height = `${size}px`;
                element.style.top = `${top}%`;
                element.style.left = `${left}%`;
                element.style.animationDuration = `${duration}s`;
                element.style.animationDelay = `${delay}s`;
                
                // Random gradient
                const gradients = [
                    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    'linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)',
                    'linear-gradient(135deg, #f39c12 0%, #f1c40f 100%)'
                ];
                
                const randomGradient = gradients[Math.floor(Math.random() * gradients.length)];
                element.style.background = randomGradient;
                
                container.appendChild(element);
            }
        }

        // Initialize floating elements
        document.addEventListener('DOMContentLoaded', function() {
            createFloatingElements();
        });