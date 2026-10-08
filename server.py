import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add the current folder to sys.path to resolve imports cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.tac_generator import TACGenerator
from compiler.optimizer import Optimizer
from compiler.codegen import CodeGenerator

def run_compilation_pipeline(code):
    lexer = Lexer(code)
    tokens, lex_errors = lexer.tokenize()
    
    if lex_errors:
        return {
            "success": False,
            "phase": "Lexical Analysis",
            "errors": lex_errors,
            "tokens": [t.to_dict() for t in tokens],
            "symbols": [],
            "tac_raw": [],
            "tac_opt": [],
            "assembly": []
        }
        
    parser = Parser(tokens)
    ast, parse_errors = parser.parse()
    
    if parse_errors:
        return {
            "success": False,
            "phase": "Syntax Analysis",
            "errors": parse_errors,
            "tokens": [t.to_dict() for t in tokens],
            "symbols": [],
            "tac_raw": [],
            "tac_opt": [],
            "assembly": []
        }
        
    analyzer = SemanticAnalyzer()
    sem_errors, symbol_table = analyzer.analyze(ast)
    
    if sem_errors:
        return {
            "success": False,
            "phase": "Semantic Analysis",
            "errors": sem_errors,
            "tokens": [t.to_dict() for t in tokens],
            "ast": ast.to_dict(),
            "symbols": symbol_table.get_all_declared_symbols(),
            "tac_raw": [],
            "tac_opt": [],
            "assembly": []
        }
        
    # TAC Generation
    tac_gen = TACGenerator()
    tac_raw = tac_gen.generate(ast)
    
    # Optimization
    optimizer = Optimizer(tac_raw)
    tac_opt = optimizer.optimize()
    
    # Target Code Generation (Assembly)
    codegen = CodeGenerator(tac_opt)
    assembly = codegen.generate()
    
    return {
        "success": True,
        "tokens": [t.to_dict() for t in tokens],
        "ast": ast.to_dict(),
        "symbols": symbol_table.get_all_declared_symbols(),
        "tac_raw": [instr.to_dict() for instr in tac_raw],
        "tac_opt": [instr.to_dict() for instr in tac_opt],
        "assembly": assembly,
        "errors": []
    }

class CompilerRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve static files from the 'web' folder
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
            
        # Parse path to prevent directory traversal
        clean_path = path.lstrip("/")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, "web", clean_path)
        
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            self.send_error(404, "File Not Found")
            return
            
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            
            self.send_response(200)
            
            # Content Type mappings
            if file_path.endswith(".html"):
                self.send_header("Content-Type", "text/html")
            elif file_path.endswith(".css"):
                self.send_header("Content-Type", "text/css")
            elif file_path.endswith(".js"):
                self.send_header("Content-Type", "application/javascript")
            elif file_path.endswith(".json"):
                self.send_header("Content-Type", "application/json")
            else:
                self.send_header("Content-Type", "application/octet-stream")
                
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))
            
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/compile":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode("utf-8"))
                code = data.get("code", "")
                
                print(f"[DEBUG] Received compile request. Code length: {len(code)}")
                print(f"[DEBUG] Code content:\n{code}\n")
                
                result = run_compilation_pipeline(code)
                
                print(f"[DEBUG] Compilation pipeline executed. Success: {result['success']}, Error count: {len(result['errors'])}")
                
                response_data = json.dumps(result)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()
                self.wfile.write(response_data.encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

def run_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CompilerRequestHandler)
    print(f"[*] Mini Compiler Web IDE Server started at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
