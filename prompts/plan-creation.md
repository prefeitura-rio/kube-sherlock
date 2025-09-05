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
Commands: `kubectl get pods`, `kubectl describe pod`, `kubectl logs`, `kubectl get events`
Focus: Events, resource constraints, image availability, probes

### Service/Network Problems  
Commands: `kubectl get svc,ep,ing`, `kubectl describe`, network connectivity tests
Focus: Endpoints, selectors, ports, DNS resolution

### Resource Problems
Commands: `kubectl top nodes/pods`, `kubectl describe nodes`, resource quotas
Focus: Resource utilization, limits, availability

### Workload Problems
Commands: `kubectl get deploy,sts,ds,jobs`, `kubectl describe`, rollout status
Focus: Replica status, update strategy, configuration

## Required Plan Structure
1. **Task Description**: Specific, actionable task (not generic troubleshooting)
2. **Kubectl Commands**: Exact commands with proper flags and selectors
3. **Expected Outcome**: Concrete data to gather or verify
4. **Verification Steps**: How to validate the findings and ensure completeness

## Quality Requirements
- Commands must be READ-ONLY (get, describe, logs, top, explain)
- Include namespace specifications when relevant
- Use label selectors for precise targeting
- Prioritize high-impact diagnostic commands first

