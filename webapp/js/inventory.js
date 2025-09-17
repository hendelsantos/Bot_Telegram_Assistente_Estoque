/**
 * Inventory Management Module
 * Gerencia a lista de itens inventariados e operações relacionadas
 */

class InventoryManager {
    constructor() {
        this.items = [];
        this.currentItem = null;
        
        this.init();
    }

    init() {
        this.setupEvents();
        this.updateCounter();
        console.log('Inventory Manager inicializado');
    }

    setupEvents() {
        // Botões de quantidade
        document.getElementById('qty-minus').addEventListener('click', () => {
            this.adjustQuantity(-1);
        });

        document.getElementById('qty-plus').addEventListener('click', () => {
            this.adjustQuantity(1);
        });

        // Campo de quantidade
        const qtyInput = document.getElementById('inventory-qty');
        qtyInput.addEventListener('input', (e) => {
            // Garantir que não seja negativo
            if (e.target.value < 0) {
                e.target.value = 0;
            }
        });

        qtyInput.addEventListener('keypress', (e) => {
            // Adicionar item ao pressionar Enter
            if (e.key === 'Enter') {
                this.addCurrentItem();
            }
        });

        // Botões de ação
        document.getElementById('add-item').addEventListener('click', () => {
            this.addCurrentItem();
        });

        document.getElementById('cancel-item').addEventListener('click', () => {
            this.cancelCurrentItem();
        });

        // Botões do inventário
        document.getElementById('clear-inventory').addEventListener('click', () => {
            this.clearInventory();
        });

        document.getElementById('finish-inventory').addEventListener('click', () => {
            this.finishInventory();
        });
    }

    setCurrentItem(item) {
        this.currentItem = {
            ...item,
            timestamp: new Date().toISOString()
        };
    }

    adjustQuantity(delta) {
        const qtyInput = document.getElementById('inventory-qty');
        const current = parseInt(qtyInput.value) || 0;
        const newValue = Math.max(0, current + delta);
        qtyInput.value = newValue;
    }

    addCurrentItem() {
        const qtyInput = document.getElementById('inventory-qty');
        const quantity = parseInt(qtyInput.value);

        if (quantity === undefined || isNaN(quantity) || quantity < 0) {
            this.showError('Por favor, insira uma quantidade válida');
            qtyInput.focus();
            return;
        }

        if (!this.currentItem) {
            this.showError('Nenhum item selecionado');
            return;
        }

        // Verificar se item já foi inventariado
        const existingIndex = this.items.findIndex(item => item.id === this.currentItem.id);
        
        if (existingIndex !== -1) {
            // Atualizar item existente
            this.items[existingIndex] = {
                ...this.currentItem,
                inventoryQuantity: quantity,
                difference: quantity - this.currentItem.quantidade,
                updated: true,
                timestamp: new Date().toISOString()
            };
            
            this.showToast(`Item ${this.currentItem.nome} atualizado!`, 'success');
        } else {
            // Adicionar novo item
            const inventoryItem = {
                ...this.currentItem,
                inventoryQuantity: quantity,
                difference: quantity - this.currentItem.quantidade,
                timestamp: new Date().toISOString()
            };

            this.items.push(inventoryItem);
            this.showToast(`Item ${this.currentItem.nome} adicionado!`, 'success');
        }

        // Atualizar interface
        this.updateInventoryList();
        this.updateCounter();
        this.updateFinishButton();

        // Voltar para scanner
        this.resumeScanning();
    }

    cancelCurrentItem() {
        this.currentItem = null;
        this.resumeScanning();
    }

    removeItem(itemId) {
        const index = this.items.findIndex(item => item.id === itemId);
        if (index !== -1) {
            const item = this.items[index];
            this.items.splice(index, 1);
            
            this.updateInventoryList();
            this.updateCounter();
            this.updateFinishButton();
            
            this.showToast(`Item ${item.nome} removido`, 'info');
        }
    }

    clearInventory() {
        if (this.items.length === 0) {
            this.showToast('Nenhum item para remover', 'info');
            return;
        }

        if (confirm(`Remover todos os ${this.items.length} itens do inventário?`)) {
            this.items = [];
            this.updateInventoryList();
            this.updateCounter();
            this.updateFinishButton();
            
            this.showToast('Inventário limpo', 'info');
        }
    }

    updateInventoryList() {
        const listContainer = document.getElementById('inventory-list');
        
        if (this.items.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-inventory">
                    <i class="fas fa-inbox"></i>
                    <p>Nenhum item inventariado ainda</p>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = this.items.map((item, index) => {
            const differenceClass = item.difference > 0 ? 'positive' : item.difference < 0 ? 'negative' : 'neutral';
            const differenceSign = item.difference > 0 ? '+' : '';
            
            return `
                <div class="inventory-item" data-item-id="${item.id}">
                    <div class="inventory-item-header">
                        <span class="inventory-item-name">${item.nome}</span>
                        <span class="inventory-item-id">ID: ${item.id}</span>
                    </div>
                    <div class="inventory-item-details">
                        <small>Código: ${item.codigo || 'N/A'} | ${item.categoria || 'N/A'}</small>
                    </div>
                    <div class="inventory-item-qty">
                        <span>Sistema: ${item.quantidade} | Inventário: ${item.inventoryQuantity}</span>
                        <span class="qty-difference ${differenceClass}">
                            ${differenceSign}${item.difference}
                        </span>
                    </div>
                    <div class="inventory-item-actions" style="margin-top: 0.5rem;">
                        <button class="btn btn-danger btn-sm" onclick="inventoryManager.removeItem(${item.id})">
                            <i class="fas fa-trash"></i>
                            Remover
                        </button>
                        ${item.updated ? '<small style="color: #28a745;"><i class="fas fa-sync"></i> Atualizado</small>' : ''}
                    </div>
                </div>
            `;
        }).join('');
    }

    updateCounter() {
        document.getElementById('item-counter').textContent = this.items.length;
    }

    updateFinishButton() {
        const finishBtn = document.getElementById('finish-inventory');
        finishBtn.disabled = this.items.length === 0;
    }

    resumeScanning() {
        // Delegar para o scanner
        if (window.qrScanner) {
            window.qrScanner.resumeScanningAfterItem();
        }
    }

    async finishInventory() {
        if (this.items.length === 0) {
            this.showError('Nenhum item inventariado');
            return;
        }

        try {
            this.showLoading(true);

            // Preparar dados para envio
            const inventoryData = {
                items: this.items,
                timestamp: new Date().toISOString(),
                totalItems: this.items.length,
                summary: this.generateSummary()
            };

            // Enviar dados para o Telegram
            await this.sendToTelegram(inventoryData);

            // Mostrar sucesso
            this.showToast('Inventário finalizado com sucesso!', 'success');
            
            // Limpar dados
            this.items = [];
            this.updateInventoryList();
            this.updateCounter();
            this.updateFinishButton();

        } catch (error) {
            console.error('Erro ao finalizar inventário:', error);
            this.showError('Erro ao finalizar inventário');
        } finally {
            this.showLoading(false);
        }
    }

    generateSummary() {
        const total = this.items.length;
        const withDifferences = this.items.filter(item => item.difference !== 0).length;
        const positive = this.items.filter(item => item.difference > 0).length;
        const negative = this.items.filter(item => item.difference < 0).length;
        const exact = this.items.filter(item => item.difference === 0).length;

        return {
            total,
            withDifferences,
            exact,
            positive,
            negative,
            accuracy: ((exact / total) * 100).toFixed(1)
        };
    }

    async sendToTelegram(data) {
        try {
            // Usar Telegram WebApp API para enviar dados
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.sendData(JSON.stringify(data));
                
                // Fechar WebApp
                setTimeout(() => {
                    window.Telegram.WebApp.close();
                }, 1000);
            } else {
                // Fallback: tentar enviar via API local
                const response = await fetch('/api/inventory/finish', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                if (!response.ok) {
                    throw new Error('Erro ao enviar dados');
                }
            }
        } catch (error) {
            console.error('Erro ao enviar para Telegram:', error);
            throw error;
        }
    }

    showError(message) {
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

    // Métodos para integração externa
    getInventoryData() {
        return {
            items: this.items,
            summary: this.generateSummary()
        };
    }

    loadInventoryData(data) {
        if (data && data.items) {
            this.items = data.items;
            this.updateInventoryList();
            this.updateCounter();
            this.updateFinishButton();
        }
    }
}

// Exportar para uso global
window.InventoryManager = InventoryManager;
