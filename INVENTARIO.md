# 📋 Módulo de Inventário - Documentação

## 🎯 Funcionalidade

O módulo de inventário permite realizar contagens rápidas de estoque usando QR Codes, gerando relatórios detalhados em múltiplos formatos.

## 🚀 Como Usar

### 1. **Iniciar Inventário**
```
/inventario
```
- Qualquer usuário pode iniciar um inventário
- O bot irá solicitar o escaneamento de QR Codes

### 2. **Processo de Inventário**

1. **Escanear QR Code**: Envie uma foto do QR Code do item
2. **Confirmar Item**: O bot mostrará os dados do item encontrado
3. **Inserir Quantidade**: Digite a quantidade encontrada fisicamente
4. **Repetir**: Continue escaneando outros itens
5. **Finalizar**: Digite `/finalizar_inventario` quando terminar

### 3. **Comandos Durante o Inventário**

- `/finalizar_inventario` - Finaliza e gera relatório
- `/cancelar` - Cancela o inventário atual

## 📊 Formatos de Relatório

Ao finalizar o inventário, você pode escolher entre:

### 📄 **TXT**
- Relatório em texto simples
- Fácil leitura
- Compatível com qualquer sistema

### 📊 **CSV**
- Dados separados por ponto e vírgula
- Compatível com Excel/Calc
- Ideal para análises

### 📗 **Excel**
- Planilha formatada
- Colunas ajustadas automaticamente
- Profissional para relatórios

## 📋 Informações no Relatório

Cada item inventariado inclui:

- **ID**: Identificador único do item
- **Nome**: Nome do produto
- **Código**: Código do produto (se disponível)
- **Categoria**: Categoria do item
- **Localização**: Local de armazenamento
- **Qtd Sistema**: Quantidade registrada no sistema
- **Qtd Inventário**: Quantidade encontrada fisicamente
- **Diferença**: Divergência entre sistema e físico
- **Data Inventário**: Timestamp da contagem

## 🔍 Funcionalidades Especiais

### ✅ **Validação Automática**
- Verifica se QR Code contém ID válido
- Confirma existência do item no banco
- Mostra dados completos antes da contagem

### ⚠️ **Indicadores Visuais**
- ✅ Verde: Quantidade confere
- ⚠️ Amarelo: Quantidade maior que sistema
- ❌ Vermelho: Quantidade menor que sistema

### 📊 **Controle de Sessão**
- Mantém lista de itens inventariados
- Contador de progresso em tempo real
- Limpeza automática dos dados ao finalizar

## 🛠️ Exemplo de Uso

```
👤 Usuário: /inventario

🤖 Bot: 📋 Inventário Iniciado!
       Envie a foto do QR Code do item que deseja inventariar.

👤 Usuário: [Envia foto do QR Code]

🤖 Bot: 📦 Item Encontrado:
       ID: 1
       Nome: Notebook Dell
       Código: NB001
       Categoria: Informática
       Localização: Estoque A
       Quantidade no Sistema: 5
       
       Digite a quantidade encontrada no inventário:

👤 Usuário: 4

🤖 Bot: ❌ Item Adicionado ao Inventário:
       Nome: Notebook Dell
       Sistema: 5
       Inventário: 4
       Diferença: -1
       
       Total de itens inventariados: 1
       
       Envie o próximo QR Code ou digite /finalizar_inventario

👤 Usuário: /finalizar_inventario

🤖 Bot: 📋 Inventário Concluído!
       Total de itens inventariados: 1
       Escolha o formato do relatório:
       [📄 TXT] [📊 CSV] [📗 Excel]
```

## 🔒 Segurança

- ✅ Acessível para todos os usuários
- ✅ Validação de dados de entrada
- ✅ Limpeza automática de dados temporários
- ✅ Controle de sessão por usuário

## ⚡ Vantagens

1. **Rapidez**: Escaneamento direto de QR Codes
2. **Precisão**: Validação automática de itens
3. **Flexibilidade**: Múltiplos formatos de saída
4. **Controle**: Acompanhamento em tempo real
5. **Profissional**: Relatórios formatados
