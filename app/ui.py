from __future__ import annotations


def render_ui() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FIR Gateway Console</title>
  <style>
    :root {
      --ink: #1d1a18;
      --paper: #f7f2e8;
      --panel: rgba(255, 252, 246, 0.88);
      --line: rgba(29, 26, 24, 0.14);
      --accent: #b6462f;
      --accent-deep: #7d2417;
      --gold: #d2a33a;
      --good: #2f6b44;
      --bad: #9f2c2c;
      --shadow: 0 18px 60px rgba(43, 26, 10, 0.16);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(210, 163, 58, 0.28), transparent 30%),
        radial-gradient(circle at top right, rgba(182, 70, 47, 0.16), transparent 25%),
        linear-gradient(135deg, #efe4d3 0%, #f8f3eb 48%, #ede2ce 100%);
      padding: 32px 18px 40px;
    }

    .shell {
      max-width: 1180px;
      margin: 0 auto;
    }

    .hero {
      display: grid;
      gap: 10px;
      margin-bottom: 22px;
    }

    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 12px;
      color: var(--accent-deep);
      font-weight: 700;
    }

    h1 {
      margin: 0;
      font-size: clamp(2.3rem, 6vw, 4.4rem);
      line-height: 0.95;
      font-family: Georgia, "Times New Roman", serif;
      max-width: 10ch;
    }

    .hero p {
      margin: 0;
      max-width: 60ch;
      line-height: 1.5;
      color: rgba(29, 26, 24, 0.78);
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 18px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      padding: 20px;
      backdrop-filter: blur(14px);
    }

    .card h2 {
      margin: 0 0 8px;
      font-size: 1.15rem;
    }

    .card p {
      margin: 0 0 16px;
      color: rgba(29, 26, 24, 0.72);
      line-height: 1.45;
    }

    .span-4 { grid-column: span 4; }
    .span-5 { grid-column: span 5; }
    .span-7 { grid-column: span 7; }
    .span-12 { grid-column: span 12; }

    .row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }

    label {
      display: grid;
      gap: 6px;
      font-size: 0.93rem;
      width: 100%;
    }

    input, textarea, button {
      font: inherit;
    }

    input, textarea {
      width: 100%;
      border: 1px solid rgba(29, 26, 24, 0.16);
      border-radius: 14px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.74);
      color: var(--ink);
    }

    textarea {
      min-height: 140px;
      resize: vertical;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 16px;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: #fff9f1;
      transition: transform 140ms ease, opacity 140ms ease;
    }

    button.secondary {
      background: rgba(29, 26, 24, 0.08);
      color: var(--ink);
    }

    button:hover {
      transform: translateY(-1px);
    }

    button:disabled {
      opacity: 0.55;
      cursor: wait;
      transform: none;
    }

    .status-strip {
      display: grid;
      gap: 10px;
    }

    .pill {
      border-radius: 999px;
      padding: 10px 14px;
      font-size: 0.93rem;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.58);
    }

    .mono, pre {
      font-family: "SFMono-Regular", "Menlo", "Monaco", monospace;
    }

    pre {
      margin: 0;
      padding: 16px;
      border-radius: 16px;
      background: #201c1a;
      color: #f8f2ea;
      min-height: 170px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }

    .response-grid {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
    }

    .tiny {
      font-size: 0.84rem;
      color: rgba(29, 26, 24, 0.66);
    }

    .good { color: var(--good); }
    .bad { color: var(--bad); }

    @media (max-width: 960px) {
      .span-4, .span-5, .span-7 { grid-column: span 12; }
      .response-grid { grid-template-columns: 1fr; }
      body { padding-inline: 14px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">FIR Gateway Console</div>
      <h1>Test the gateway without living in curl.</h1>
      <p>Use this local console to create a dev API key, probe health checks, and send chat requests through the same FastAPI backend your scripts hit.</p>
    </section>

    <section class="grid">
      <article class="card span-4">
        <h2>Gateway Status</h2>
        <p>Quick probes for the two operational endpoints.</p>
        <div class="row">
          <button id="healthBtn" type="button">Check /healthz</button>
          <button id="readyBtn" type="button" class="secondary">Check /readyz</button>
        </div>
        <div class="status-strip" style="margin-top: 14px;">
          <div id="healthResult" class="pill mono">/healthz not checked yet</div>
          <div id="readyResult" class="pill mono">/readyz not checked yet</div>
        </div>
      </article>

      <article class="card span-4">
        <h2>Create Dev API Key</h2>
        <p>This browser helper is only enabled when <span class="mono">APP_ENV=development</span>.</p>
        <label>
          Owner Label
          <input id="ownerInput" type="text" value="browser-dev" />
        </label>
        <div class="row" style="margin-top: 14px;">
          <button id="keyBtn" type="button">Create Key</button>
        </div>
        <p class="tiny" style="margin-top: 14px;">The raw key is only shown once. Copy it into the chat form below.</p>
        <pre id="keyOutput">No key generated yet.</pre>
      </article>

      <article class="card span-4">
        <h2>Quick Guide</h2>
        <p>Default local flow for the browser console.</p>
        <pre>1. Run the app
2. Create a dev API key
3. Paste the key below
4. Send a prompt
5. Inspect raw JSON output</pre>
      </article>

      <article class="card span-7">
        <h2>Chat Playground</h2>
        <p>Calls <span class="mono">POST /v1/chat/completions</span> with the same payload shape used by the API.</p>
        <div class="row">
          <label style="flex: 1 1 220px;">
            Model
            <input id="modelInput" type="text" value="fake-model" />
          </label>
          <label style="flex: 1 1 260px;">
            X-API-Key
            <input id="apiKeyInput" type="text" placeholder="Paste raw API key here" />
          </label>
        </div>
        <label style="margin-top: 12px;">
          Prompt
          <textarea id="promptInput" placeholder="Ask the fake provider something simple...">hello</textarea>
        </label>
        <div class="row" style="margin-top: 14px;">
          <button id="chatBtn" type="button">Send Chat Request</button>
        </div>
      </article>

      <article class="card span-5">
        <h2>Response Snapshot</h2>
        <p>High-signal summary of the last request.</p>
        <div id="summary" class="pill mono">No request sent yet</div>
      </article>

      <article class="card span-12">
        <div class="response-grid">
          <div>
            <h2>Raw Response</h2>
            <p>Exact JSON or error body returned by the backend.</p>
            <pre id="chatOutput">No chat response yet.</pre>
          </div>
          <div>
            <h2>Browser Notes</h2>
            <p>Useful details from the last action.</p>
            <pre id="eventLog">Waiting for interaction.</pre>
          </div>
        </div>
      </article>
    </section>
  </div>

  <script>
    const healthBtn = document.getElementById("healthBtn");
    const readyBtn = document.getElementById("readyBtn");
    const keyBtn = document.getElementById("keyBtn");
    const chatBtn = document.getElementById("chatBtn");

    const healthResult = document.getElementById("healthResult");
    const readyResult = document.getElementById("readyResult");
    const keyOutput = document.getElementById("keyOutput");
    const chatOutput = document.getElementById("chatOutput");
    const eventLog = document.getElementById("eventLog");
    const summary = document.getElementById("summary");

    const ownerInput = document.getElementById("ownerInput");
    const modelInput = document.getElementById("modelInput");
    const apiKeyInput = document.getElementById("apiKeyInput");
    const promptInput = document.getElementById("promptInput");

    function writeLog(message, payload) {
      const lines = [message];
      if (payload !== undefined) {
        lines.push(JSON.stringify(payload, null, 2));
      }
      eventLog.textContent = lines.join("\\n\\n");
    }

    async function callJson(url, options = {}) {
      const response = await fetch(url, options);
      const text = await response.text();
      let body;
      try {
        body = JSON.parse(text);
      } catch {
        body = text;
      }
      return { response, body };
    }

    async function probe(url, target) {
      target.textContent = "Checking...";
      try {
        const { response, body } = await callJson(url);
        target.textContent = response.ok
          ? `${url} -> ${response.status} ${JSON.stringify(body)}`
          : `${url} -> ${response.status} ${JSON.stringify(body)}`;
        target.className = `pill mono ${response.ok ? "good" : "bad"}`;
        writeLog(`Probe completed for ${url}`, body);
      } catch (error) {
        target.textContent = `${url} -> network error`;
        target.className = "pill mono bad";
        writeLog(`Probe failed for ${url}`, { error: String(error) });
      }
    }

    async function createKey() {
      keyBtn.disabled = true;
      keyOutput.textContent = "Creating key...";
      try {
        const { response, body } = await callJson("/ui/api-keys", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ owner: ownerInput.value || "browser-dev" })
        });
        keyOutput.textContent = JSON.stringify(body, null, 2);
        if (response.ok && body.raw_key) {
          apiKeyInput.value = body.raw_key;
          summary.textContent = `Created key for ${body.owner}`;
        }
        writeLog("Key creation response", body);
      } catch (error) {
        keyOutput.textContent = String(error);
        writeLog("Key creation failed", { error: String(error) });
      } finally {
        keyBtn.disabled = false;
      }
    }

    async function sendChat() {
      chatBtn.disabled = true;
      chatOutput.textContent = "Sending request...";
      summary.textContent = "Request in flight";
      try {
        const { response, body } = await callJson("/v1/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": apiKeyInput.value
          },
          body: JSON.stringify({
            model: modelInput.value,
            prompt: promptInput.value
          })
        });
        chatOutput.textContent = JSON.stringify(body, null, 2);
        summary.textContent = response.ok
          ? `HTTP ${response.status} · model ${body.model}`
          : `HTTP ${response.status} · request failed`;
        writeLog("Chat request completed", {
          status: response.status,
          ok: response.ok
        });
      } catch (error) {
        chatOutput.textContent = String(error);
        summary.textContent = "Network error";
        writeLog("Chat request failed", { error: String(error) });
      } finally {
        chatBtn.disabled = false;
      }
    }

    healthBtn.addEventListener("click", () => probe("/healthz", healthResult));
    readyBtn.addEventListener("click", () => probe("/readyz", readyResult));
    keyBtn.addEventListener("click", createKey);
    chatBtn.addEventListener("click", sendChat);
  </script>
</body>
</html>"""
