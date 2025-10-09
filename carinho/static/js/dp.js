// Inicializar AOS (Animate On Scroll)
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
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

        // Back to top functionality
        document.querySelector('.back-to-top').addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });

        // Atualizar a página a cada 30 segundos se o pedido não estiver finalizado
        // Verificação do lado do cliente
        var estadoPedido = "{{ pedido.estado }}";
        if (estadoPedido !== 'entregue' && estadoPedido !== 'cancelado') {
            setTimeout(function() {
                window.location.reload();
            }, 30000);
        }

        // Efeitos de hover nos cards
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.order-card, .info-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-10px)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
        });