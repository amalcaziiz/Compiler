// Preset Code Samples
const PRESETS = {
    valid: `// Sample Program: Valid Compilation
int a = 10;
int b = 20;
int c;
c = a + b;

if (c > 20) {
    print(c);
}`,
    syntax_err: `// Sample Program: Syntax Error
int a = 10;
int = b 20; // Error: unexpected '=' in declaration`,
    semantic_err: `// Sample Program: Semantic Error
int x;
x = "Hello"; // Error: Cannot assign string to integer`
};

document.addEventListener("DOMContentLoaded", () => {
    const editor = document.getElementById("code-editor");
    const lineNumbers = document.getElementById("line-numbers");
    const btnCompile = document.getElementById("btn-compile");
    const consoleOutput = document.getElementById("console-output");
    const consoleStatus = document.getElementById("console-status");

    // Initialize with Valid preset
    editor.value = PRESETS.valid;
    updateLineNumbers();
    checkServerConnection();

    async function checkServerConnection() {
        const host = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
        try {
            await fetch(`${host}/api/compile`, {
                method: "OPTIONS"
            });
            setConsoleStatus("success", "Online");
            logToConsole("Ready to compile. Select a preset or write your code, and click 'Compile Code'.");
        } catch (err) {
            setConsoleStatus("error", "Offline");
            logToConsole("[!] WARNING: Compiler Server is unreachable.\n- If you opened index.html directly from a folder (file://), make sure the server is running by typing 'python server.py' in the terminal.\n- If the server is running, try opening http://localhost:8000 directly in your browser.", true);
        }
    }

    // Editor line numbers sync
    editor.addEventListener("input", updateLineNumbers);
    editor.addEventListener("scroll", () => {
        lineNumbers.scrollTop = editor.scrollTop;
    });

    function updateLineNumbers() {
        const lines = editor.value.split("\n");
        const numbers = Array.from({ length: lines.length }, (_, i) => i + 1).join("<br>");
        lineNumbers.innerHTML = numbers;
    }

    // Tab switching
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            document.getElementById(`pane-${tabId}`).classList.add("active");
        });
    });

    // Preset loading
    const presetButtons = document.querySelectorAll(".preset-btn");
    presetButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-preset");
            if (PRESETS[key]) {
                editor.value = PRESETS[key];
                updateLineNumbers();
                logToConsole(`Loaded sample preset: ${btn.textContent.trim()}`);
            }
        });
    });

    // Compile action
    btnCompile.addEventListener("click", async () => {
        const code = editor.value;
        if (!code.trim()) {
            alert("Please write some code first!");
            return;
        }

        // Set compiling UI state
        setConsoleStatus("compiling", "Compiling...");
        logToConsole("Initializing compiler compilation pipeline...\n");

        // Determine backend host (e.g. if loaded via file:// protocol, fallback to localhost:8000)
        const host = window.location.protocol === 'file:' ? 'http://localhost:8000' : '';
        try {
            const response = await fetch(`${host}/api/compile`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code })
            });

            if (!response.ok) {
                throw new Error(`Server responded with HTTP ${response.status}`);
            }

            const data = await response.json();
            handleCompileResult(data);

        } catch (err) {
            setConsoleStatus("error", "Error");
            logToConsole(`[!] Connection / API Error:\n${err.message}`, true);
        }
    });

    function setConsoleStatus(state, label) {
        consoleStatus.className = `status-badge ${state}`;
        consoleStatus.textContent = label;
    }

    function logToConsole(text, isError = false) {
        if (isError) {
            consoleOutput.innerHTML = `<div class="console-err-line">${text}</div>`;
        } else {
            consoleOutput.textContent = text;
        }
    }

    function handleCompileResult(data) {
        // Clear old states
        const tokensBody = document.getElementById("tokens-table-body");
        const symbolsBody = document.getElementById("symbols-table-body");
        const astTree = document.getElementById("ast-tree");
        const semanticReport = document.getElementById("semantic-report");
        const tacRawBox = document.getElementById("tac-raw-box");
        const tacBeforeBox = document.getElementById("tac-before-box");
        const tacAfterBox = document.getElementById("tac-after-box");
        const assemblyBox = document.getElementById("assembly-box");

        // 1. Fill Token Table
        if (data.tokens && data.tokens.length > 0) {
            tokensBody.innerHTML = data.tokens.map((t, idx) => `
                <tr class="${t.type === 'INVALID' ? 'text-error' : ''}">
                    <td>${idx + 1}</td>
                    <td><code>${escapeHtml(t.value)}</code></td>
                    <td><span class="editor-lang">${t.type}</span></td>
                    <td>Line ${t.line}, Col ${t.column}</td>
                </tr>
            `).join("");
        } else {
            tokensBody.innerHTML = `<tr><td colspan="4" class="empty-state">No tokens found.</td></tr>`;
        }

        // Check if compiler failed
        if (!data.success) {
            setConsoleStatus("error", "Failed");
            
            // Format and print all compiling errors
            let errText = `[-] Compilation FAILED at phase: ${data.phase}\n\n`;
            data.errors.forEach(err => {
                errText += `Error at Line ${err.line}, Column ${err.column}: ${err.message}\n`;
            });
            logToConsole(errText, true);

            // Display errors in semantic pane
            semanticReport.className = "console-box error";
            semanticReport.innerHTML = data.errors.map(err => `
                <div class="sem-err-entry">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <div>
                        <strong>Line ${err.line}, Col ${err.column}</strong><br>
                        ${escapeHtml(err.message)}
                    </div>
                </div>
            `).join("");

            // Render AST Tree if available
            if (data.ast) {
                astTree.innerHTML = renderASTNode(data.ast);
            } else {
                astTree.innerHTML = `<div class="empty-state text-error">Syntax / Semantic Errors detected. Tree unavailable.</div>`;
            }

            // Render Symbol Table if available
            if (data.symbols && data.symbols.length > 0) {
                symbolsBody.innerHTML = data.symbols.map(sym => `
                    <tr>
                        <td><code>${escapeHtml(sym.name)}</code></td>
                        <td><span class="editor-lang">${sym.type}</span></td>
                        <td>${sym.scope_level}</td>
                        <td><code>${escapeHtml(sym.initial_value)}</code></td>
                        <td><code>${sym.memory_address}</code></td>
                    </tr>
                `).join("");
            } else {
                symbolsBody.innerHTML = `<tr><td colspan="5" class="empty-state">Compilation failed before symbol table creation.</td></tr>`;
            }

            // Clear codes that are not available
            tacRawBox.textContent = `// TAC unavailable due to compile errors`;
            tacBeforeBox.textContent = `// TAC unavailable`;
            tacAfterBox.textContent = `// TAC unavailable`;
            assemblyBox.textContent = `// Assembly generation unavailable`;

            // Switch to relevant error tab
            if (data.phase === "Lexical Analysis") {
                switchTab("tokens");
            } else if (data.phase === "Syntax Analysis") {
                switchTab("syntax");
            } else {
                switchTab("semantic");
            }
            return;
        }

        // 2. Successful Compilation Path
        setConsoleStatus("success", "Success");
        logToConsole("[+] Compilation Completed Successfully!\nNo errors detected.\nSymbol Table, AST, TAC, Optimizations and Assembly code populated successfully.");

        // Switch tab to Assembly to show end result (wow effect)
        switchTab("assembly");

        // Render AST Tree
        if (data.ast) {
            astTree.innerHTML = renderASTNode(data.ast);
        } else {
            astTree.innerHTML = `<div class="empty-state">No AST node returned.</div>`;
        }

        // Render Symbol Table
        if (data.symbols && data.symbols.length > 0) {
            symbolsBody.innerHTML = data.symbols.map(sym => `
                <tr>
                    <td><code>${escapeHtml(sym.name)}</code></td>
                    <td><span class="editor-lang">${sym.type}</span></td>
                    <td>${sym.scope_level}</td>
                    <td><code>${escapeHtml(sym.initial_value)}</code></td>
                    <td><code>${sym.memory_address}</code></td>
                </tr>
            `).join("");
        } else {
            symbolsBody.innerHTML = `<tr><td colspan="5" class="empty-state">No symbols declared.</td></tr>`;
        }

        // Render Semantic Report (Clean Success)
        semanticReport.className = "console-box success";
        semanticReport.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fa-solid fa-circle-check" style="font-size: 24px;"></i>
                <div>
                    <strong>Semantic Check Passed</strong><br>
                    All variables declared correctly, no duplicate variables, type checks validated.
                </div>
            </div>
        `;

        // Render Raw TAC
        if (data.tac_raw && data.tac_raw.length > 0) {
            tacRawBox.textContent = data.tac_raw.map(t => t.text).join("\n");
            tacBeforeBox.textContent = data.tac_raw.map(t => t.text).join("\n");
        } else {
            tacRawBox.textContent = "// No TAC instructions generated";
            tacBeforeBox.textContent = "// No TAC instructions generated";
        }

        // Render Optimized TAC
        if (data.tac_opt && data.tac_opt.length > 0) {
            tacAfterBox.textContent = data.tac_opt.map(t => t.text).join("\n");
        } else {
            tacAfterBox.textContent = "// No TAC instructions generated";
        }

        // Render Assembly-like instructions
        if (data.assembly && data.assembly.length > 0) {
            assemblyBox.textContent = data.assembly.join("\n");
        } else {
            assemblyBox.textContent = "; No assembly instructions generated";
        }
    }

    function switchTab(tabId) {
        tabButtons.forEach(b => {
            if (b.getAttribute("data-tab") === tabId) {
                b.click();
            }
        });
    }

    // Helper for HTML escaping
    function escapeHtml(text) {
        if (typeof text !== "string") return String(text);
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Recursive AST Renderer
    function renderASTNode(node) {
        if (!node) return "";
        const name = node.name || "Unknown";
        
        let headerClass = "ast-node-header";
        if (name === "Program") headerClass += " root";
        else if (name.startsWith("VarDecl") || name.startsWith("Assign") || name.startsWith("Print") || name.endsWith("Statement")) {
            headerClass += " keyword";
        }
        else if (name.startsWith("Op:")) headerClass += " op";
        else if (name.startsWith("ID:")) headerClass += " id";
        else if (name.startsWith("Literal")) headerClass += " literal";

        let html = `<div class="ast-node">`;
        html += `<div class="${headerClass}">${escapeHtml(name)}</div>`;

        if (node.children && node.children.length > 0) {
            html += `<div class="ast-node-children" style="margin-left: 20px;">`;
            for (const child of node.children) {
                html += renderASTNode(child);
            }
            html += `</div>`;
        }

        html += `</div>`;
        return html;
    }
});
