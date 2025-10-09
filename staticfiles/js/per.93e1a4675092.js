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
        const heroBackground = document.querySelector('.profile-hero-background img');
        if (heroBackground) {
            setInterval(() => {
                heroBackground.style.animation = 'none';
                setTimeout(() => {
                    heroBackground.style.animation = 'kenburns 20s infinite alternate';
                }, 10);
            }, 20000);
        }

        // Preview da imagem do avatar
        const avatarInput = document.getElementById('foto_perfil');
        const avatarPreview = document.getElementById('avatarPreview');
        
        if (avatarInput && avatarPreview) {
            avatarInput.addEventListener('change', function() {
                const file = this.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        avatarPreview.src = e.target.result;
                    }
                    reader.readAsDataURL(file);
                }
            });
        }

        // Validação para excluir conta
        const confirmDeleteInput = document.getElementById('confirmDelete');
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        
        if (confirmDeleteInput && confirmDeleteBtn) {
            confirmDeleteInput.addEventListener('input', function() {
                if (this.value.toUpperCase() === 'EXCLUIR CONTA') {
                    confirmDeleteBtn.disabled = false;
                } else {
                    confirmDeleteBtn.disabled = true;
                }
            });

            confirmDeleteBtn.addEventListener('click', function() {
                if (confirm('Tem certeza absoluta que deseja excluir sua conta? Esta ação é PERMANENTE!')) {
                    // Aqui você pode fazer uma requisição para excluir a conta
                    window.location.href = "{% url 'excluir_conta' %}";
                }
            });
        }

        // Efeitos de hover nos cards
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.profile-card, .stat-card, .info-card');
            cards.forEach(card => {
                card.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-10px)';
                });
                card.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            });
        });