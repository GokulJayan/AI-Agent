# NVIDIA AI Agent

A terminal-based AI agent powered by NVIDIA's OpenAI-compatible API. It supports streaming responses, an interactive CLI, response-time reporting, and tool calling.

## Setup

Create and activate the project virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### NVIDIA API Key and Model

1. Sign in to [NVIDIA Build](https://build.nvidia.com/).
2. Open [Explore / Discover](https://build.nvidia.com/explore/discover).
3. Choose a model you want to use and create or copy an NVIDIA API key from the model page.
4. Add the API key and selected model name to a `.env` file in the project root:

Your `.env` file should contain:

```env
NVIDIA_API_KEY=your_api_key
NVIDIA_LLM_MODEL=your_model_name
```

Keep `.env` private. It is excluded by `.gitignore`.

## Sample Models

These are example NVIDIA Build model IDs you can place in `NVIDIA_LLM_MODEL`:

- **`nvidia/nemotron-3.5-lightning-30b-a3b`**
	- The model initially used with this Python/OpenAI-compatible client.
	- 30B total parameters and approximately 3B active parameters.
	- Positioned by NVIDIA for fast, agentic workloads.
- **`nvidia/nemotron-3-nano-30b-a3b`**
	- A lower-traffic, general-purpose option.
	- Suitable for reasoning, coding, instruction following, and tool use.
- **`glm-5-3-flash`**
	- Considered for very low API traffic.
	- Approximately 2K API calls were shown for the relevant 30-day period at the time of review.
	- Traffic figures can change and should be checked on NVIDIA Build.
- **`nemotron-3.5-content-safety`**
	- A very low-traffic NVIDIA model option.
	- This is a content-safety and moderation model, not a general-purpose chat model.

## Run

Start interactive chat mode:

```bash
.venv/bin/python main.py
```

Ask a one-shot question:

```bash
.venv/bin/python main.py "What is an AI agent?"
```

Read a prompt from a text file:

```bash
.venv/bin/python main.py --file prompts/question.txt
```

## Interactive Commands

```text
/help       Show available commands
/model      Show the configured model
/clear      Clear the terminal
/file PATH  Read a text file and send it as a prompt
/exit       Exit the application
```

The CLI displays a status animation while waiting, streams the answer as it arrives, and reports the total response time.

## Tools

The agent can select tools when appropriate:

- `calculate`: safely evaluates numeric arithmetic.
- `web_search`: searches the web using `ddgs`.
- `wikipedia_search`: retrieves a Wikipedia page summary.
- `read_file`: reads text files inside the project workspace.
- `safe_shell`: runs limited read-only commands such as `pwd`, `ls`, `find`, and selected Git commands.

Tool results are sent back to the model so it can produce a final answer.

## Safety Limits

- Arithmetic does not use `eval`.
- File access is restricted to the project workspace.
- Shell execution uses `shell=False`.
- Shell pipes, redirects, chaining, and expansion are disabled.
- Git is limited to `status`, `diff`, and `log`.
- `find` execution and deletion flags are blocked.

## Project Structure

```text
AIAgent/
├── main.py              # Application entry point
├── source/
│   ├── agent.py         # Model requests and tool-calling loop
│   ├── cli.py           # CLI argument parsing and chat loop
│   ├── client.py        # NVIDIA API client
│   ├── commands.py      # Interactive commands
│   ├── prompts.py       # Prompt-file handling
│   ├── settings.py      # Environment configuration
│   ├── timing.py        # Response-time formatting
│   ├── tools.py         # Tool implementations and schemas
│   └── ui.py             # Terminal status animation
├── requirements.txt     # Python dependencies
└── .env                 # Local secrets and model settings
```
