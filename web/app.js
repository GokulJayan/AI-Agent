const composer = document.querySelector("#composer");
const promptInput = document.querySelector("#prompt");
const sendButton = document.querySelector("#send");
const messages = document.querySelector("#messages");
const intro = document.querySelector("#intro");
const statusWords = [
  "Fetching",
  "Brewing",
  "Thinking",
  "Processing",
  "Working",
  "Analyzing",
  "Computing",
  "Preparing",
  "Generating",
  "Connecting",
  "Decoding",
  "Calculating",
  "Searching",
  "Reasoning",
  "Cooking",
];

function startStatusAnimation(target = status) {
  let wordIndex = 0;
  let dotCount = 0;
  const update = () => {
    target.textContent = `${statusWords[wordIndex]}${".".repeat(dotCount)}`;
    dotCount = (dotCount + 1) % 4;
    if (dotCount === 0) wordIndex = (wordIndex + 1) % statusWords.length;
  };

  update();
  const interval = window.setInterval(update, 500);
  return () => window.clearInterval(interval);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function formatInline(value) {
  let formatted = escapeHtml(value);
  formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  formatted = formatted.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  formatted = formatted.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  formatted = formatted.replace(/_([^_]+)_/g, "<em>$1</em>");
  formatted = formatted.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noreferrer">$1</a>'
  );
  return formatted;
}

function renderMarkdown(markdown) {
  const lines = markdown.replace(/\r/g, "").split("\n");
  const blocks = [];
  let paragraph = [];
  let listType = null;
  let listItems = [];
  let codeBlock = null;

  const closeParagraph = () => {
    if (paragraph.length) {
      blocks.push(`<p>${formatInline(paragraph.join(" "))}</p>`);
      paragraph = [];
    }
  };
  const closeList = () => {
    if (!listItems.length) return;
    const tag = listType === "ordered" ? "ol" : "ul";
    blocks.push(`<${tag}>${listItems.map((item) => `<li>${formatInline(item)}</li>`).join("")}</${tag}>`);
    listItems = [];
    listType = null;
  };
  const closeCodeBlock = () => {
    if (codeBlock) {
      const language = codeBlock.lang;
      const content = codeBlock.content.join("\n");
      blocks.push(`<pre><code class="language-${language}">${escapeHtml(content)}</code></pre>`);
      codeBlock = null;
    }
  };

  for (const line of lines) {
    const trimmedLine = line.trim();

    if (codeBlock) {
      if (trimmedLine.startsWith("```") || trimmedLine.startsWith("``")) {
        closeCodeBlock();
      } else {
        codeBlock.content.push(line);
      }
      continue;
    }

    if (trimmedLine.startsWith("```") || trimmedLine.startsWith("``")) {
      closeParagraph();
      closeList();
      const lang = trimmedLine.replace(/^```|^``/, "").trim() || "text";
      codeBlock = { lang, content: [] };
      continue;
    }

    const heading = line.match(/^#{1,3}\s+(.+)$/);
    const unordered = line.match(/^\s*[-*]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);

    if (heading) {
      closeParagraph();
      closeList();
      const level = line.match(/^#+/)[0].length;
      blocks.push(`<h${level}>${formatInline(heading[1])}</h${level}>`);
    } else if (unordered || ordered) {
      closeParagraph();
      const nextType = ordered ? "ordered" : "unordered";
      if (listType && listType !== nextType) closeList();
      listType = nextType;
      listItems.push((ordered ? ordered[1] : unordered[1]).trim());
    } else if (!line.trim()) {
      closeParagraph();
      closeList();
    } else {
      closeList();
      paragraph.push(line.trim());
    }
  }

  closeCodeBlock();
  closeParagraph();
  closeList();
  return blocks.join("");
}

function addMessage(role, text = "") {
  const message = document.createElement("article");
  message.className = `message ${role}`;
  message.innerHTML = `<div class="message-label">${role === "user" ? "You" : "Agent"}</div><div class="assistant-thinking" hidden></div><div class="message-body"></div>`;
  message.querySelector(".message-body").textContent = text;
  messages.appendChild(message);
  return {
    body: message.querySelector(".message-body"),
    thinking: message.querySelector(".assistant-thinking"),
  };
}

function addToolEvent(text) {
  const tool = document.createElement("div");
  tool.className = "tool";
  tool.textContent = text;
  messages.appendChild(tool);
}

async function sendPrompt(prompt) {
  const userMessage = addMessage("user", prompt);
  userMessage.body.textContent = prompt;
  const assistantMessage = addMessage("assistant");
  const assistantBody = assistantMessage.body;
  assistantMessage.thinking.hidden = false;
  const stopResponseAnimation = startStatusAnimation(assistantMessage.thinking);
  let assistantText = "";
  intro.hidden = true;
  sendButton.disabled = true;

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok || !response.body) throw new Error(`Request failed (${response.status})`);

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop();
      for (const rawEvent of events) {
        if (!rawEvent.startsWith("data: ")) continue;
        const event = JSON.parse(rawEvent.slice(6));
        if (event.type === "content") {
          if (!assistantMessage.thinking.hidden) {
            assistantMessage.thinking.hidden = true;
            stopResponseAnimation();
          }
          assistantText += event.content;
          assistantBody.innerHTML = renderMarkdown(assistantText);
        }
        if (event.type === "tool_result") addToolEvent(`Tool completed: ${event.name}`);
        if (event.type === "error") throw new Error(event.content);
      }
    }
  } catch (error) {
    assistantBody.textContent = `Error: ${error.message}`;
  } finally {
    assistantMessage.thinking.hidden = true;
    stopResponseAnimation();
    sendButton.disabled = false;
  }
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt || sendButton.disabled) return;
  promptInput.value = "";
  promptInput.style.height = "auto";
  sendPrompt(prompt);
});

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    composer.requestSubmit();
  }
});

promptInput.addEventListener("input", () => {
  promptInput.style.height = "auto";
  promptInput.style.height = `${Math.min(promptInput.scrollHeight, 160)}px`;
});

