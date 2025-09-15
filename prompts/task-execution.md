# Execução de Tarefa

**Pergunta Original**: Lembre-se que o usuário perguntou sobre um contexto específico de cluster/namespace.

**Tarefa**: $task_description

**Ações**: $actions

**Esperado**: $expected_outcome

**Verificar**: $verification_steps

## Diretrizes de Execução

### Estratégia de Execução de Ferramentas
- Execute ferramentas MCP na ordem planejada
- Se uma ferramenta falhar, tente abordagens alternativas antes de desistir
- Documente quaisquer erros mas continue com as ações restantes
- Foque em coletar os dados mais críticos primeiro

### Requisitos de Qualidade de Dados
- Use apenas dados reais do cluster das ferramentas MCP
- Filtre informações sensíveis (secrets, chaves, etc.)
- Verifique se as saídas das ferramentas são realistas (não dados de placeholder)
- Cruze achados entre múltiplas ferramentas quando possível

### Diretrizes de Resposta
- Responda em português brasileiro
- Mantenha-se sob o limite de 2000 caracteres do Discord
- Estruture achados claramente: problema → evidência → próximos passos
- Inclua nomes específicos de pods, deployments e mensagens de erro
- Se ferramentas falharem completamente, explique quais dados não puderam ser recuperados

### Tratamento de Erros
- Se ferramentas MCP falharem, mencione a limitação claramente
- Sugira comandos kubectl manuais como fallback quando apropriado
- Não fabrique dados quando ferramentas não estão disponíveis
- Foque no que PODE ser determinado das informações disponíveis

### Prioridade do Formato de Saída
1. **Achados imediatos** (erros, falhas, status)
2. **Análise de causa raiz** (por que o problema ocorreu)
3. **Próximos passos acionáveis** (o que fazer sobre isso)
4. **Contexto adicional** (se o espaço permitir)
