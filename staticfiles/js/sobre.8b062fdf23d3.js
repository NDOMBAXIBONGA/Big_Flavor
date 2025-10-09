// Inicializar AOS
        AOS.init({
            duration: 1000,
            once: true,
            offset: 100
        });

        // Variáveis globais para controle do vídeo
        let currentVideo = null;
        let isPlaying = false;

        // Video Modal functionality - CORRIGIDO
        const videoModal = document.getElementById('videoModal');
        if (videoModal) {
            videoModal.addEventListener('show.bs.modal', function (event) {
                const button = event.relatedTarget;
                const videoUrl = button.getAttribute('data-video-url');
                const videoType = button.getAttribute('data-video-type');
                const videoTitle = button.getAttribute('data-video-title') || 'Vídeo da História';
                const videoFormat = button.getAttribute('data-video-format');
                
                // Atualizar título do modal
                document.getElementById('videoModalLabel').textContent = videoTitle;
                
                // Mostrar indicador de carregamento
                showLoading(true);
                hideError();
                
                // Esconder players anteriores
                document.getElementById('youtubePlayer').style.display = 'none';
                document.getElementById('localVideoPlayer').style.display = 'none';
                document.getElementById('formatWarning').style.display = 'none';
                
                if (videoType === 'youtube') {
                    loadYouTubeVideo(videoUrl);
                } else {
                    loadLocalVideo(videoUrl, videoFormat);
                }
            });

            videoModal.addEventListener('hidden.bs.modal', function () {
                // Parar e limpar vídeos
                stopAllVideos();
                hideLoading();
                hideError();
            });
        }

        function loadYouTubeVideo(url) {
            const youtubePlayer = document.getElementById('youtubePlayer');
            const youtubeIframe = document.getElementById('youtubeIframe');
            
            // Extrair ID do vídeo do YouTube
            let videoId = url;
            if (url.includes('youtube.com/watch?v=')) {
                videoId = url.split('v=')[1]?.split('&')[0];
            } else if (url.includes('youtu.be/')) {
                videoId = url.split('/').pop();
            }
            
            if (videoId) {
                youtubeIframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`;
                youtubePlayer.style.display = 'block';
                hideLoading();
            } else {
                showError('URL do YouTube inválida.');
            }
        }

        function loadLocalVideo(url, format) {
            const localPlayer = document.getElementById('localVideoPlayer');
            const localVideo = document.getElementById('localVideo');
            const formatWarning = document.getElementById('formatWarning');
            const warningText = document.getElementById('warningText');
            
            // Mostrar aviso se não for MP4
            if (format !== 'mp4') {
                warningText.textContent = `Vídeo no formato ${format?.toUpperCase()}. Para melhor compatibilidade, recomendamos MP4 (H.264).`;
                formatWarning.style.display = 'block';
            }
            
            // Configurar source do vídeo
            localVideo.innerHTML = '';
            const source = document.createElement('source');
            source.src = url;
            source.type = getMimeType(format);
            localVideo.appendChild(source);
            
            // Adicionar fallback
            const fallback = document.createElement('p');
            fallback.textContent = 'Seu navegador não suporta a reprodução de vídeos.';
            fallback.style.padding = '20px';
            fallback.style.textAlign = 'center';
            fallback.style.color = 'white';
            localVideo.appendChild(fallback);
            
            // Configurar eventos do vídeo
            localVideo.addEventListener('loadeddata', function() {
                hideLoading();
                setupVideoControls(localVideo);
            });
            
            localVideo.addEventListener('error', function(e) {
                console.error('Erro no vídeo:', e);
                showError('Erro ao carregar o vídeo. Verifique o formato e codec.');
            });
            
            localVideo.addEventListener('waiting', function() {
                showLoading(true);
            });
            
            localVideo.addEventListener('canplay', function() {
                hideLoading();
            });
            
            // Tentar carregar
            localVideo.load();
            localPlayer.style.display = 'block';
            currentVideo = localVideo;
        }

        function getMimeType(format) {
            const mimeTypes = {
                'mp4': 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"',
                'webm': 'video/webm; codecs="vp8, vorbis"',
                'ogg': 'video/ogg; codecs="theora, vorbis"'
            };
            return mimeTypes[format] || 'video/mp4';
        }

        function setupVideoControls(video) {
            const playPauseBtn = document.getElementById('playPauseBtn');
            const progressBar = document.getElementById('progress');
            const currentTimeEl = document.getElementById('currentTime');
            const durationEl = document.getElementById('duration');
            const progressContainer = document.getElementById('progressBar');
            const fullscreenBtn = document.getElementById('fullscreenBtn');

            // Atualizar tempo e progresso
            video.addEventListener('timeupdate', function() {
                const progress = (video.currentTime / video.duration) * 100;
                progressBar.style.width = `${progress}%`;
                currentTimeEl.textContent = formatTime(video.currentTime);
            });

            video.addEventListener('loadedmetadata', function() {
                durationEl.textContent = formatTime(video.duration);
            });

            // Controles de play/pause
            playPauseBtn.addEventListener('click', function() {
                if (video.paused) {
                    video.play();
                    playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
                } else {
                    video.pause();
                    playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
                }
            });

            // Barra de progresso clicável
            progressContainer.addEventListener('click', function(e) {
                const rect = progressContainer.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                video.currentTime = percent * video.duration;
            });

            // Tela cheia
            fullscreenBtn.addEventListener('click', function() {
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                } else if (video.mozRequestFullScreen) {
                    video.mozRequestFullScreen();
                }
            });

            // Atualizar botão play/pause automaticamente
            video.addEventListener('play', function() {
                playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
            });

            video.addEventListener('pause', function() {
                playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            });
        }

        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
        }

        function showLoading(show) {
            document.getElementById('videoLoading').style.display = show ? 'block' : 'none';
        }

        function hideLoading() {
            showLoading(false);
        }

        function showError(message) {
            document.getElementById('errorMessage').textContent = message;
            document.getElementById('videoError').style.display = 'block';
            hideLoading();
        }

        function hideError() {
            document.getElementById('videoError').style.display = 'none';
        }

        function stopAllVideos() {
            // Parar YouTube
            const youtubeIframe = document.getElementById('youtubeIframe');
            if (youtubeIframe.src) {
                youtubeIframe.src = '';
            }
            
            // Parar vídeo local
            if (currentVideo) {
                currentVideo.pause();
                currentVideo.currentTime = 0;
                currentVideo = null;
            }
        }

        function retryVideo() {
            hideError();
            // Recarregar a página ou tentar novamente
            location.reload();
        }

        // Navigation e outros scripts (manter iguais)
        // ...

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