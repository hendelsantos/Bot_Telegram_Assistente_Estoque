/**
 * Telegram WebApp Integration Module
 * Gerencia a comunicação entre o WebApp e o bot do Telegram
 */

class TelegramIntegration {
    constructor() {
        this.webApp = null;
        this.user = null;
        this.initData = null;
        
        this.init();
    }

    init() {
        try {
            // Verificar se estamos em um ambiente Telegram WebApp
            if (window.Telegram && window.Telegram.WebApp) {
                this.webApp = window.Telegram.WebApp;
                this.setupTelegramWebApp();
            } else {
                console.warn('Telegram WebApp não detectado - modo desenvolvimento');
                this.setupDevelopmentMode();
            }
        } catch (error) {
            console.error('Erro ao inicializar integração Telegram:', error);
            this.setupDevelopmentMode();
        }
    }

    setupTelegramWebApp() {
        console.log('Configurando Telegram WebApp...');
        
        // Configurar tema
        this.setupTheme();
        
        // Obter dados do usuário
        this.user = this.webApp.initDataUnsafe?.user;
        this.initData = this.webApp.initData;
        
        // Configurar botões principais
        this.setupMainButton();
        this.setupBackButton();
        
        // Expandir WebApp
        this.webApp.expand();
        
        // Configurar eventos
        this.setupEvents();
        
        // Notificar que está pronto
        this.webApp.ready();
        
        console.log('Telegram WebApp configurado para usuário:', this.user?.first_name);
    }

    setupDevelopmentMode() {
        console.log('Modo desenvolvimento ativo');
        
        // Simular dados do usuário para desenvolvimento
        this.user = {
            id: 123456789,
            first_name: 'Usuário',
            last_name: 'Teste',
            username: 'teste'
        };
        
        // Simular WebApp básico
        this.webApp = {
            ready: () => console.log('WebApp ready (dev mode)'),
            close: () => console.log('WebApp close (dev mode)'),
            sendData: (data) => console.log('Enviando dados (dev mode):', data),
            showAlert: (message) => alert(message),
            showConfirm: (message) => confirm(message),
            MainButton: {
                show: () => console.log('MainButton show'),
                hide: () => console.log('MainButton hide'),
                setText: (text) => console.log('MainButton setText:', text),
                onClick: (callback) => console.log('MainButton onClick set'),
                enable: () => console.log('MainButton enable'),
                disable: () => console.log('MainButton disable')
            },
            BackButton: {
                show: () => console.log('BackButton show'),
                hide: () => console.log('BackButton hide'),
                onClick: (callback) => console.log('BackButton onClick set')
            }
        };
    }

    setupTheme() {
        if (!this.webApp.themeParams) return;
        
        const root = document.documentElement;
        const theme = this.webApp.themeParams;
        
        // Aplicar cores do tema do Telegram
        if (theme.bg_color) {
            root.style.setProperty('--bg-primary', theme.bg_color);
        }
        
        if (theme.text_color) {
            root.style.setProperty('--dark-color', theme.text_color);
        }
        
        if (theme.hint_color) {
            root.style.setProperty('--secondary-color', theme.hint_color);
        }
        
        if (theme.button_color) {
            root.style.setProperty('--primary-color', theme.button_color);
        }
        
        if (theme.button_text_color) {
            root.style.setProperty('--button-text-color', theme.button_text_color);
        }
    }

    setupMainButton() {
        const mainButton = this.webApp.MainButton;
        
        // Configurar botão principal como "Finalizar Inventário"
        mainButton.setText('Finalizar Inventário');
        mainButton.hide(); // Inicialmente oculto
        
        // Evento do botão principal
        mainButton.onClick(() => {
            if (window.inventoryManager) {
                window.inventoryManager.finishInventory();
            }
        });
    }

    setupBackButton() {
        const backButton = this.webApp.BackButton;
        
        // Mostrar botão voltar
        backButton.show();
        
        // Evento do botão voltar
        backButton.onClick(() => {
            this.handleBackButton();
        });
    }

    setupEvents() {
        // Escutar mudanças no viewport
        this.webApp.onEvent('viewportChanged', () => {
            console.log('Viewport changed');
            this.adjustLayout();
        });
        
        // Escutar fechamento do WebApp
        this.webApp.onEvent('mainButtonClicked', () => {
            console.log('Main button clicked');
        });
    }

    handleBackButton() {
        const itemSection = document.getElementById('item-section');
        const scannerSection = document.getElementById('scanner-section');
        
        // Se estiver na tela de item, voltar para scanner
        if (itemSection.style.display !== 'none') {
            if (window.inventoryManager) {
                window.inventoryManager.cancelCurrentItem();
            }
            return;
        }
        
        // Senão, confirmar saída
        this.webApp.showConfirm('Deseja sair do inventário?', (confirmed) => {
            if (confirmed) {
                this.exitWebApp();
            }
        });
    }

    adjustLayout() {
        // Ajustar layout baseado no viewport do Telegram
        const viewportHeight = this.webApp.viewportHeight;
        const viewportStableHeight = this.webApp.viewportStableHeight;
        
        if (viewportHeight && viewportStableHeight) {
            document.body.style.height = `${viewportHeight}px`;
        }
    }

    showMainButton() {
        if (this.webApp.MainButton) {
            this.webApp.MainButton.show();
            this.webApp.MainButton.enable();
        }
    }

    hideMainButton() {
        if (this.webApp.MainButton) {
            this.webApp.MainButton.hide();
        }
    }

    updateMainButton(text, enabled = true) {
        if (this.webApp.MainButton) {
            this.webApp.MainButton.setText(text);
            
            if (enabled) {
                this.webApp.MainButton.enable();
            } else {
                this.webApp.MainButton.disable();
            }
        }
    }

    sendInventoryData(data) {
        try {
            const payload = {
                type: 'inventory_completed',
                user_id: this.user?.id,
                timestamp: new Date().toISOString(),
                data: data
            };
            
            const jsonData = JSON.stringify(payload);
            
            console.log('Enviando dados do inventário:', payload);
            
            // Enviar dados para o bot
            this.webApp.sendData(jsonData);
            
            // Mostrar feedback
            this.showAlert('Inventário enviado com sucesso!');
            
            // Fechar WebApp após 2 segundos
            setTimeout(() => {
                this.exitWebApp();
            }, 2000);
            
        } catch (error) {
            console.error('Erro ao enviar dados:', error);
            this.showAlert('Erro ao enviar inventário. Tente novamente.');
        }
    }

    showAlert(message) {
        if (this.webApp.showAlert) {
            this.webApp.showAlert(message);
        } else {
            alert(message);
        }
    }

    showConfirm(message, callback) {
        if (this.webApp.showConfirm) {
            this.webApp.showConfirm(message, callback);
        } else {
            const result = confirm(message);
            callback(result);
        }
    }

    exitWebApp() {
        console.log('Fechando WebApp...');
        
        if (this.webApp.close) {
            this.webApp.close();
        } else {
            // Fallback para desenvolvimento
            window.close();
        }
    }

    // Métodos utilitários
    getUserInfo() {
        return {
            id: this.user?.id,
            name: `${this.user?.first_name} ${this.user?.last_name || ''}`.trim(),
            username: this.user?.username
        };
    }

    isInTelegram() {
        return !!(window.Telegram && window.Telegram.WebApp && this.webApp.initData);
    }

    getInitData() {
        return this.initData;
    }

    // Haptic feedback
    impactOccurred(style = 'medium') {
        if (this.webApp.HapticFeedback) {
            this.webApp.HapticFeedback.impactOccurred(style);
        }
    }

    notificationOccurred(type = 'success') {
        if (this.webApp.HapticFeedback) {
            this.webApp.HapticFeedback.notificationOccurred(type);
        }
    }

    selectionChanged() {
        if (this.webApp.HapticFeedback) {
            this.webApp.HapticFeedback.selectionChanged();
        }
    }
}

// Exportar para uso global
window.TelegramIntegration = TelegramIntegration;
