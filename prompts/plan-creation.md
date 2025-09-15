Crie um plano de execução para: $question

## Contexto por Tipo de Problema

**Problemas de Pod** (CrashLoopBackOff, ImagePullBackOff, Pending):

- Ferramentas: `list-k8s-resources`, `get-k8s-resource`, `get-k8s-pod-logs`, `list-k8s-events`
- Foco: Eventos, logs de erro, restrições de recursos

**Problemas de Serviço/Rede** (conectividade, DNS):

- Ferramentas: `list-k8s-resources` (Service, Endpoints), `get-k8s-resource`
- Foco: Endpoints, seletores, portas

**Problemas de Workload** (deployments, scaling):

- Ferramentas: `list-k8s-resources` (Deployment), `get-k8s-resource`
- Foco: Status de réplicas, estratégia de atualização

**Investigações de Erros** (500s, crashes):

- Prioridade: `get-k8s-pod-logs` PRIMEIRO, depois `list-k8s-events`
- Foco: Stack traces, erros recentes em logs de aplicação

## Estrutura Obrigatória do Plano

1. **Descrição da Tarefa**: Ação específica e acionável
2. **Ferramentas MCP**: Lista exata com preferência para ferramentas MCP
3. **Resultado Esperado**: Dados concretos para coletar
4. **Passos de Verificação**: Como validar completude dos achados

## Importantes:

- Para pods parciais (ex: "letta"): inclua `list-k8s-resources` para encontrar nome completo
- Prefira sempre ferramentas MCP; sugira kubectl apenas como último recurso
- Seja específico sobre namespace e contexto quando relevante
