from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import ChatPromptTemplate # Importação moderna
from langchain_core.output_parsers import StrOutputParser # Novo parser de saída

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO INICIAL (O que só precisa rodar uma vez) ---
app = FastAPI(
    title="API Tutor de Kubernetes",
    description="Analisa anotações de estudo e sugere os próximos passos.",
    version="2.0.0" # Versão atualizada!
)

# Instancia o LLM uma única vez para reutilizar a conexão
llm = ChatOpenAI(
    model="gpt-4o", 
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.3
)

# Molde do prompt final. Usamos ChatPromptTemplate que é mais flexível.
prompt_template_tutor = ChatPromptTemplate.from_template(
"""Você é um tutor de tecnologia sênior, especialista em Kubernetes. Sua tarefa é analisar o que um aluno já sabe e criar um plano de estudos claro e lógico para ele.

O resumo do conhecimento do aluno é o seguinte:
---
{resumo_do_conhecimento}
---

Com base neste resumo, sugira os próximos 3 a 5 tópicos que este aluno deve estudar em uma lista numerada, explicando brevemente por que cada um é o próximo passo lógico."""
)

# --- MUDANÇA PRINCIPAL: O NOVO ESTILO (LCEL) ---
# Em vez de LLMChain, agora "encanamos" (pipe) o prompt direto para o LLM.
# O StrOutputParser garante que a saída seja uma string simples.
cadeia_tutora = prompt_template_tutor | llm | StrOutputParser()
# -------------------------------------------------------------

@app.post("/gerar-plano-de-estudos")
async def gerar_plano_de_estudos():
    """
    Lê o arquivo de estudos, resume o conhecimento e gera um novo
    plano de estudos baseado no conteúdo atual do arquivo.
    """
    try:
        # --- LÓGICA DA REQUISIÇÃO (O que roda a cada chamada na API) ---

        # 1. Lê o arquivo Markdown
        nome_do_arquivo_markdown = "meus_estudos_k8s.md"
        with open(nome_do_arquivo_markdown, "r", encoding="utf-8") as f:
            conteudo_markdown = f.read()

        # 2. Divide o texto
        headers_to_split_on = [("#", "Tópico Principal"), ("##", "Subtópico")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        documentos_divididos = markdown_splitter.split_text(conteudo_markdown)
        
        if not documentos_divididos:
            raise HTTPException(status_code=400, detail="O arquivo de anotações está vazio.")

        # 3. Resume o conhecimento usando o método moderno '.ainvoke'
        cadeia_de_resumo = load_summarize_chain(llm, chain_type="stuff")
        # A entrada para .ainvoke é um dicionário
        resumo = await cadeia_de_resumo.ainvoke({"input_documents": documentos_divididos})
        resumo_do_conhecimento = resumo['output_text']

        # 4. Gera o plano de estudos com a nova cadeia e '.ainvoke'
        # A entrada também é um dicionário, com a chave que o prompt espera
        plano_de_estudos = await cadeia_tutora.ainvoke({"resumo_do_conhecimento": resumo_do_conhecimento})
        
        return {"plano_de_estudos": plano_de_estudos}

    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": f"Arquivo não encontrado: {nome_do_arquivo_markdown}"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})