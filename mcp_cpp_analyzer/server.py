from fastapi import FastAPI, Request
import subprocess, os, json

app = FastAPI()

# ✅ cppcheck 실행 함수
def run_cppcheck_clean(path: str):
    if not os.path.exists(path):
        return f"❌ 경로를 찾을 수 없습니다: {path}"

    try:
        # cppcheck 실행 (진행 로그 제외, 결과만 추출)
        cmd = [
            "cppcheck",
            "--enable=all",
            "--quiet",
            "--template={file}:{line}:{severity}:{message}",
            path
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        output = proc.stdout.strip()
        if not output:
            return "✅ 코드 분석 결과: 오류나 경고가 없습니다."
        return output
    except Exception as e:
        return f"cppcheck 실행 실패: {e}"

# ✅ MCP 서버 엔드포인트
@app.post("/")
async def mcp_handler(request: Request):
    body = await request.json()
    method = body.get("method")
    request_id = body.get("id")

    # 1️⃣ 초기화 (initialize)
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"list": True, "call": True}
                },
                "serverInfo": {
                    "name": "cpp-analyzer",
                    "version": "1.0.0"
                }
            }
        }

    # 2️⃣ 도구 목록 (tools/list)
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "run_cppcheck",
                        "description": "Run cppcheck static analysis on a C++ project folder",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Absolute path to the source folder"
                                }
                            },
                            "required": ["path"]
                        }
                    }
                ]
            }
        }

    # 3️⃣ 도구 호출 (tools/call)
    elif method == "tools/call":
        params = body.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "run_cppcheck":
            path = args.get("path")
            result = run_cppcheck_clean(path)

            # Gemini가 인식 가능한 content/text 형식으로 반환
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {"type": "text", "text": f"📊 정적 분석 결과:\n{result}"}
                    ]
                }
            }

        # 등록되지 않은 도구
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unknown tool: {tool_name}"
            }
        }

    # 4️⃣ 알 수 없는 메서드
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Method {method} not found"
        }
    }

# ✅ 실행 진입점
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
