# Evaluation

Avalie se a resposta do worker está adequada.

## Critérios de Avaliação (5 pontos cada)

1. **Completude** - Responde à pergunta original completamente
2. **Precisão** - Dados reais do cluster via MCP tools, não inventados ou genéricos
3. **Diagnóstico** - Analisa causa raiz usando logs/eventos, não só sintomas
4. **Utilidade** - Próximos passos claros e acionáveis (comandos específicos, recursos a verificar)
5. **Comunicação** - Clara em português, concisa para Discord (≤2000 chars)

## Critérios Específicos para Kubernetes

**Para problemas de pods/deployments:**
- Verificou logs de containers aplicação? (não sidecars)
- Checou eventos recentes do namespace?
- Analisou status de réplicas e readiness?

**Para erros de aplicação (500, crashes):**
- Obteve logs específicos dos containers com erro?
- Identificou stack traces ou mensagens de erro?
- Sugeriu próximos passos baseados nos logs?

**Para investigações gerais:**
- Usou tools MCP corretos para o contexto?
- Filtrou informações sensíveis?
- Focou no problema específico mencionado?

## Aprovação

**APROVADO**: Score ≥ 20/25 E critérios essenciais atendidos
**REFINAR**: Score < 20/25 OU faltam essenciais

## Essenciais

- Pergunta respondida
- Dados reais utilizados
- Próximos passos fornecidos

## Formato

**Aprovado**: `APROVADO`
**Refinar**: `REFINAR: [instrução específica]`
