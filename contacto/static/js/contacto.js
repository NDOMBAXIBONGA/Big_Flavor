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
            if (window.pageYOffset > 300) {
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

        // FAQ accordion
        const faqItems = document.querySelectorAll('.faq-item');
        
        faqItems.forEach(item => {
            const question = item.querySelector('.faq-question');
            
            question.addEventListener('click', () => {
                // Close all other items
                faqItems.forEach(otherItem => {
                    if (otherItem !== item) {
                        otherItem.classList.remove('active');
                    }
                });
                
                // Toggle current item
                item.classList.toggle('active');
            });
        });

        // Character counter for message field
        document.addEventListener('DOMContentLoaded', function() {
            const mensagemField = document.querySelector('#{{ form.mensagem.id_for_label }}');
            const charCount = document.getElementById('charCount');
            
            if (mensagemField && charCount) {
                mensagemField.addEventListener('input', function() {
                    charCount.textContent = this.value.length;
                    
                    if (this.value.length > 1000) {
                        charCount.style.color = 'var(--accent-color)';
                    } else {
                        charCount.style.color = '#6c757d';
                    }
                });
                
                // Initialize counter
                charCount.textContent = mensagemField.value.length;
            }

            // Debug: Verificar se o card social está visível
            const socialCard = document.querySelector('.social-card');
            if (socialCard) {
                console.log('Social card encontrado e visível');
                socialCard.style.display = 'block';
                socialCard.style.visibility = 'visible';
                socialCard.style.opacity = '1';
            }
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