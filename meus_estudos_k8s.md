# kubernetes d cria

Este guia detalha o processo para subir e expor uma ou mais aplicações no Kubernetes, utilizando Minikube para o ambiente de desenvolvimento local.

### 📦 **1. Componentes Essenciais**

Para uma aplicação funcionar e ser acessada, você precisa de três componentes principais:

- **Deployment**: Define o estado desejado da sua aplicação. Ele gerencia os **Pods** e garante que o número de réplicas do seu contêiner esteja sempre em execução.
    - **Exemplo**: Para uma aplicação Node.js, você define a imagem do contêiner e a `containerPort` (porta interna da aplicação, ex: `3001`).
- **Service**: Cria um ponto de acesso interno e estável para os seus Pods. Ele expõe o Deployment dentro do cluster.
    - **Tipo `ClusterIP`**: Expõe o serviço apenas internamente. Você mapeia a `port` do serviço (ex: `80`) para a `targetPort` do contêiner (ex: `3001`).
- **Ingress**: Gerencia o acesso externo ao cluster, permitindo criar regras de roteamento HTTP/HTTPS baseadas em domínios (`hosts`) e caminhos (`paths`). Ele direciona o tráfego para o `Service` correto.

### ⚙️ **2. Comandos `kubectl` Fundamentais**

Aqui estão os comandos básicos para gerenciar seus recursos no Kubernetes.

> 💡 Dica: O comando kubectl apply -f <arquivo.yaml> é usado para criar ou atualizar qualquer recurso a partir de um arquivo de configuração.
> 

**Para aplicar um arquivo de configuração:**

```
kubectl apply -f seu-arquivo.yaml

```

**Para listar recursos criados:**

```
# Listar Pods
kubectl get pods

# Listar Deployments
kubectl get deployments

# Listar Services
kubectl get services

# Listar Ingresses
kubectl get ingress

```

**Para deletar um recurso específico:**

```
kubectl delete deployment <nome-do-deployment>
kubectl delete service <nome-do-service>
kubectl delete ingress <nome-do-ingress>
kubectl delete pod <nome-do-pod>

```

> Atenção: Se um Pod for gerenciado por um Deployment, ele será recriado automaticamente após ser deletado. Para parar a aplicação, delete o Deployment.
> 

### 🌐 **3. Configurando Múltiplos Domínios (Ingress)**

Para acessar várias aplicações no mesmo cluster com domínios locais diferentes (ex: `app1.local` e `app2.local`), configure seu `Ingress` com múltiplas regras de `host`.

**Exemplo de `ingress.yaml` para dois hosts:**

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: meu-ingress-multihost
spec:
  rules:
  - host: "app1.local"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app1-service
            port:
              number: 80
  - host: "app2.local"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app2-service
            port:
              number: 80

```

### 💻 **4. Configuração do Ambiente Local (Windows)**

Para que os domínios locais funcionem, você precisa mapeá-los para o IP do seu cluster Minikube no arquivo `hosts` do seu sistema.

**1. Obtenha o IP do Minikube:**

```
minikube ip

```

**2. Edite o arquivo `hosts`:**

- **Caminho:** `C:\Windows\System32\drivers\etc\hosts`
- **Permissão:** Você precisa abrir seu editor de texto (ex: Bloco de Notas) **como Administrador** para salvar as alterações.

**3. Adicione as entradas no arquivo `hosts` (use o IP retornado pelo comando anterior):**

```
192.168.49.2 app1.local
192.168.49.2 app2.local

```

**4. Limpe o cache DNS (opcional, mas recomendado):**
Abra o `cmd` ou `PowerShell` e execute:

```
ipconfig /flushdns

```

> Reiniciar o navegador também pode ajudar a garantir que as novas regras de DNS sejam aplicadas.
> 

### 🤔 **Troubleshooting e Alternativas**

- **Estou vendo a aplicação errada?**
Se você tentar acessar um domínio que não está configurado no `Ingress`, o tráfego pode ser direcionado para um backend padrão (geralmente o primeiro da lista). Certifique-se de que cada `host` no `Ingress` está definido corretamente.
- **Expor via IP sem domínio:**
Se você não precisa de múltiplos domínios, pode usar um `Service` do tipo **`NodePort`**. Isso expõe a aplicação em uma porta específica no IP do nó (Minikube), mas não permite roteamento baseado em host. Para múltiplos domínios no mesmo IP, o `Ingress` é a solução ideal.

> Se precisar de ajuda para montar os arquivos YAML completos para esse cenário (Deployment, Service e Ingress), é só pedir!
> 

# 🧭 Gerenciando Perfis e Clusters no Kubernetes (`kubectl`)

Quando você trabalha com mais de um cluster Kubernetes (ou com diferentes usuários no mesmo cluster), precisa de uma forma de alternar entre eles. O `kubectl` gerencia isso através de **Contextos**.

Um **Contexto** é a combinação de três elementos:

1. **Cluster:** O endereço do servidor da API do Kubernetes (ex: cluster de dev, cluster de prod).
2. **User:** As credenciais que você usa para se autenticar (ex: seu usuário, uma conta de serviço).
3. **Namespace:** O namespace padrão a ser usado com este contexto.

### 📋 **Listar Todos os Perfis (Contextos) Disponíveis**

Para ver todos os contextos configurados no seu arquivo `kubeconfig`, use o comando:

```
kubectl config get-contexts

```

A saída mostrará uma lista de todos os seus perfis. Aquele que estiver ativo será marcado com um asterisco (`*`) na coluna `CURRENT`.

| CURRENT | NAME | CLUSTER | AUTHINFO | NAMESPACE |
| --- | --- | --- | --- | --- |
| * | minikube | minikube | minikube | default |
|  | docker-desktop | docker-desktop | docker-desktop |  |
|  | meu-cluster-prod | cluster-prod | admin-prod | producao |

### 👀 **Ver o Perfil Ativo no Momento**

Para verificar rapidamente qual contexto está sendo usado no seu terminal, sem listar todos os outros:

```
kubectl config current-context

```

**Saída:**

```
minikube

```

### 🔄 **Trocar de Perfil (Mudar de Cluster/Usuário)**

Este é o comando principal para alternar entre seus perfis. Para mudar para o contexto do cluster de produção do exemplo acima, você faria:

```
kubectl config use-context meu-cluster-prod

```

**Saída:**

```
Switched to context "meu-cluster-prod".

```

Agora, todos os seus comandos `kubectl` (como `get pods`, `get deployments`) serão executados no cluster `cluster-prod` usando o usuário `admin-prod` e terão como padrão o namespace `producao`.

### ➕ **Dica Pro: Fundindo Múltiplos Arquivos `kubeconfig`**

Se você recebe arquivos `config` separados para cada cluster, pode ser cansativo gerenciá-los. Você pode "fundi-los" temporariamente definindo a variável de ambiente `KUBECONFIG`.

O `kubectl` lê os arquivos na ordem em que aparecem, separados por dois pontos (`:` no Linux/macOS) ou ponto e vírgula (`;` no Windows).

**Exemplo (Linux/macOS):**

```
# Funde o arquivo padrão com o config do novo cluster e um config da VPS
export KUBECONFIG=~/.kube/config:/caminho/para/cluster-novo.yaml:/caminho/para/config-vps.yaml

# Agora, `kubectl config get-contexts` mostrará os contextos de todos os 3 arquivos!

```

Para tornar isso permanente, adicione a linha `export KUBECONFIG=...` ao seu arquivo de perfil do shell (como `.zshrc` ou `.bashrc`)