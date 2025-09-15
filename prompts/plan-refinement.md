# Refinamento de Plano Baseado no Feedback de Avaliação

## Revisão de Contexto

- **Pergunta Original**: $question
- **Plano Anterior**: $previous_plan
- **Resultado Anterior**: $previous_result
- **Feedback do Supervisor**: $feedback

## Estratégia de Refinamento

### 1. Analisar a Lacuna

Identifique o que estava faltando ou inadequado:

- **Coleta de dados incompleta**: Ferramentas MCP faltando para diagnóstico completo
- **Foco errado**: Abordando sintomas em vez de causa raiz
- **Detalhe insuficiente**: Ferramentas muito amplas ou não específicas o suficiente
- **Verificação ausente**: Nenhuma validação de achados ou próximos passos

### 2. Padrões de Refinamento Comuns

#### Detalhe Insuficiente → Investigação Mais Profunda

- Adicione chamadas `get-k8s-resource` para recursos específicos
- Inclua `list-k8s-events` para atividades recentes
- Adicione `get-k8s-pod-logs` para pods específicos

#### Escopo Errado → Direcionamento Correto

- Use namespaces apropriados em vez de buscas em todo o cluster
- Aplique seletores de label para direcionamento preciso de recursos
- Foque em tipos específicos de workload (deployment vs pod vs service)

#### Contexto Ausente → Quadro Completo

- Adicione verificações de recursos relacionados (services → endpoints → pods)
- Inclua utilização de recursos (via `list-k8s-resources` e `get-k8s-resource`)
- Verifique dependências (ingress → service → pods → nodes)

#### Verificação Inadequada → Validação Abrangente

- Adicione comandos de verificação para confirmar achados
- Inclua passos de execução manual para cenários complexos
- Forneça abordagens alternativas se o método primário falhar

### 3. Execução do Refinamento

Baseado no feedback, crie um plano MELHORADO que:

#### Aborde Feedback Específico

- Corrija os problemas exatos mencionados no feedback do supervisor
- Adicione ferramentas MCP ausentes ou passos de coleta de dados
- Corrija parâmetros de ferramentas ou direcionamento

#### Melhore a Profundidade Diagnóstica

- Vá mais fundo que a tentativa anterior
- Inclua ferramentas MCP adicionais de coleta de contexto
- Adicione passos de verificação e validação

#### Garanta Completude

- Cubra todos os aspectos da pergunta original
- Inclua abordagens adequadas de tratamento de erros
- Forneça resultados esperados claros

## Saída Obrigatória

Crie um TaskPlan refinado com:

1. **Descrição de Tarefa Melhorada**: Mais específica e abrangente que a anterior
2. **Ferramentas MCP Direcionadas**: Abordando lacunas do feedback com parâmetros adequados
3. **Resultado Esperado Claro**: Quais dados/insights específicos esperamos coletar
4. **Passos de Verificação Robustos**: Como validar achados e garantir qualidade

Foque em resolver as preocupações do supervisor mantendo rigor diagnóstico.
