/**
 * Main Application File
 * Inicializa e coordena todos os módulos do WebApp
 */

class InventoryApp {
    constructor() {
        this.scanner = null;
        this.inventory = null;
        this.telegram = null;
        this.initialized = false;
        
        this.init();
    }

    async init() {
        try {
            console.log('Inicializando Inventory App...');
            
            // Aguardar DOM estar pronto
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.start());
            } else {
                this.start();
            }
            
        } catch (error) {
            console.error('Erro ao inicializar app:', error);
            this.showError('Erro ao inicializar aplicação');
        }
    }

    async start() {
        try {
            // Mostrar loading inicial
            this.showLoading(true);
            
            // Inicializar integração com Telegram
            this.telegram = new TelegramIntegration();
            
            // Aguardar um pouco para Telegram WebApp estar pronto
            await this.delay(500);
            
            // Inicializar gerenciador de inventário
            this.inventory = new InventoryManager();
            
            // Inicializar scanner QR
            this.scanner = new QRScanner();
            
            // Configurar integrações entre módulos
            this.setupIntegrations();
            
            // Configurar eventos globais
            this.setupGlobalEvents();
            
            // Marcar como inicializado
            this.initialized = true;
            
            // Ocultar loading
            this.showLoading(false);
            
            // Mostrar mensagem de boas-vindas
            this.showWelcomeMessage();
            
            console.log('Inventory App inicializado com sucesso!');
            
        } catch (error) {
            console.error('Erro ao iniciar app:', error);
            this.showError('Erro ao iniciar aplicação');
            this.showLoading(false);
        }
    }

    setupIntegrations() {
        // Integrar scanner com inventory
        if (this.scanner && this.inventory) {
            // Modificar método do scanner para usar inventory manager
            const originalProcessQR = this.scanner.processQRCode.bind(this.scanner);
            this.scanner.processQRCode = async (data) => {
                try {
                    this.showLoading(true);
                    
                    // Validar QR code
                    if (!/^\d+$/.test(data)) {
                        throw new Error('QR Code não contém um ID válido');
                    }
                    
                    const itemId = parseInt(data);
                    
                    // Buscar item
                    const item = await this.fetchItem(itemId);
                    
                    if (!item) {
                        throw new Error('Item não encontrado no sistema');
                    }
                    
                    // Configurar item atual no inventory
                    this.inventory.setCurrentItem(item);
                    
                    // Mostrar detalhes do item
                    this.scanner.showItemDetails(item);
                    
                    // Feedback haptic
                    if (this.telegram) {
                        this.telegram.notificationOccurred('success');
                    }
                    
                } catch (error) {
                    console.error('Erro ao processar QR code:', error);
                    this.showError(error.message);
                    
                    // Feedback haptic de erro
                    if (this.telegram) {
                        this.telegram.notificationOccurred('error');
                    }
                    
                    // Retomar escaneamento após erro
                    setTimeout(() => {
                        if (this.scanner && !this.scanner.scanning && this.scanner.stream) {
                            this.scanner.scanning = true;
                            this.scanner.scanFrame();
                        }
                    }, 2000);
                } finally {
                    this.showLoading(false);
                }
            };
        }

        // Integrar inventory com Telegram
        if (this.inventory && this.telegram) {
            // Sobrescrever método de finalizar inventário
            const originalFinish = this.inventory.finishInventory.bind(this.inventory);
            this.inventory.finishInventory = async () => {
                try {
                    if (this.inventory.items.length === 0) {
                        this.showError('Nenhum item inventariado');
                        return;
                    }

                    this.showLoading(true);

                    // Preparar dados
                    const inventoryData = {
                        items: this.inventory.items,
                        timestamp: new Date().toISOString(),
                        totalItems: this.inventory.items.length,
                        summary: this.inventory.generateSummary(),
                        user: this.telegram.getUserInfo()
                    };

                    // Enviar via Telegram
                    this.telegram.sendInventoryData(inventoryData);

                } catch (error) {
                    console.error('Erro ao finalizar inventário:', error);
                    this.showError('Erro ao finalizar inventário');
                } finally {
                    this.showLoading(false);
                }
            };

            // Atualizar botão principal do Telegram baseado no inventário
            const originalUpdateFinish = this.inventory.updateFinishButton.bind(this.inventory);
            this.inventory.updateFinishButton = () => {
                originalUpdateFinish();
                
                // Atualizar botão do Telegram
                if (this.inventory.items.length > 0) {
                    this.telegram.updateMainButton(`Finalizar (${this.inventory.items.length} itens)`);
                    this.telegram.showMainButton();
                } else {
                    this.telegram.hideMainButton();
                }
            };
        }

        // Disponibilizar instâncias globalmente para integração
        window.qrScanner = this.scanner;
        window.inventoryManager = this.inventory;
        window.telegramIntegration = this.telegram;
    }

    setupGlobalEvents() {
        // Tratar erros globais
        window.addEventListener('error', (event) => {
            console.error('Erro global:', event.error);
            this.showError('Erro inesperado ocorreu');
        });

        // Tratar promessas rejeitadas
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Promise rejeitada:', event.reason);
            this.showError('Erro de conexão');
        });

        // Tratar visibilidade da página
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('App ficou invisível');
            } else {
                console.log('App ficou visível');
                // Reativar scanner se necessário
                if (this.scanner && this.scanner.stream && !this.scanner.scanning) {
                    this.scanner.resumeScanning();
                }
            }
        });

        // Tratar orientação da tela
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                if (this.telegram) {
                    this.telegram.adjustLayout();
                }
            }, 300);
        });
    }

    async fetchItem(itemId) {
        try {
            // Tentar buscar via API local primeiro
            const response = await fetch(`/api/items/${itemId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Telegram-Init-Data': this.telegram?.getInitData() || ''
                }
            });

            if (response.ok) {
                return await response.json();
            }
            
            throw new Error('Item não encontrado na API');
            
        } catch (error) {
            console.warn('API local não disponível, usando dados simulados');
            
            // Fallback: dados simulados para desenvolvimento/teste
            return this.generateMockItem(itemId);
        }
    }

    generateMockItem(itemId) {
        const categories = ['Informática', 'Mobiliário', 'Equipamentos', 'Material Escritório'];
        const locations = ['Estoque A', 'Estoque B', 'Sala 1', 'Sala 2', 'Depósito'];
        
        return {
            id: itemId,
            nome: `Item de Teste ${itemId}`,
            codigo: `COD${String(itemId).padStart(4, '0')}`,
            categoria: categories[itemId % categories.length],
            localizacao: locations[itemId % locations.length],
            quantidade: Math.floor(Math.random() * 50) + 1,
            observacoes: 'Item gerado para teste',
            data_cadastro: new Date().toISOString()
        };
    }

    showWelcomeMessage() {
        const user = this.telegram?.getUserInfo();
        const message = user?.name 
            ? `Bem-vindo, ${user.name}! Inicie a câmera para começar o inventário.`
            : 'Bem-vindo! Inicie a câmera para começar o inventário.';
        
        this.showToast(message, 'info');
    }

    showError(message) {
        this.showToast(message, 'error');
        
        // Vibração de erro se disponível
        if (this.telegram) {
            this.telegram.notificationOccurred('error');
        }
    }

    showSuccess(message) {
        this.showToast(message, 'success');
        
        // Vibração de sucesso se disponível
        if (this.telegram) {
            this.telegram.notificationOccurred('success');
        }
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
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Métodos públicos para debugging
    getStatus() {
        return {
            initialized: this.initialized,
            scanner: !!this.scanner,
            inventory: !!this.inventory,
            telegram: !!this.telegram,
            inventoryItems: this.inventory?.items?.length || 0
        };
    }

    restart() {
        console.log('Reiniciando aplicação...');
        window.location.reload();
    }
}

// Inicializar aplicação quando o script carregar
window.addEventListener('load', () => {
    try {
        window.inventoryApp = new InventoryApp();
        console.log('Inventory App carregado');
    } catch (error) {
        console.error('Erro ao carregar Inventory App:', error);
    }
});

// Exportar para depuração
window.InventoryApp = InventoryApp;
