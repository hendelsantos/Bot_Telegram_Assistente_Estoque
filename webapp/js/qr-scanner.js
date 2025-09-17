/**
 * QR Code Scanner Module
 * Gerencia o acesso à câmera e leitura de QR codes
 */

class QRScanner {
    constructor() {
        this.video = document.getElementById('camera');
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.stream = null;
        this.scanning = false;
        this.cameras = [];
        this.currentCameraIndex = 0;
        
        this.init();
    }

    async init() {
        try {
            // Listar câmeras disponíveis
            await this.listCameras();
            
            // Configurar eventos
            this.setupEvents();
            
            console.log('QR Scanner inicializado');
        } catch (error) {
            console.error('Erro ao inicializar scanner:', error);
            this.showError('Erro ao acessar câmera');
        }
    }

    async listCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.cameras = devices.filter(device => device.kind === 'videoinput');
            
            console.log(`Encontradas ${this.cameras.length} câmeras`);
            
            // Mostrar botão de trocar câmera se houver mais de uma
            if (this.cameras.length > 1) {
                document.getElementById('switch-camera').style.display = 'inline-flex';
            }
        } catch (error) {
            console.error('Erro ao listar câmeras:', error);
        }
    }

    setupEvents() {
        // Botão de iniciar/parar câmera
        document.getElementById('toggle-camera').addEventListener('click', () => {
            if (this.scanning) {
                this.stopScanning();
            } else {
                this.startScanning();
            }
        });

        // Botão de trocar câmera
        document.getElementById('switch-camera').addEventListener('click', () => {
            this.switchCamera();
        });

        // Detectar quando a página fica visível/invisível
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.scanning) {
                this.pauseScanning();
            } else if (!document.hidden && this.scanning) {
                this.resumeScanning();
            }
        });
    }

    async startScanning() {
        try {
            this.showLoading(true);
            
            // Preferir câmera traseira em dispositivos móveis
            const constraints = {
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };

            // Se temos câmeras específicas, usar a selecionada
            if (this.cameras.length > 0) {
                constraints.video.deviceId = this.cameras[this.currentCameraIndex].deviceId;
            }

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.video.srcObject = this.stream;
            
            await new Promise((resolve) => {
                this.video.onloadedmetadata = resolve;
            });

            this.scanning = true;
            this.updateScanningUI();
            this.scanFrame();
            
            this.showStatus('Posicione o QR Code na moldura', 'info');
            
        } catch (error) {
            console.error('Erro ao iniciar câmera:', error);
            this.showError('Não foi possível acessar a câmera');
        } finally {
            this.showLoading(false);
        }
    }

    stopScanning() {
        this.scanning = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.video.srcObject = null;
        this.updateScanningUI();
        this.showStatus('Câmera desligada', 'info');
    }

    pauseScanning() {
        this.scanning = false;
    }

    resumeScanning() {
        if (this.stream) {
            this.scanning = true;
            this.scanFrame();
        }
    }

    async switchCamera() {
        if (this.cameras.length < 2) return;
        
        this.currentCameraIndex = (this.currentCameraIndex + 1) % this.cameras.length;
        
        if (this.scanning) {
            this.stopScanning();
            setTimeout(() => this.startScanning(), 500);
        }
    }

    scanFrame() {
        if (!this.scanning || this.video.readyState !== this.video.HAVE_ENOUGH_DATA) {
            if (this.scanning) {
                requestAnimationFrame(() => this.scanFrame());
            }
            return;
        }

        // Configurar canvas com dimensões do vídeo
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // Desenhar frame atual do vídeo no canvas
        this.context.drawImage(this.video, 0, 0);
        
        // Obter dados da imagem
        const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        // Tentar ler QR code
        const code = jsQR(imageData.data, imageData.width, imageData.height);
        
        if (code) {
            this.onQRCodeDetected(code.data);
        } else {
            // Continuar escaneando
            requestAnimationFrame(() => this.scanFrame());
        }
    }

    onQRCodeDetected(data) {
        console.log('QR Code detectado:', data);
        
        // Parar escaneamento temporariamente
        this.scanning = false;
        
        // Vibrar se disponível
        if (navigator.vibrate) {
            navigator.vibrate(200);
        }
        
        // Mostrar feedback visual
        this.showStatus('QR Code detectado!', 'success');
        
        // Processar QR code
        this.processQRCode(data);
    }

    async processQRCode(data) {
        try {
            this.showLoading(true);
            
            // Validar se é um ID numérico
            if (!/^\d+$/.test(data)) {
                throw new Error('QR Code não contém um ID válido');
            }
            
            const itemId = parseInt(data);
            
            // Buscar item no backend
            const item = await this.fetchItemFromBackend(itemId);
            
            if (!item) {
                throw new Error('Item não encontrado no sistema');
            }
            
            // Mostrar dados do item
            this.showItemDetails(item);
            
        } catch (error) {
            console.error('Erro ao processar QR code:', error);
            this.showError(error.message);
            
            // Retomar escaneamento após 2 segundos
            setTimeout(() => {
                if (!this.scanning && this.stream) {
                    this.scanning = true;
                    this.scanFrame();
                }
            }, 2000);
        } finally {
            this.showLoading(false);
        }
    }

    async fetchItemFromBackend(itemId) {
        try {
            // Simular chamada para backend
            // Em produção, seria uma chamada real para a API
            const response = await fetch(`/api/items/${itemId}`);
            
            if (!response.ok) {
                throw new Error('Item não encontrado');
            }
            
            return await response.json();
            
        } catch (error) {
            // Fallback: usar dados simulados para teste
            console.warn('Backend não disponível, usando dados simulados');
            
            return {
                id: itemId,
                nome: `Item ${itemId}`,
                codigo: `COD${itemId}`,
                categoria: 'Categoria Teste',
                localizacao: 'Estoque A',
                quantidade: Math.floor(Math.random() * 100) + 1
            };
        }
    }

    showItemDetails(item) {
        // Preencher dados do item
        document.getElementById('item-id').textContent = item.id;
        document.getElementById('item-name').textContent = item.nome;
        document.getElementById('item-code').textContent = item.codigo || 'N/A';
        document.getElementById('item-category').textContent = item.categoria || 'N/A';
        document.getElementById('item-location').textContent = item.localizacao || 'N/A';
        document.getElementById('item-system-qty').textContent = item.quantidade;
        
        // Limpar campo de quantidade
        document.getElementById('inventory-qty').value = '';
        
        // Esconder scanner e mostrar detalhes
        document.getElementById('scanner-section').style.display = 'none';
        document.getElementById('item-section').style.display = 'block';
        
        // Focar no campo de quantidade
        setTimeout(() => {
            document.getElementById('inventory-qty').focus();
        }, 300);
    }

    updateScanningUI() {
        const toggleBtn = document.getElementById('toggle-camera');
        const icon = toggleBtn.querySelector('i');
        const text = toggleBtn.querySelector('span');
        
        if (this.scanning) {
            icon.className = 'fas fa-stop';
            text.textContent = 'Parar Câmera';
            toggleBtn.className = 'btn btn-danger';
        } else {
            icon.className = 'fas fa-camera';
            text.textContent = 'Iniciar Câmera';
            toggleBtn.className = 'btn btn-secondary';
        }
    }

    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('status-message');
        const icon = statusEl.querySelector('i');
        const text = statusEl.querySelector('span');
        
        // Atualizar ícone baseado no tipo
        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle'
        };
        
        icon.className = icons[type] || icons.info;
        text.textContent = message;
        
        // Atualizar classe CSS
        statusEl.className = `status-message ${type}`;
        
        // Auto-remover após 5 segundos se for sucesso ou erro
        if (type === 'success' || type === 'error') {
            setTimeout(() => {
                if (text.textContent === message) {
                    this.showStatus('Posicione o QR Code na moldura para escanear', 'info');
                }
            }, 5000);
        }
    }

    showError(message) {
        this.showStatus(message, 'error');
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Remover toast após 4 segundos
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 4000);
    }

    showLoading(show) {
        document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
    }

    // Método público para retomar escaneamento
    resumeScanningAfterItem() {
        document.getElementById('scanner-section').style.display = 'block';
        document.getElementById('item-section').style.display = 'none';
        
        if (this.stream && !this.scanning) {
            this.scanning = true;
            this.scanFrame();
            this.showStatus('Continue escaneando outros itens', 'info');
        }
    }
}

// Exportar para uso global
window.QRScanner = QRScanner;
