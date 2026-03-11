#!/bin/bash

# 1. Initialize session
curl -i -X POST "http://localhost:8005/mcp" \
  -H "Accept: application/json,text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {
        "roots": {
          "listChanged": true
        },
        "sampling": {}
      },
      "clientInfo": {
        "name": "test-client",
        "version": "1.0.0"
      }
    }
  }'

# 2. Send initialized notification (replace <SESSION_ID> with value from previous response header)
curl -i -X POST "http://localhost:8005/mcp" \
  -H "Accept: application/json,text/event-stream" \
  -H "mcp-session-id: $MCP_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notifications/initialized"
  }'

# 3. List tools (replace <SESSION_ID>)
curl -i -X POST "http://localhost:8005/mcp" \
  -H "Accept: application/json,text/event-stream" \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: $MCP_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# 4. Call tool (replace <SESSION_ID>)
curl -i -X POST "http://localhost:8005/mcp" \
  -H "Accept: application/json,text/event-stream" \
  -H "Content-Type: application/json" \
  -H "mcp-session-id: $MCP_SESSION_ID" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_user_by_id",
      "arguments": {
        "user_id": 999
      }
    }
  }'
