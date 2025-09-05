# Plan Refinement Based on Evaluation Feedback

## Context Review

- **Original Question**: $question
- **Previous Plan**: $previous_plan
- **Previous Result**: $previous_result
- **Supervisor Feedback**: $feedback

## Refinement Strategy

### 1. Analyze the Gap

Identify what was missing or inadequate:

- **Incomplete data collection**: Missing MCP tools for full diagnosis
- **Wrong focus**: Addressing symptoms instead of root cause
- **Insufficient detail**: Tools too broad or not specific enough
- **Missing verification**: No validation of findings or next steps

### 2. Common Refinement Patterns

#### Insufficient Detail → Deeper Investigation

- Add `resources_get` calls for specific resources
- Include `events_list` for recent activities
- Add `pods_log` for specific pods

#### Wrong Scope → Correct Targeting

- Use proper namespaces instead of cluster-wide searches
- Apply label selectors for precise resource targeting
- Focus on specific workload types (deployment vs pod vs service)

#### Missing Context → Complete Picture

- Add related resource checks (services → endpoints → pods)
- Include resource utilization (`pods_top`)
- Check dependencies (ingress → service → pods → nodes)

#### Inadequate Verification → Comprehensive Validation

- Add verification commands to confirm findings
- Include manual execution steps for complex scenarios
- Provide alternative approaches if primary method fails

### 3. Refinement Execution

Based on the feedback, create an IMPROVED plan that:

#### Addresses Specific Feedback

- Fix the exact issues mentioned in supervisor feedback
- Add missing MCP tools or data collection steps
- Correct tool parameters or targeting

#### Enhances Diagnostic Depth

- Go deeper than previous attempt
- Include additional context-gathering MCP tools
- Add verification and validation steps

#### Ensures Completeness

- Cover all aspects of the original question
- Include proper error handling approaches
- Provide clear expected outcomes

## Required Output

Create a refined TaskPlan with:

1. **Enhanced Task Description**: More specific and comprehensive than previous
2. **Targeted MCP Tools**: Addressing feedback gaps with proper parameters
3. **Clear Expected Outcome**: What specific data/insights we expect to gather
4. **Robust Verification Steps**: How to validate findings and ensure quality

Focus on resolving the supervisor's concerns while maintaining diagnostic rigor.
