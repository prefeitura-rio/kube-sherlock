# Task Execution Instructions

## Mission
**DESCRIPTION**: $task_description

## Kubectl Commands to Execute
$commands

## Expected Outcome
$expected_outcome

## Verification Steps
$verification_steps

---

## Execution Guidelines

### 1. Command Execution Order
- Execute commands in the specified order
- Wait for each command to complete before proceeding
- Validate output before moving to next command

### 2. Error Handling Protocol
If a command fails:
1. **Document the error** - Include exact error message
2. **Try alternative approaches** - Use different namespaces, broader scopes
3. **Continue with remaining commands** - Don't stop execution
4. **Report partial findings** - Share what data was successfully gathered

### 3. Data Collection Standards
- **Real data only** - Never fabricate or guess cluster information
- **Complete output** - Include relevant details, not just summaries
- **Filter sensitive data** - Exclude secrets, tokens, passwords
- **Highlight key findings** - Focus on data that addresses the user's question

### 4. Response Format Requirements
Structure your response as:

```
🔍 **Diagnóstico**: [Brief assessment of findings]
📊 **Dados encontrados**: [Key data from commands]
⚡ **Próximos passos**: [Specific actionable recommendations]
```

### 5. Quality Control
Before finalizing response, verify:
- ✅ Original question answered completely
- ✅ All commands attempted (document failures)
- ✅ Real cluster data included
- ✅ Next steps provided
- ✅ Portuguese brasileiro used consistently
- ✅ Discord character limit respected (~1800 chars safe)

### 6. Failure Recovery
If MCP tools fail completely:
- Acknowledge the limitation clearly
- Provide manual kubectl commands for user execution
- Explain expected output format
- Offer alternative diagnostic approaches

Execute with precision and provide actionable intelligence.

