# openai-langchain-example

A small FastAPI service that reads my Kubernetes study notes and asks GPT-4o, through LangChain, what I should study next.

This is a learning project. The goal was less the app itself and more taking an LLM-backed Python API all the way from local code to a Docker image to a Kubernetes cluster (Minikube) behind an Ingress. The notes the app reads, `meus_estudos_k8s.md`, are the notes I wrote while doing that deployment.

## How it works

```mermaid
flowchart LR
    A[POST /gerar-plano-de-estudos] --> B[Read meus_estudos_k8s.md]
    B --> C[MarkdownHeaderTextSplitter<br/>split by # and ##]
    C --> D[GPT-4o<br/>summarize chain]
    D --> E[GPT-4o<br/>tutor prompt]
    E --> F[JSON study plan]
```

On each request, `main.py`:

1. **Reads the notes.** Opens `meus_estudos_k8s.md` from the working directory.
2. **Splits them.** `MarkdownHeaderTextSplitter` breaks the file into documents by `#` and `##` headers.
3. **Summarizes.** LangChain's `load_summarize_chain` (`chain_type="stuff"`) sends all sections to the model and returns one summary of what I already know.
4. **Plans.** An LCEL chain (`ChatPromptTemplate | ChatOpenAI | StrOutputParser`) asks the model, acting as a senior Kubernetes tutor, for the next 3 to 5 topics to study, with a short reason for each.

The model is `gpt-4o` with `temperature=0.3`. It is created once at startup and reused. Prompts are in Portuguese, so the answer comes back in Portuguese.

There is no retrieval step, vector store or embeddings. The whole notes file goes to the model every time.

## Stack

| | |
| --- | --- |
| API | FastAPI · Gunicorn with Uvicorn workers |
| AI | LangChain · langchain-openai · OpenAI GPT-4o |
| Infra | Docker · Kubernetes (Deployment, Service, Ingress) · Minikube |

## API

`POST /gerar-plano-de-estudos`

- No request body. The input is always the notes file shipped with the app.
- Returns `{"plano_de_estudos": "<numbered list of topics>"}`
- Returns `404` if the notes file is missing and `500` with `{"error": "..."}` for any other failure (for example a missing or invalid API key).

```bash
curl -X POST http://localhost:8000/gerar-plano-de-estudos
```

FastAPI also serves its interactive docs at `/docs`.

## Run it locally

Requirements: Python 3 and an OpenAI API key.

```bash
git clone https://github.com/gustavokurtz/openai-langchain-example.git
cd openai-langchain-example
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```bash
OPENAI_API_KEY=your-openai-key
```

Start the server from the repository root, since the app opens `meus_estudos_k8s.md` by relative path:

```bash
uvicorn main:app --reload --port 8000
```

The dependencies in `requirements.txt` are not pinned. `main.py` imports `langchain.text_splitter` and `langchain.chains.summarize`, which newer LangChain releases have moved, so you may need an older `langchain` version for the imports to resolve.

## Run with Docker

The `Dockerfile` uses `python:3.9-slim`, installs the requirements, copies the project into `/app` and starts Gunicorn with 4 Uvicorn workers on port 8000:

```bash
docker build -t api-python .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-openai-key api-python
```

There is no `.dockerignore`, so `COPY . .` will copy a local `.env` into the image if one exists. Pass the key at runtime as above instead, especially before pushing the image to a registry.

## Deploy to Kubernetes

The manifests in `.kubernetes/` were written for a local Minikube cluster with an Ingress controller enabled.

| File | Resource | What it does |
| --- | --- | --- |
| `deployment.yml` | Deployment `app-rag-estudos` | Runs 3 replicas of the image `kurtzz171/api-python:latest`, exposing container port `8000`. |
| `service.yml` | Service `app-rag-estudos-service` | `ClusterIP` service that selects `app: app-rag-estudos` and maps port `80` to target port `8000`. |
| `ingress.yml` | Ingress `app-rag-estudos-ingress` | Routes all paths (`/`, `Prefix`) on host `app2.local` to the service on port `80`. |

```bash
kubectl apply -f .kubernetes/
kubectl get pods
kubectl get ingress
```

To reach `app2.local`, map it to the Minikube IP (`minikube ip`) in your hosts file, then:

```bash
curl -X POST http://app2.local/gerar-plano-de-estudos
```

The Deployment does not set `OPENAI_API_KEY`. Without a Secret or env entry in the pod spec, the endpoint will fail with a 500 unless the key was baked into the image.

## What I learned

From my notes in `meus_estudos_k8s.md`:

- An app needs three pieces to be reachable: a **Deployment** that keeps the desired number of Pod replicas running, a **Service** that gives those Pods a stable internal address, and an **Ingress** that routes external HTTP traffic by host and path to the right Service.
- A `ClusterIP` Service is internal only. Its `port` maps to the container's `targetPort`, which must match the `containerPort` the app listens on.
- `kubectl apply -f` creates or updates any resource from a file. Deleting a Pod managed by a Deployment just gets it recreated; to stop the app, delete the Deployment.
- One Ingress can serve several apps on the same cluster with multiple `host` rules (for example `app1.local` and `app2.local`). Locally, those hosts have to be mapped to `minikube ip` in the system hosts file, and a host that is not configured may fall through to a default backend.
- A `NodePort` Service exposes an app on the node IP without a domain, but cannot route by host. For several domains on one IP, Ingress is the right tool.
- `kubectl` switches between clusters with **contexts** (cluster + user + namespace): `kubectl config get-contexts`, `current-context` and `use-context`. Several kubeconfig files can be merged by listing them in the `KUBECONFIG` environment variable.
