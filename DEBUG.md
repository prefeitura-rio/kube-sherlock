# Debugging Kube-Sherlock

This guide explains how to debug the Kube-Sherlock Discord bot using debugpy and Docker Compose.

## Prerequisites

- VS Code with Python extension
- Docker and Docker Compose
- Service account JSON file for GKE access

## Quick Start

1. **Start debug services:**
   ```bash
   docker-compose -f docker-compose.debug.yaml up --build
   ```

2. **Connect debugger in VS Code:**
   - Open VS Code
   - Go to Run and Debug (Ctrl+Shift+D)
   - Select "Python: Remote Attach"
   - Host: `localhost`, Port: `5678`
   - Click "Start Debugging"

3. **The application will start** after debugger connects

## VS Code Launch Configuration

Add this to your `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug Kube-Sherlock",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ],
            "justMyCode": false
        }
    ]
}
```

## Debug Features

### Live Code Reloading
- Changes to `src/`, `main.py`, and `system-prompt.txt` are synced automatically
- No need to rebuild container for code changes

### Breakpoints
- Set breakpoints in VS Code
- Debugger will pause execution
- Inspect variables, call stack, etc.

### Environment
- Same environment as production
- GKE authentication included
- Redis service available
- All environment variables from `.env`

## Debug Commands

```bash
# Start debug services
docker-compose -f docker-compose.debug.yaml up --build

# Start in background
docker-compose -f docker-compose.debug.yaml up -d --build

# View logs
docker-compose -f docker-compose.debug.yaml logs -f kube-sherlock-debug

# Stop services
docker-compose -f docker-compose.debug.yaml down

# Clean up volumes
docker-compose -f docker-compose.debug.yaml down -v
```

## Debugging Tips

1. **Container won't start without debugger:** The app waits for debugger connection
2. **Code changes:** Use the file sync feature for live updates
3. **Breakpoints:** Set them before connecting the debugger
4. **Performance:** Debug mode is slower due to debugging overhead
5. **Logs:** Check container logs if connection fails

## Troubleshooting

### Debugger won't connect
- Ensure port 5678 is not blocked
- Check if container is running: `docker-compose -f docker-compose.debug.yaml ps`
- Verify logs: `docker-compose -f docker-compose.debug.yaml logs kube-sherlock-debug`

### GKE authentication fails
- Verify `service-account.json` exists and has correct permissions
- Check environment variables in `.env`
- Ensure GKE cluster is accessible

### Code changes not reflected
- Verify file sync is working in container logs
- Restart debugger session if needed
- Check file paths in volume mounts