from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from db import list_procedures

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_sp_list():
    procs = list_procedures()
    return [{"name": p["name"], "params": p.get("params", [])} for p in procs]

@app.post("/")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Invalid JSON"}}

    method = body.get("method")
    request_id = body.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "list": True,
                        "call": True
                    }
                },
                "serverInfo": {
                    "name": "SP Metadata MCP Server",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "get_sp_list",
                        "description": "Returns stored procedure list with parameters",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")

        if tool_name == "get_sp_list":
            result = get_sp_list()
            import json
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2)
                        }
                    ]
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        }



    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method {method} not found"}
    }
