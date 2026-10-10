# Step 01 · Hello, Barista Bot

> **You'll learn:** how to get a chat model with one line, send it messages, and read its reply.
> **Time:** about 10 minutes · **Next:** [Step 02 · Prompts and chains](../step02_prompts_chains/)

## What changed

Everything is new. This is the smallest useful LangChain program.

| Added | Changed | Removed |
| --- | --- | --- |
| `model = init_chat_model(MODEL)` | | |
| `SYSTEM_PROMPT`: Barista Bot's role and one rule | | |
| `ask()`: sends a `SystemMessage` and a `HumanMessage`, prints the reply and its token count | | |

## Why

Before agents, tools or RAG, you need to talk to a model. LangChain gives every provider (Google, OpenAI,
Anthropic, Ollama and dozens more) the **same interface**, so the rest of this course works with any of
them. You learn it once here.

## Key concepts

- **Chat model.** An LLM you talk to in messages. In LangChain it is an object with `invoke()`,
  `stream()` and `batch()` methods. Every provider's model has the same methods.
- **`init_chat_model("provider:model")`.** One function for every provider. This course uses
  `google_genai:gemini-flash-latest` (from `MODEL` in `.env`). Change that one string to switch provider.
- **Messages.** A conversation is a list of messages, each with a role:

  | Class | Role | Who writes it |
  | --- | --- | --- |
  | `SystemMessage` | system | You, the developer: the model's role and rules |
  | `HumanMessage` | human / user | The user |
  | `AIMessage` | ai / assistant | The model (it's what `invoke()` returns) |
  | `ToolMessage` | tool | Your code, with a tool's result (step 05) |

- **The model has no memory.** Each `invoke()` sends the whole list. To "continue" a chat you send all
  the earlier messages again (step 07 automates that).
- **Tokens.** Models read and write text in small pieces called tokens. You pay per token, and
  `usage_metadata` tells you how many a call used.

## Key code

```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

model = init_chat_model(MODEL)  # "google_genai:gemini-flash-latest"

messages = [
    SystemMessage(SYSTEM_PROMPT),
    HumanMessage(question),
]
response = model.invoke(messages)
print(response.text)
print(response.usage_metadata)
```

| Part | What it does |
| --- | --- |
| `init_chat_model(MODEL)` | Picks the integration package from the `provider:` prefix (`langchain-google-genai` here) and builds the model. It reads the API key from the environment. |
| `SystemMessage(...)` | Instructions for the model. Users don't see it. |
| `HumanMessage(question)` | The user's message. |
| `model.invoke(messages)` | One request, one reply. Returns an `AIMessage`. |
| `response.text` | The reply as plain text. Newer models can return `.content` as a list of "content blocks" (text, reasoning, images), so `.text` is the safe way to get just the words. |
| `response.usage_metadata` | `input_tokens`, `output_tokens` and `total_tokens` for this call. |

> **Shortcut.** `model.invoke("How do I store beans?")` also works: a plain string becomes one
> `HumanMessage`. You can also write messages as dicts: `{"role": "user", "content": "..."}`.
> Step 06 uses that form.

## Run it

From the repo root, with your virtual environment active:

```bash
python steps/step01_hello/app.py
```

That sends the three prompts below. To send your own message, or to chat:

```bash
python steps/step01_hello/app.py "What grind size is best for a French press?"
python steps/step01_hello/app.py --chat
```

## Try these prompts

1. `What's the difference between Arabica and Robusta beans?` A good, general answer. The model
   knows a lot about coffee from its training.
2. `How should I store my coffee beans at home?` Also good. Notice it follows the "at most three
   sentences" rule from the system message.
3. `Where is my order BS-1002?` **This is the limit.** The model can't look anything up, so it asks for
   your phone number or makes up a helpful-sounding answer. When we ran it, it also claimed in prompt 1
   that the shop sells "both" kinds of beans, which nobody told it. Step 05 gives it tools to look things
   up; step 02 tells it not to guess.

## Look at the output

```text
[user] What's the difference between Arabica and Robusta beans?
[barista_bot] Arabica beans offer a smoother, sweeter taste ... Robusta beans are bolder ...
  (tokens: 51 in, 439 out)
```

51 tokens in for a system message plus one question, but ~440 out for three sentences? Gemini Flash
**thinks** before it answers, and those reasoning tokens count as output (see
`usage_metadata["output_token_details"]["reasoning"]`). They're part of the cost of a good answer.

## Break it

Remove the `SystemMessage` line from `messages` and ask prompt 3 again. Without a role, the model
doesn't know it is Barista Bot: when we tried, it answered as a generic assistant with a long numbered
list, telling you to check your email and "contact the store where you made the purchase". The
three-sentence rule is gone too. The system message is the only place the model learns who it is and
how to answer.

## Recap

- `init_chat_model("provider:model")` gives you a chat model from any provider.
- A conversation is a list of messages: system, human, ai (and tool, later).
- `model.invoke(messages)` returns an `AIMessage`; read it with `.text`.
- The model knows only its training and what you send it. It can't look anything up yet.

## Learn more

- [Models](https://docs.langchain.com/oss/python/langchain/models)
- [Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [Chat model integrations](https://docs.langchain.com/oss/python/integrations/chat) (every provider)
