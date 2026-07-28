# BemGestar (Backend API)

API RESTful desenvolvida em **Python** e **Django REST Framework (DRF)** para a plataforma de telemonitoramento e acompanhamento gestacional **BemGestar**. A API atua como o servidor central, processando dados clínicos, gerando alertas de riscos e gerenciando a comunicação entre pacientes, médicos e a administração da plataforma.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: Python (>= 3.10)
- **Framework Web**: [Django](https://www.djangoproject.com/) (>= 5.0, < 7.0)
- **Framework de API**: [Django REST Framework (DRF)](https://www.django-rest-framework.org/) (>= 3.14)
- **Banco de Dados**: [PostgreSQL](https://www.postgresql.org/) (via Docker) / SQLite (para desenvolvimento rápido se desejado)
- **Autenticação**: JWT (JSON Web Tokens) via [django-rest-framework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/)
- **Documentação de API**: OpenAPI 3.0 & Swagger via [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- **Upload de Imagens/Arquivos**: [Pillow](https://python-pillow.org/) (Processamento de Imagens)
- **Variáveis de Ambiente**: `python-decouple`
- **Filtros e Buscas**: `django-filter`
- **Gerenciador de Contêineres**: Docker & Docker Compose

---

## 📂 Estrutura de Módulos (Apps) Implementados

A API é modularizada seguindo as melhores práticas do Django, separada nos seguintes aplicativos dentro de `apps/`:

1. **`accounts` (Contas e Autenticação)**:
   - Gerenciamento de usuários customizados (`User`), distinguindo entre **Paciente (gestante)**, **Médico** e **Administrador**.
   - Fluxo completo de login, cadastro e autenticação JWT.
   - Perfis de usuário detalhados:
     - `PatientProfile`: Idade gestacional, tipo sanguíneo, altura, peso pré-gestacional, data da última menstruação (DUM), data provável do parto (DPP) e médico responsável associado.
     - `DoctorProfile`: CRM, UF de atuação, especialidade (obstetrícia/ginecologia), instituição médica e status de validação de registro (`is_crm_validated`).
   - Endpoints administrativos (`/api/auth/admin/...`) para o administrador validar CRMs pendentes, listar médicos/pacientes e vincular pacientes a médicos.

2. **`monitoring` (Acompanhamento e Sinais Vitais)**:
   - **Sinais Vitais (`VitalSign`)**: Registro de pressão arterial (sistólica/diastólica), frequência cardíaca, temperatura corporal, peso, saturação de oxigênio e glicemia.
   - **Sintomas (`Symptom`)**: Registro de sintomas típicos (dor de cabeça, náuseas, vômitos, dor abdominal, sangramentos, redução de movimentos fetais, etc.) com classificação de gravidade (leve, moderado, grave).
   - **Score de Risco (`RiskScore`)**: Algoritmo para cálculo automático do nível de risco gestacional (baixo, médio, alto, crítico) combinando fatores de sinais vitais alterados e sintomas relatados.
   - **Alertas**: Disparo automático de alertas clínicos a partir do cruzamento de valores fora dos limites saudáveis.

3. **`consultations` (Agenda e Prescrições)**:
   - Agendamento, edição, cancelamento e exclusão de consultas pré-natal pelo médico responsável.
   - Solicitação, edição, mudança de status (pendente/realizado/cancelado) e exclusão de exames clínicos.
   - Emissão, edição e exclusão de receitas digitais.

4. **`messaging` (Comunicação Médica/Paciente)**:
   - Canal de bate-papo (chat) assíncrono seguro entre a gestante e o seu obstetra/médico responsável para acompanhamento contínuo e esclarecimento de dúvidas.

5. **`education` (Biblioteca Educativa)**:
   - Biblioteca de artigos informativos categorizados (Ex: *Nutrição na Gestação*, *Exercícios*, *Saúde Mental*, *Pré-natal*, *Preparação para o Parto*, *Amamentação*).
   - Filtragem e recomendação personalizada de artigos com base na **semana gestacional** atual da paciente.
   - Criação, edição e exclusão de conteúdos por médicos e administradores.

---

## 🚀 Como Executar o Projeto

Siga os passos abaixo de acordo com seu sistema operacional para rodar a API localmente.

### 📋 Pré-requisitos
- **Python 3.10 ou superior** instalado em sua máquina.
- **Docker** e **Docker Compose** instalados (para o banco de dados PostgreSQL).
- Git.

---

### 🐳 Passo 1: Subir o Banco de Dados (PostgreSQL)

O projeto inclui um arquivo `docker-compose.yml` pré-configurado para inicializar a instância de banco de dados PostgreSQL. Por padrão, o `docker-compose.yml` deste projeto mapeia o Postgres do contêiner (porta interna `5432`) para a **porta `5433` do host** (`"5433:5432"`), e não para a `5432` padrão.

No terminal da pasta raiz do projeto (`bem-gestar`), execute:
```bash
docker compose up -d
```
> **Nota**: Caso utilize versões mais antigas do docker, utilize `docker-compose up -d`.

> ⚠️ **Por que a porta 5433 e não a 5432?** Em ambientes com um PostgreSQL nativo já instalado no host (comum em instalações Windows, inclusive quando acessadas via WSL2 com `networkingMode=mirrored` no `.wslconfig`), a porta `5432` pode já estar ocupada pelo serviço nativo, causando erros de conexão (`UnicodeDecodeError`/timeout) mesmo com o contêiner rodando corretamente. Se a porta `5432` estiver livre na sua máquina, você pode alterar o mapeamento de volta para `"5432:5432"` no `docker-compose.yml` e usar `DB_PORT=5432` no `.env` — o importante é que a porta do `docker-compose.yml` e a `DB_PORT` do `.env` sejam sempre a mesma.

---

### 💻 Passo 2: Instalação e Configuração da API

Acesse a pasta do backend (`bem-gestar/bem-gestar`):

#### No Linux / macOS:
```bash
# 1. Crie o ambiente virtual
python3 -m venv .venv

# 2. Ative o ambiente virtual
source .venv/bin/activate

# 3. Atualize o pip e instale as dependências
pip install --upgrade pip
pip install -r requirements.txt
```

#### No Windows (PowerShell):
```powershell
# 1. Crie o ambiente virtual
python -m venv .venv

# 2. Ative o ambiente virtual
.venv\Scripts\Activate.ps1

# 3. Atualize o pip e instale as dependências
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### 📝 Passo 3: Configurar Variáveis de Ambiente

Na pasta `bem-gestar/bem-gestar/`, verifique ou crie o arquivo `.env` com base no arquivo de configurações padrão:

```env
SECRET_KEY=django-insecure-change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2,0.0.0.0

DB_ENGINE=django.db.backends.postgresql
DB_NAME=bemgestar_db
DB_USER=bemgestar_user
DB_PASSWORD=bemgestar_password
DB_HOST=127.0.0.1
DB_PORT=5433
```

> ⚠️ **`DB_PORT` deve ser igual à porta que você mapeou no `docker-compose.yml`** (veja o Passo 1). Neste projeto o padrão é `5433`. Se você alterou o `docker-compose.yml` para usar a porta `5432`, ajuste `DB_PORT=5432` aqui também.

> ⚠️ **`SECRET_KEY`**: o valor `django-insecure-change-me` é só um placeholder de exemplo — nunca use uma chave fraca/previsível, mesmo em desenvolvimento (o Django emite um aviso `InsecureKeyLengthWarning` para chaves curtas). Gere uma chave forte com:
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```
> Trocar o `SECRET_KEY` invalida todos os tokens JWT emitidos anteriormente — usuários logados precisarão entrar novamente.

*Observação: A rota de host `10.0.2.2` é necessária para permitir que o emulador do Android no Windows/Linux consiga fazer requisições HTTP para a API local (localhost do computador). O `0.0.0.0` é necessário para aceitar requisições vindas de outros dispositivos na rede (celular físico via Expo Go) quando o servidor é iniciado com `python manage.py runserver 0.0.0.0:8000` (Passo 5).*

---

### 🌐 Conectando o Frontend (Expo/React Native) a este Backend

O app mobile (`front-bem-gestar`) precisa saber o IP e a porta onde esta API está rodando, configurados na variável `EXPO_PUBLIC_API_BASE_URL` do `.env` do frontend. **A porta é sempre `8000`** (a porta do `runserver`, não a do Postgres). O IP depende de como o frontend vai se conectar:

| Cenário | IP a usar no `.env` do frontend |
|---|---|
| Emulador Android (no mesmo PC do backend) | `10.0.2.2` |
| Simulador iOS (macOS, no mesmo Mac do backend) | `localhost` |
| Celular físico via Expo Go (mesma rede Wi-Fi) | IP local (LAN) da máquina que roda o backend, ex: `192.168.15.4` |

Para descobrir o IP local (LAN) da máquina que roda o backend:
- **Windows (PowerShell/CMD)**: `ipconfig` → procure o "Endereço IPv4" do adaptador Wi-Fi/Ethernet ativo.
- **Linux/macOS**: `hostname -I` ou `ifconfig` / `ip addr`.
- **WSL2 com `networkingMode=mirrored`** (`.wslconfig`): o WSL2 compartilha a interface de rede do Windows, então o IP LAN do Windows (visto pelo `ipconfig` no Windows) é o mesmo a usar — não é necessário nenhum IP especial do WSL. Sem o modo mirrored (NAT padrão), o WSL2 tem seu próprio IP interno (via `ip addr` dentro do WSL) que muda a cada reinício e normalmente **não é alcançável** por um celular físico na rede — por isso o modo mirrored (ou o roteamento manual de portas) é recomendado para testar em dispositivo físico com o backend rodando dentro do WSL2.

Veja também o [README do frontend](../front-bem-gestar/README.md) para o passo a passo completo de configuração do `.env` do app.

---

### 🗄️ Passo 4: Executar as Migrações e Popular o Banco (Seed)

Com o banco de dados ativo e o ambiente virtual ligado, execute as migrações para criar as tabelas estruturais no PostgreSQL:

```bash
python manage.py migrate
```

Para facilitar o desenvolvimento, você pode rodar o script de **semeadura (seed)** que criará automaticamente contas de teste de médicos, gestantes, artigos educativos, categorias e conexões padrão:

```bash
python seed.py
```
*(Este script utiliza o setup integrado do Django e insere dados iniciais no banco PostgreSQL)*.

Os usuários criados por padrão para testes rápidos são:
- **Administrador**: `admin@bemgestar.com` / Senha: `admin123@`
- **Médico**: `medico@bemgestar.com` / Senha: `medico123@` (Dra. Ana Lima)
- **Paciente**: `paciente@bemgestar.com` / Senha: `paciente123@` (Maria Silva - gestante de 24 semanas associada à Dra. Ana Lima)

---

### 🏃‍♂️ Passo 5: Inicializar o Servidor de Desenvolvimento

Execute o servidor local especificando o bind de IP `0.0.0.0` para que dispositivos na mesma rede Wi-Fi consigam se conectar ao servidor:

```bash
python manage.py runserver 0.0.0.0:8000
```

- A API estará disponível no endereço: `http://localhost:8000/`
- O Painel Administrativo do Django estará em: `http://localhost:8000/admin/`

---

## 📖 Documentação Interativa da API (Swagger / ReDoc)

O projeto conta com o gerador automático de esquemas OpenAPI. Com o servidor rodando, você pode acessar a documentação detalhada de rotas, payloads, cabeçalhos de autenticação e testar endpoints diretamente do navegador:

- **Swagger UI**: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) (Interativo, ideal para testes de requisição)
- **ReDoc**: [http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/) (Organizado em colunas, ideal para leitura de especificações)
- **JSON Schema**: [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)
