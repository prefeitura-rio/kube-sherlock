Crie um plano de execução consciente do contexto para: $question

## Análise de Contexto Primeiro

Identifique o domínio do problema:

- **Problemas de Pod**: CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled
- **Problemas de Serviço**: Falhas de conexão, resolução DNS, balanceamento de carga
- **Problemas de Rede**: Ingress, NetworkPolicy, problemas CNI
- **Problemas de Recursos**: Limites CPU/Memória, armazenamento, quotas
- **Problemas de Workload**: Deployments, StatefulSets, Jobs, DaemonSets

## Diretrizes de Planejamento por Contexto

### Problemas de Pod

Ferramentas MCP: `list-k8s-resources`, `get-k8s-resource`, `get-k8s-pod-logs`, `list-k8s-events`
Foco: Eventos, restrições de recursos, disponibilidade de imagem, probes

### Problemas de Serviço/Rede

Ferramentas MCP: `list-k8s-resources` (Service, Endpoints, Ingress), `get-k8s-resource`
Foco: Endpoints, seletores, portas, resolução DNS

### Problemas de Recursos

Ferramentas MCP: `list-k8s-resources` (Node), `get-k8s-resource`
Foco: Utilização de recursos, limites, disponibilidade

### Problemas de Workload

Ferramentas MCP: `list-k8s-resources` (Deployment, StatefulSet, DaemonSet, Job), `get-k8s-resource`
Foco: Status de réplicas, estratégia de atualização, configuração

### Investigações de Erros (erros 500, crashes, falhas)

Ferramentas MCP: `list-k8s-resources` (Pod), `get-k8s-pod-logs`, `list-k8s-events`
Foco: IMEDIATAMENTE verifique logs de containers de aplicação, erros recentes, stack traces
Prioridade: Obter logs primeiro, depois status do deployment, depois eventos

## Estrutura de Plano Obrigatória

1. **Descrição da Tarefa**: Tarefa específica e acionável (não troubleshooting genérico)
2. **Ferramentas MCP**: Ferramentas específicas com parâmetros obrigatórios
3. **Resultado Esperado**: Dados concretos para coletar ou verificar
4. **Passos de Verificação**: Como validar os achados e garantir completude

## Requisitos de Qualidade

- Ferramentas devem ser SOMENTE-LEITURA (operações list, get, log)
- Inclua especificações de namespace quando relevante
- Use seletores de label para direcionamento preciso
- Priorize comandos de diagnóstico de alto impacto primeiro
