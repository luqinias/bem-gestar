# Guia de Criação das Telas - BemGestar Pencil

## Como Usar Este Guia

Este arquivo documenta a estrutura de todas as 9 telas da aplicação BemGestar para implementação no Pencil Design System.

## Checklist de Telas

- [ ] 1. Login
- [ ] 2. Cadastro
- [ ] 3. Home (Tela Principal)
- [ ] 4. Sinais Vitais
- [ ] 5. Sintomas
- [ ] 6. Acompanhamento
- [ ] 7. Perfil
- [ ] 8. Mensagens
- [ ] 9. Educação

## Estrutura Padrão de Cada Tela

Todas as telas seguem este padrão:

```
┌─────────────────────────┐
│   Status Bar (62px)     │  ← Hora, sinal, bateria (nunca UI abaixo)
├─────────────────────────┤
│                         │
│   CONTENT AREA          │  ← Padding: 16px horizontal
│   Organizado em seções  │  ← Gap entre seções: 24px
│   com gap de 24px       │
│                         │
├─────────────────────────┤
│   Tab Bar (56px)        │  ← Flutuante, 12px do bottom
│ [H][C][+][M][P]         │  ← H=Home, C=Chart, +Add, M=Message, P=Profile
└─────────────────────────┘
```

## Variáveis de Design (Já Definidas)

### Cores
```
$color-primary-pink:    #E94B8B
$color-primary-purple:  #6B4FA8
$color-background:      #FAFBFC
$color-surface:         #FFFFFF
$color-text-primary:    #2C2D3D
$color-text-secondary:  #707079
$color-text-light:      #A8AABA
$color-border:          #E8E8EA
$color-success:         #10A37F
$color-warning:         #FFA500
$color-danger:          #EF4444
```

### Espaçamento
```
$spacing-xs: 4px
$spacing-sm: 8px
$spacing-md: 16px
$spacing-lg: 24px
$spacing-xl: 32px
```

### Border Radius
```
$corner-radius-sm:  8px   (inputs)
$corner-radius-md:  12px  (buttons, cards)
$corner-radius-lg:  16px  (large cards)
$corner-radius-full: 999px (avatars)
```

## Detalhes de Cada Tela

### Tela 1: LOGIN

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px) - transparent, text white
2. Spacing: 40px (top padding)
3. Logo/Wordmark "BemGestar" 
   - Font: Inter Bold 28px
   - Color: $color-primary-purple
   - Center aligned
4. Spacing: 8px
5. Text "Bem-vindo de volta!" 
   - Font: Inter Regular 14px
   - Color: $color-text-secondary
   - Center aligned
6. Spacing: 32px
7. Input "Email"
   - Width: full (16px padding)
   - Height: 48px
   - Placeholder: "seu@email.com"
   - Border: 1px $color-border
   - Border Radius: 8px
   - Padding: 12px 16px
8. Spacing: 12px
9. Input "Senha"
   - Same as email
   - Placeholder: "Sua senha"
   - Show/hide toggle icon (direita)
10. Spacing: 16px
11. Text "Esqueceu a senha?" (right aligned, $color-primary-purple, underline)
12. Spacing: 24px
13. Button "Entrar"
    - Width: full (16px padding)
    - Height: 48px
    - Background: $color-primary-pink
    - Text: "Entrar" (white, Inter Bold 16px)
    - Border Radius: 8px
14. Spacing: 16px
15. Text "Não tem conta?"
    - Color: $color-text-secondary
    - Center aligned
16. Link "Cadastre-se"
    - Color: $color-primary-purple
    - Underline
17. Tab Bar (56px) - hidden on this screen or minimal

---

### Tela 2: CADASTRO

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Back button (< icon) - left, $color-primary-purple
   - Title "Criar Conta" - center, Inter Bold 24px
3. Spacing: 24px
4. Inputs (each with 12px bottom spacing):
   ```
   [Input] "Nome completo"
   [Input] "Data de nascimento" (date picker)
   [Input] "CPF" (máscara: XXX.XXX.XXX-XX)
   [Input] "Telefone" (com código país)
   [Input] "Email"
   [Input] "Senha"
   [Input] "Confirmar Senha"
   ```
5. Spacing: 24px
6. Button "Registrar" (like in Login)
7. Spacing: 12px
8. Text "Já tem conta?" + Link "Faça login"
9. Spacing: 24px (bottom)
10. Tab Bar (não visível)

---

### Tela 3: HOME (Principal)

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header Container (16px padding, flex row):
   - Left: Logo "BemGestar" (logo icon + text, 16px)
   - Right: Bell icon with badge (red dot if notifications)
3. Spacing: 24px
4. Greeting Section:
   ```
   "Olá, Ana!" (Inter SemiBold 24px, $color-primary-purple)
   "Que bom ter você aqui hoje." (Inter Regular 14px, $color-text-secondary)
   ```
5. Spacing: 24px
6. Card Gestational (Gradient pink to purple):
   - Border Radius: 16px
   - Padding: 20px
   - Inside:
     ```
     [📅 Icon]
     "Você está em"
     "24 semanas" (Inter Bold 28px, white)
     "2º trimestre" (14px, white opacity 80%)
     
     [Circle Progress 60%]
     "60% da gestação"
     ```
7. Spacing: 24px
8. Section Title "Ações rápidas" (with "Ver todas >" link right)
9. Grid 2x2 action cards:
   ```
   ┌─────────────────┐ ┌─────────────────┐
   │ 💓 Registrar    │ │ 📅 Agenda       │
   │ sinais/sintomas │ │ e lembretes     │
   └─────────────────┘ └─────────────────┘
   ┌─────────────────┐ ┌─────────────────┐
   │ 📖 Conteúdos    │ │ 💬 Falar com    │
   │ educativos      │ │ equipe médica   │
   └─────────────────┘ └─────────────────┘
   ```
   - Each card: 16px padding, border-radius 12px, white background
10. Spacing: 24px
11. Card Score de Risco (Background: $color-primary-pink):
    - Padding: 20px
    - Border Radius: 16px
    - Inside:
      ```
      [🛡️ Icon]
      "Seu score de risco" (14px, white opacity 80%)
      "Baixo risco" (Inter Bold 24px, white)
      "Continue acompanhando e cuidado de você!"
      [ℹ️ Info icon] [>]
      ```
12. Spacing: 24px
13. Section "Próxima consulta":
    ```
    [📅 Icon] "Próxima consulta"
    "18 de maio de 2024 • 09:30" (Inter SemiBold 16px)
    "Dr. Lucas Almeida" (14px, secondary)
    [Ver detalhes >]
    ```
14. Spacing: 24px
15. Quote card:
    ```
    "❤️ Cada pequeno cuidado hoje,
    é um grande passo para o amanhã. ❤️"
    ```
    - Center aligned, italic, secondary color
16. Spacing: 24px (bottom padding before tab bar)
17. **Tab Bar** (Bottom Navigation):
    - 56px height
    - Background: white with shadow, corner radius full
    - 12px from bottom, 16px from sides
    - Items:
      ```
      🏠 Home (active: filled, pink, background capsule)
      📊 Acompanhar
      ➕ Registrar (larger, central)
      💬 Mensagens
      👤 Perfil
      ```

---

### Tela 4: SINAIS VITAIS

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Registrar Sinais Vitais" (Inter SemiBold 24px)
   - Subtitle "Preencha os dados abaixo" (14px, secondary)
3. Spacing: 24px
4. Form Fields (each 48px height, 12px spacing):
   ```
   [Input] "PA Sistólica (mmHg)" [Input] "PA Diastólica"
   [Input] "Frequência Cardíaca (bpm)"
   [Input] "Temperatura (°C)"
   [Input] "Peso (kg)"
   [Input] "Saturação de Oxigênio (%)"
   [Input] "Glicemia (mg/dL)"
   [Input] "Horas de Sono"
   ```
5. Spacing: 16px
6. Text area "Observações (opcional)"
   - Min-height: 100px
   - Border: 1px $color-border
7. Spacing: 12px
8. Text "Último registro: 15 de maio às 14:30"
   - Font: Inter Regular 12px
   - Color: $color-text-light
9. Spacing: 24px
10. Button "Salvar" (Primary pink, full width)
11. Spacing: 8px
12. Button "Cancelar" (Outline, full width)
13. Spacing: 24px (bottom)
14. Tab Bar

---

### Tela 5: SINTOMAS

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Registrar Sintomas" (Inter SemiBold 24px)
   - Subtitle "Selecione os sintomas que você sente" (14px)
3. Spacing: 24px
4. Symptom List (scrollable):
   - Each symptom: Card (white, 16px padding, 12px border)
     ```
     ☐ Dor de cabeça
     ☐ Enjoo
     ☐ Vômito
     ☐ Dor abdominal
     ☐ Sangramento
     ☐ Inchaço (edema)
     ☐ Visão turva
     ☐ Dor no peito
     ☐ Falta de ar
     ☐ Redução movimentos fetais
     ☐ Ardência ao urinar
     ☐ Febre
     ☐ Tontura
     ☐ Dor lombar
     ☐ Contrações
     ☐ Outro
     ```
5. Spacing: 24px
6. Section "Intensidade":
   ```
   ○ Leve
   ○ Moderado
   ○ Grave
   ```
   - Radio buttons, default "Leve"
7. Spacing: 16px
8. Text area "Descrição adicional (opcional)"
9. Spacing: 24px
10. Button "Salvar" (full width, primary)
11. Spacing: 8px
12. Button "Cancelar" (outline)
13. Spacing: 24px
14. Tab Bar

---

### Tela 6: ACOMPANHAMENTO

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Acompanhamento" (Inter SemiBold 24px)
3. Spacing: 16px
4. Tab Navigation:
   - "Gráficos" (active: pink underline)
   - "Histórico"
5. Spacing: 16px
6. **TAB CONTENT - Gráficos**:
   - Chart Title "Pressão Arterial (últimas 4 semanas)" (12px)
   - Line chart (área cinza clara, linha pink)
   - Y-axis: 80-160 mmHg
   - X-axis: Datas
   - Height: 200px
   - Spacing: 24px
   
   - Chart Title "Peso (últimas 4 semanas)"
   - Similar line chart
   - Height: 200px
   - Spacing: 24px
   
   - Chart Title "Frequência Cardíaca (últimas 4 semanas)"
   - Similar line chart
   - Height: 200px
   - Spacing: 24px
   
   - Chart Title "Score de Risco (últimas 4 semanas)"
   - Line chart com área colorida (vermelho/amarelo/verde)
   - Height: 200px

7. **TAB CONTENT - Histórico**:
   - List items:
     ```
     [date] [time] | 💓 Sinais Vitais
     PA: 120/80, FC: 75, Temp: 36.8°C
     
     [date] [time] | ⚠️ Sintomas
     Dor de cabeça (Moderado)
     
     ... more items
     ```
   - Each with expand/delete action

8. Spacing: 24px
9. Filter section:
   - Dropdown "Período" (Últimos 7 dias, 30 dias, 3 meses, Custom)
10. Spacing: 24px
11. Tab Bar

---

### Tela 7: PERFIL

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Meu Perfil" (Inter SemiBold 24px)
3. Spacing: 24px
4. Avatar Section (center):
   - Avatar circle (80px diameter)
   - Name "Ana Silva" (Inter SemiBold 20px)
   - Status "Paciente" (14px, secondary)
5. Spacing: 32px
6. Section "Informações Pessoais":
   - Card (white, 16px padding):
     ```
     📧 Email
     ana@email.com [copy icon]
     
     📱 Telefone
     +55 11 98765-4321 [copy icon]
     
     🎂 Data de Nascimento
     10 de março de 1990
     
     🆔 CPF
     123.456.789-** [copy icon]
     ```
7. Spacing: 24px
8. Section "Histórico Médico":
   - Card (white, 16px padding):
     ```
     Histórico Pessoal:
     Hipertensão controlada desde 2018
     
     Histórico Familiar:
     Mãe com diabetes tipo 2
     Avó materna com hipertensão
     ```
9. Spacing: 24px
10. Section "Dados Gestacionais":
    - Card (white, 16px padding):
      ```
      📅 Semana Gestacional: 24 semanas
      
      📆 Data Prevista do Parto: 15 de outubro de 2024
      
      🩸 Tipo Sanguíneo: O+
      
      📏 Altura: 165 cm
      
      ⚖️ Peso Pré-gestacional: 65 kg
      
      👨‍⚕️ Médico Responsável: Dr. Lucas Almeida
      ```
11. Spacing: 32px
12. Button "Editar Perfil" (full width, primary pink)
13. Spacing: 8px
14. Button "Desconectar" (full width, outline red border)
15. Spacing: 24px
16. Tab Bar

---

### Tela 8: MENSAGENS

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Mensagens" (Inter SemiBold 24px)
3. Spacing: 16px
4. Search Bar:
   - Input with magnifying glass icon
   - Placeholder: "Procurar conversas"
5. Spacing: 16px
6. **Conversation List**:
   - Each item:
     ```
     [Avatar 40px]  | Dr. Lucas Almeida
                    | "Tudo bem? Recebemos seu último registro..."
                    | 14:30 [unread badge if any]
     ```
   - Swipe actions: Mute, Delete
7. **Empty State** (if no conversations):
   ```
   [Empty icon]
   "Nenhuma conversa iniciada"
   
   [Button] "Contatar Médico"
   ```
8. Spacing: 24px
9. Tab Bar

---

### Tela 8b: CHAT (dentro de MENSAGENS)

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Back button (<)
   - Avatar (32px) + "Dr. Lucas Almeida"
   - Info icon (ⓘ)
3. Spacing: 16px
4. **Messages List** (scrollable, main area):
   - User message (right-aligned):
     ```
     ┌──────────────────────────┐
     │ Bom dia, doutor!         │ (bubble pink)
     │ Como posso ajudar?       │
     └──────────────────────────┘
     14:20
     ```
   - Doctor message (left-aligned):
     ```
     14:25
     ┌──────────────────────────┐
     │ Oi Ana! Tudo bem?        │ (bubble white, border)
     │ Recebi seus últimos      │
     │ registros...             │
     └──────────────────────────┘
     ```
   - System message (center):
     ```
     ——— 15 de maio ———
     ```

5. Spacing: 16px
6. Typing indicator (if doctor typing):
   ```
   "Dr. Lucas está digitando..."
   ```

7. **Bottom Input Area** (sticky):
   - Flex row:
     - Text input: "Digitar mensagem..."
     - Send button: Paper plane icon (primary pink)
   - Keyboard support

8. Tab Bar (may be hidden during chat)

---

### Tela 9: EDUCAÇÃO

**Dimensões**: 390x844px
**Background**: $color-background

**Componentes** (top to bottom):
1. Status Bar (62px)
2. Header:
   - Title "Conteúdos Educativos" (Inter SemiBold 24px)
3. Spacing: 16px
4. Search Bar:
   - Input with magnifying glass
   - Placeholder: "Procurar artigos..."
5. Spacing: 16px
6. Filter Tabs:
   - "Todos" (active: pink background)
   - "Semanas"
   - "Sintomas"
   - "Risco"
   - Horizontal scrolling tabs
7. Spacing: 16px
8. **Article Card List** (vertical scrolling):
   - Each card:
     ```
     ┌─────────────────────────┐
     │                         │
     │   [Thumbnail 16:9]      │  (background gradient)
     │                         │
     ├─────────────────────────┤
     │ 📖 Nutrição na Gestação │ (title, 16px bold)
     │ [Tag: Nutrição]         │ (pink background tag)
     │ "Saiba como manter uma  │
     │  alimentação saudável   │
     │  durante a gravidez..." │ (14px secondary, 2 lines ellipsis)
     │ ⏱️ 5 min de leitura      │ (12px, light)
     └─────────────────────────┘
     ```
   - Cards: white, 12px border-radius, shadow
9. Spacing: 24px (bottom)
10. Tab Bar

---

## Implementação Step by Step

1. **Criar Design System Variables** ✅ (já feito)
2. **Criar componentes reutilizáveis**:
   - Button (variants: primary, secondary, sizes: small, medium, large)
   - Input (text, password, number, date)
   - Card (base component)
   - Avatar (sizes: small, medium, large)
   - Badge (color variants)
   - Tab Navigation
   - Tab Bar (bottom navigation)

3. **Criar Frames de Telas**:
   - Frame 1: Login (390x844)
   - Frame 2: Cadastro (390x844)
   - Frame 3: Home (390x1200) - tela longa com scroll
   - Frame 4: Sinais Vitais (390x1000)
   - Frame 5: Sintomas (390x1200)
   - Frame 6: Acompanhamento - Gráficos (390x1400)
   - Frame 6b: Acompanhamento - Histórico (390x1200)
   - Frame 7: Perfil (390x1400)
   - Frame 8: Mensagens (390x844)
   - Frame 8b: Chat (390x844)
   - Frame 9: Educação (390x1200)

4. **Adicionar interatividade** (prototyping):
   - Login → Home
   - Home buttons → suas respectivas telas
   - Tab bar navigation
   - Chat expand/collapse
   - Tab switching

5. **QA & Polish**:
   - Verificar alinhamento
   - Verificar espaçamento
   - Verificar cores
   - Verificar tipografia
   - Testar fluxo completo

---

## Notas Importantes

- **Responsive**: Todas as telas para 390px de width
- **Content scrolling**: Telas longas devem ter scroll interno
- **Safe area**: Respeitar espaço do notch (se necessário)
- **Touch targets**: Mínimo 44x44px
- **Contrast**: Ratio mínimo 4.5:1 para acessibilidade
