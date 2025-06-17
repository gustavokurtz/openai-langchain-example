# ===================================================================
# PASSO 1: Use uma imagem base oficial e leve do Python
# Usar 'python:3.9-slim' é muito melhor que 'ubuntu', pois já vem
# com Python configurado e é muito menor.
# ===================================================================
FROM python:3.9-slim

# ===================================================================
# PASSO 2: Crie e defina o diretório de trabalho dentro do contêiner
# ===================================================================
WORKDIR /app

# ===================================================================
# PASSO 3: Otimização de Cache do Docker
# Copie APENAS o arquivo de requisitos primeiro. O Docker só vai
# reinstalar as dependências se este arquivo mudar, o que torna
# os builds futuros muito mais rápidos.
# ===================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===================================================================
# PASSO 4: Copie o resto do código da sua aplicação
# ===================================================================
COPY . .

# ===================================================================
# PASSO 5: Comando para iniciar o servidor em modo de PRODUÇÃO
# Este é o coração da configuração de produção.
# ===================================================================
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]