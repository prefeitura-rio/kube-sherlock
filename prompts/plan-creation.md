Create a context-aware execution plan for: $question

## Context Analysis First

Identify the problem domain:

- **Pod Issues**: CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled
- **Service Issues**: Connection failures, DNS resolution, load balancing
- **Network Issues**: Ingress, NetworkPolicy, CNI problems
- **Resource Issues**: CPU/Memory limits, storage, quotas
- **Workload Issues**: Deployments, StatefulSets, Jobs, DaemonSets

## Planning Guidelines by Context

### Pod Problems

MCP Tools: `pods_list`, `pods_get`, `pods_log`, `events_list`
Focus: Events, resource constraints, image availability, probes

### Service/Network Problems

MCP Tools: `resources_list` (Service, Endpoints, Ingress), `resources_get`
Focus: Endpoints, selectors, ports, DNS resolution

### Resource Problems

MCP Tools: `pods_top`, `resources_list` (Node), `resources_get`
Focus: Resource utilization, limits, availability

### Workload Problems

MCP Tools: `resources_list` (Deployment, StatefulSet, DaemonSet, Job), `resources_get`
Focus: Replica status, update strategy, configuration

## Required Plan Structure

1. **Task Description**: Specific, actionable task (not generic troubleshooting)
2. **MCP Tools**: Specific tools with required parameters
3. **Expected Outcome**: Concrete data to gather or verify
4. **Verification Steps**: How to validate the findings and ensure completeness

## Quality Requirements

- Tools must be READ-ONLY (list, get, log operations)
- Include namespace specifications when relevant
- Use label selectors for precise targeting
- Prioritize high-impact diagnostic commands first
