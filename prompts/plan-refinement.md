Refine o plano baseado no feedback:

**Contexto:**

- Pergunta: $question
- Plano anterior: $previous_plan
- Resultado anterior: $previous_result
- Feedback: $feedback

## Padrões de Refinamento

**Dados incompletos** → Adicione ferramentas MCP específicas:

- `get-k8s-resource` para recursos específicos
- `list-k8s-events` para atividade recente
- `get-k8s-pod-logs` para pods problemáticos

**Escopo errado** → Foque melhor:

- Use namespaces específicos vs cluster-wide
- Aplique seletores de label precisos
- Direcione tipos de workload corretos

**Falta contexto** → Adicione relacionados:

- Verifique recursos relacionados (service → endpoints → pods)
- Inclua dependências (ingress → service → pods)
- Adicione verificação de recursos

## Saída Refinada

Crie TaskPlan melhorado com:

1. **Tarefa mais específica** que a anterior
2. **Ferramentas MCP adicionais** para cobrir lacunas
3. **Resultado esperado claro**
4. **Verificação robusta** dos achados

Resolva as preocupações específicas do supervisor.
