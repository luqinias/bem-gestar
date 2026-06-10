# BemGestar - Especificação de Design Mobile

## Design System

### Paleta de Cores
- **Primary Pink**: #E94B8B (Rosa vibrante, principal)
- **Primary Purple**: #6B4FA8 (Roxo, secundária)
- **Background**: #FAFBFC (Cinza muito claro)
- **Surface**: #FFFFFF (Branco, cards)
- **Text Primary**: #2C2D3D (Cinza escuro, textos)
- **Text Secondary**: #707079 (Cinza médio, subtítulos)
- **Text Light**: #A8AABA (Cinza claro, labels)
- **Border**: #E8E8EA (Cinza muito claro, divisores)
- **Success**: #10A37F (Verde, validações)
- **Warning**: #FFA500 (Laranja, alertas)
- **Danger**: #EF4444 (Vermelho, erros)

### Tipografia
- **Font Primary**: Inter
- **Heading 1**: 28px, Bold, Text Primary
- **Heading 2**: 24px, SemiBold, Text Primary
- **Heading 3**: 20px, SemiBold, Text Primary
- **Body Large**: 16px, Regular, Text Primary
- **Body Regular**: 14px, Regular, Text Secondary
- **Body Small**: 12px, Regular, Text Light
- **Button**: 16px, SemiBold, White

### Espaçamento
- **XS**: 4px
- **SM**: 8px
- **MD**: 16px
- **LG**: 24px
- **XL**: 32px

### Corner Radius
- **SM**: 8px (inputs, small buttons)
- **MD**: 12px (cards, buttons)
- **LG**: 16px (large cards)
- **FULL**: 999px (avatars, pills)

---

## Estrutura de Telas (390px x 844px - iPhone SE)

### 1. Tela de Login
**Objetivo**: Autenticação do usuário

**Componentes**:
- Status Bar (62px)
- Logo BemGestar (center top)
- Text: "Bem-vindo ao BemGestar"
- Email Input (placeholder: "seu@email.com")
- Password Input (placeholder: "Sua senha")
- Button "Entrar" (Full width, Primary Pink)
- Text: "Não tem conta?" + Link "Cadastre-se" (Primary Purple)
- Content Padding: 16px

---

### 2. Tela de Cadastro de Paciente
**Objetivo**: Criar novo usuário paciente

**Componentes**:
- Status Bar (62px)
- Back Button + Title "Criar Conta"
- Inputs (cada um com padding vertical 8px):
  - Name (texto)
  - Date of Birth (data picker)
  - CPF (máscara XXX.XXX.XXX-XX)
  - Phone (máscara com país)
  - Email (validação)
  - Password (mascarado)
  - Confirm Password (mascarado)
- Button "Registrar" (Full width, Primary Pink)
- Text: "Já tem conta?" + Link "Faça login"
- Content Padding: 16px

---

### 3. Tela Inicial (Home)
**Objetivo**: Dashboard principal com resumo de saúde

**Componentes**:
- Status Bar (62px)
- Header:
  - Logo BemGestar left
  - Bell notification icon right (com badge se houver alertas)
- Greeting: "Olá, [Nome]!" (Heading 3, Primary Purple)
- Subtext: "Que bom ter você aqui hoje." (Body Regular, Text Secondary)
- Card Gestational (Background: gradient pink-purple):
  - Icon calendar
  - "Você está em 24 semanas"
  - "2º trimestre"
  - Progress circle "60% da gestação"
- Section "Ações rápidas" (4 items em grid 2x2):
  - Registrar sinais/sintomas (icon heart)
  - Agenda/Lembretes (icon calendar)
  - Conteúdos educativos (icon book)
  - Falar com médico (icon chat)
- Card Risk Score (Background: Primary Pink):
  - Shield icon
  - "Seu score de risco"
  - Large badge "Baixo risco" com cor (verde/amarelo/vermelho)
  - Info text: "Continue acompanhando"
- Next Consultation:
  - Calendar icon
  - "Próxima consulta"
  - Date/time: "18 de maio de 2024 • 09:30"
  - Doctor: "Dr. Lucas Almeida"
  - Link: "Ver detalhes"
- Motivational quote at bottom
- Tab Bar (56px) com 5 items:
  1. Home (icon house, ativo)
  2. Acompanhar (icon chart)
  3. Registrar (icon + em destaque)
  4. Mensagens (icon chat)
  5. Perfil (icon person)

---

### 4. Tela de Registro de Sinais Vitais
**Objetivo**: Registrar medições de saúde

**Componentes**:
- Status Bar (62px)
- Title: "Registrar Sinais Vitais" (Heading 2)
- Form com inputs numéricos:
  - Pressão Sistólica/Diastólica (lado a lado, em mmHg)
  - Frequência Cardíaca (bpm)
  - Temperatura (°C)
  - Peso (kg)
  - Saturação de Oxigênio (%)
  - Glicemia (mg/dL)
  - Horas de Sono (com spinner ou input)
  - Text area: "Observações" (opcional)
- Last recorded: "Último registro: [data/hora]"
- Button "Salvar" (Full width, Primary Pink)
- Button "Cancelar" (Full width, outline)
- Tab Bar (56px)

---

### 5. Tela de Registro de Sintomas
**Objetivo**: Registrar sintomas e sensações

**Componentes**:
- Status Bar (62px)
- Title: "Registrar Sintomas" (Heading 2)
- Text: "Selecione os sintomas que você sente" (Body Small)
- Symptom List (Cards com checkbox):
  - Dor de cabeça
  - Enjoo
  - Vômito
  - Dor abdominal
  - Sangramento
  - Inchaço
  - Visão turva
  - Dor no peito
  - Falta de ar
  - Redução movimentos fetais
  - Ardência ao urinar
  - Febre
  - Tontura
  - Dor lombar
  - Contrações
  - Outro
- Severity selector (Leve, Moderado, Grave) - Radio buttons
- Text area: "Descrição adicional" (opcional)
- Button "Salvar" (Full width, Primary Pink)
- Tab Bar (56px)

---

### 6. Tela de Acompanhamento
**Objetivo**: Visualizar histórico e gráficos de monitoramento

**Componentes**:
- Status Bar (62px)
- Title: "Acompanhamento" (Heading 2)
- Tabs: "Gráficos" | "Histórico"
- Tab "Gráficos":
  - Chart: Pressão Arterial (últimos 30 dias)
  - Chart: Peso (últimos 30 dias)
  - Chart: Frequência Cardíaca (últimos 30 dias)
  - Chart: Score de Risco (últimos 30 dias)
- Tab "Histórico":
  - List de registros com:
    - Data/hora
    - Ícone do tipo (heart para vitals, alert para symptoms)
    - Resumo dos valores
    - Botão de detalhe ou delete
- Filter: Data range (picker)
- Tab Bar (56px)

---

### 7. Tela de Perfil
**Objetivo**: Visualizar e editar informações pessoais

**Componentes**:
- Status Bar (62px)
- Header com Avatar (circular, 80px)
- Nome: "[Nome da Paciente]" (Heading 2)
- Section "Informações Pessoais":
  - Email: [email] (copiar icon)
  - Telefone: [phone] (copiar icon)
  - Data de Nascimento: [data]
  - CPF: [CPF] (mascarado, copiar icon)
- Section "Histórico Médico":
  - Histórico Médico: [texto]
  - Histórico Familiar: [texto]
- Section "Dados Gestacionais":
  - Semana gestacional: [semana]
  - Data prevista do parto: [data]
  - Tipo sanguíneo: [tipo]
  - Altura: [cm]
  - Peso pré-gestacional: [kg]
  - Médico responsável: [nome]
- Button "Editar Perfil" (Full width, Primary Pink)
- Button "Desconectar" (Full width, outline red)
- Tab Bar (56px)

---

### 8. Tela de Mensagens
**Objetivo**: Chat com médico responsável

**Componentes**:
- Status Bar (62px)
- Title: "Mensagens" (Heading 2)
- Search bar: "Procurar conversas" (com icon)
- List de conversas:
  - Avatar do médico (circular, 40px)
  - Nome: "Dr(a). [Nome]"
  - Última mensagem: "[preview]" (Text Secondary)
  - Horário: "[hora]" (Text Light)
  - Unread badge (se houver)
- Empty state (se nenhuma conversa):
  - Icon
  - Text: "Nenhuma conversa iniciada"
  - Button: "Contatar Médico"
- Tab Bar (56px)

### 8b. Tela de Chat
**Objetivo**: Conversa com um médico específico

**Componentes**:
- Status Bar (62px)
- Header:
  - Back button
  - Avatar + Nome do médico
  - Ícone info
- Messages list (chat bubbles):
  - User messages (right, Primary Pink background)
  - Doctor messages (left, Surface background, border)
  - Timestamp (Body Small)
- Input area (sticky bottom):
  - Text input: "Digitar mensagem..."
  - Send button (icon, Primary Pink)
- Indicator: "Digitando..." (Body Small, Text Light)

---

### 9. Tela de Educação
**Objetivo**: Biblioteca de conteúdos educacionais

**Componentes**:
- Status Bar (62px)
- Title: "Conteúdos Educativos" (Heading 2)
- Search bar: "Procurar artigos..."
- Tabs/Filter: "Todos" | "Semanas" | "Sintomas" | "Risco"
- Card list de artigos:
  - Card (Surface, rounded LG, shadow):
    - Thumbnail (aspect 16:9)
    - Title (Body Large, Bold)
    - Category tag (Primary Pink, Text White)
    - Excerpt (Body Small, Text Secondary)
    - Read time: "[X] min de leitura"
- Tab Bar (56px)

---

## Componentes Reutilizáveis

### Button
- **Variants**: Primary (filled), Secondary (outline)
- **Sizes**: Large (full width), Medium, Small
- **States**: Default, Hover, Active, Disabled
- **Corner Radius**: MD (12px)

### Input
- **Text Input**: placeholder, icon, error state
- **Password Input**: toggle show/hide
- **Number Input**: min/max, spinner
- **Date Picker**: calendar
- **Corner Radius**: SM (8px)
- **Border**: 1px Border color

### Card
- **Background**: Surface
- **Padding**: MD (16px)
- **Corner Radius**: LG (16px)
- **Shadow**: soft shadow
- **States**: Normal, Hover (slight lift)

### Avatar
- **Sizes**: XL (80px), Large (48px), Medium (40px), Small (32px)
- **Corner Radius**: FULL (circular)

### Badge
- **Variants**: Primary, Secondary, Success, Warning, Danger
- **Corner Radius**: FULL
- **Padding**: 4px 12px

### Tab Bar (Bottom Navigation)
- **Height**: 56px
- **Items**: 3-5 icons + labels
- **Corner Radius**: FULL (capsule shape)
- **Background**: Surface with opacity, frosted glass effect
- **Position**: Floating above bottom edge (12px padding)
- **Active Item**: filled icon + colored background

---

## Fluxo de Navegação

```
Login → Cadastro → Home
                    ├─ Sinais Vitais (via botão "Registrar")
                    ├─ Sintomas (via botão "Registrar")
                    ├─ Acompanhamento
                    ├─ Mensagens → Chat
                    ├─ Educação
                    └─ Perfil
```

---

## Notas de Implementação

1. **Responsividade**: Design para iPhone SE (390px), testar também em dispositivos maiores
2. **Acessibilidade**: 
   - Contrast ratio mínimo 4.5:1
   - Touch targets: mínimo 44x44px
   - Labels claros para inputs
3. **Performance**: 
   - Lazy loading de imagens
   - Paginação de listas longas
4. **Offline**: 
   - Indicador de sincronização
   - Suporte a modo offline (dados em cache)
5. **Localization**: Textos em português (PT-BR)
