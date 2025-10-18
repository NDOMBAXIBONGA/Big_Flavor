// Inicializar AOS (Animate On Scroll)
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });

        // Criar partículas dinâmicas
        function createParticles() {
            const container = document.getElementById('particlesContainer');
            const particleCount = 30;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                
                // Tamanho aleatório
                const size = Math.random() * 6 + 2;
                particle.style.width = `${size}px`;
                particle.style.height = `${size}px`;
                
                // Posição inicial aleatória
                particle.style.left = `${Math.random() * 100}%`;
                
                // Atraso de animação aleatório
                const delay = Math.random() * 15;
                particle.style.animationDelay = `${delay}s`;
                
                // Duração de animação aleatória
                const duration = Math.random() * 10 + 10;
                particle.style.animationDuration = `${duration}s`;
                
                container.appendChild(particle);
            }
        }

        // Toggle password visibility
        document.addEventListener('DOMContentLoaded', function() {
            createParticles();
            
            const passwordToggle = document.getElementById('passwordToggle');
            const passwordField = document.querySelector('input[type="password"]');
            
            if (passwordToggle && passwordField) {
                passwordToggle.addEventListener('click', function() {
                    const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordField.setAttribute('type', type);
                    this.innerHTML = type === 'password' ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
                });
            }

            // Efeito de digitação no título
            const welcomeText = document.querySelector('.login-welcome');
            if (welcomeText) {
                const text = welcomeText.textContent;
                welcomeText.textContent = '';
                let i = 0;
                
                function typeWriter() {
                    if (i < text.length) {
                        welcomeText.textContent += text.charAt(i);
                        i++;
                        setTimeout(typeWriter, 50);
                    }
                }
                
                setTimeout(typeWriter, 500);
            }

            // Efeito de partículas no botão de login
            const loginBtn = document.querySelector('.btn-login');
            if (loginBtn) {
                loginBtn.addEventListener('mouseenter', function() {
                    for (let i = 0; i < 8; i++) {
                        const particle = document.createElement('div');
                        particle.style.cssText = `
                            position: absolute;
                            width: 6px;
                            height: 6px;
                            background: white;
                            border-radius: 50%;
                            pointer-events: none;
                            z-index: 2;
                            left: ${Math.random() * 100}%;
                            top: ${Math.random() * 100}%;
                            animation: particle-explode 0.8s ease-out forwards;
                        `;
                        
                        this.appendChild(particle);
                        
                        setTimeout(() => {
                            particle.remove();
                        }, 800);
                    }
                });
            }

            // Adicionar estilo para animação de partículas
            const style = document.createElement('style');
            style.textContent = `
                @keyframes particle-explode {
                    0% {
                        opacity: 1;
                        transform: translate(0, 0) scale(1);
                    }
                    100% {
                        opacity: 0;
                        transform: translate(${Math.random() * 100 - 50}px, ${Math.random() * 100 - 50}px) scale(0);
                    }
                }
            `;
            document.head.appendChild(style);
        });

        // Efeito parallax no background
        window.addEventListener('scroll', function() {
            const scrolled = window.pageYOffset;
            const background = document.querySelector('.login-background img');
            if (background) {
                background.style.transform = `scale(1.1) translateY(${scrolled * 0.5}px)`;
            }
        });