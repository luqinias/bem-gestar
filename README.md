# BemGestar (Backend API)

API RESTful desenvolvida em **Python** e **Django REST Framework (DRF)** para a plataforma de telemonitoramento e acompanhamento gestacional **BemGestar**. A API atua como o servidor central, processando dados clínicos, gerando alertas de riscos, gerenciando a comunicação entre médicos e gestantes, e disponibilizando metadados/modelos 3D para a simulação em Realidade Aumentada (RA).

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
   - Gerenciamento de usuários customizados (`User`), distinguindo entre **Paciente (gestante)** e **Médico**.
   - Fluxo completo de login, cadastro e autenticação JWT.
   - Perfis de usuário detalhados:
     - `PatientProfile`: Idade gestacional, tipo sanguíneo, altura, peso pré-gestacional, data da última menstruação (DUM), data provável do parto (DPP) e médico responsável associado.
     - `DoctorProfile`: CRM, UF de atuação, especialidade (obstetrícia/ginecologia), instituição médica e status de validação de registro.

2. **`monitoring` (Acompanhamento e Sinais Vitais)**:
   - **Sinais Vitais (`VitalSign`)**: Registro de pressão arterial (sistólica/diastólica), frequência cardíaca, temperatura corporal, peso, saturação de oxigênio e glicemia.
   - **Sintomas (`Symptom`)**: Registro de sintomas típicos (dor de cabeça, náuseas, vômitos, dor abdominal, sangramentos, redução de movimentos fetais, etc.) com classificação de gravidade (leve, moderado, grave).
   - **Score de Risco (`RiskScore`)**: Algoritmo para cálculo automático do nível de risco gestacional (baixo, médio, alto, crítico) combinando fatores de sinais vitais alterados e sintomas relatados.
   - **Alertas**: Disparo automático de alertas clínicos a partir do cruzamento de valores fora dos limites saudáveis.

3. **`consultations` (Agenda e Prescrições)**:
   - Agendamento e gerenciamento de consultas pré-natal.
   - Solicitação de exames clínicos por parte dos médicos.
   - Emissão e armazenamento de receitas digitais.

4. **`messaging` (Comunicação Médica/Paciente)**:
   - Canal de bate-papo (chat) assíncrono seguro entre a gestante e o seu obstetra/médico responsável para acompanhamento contínuo e esclarecimento de dúvidas.

5. **`education` (Biblioteca Educativa)**:
   - Biblioteca de artigos informativos categorizados (Ex: *Nutrição na Gestação*, *Exercícios*, *Saúde Mental*, *Pré-natal*, *Preparação para o Parto*, *Amamentação*).
   - Filtragem e recomendação personalizada de artigos com base na **semana gestacional** atual da paciente.

6. **`ar` (Realidade Aumentada - Simulador do Feto)**:
   - Armazenamento e fornecimento de modelos 3D em formatos compatíveis (como `.glb` e `.usdz`) correspondentes a cada semana gestacional.
   - Metadados de crescimento (tamanho/peso estimados do bebê) e proporções físicas reais (bounding boxes) para o renderizador do aplicativo.
   - **Telemetria de RA (`ARTelemetry`)**: Captura e análise de métricas de desempenho no uso do simulador 3D (FPS médio, tempo na experiência gestacional, capturas de tela e registros de erros/crashes por modelo/aparelho).

---

## 🚀 Como Executar o Projeto

Siga os passos abaixo de acordo com seu sistema operacional para rodar a API localmente.

### 📋 Pré-requisitos
- **Python 3.10 ou superior** instalado em sua máquina.
- **Docker** e **Docker Compose** instalados (para o banco de dados PostgreSQL).
- Git.

---

### 🐳 Passo 1: Subir o Banco de Dados (PostgreSQL)

O projeto inclui um arquivo `docker-compose.yml` pré-configurado para inicializar a instância de banco de dados PostgreSQL na porta `5432`.

No terminal da pasta raiz do projeto (`bem-gestar`), execute:
```bash
docker compose up -d
```
> **Nota**: Caso utilize versões mais antigas do docker, utilize `docker-compose up -d`.

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
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2

DB_ENGINE=django.db.backends.postgresql
DB_NAME=bemgestar_db
DB_USER=bemgestar_user
DB_PASSWORD=bemgestar_password
DB_HOST=127.0.0.1
DB_PORT=5432
```
*Observação: A rota de host `10.0.2.2` é necessária para permitir que o emulador do Android no Windows/Linux consiga fazer requisições HTTP para a API local (localhost do computador).*

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
