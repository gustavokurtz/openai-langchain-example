from fastapi import FastAPI
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
# Importação correta para versões recentes do LangChain
from langchain_core.messages import HumanMessage 
from pydantic import BaseModel
from fastapi.responses import JSONResponse

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Instancia a aplicação FastAPI
app = FastAPI(
    title="API de Chat com LangChain",
    description="Uma API simples para interagir com modelos de linguagem da OpenAI.",
    version="1.0.0"
)

# Define o modelo de dados para a requisição
class ChatRequest(BaseModel):
    message: str

# Instancia o modelo de chat da OpenAI
# Certifique-se de que a variável OPENAI_API_KEY está no seu arquivo .env
chat_model = ChatOpenAI(
    model="gpt-4", 
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7 # Parâmetro opcional para controlar a criatividade
)

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Recebe uma mensagem e retorna a resposta do modelo de linguagem.
    """
    try:
        # Cria a mensagem no formato esperado pelo modelo
        message = HumanMessage(content=request.message)
        
        # Usa o método assíncrono 'ainvoke' para não bloquear o servidor
        # A palavra-chave 'await' é crucial aqui
        response = await chat_model.ainvoke([message])
        
        # O método 'ainvoke' retorna um objeto de mensagem, 
        # facilitando o acesso ao conteúdo da resposta
        return {"response": response.content}

    except Exception as e:
        # Retorna uma resposta de erro genérica em caso de falha
        return JSONResponse(status_code=500, content={"error": str(e)})

# Para rodar este servidor, salve o arquivo como main.py e execute no terminal:
# uvicorn main:app --reload