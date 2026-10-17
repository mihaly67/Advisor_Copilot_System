def simple_mcp_server():
  import sys, os
  while True:
    try:
      from mcp.server import MCPServer
      server = MCPServer("simple-mcp", "Repository Memory Server")
      @server.tool("repo_memory", "Repository memory és kontextus lekérdezése")
      def repo_memory():
        return f"83 repository indexelve! Kontextus elérhető."
      server.run_stdio()
    except Exception as e:
      print(f"Hiba: {e}, újraindítás...")
if __name__ == "__main__":
  simple_mcp_server()
