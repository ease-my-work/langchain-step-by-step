# Step 13 · A team of agents

> **You'll learn:** how to split one big agent into specialists, call each specialist as a tool, and get structured answers back from an agent.
> **Time:** about 20 minutes · **Previous:** [Step 12 · Human in the loop](../step12_human_in_the_loop/) · **Next:** [Step 14 · Next level](../step14_next_level/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `orders_agent`: a specialist with the four order and catalogue tools | `SYSTEM_PROMPT` is a front-desk prompt: delegate, then answer | The front desk's direct access to order, catalogue and handbook tools |
| `policy_agent`: a specialist with `search_handbook` and `response_format=PolicyAnswer` | The front desk has 3 tools instead of 6 | |
| `PolicyAnswer`: answer, sources, found_in_handbook | `create_agent(..., name="front_desk")` | |
| `ask_orders_specialist` and `ask_policy_specialist`: tools that call the specialists | `ask()` streams with `subgraphs=True` | |
| | `issue_refund` moved to [`shop_tools.py`](shop_tools.py); `review` to [`review.py`](review.py) | |

```bash
git diff --no-index steps/step12_human_in_the_loop/app.py steps/step13_multi_agent/app.py
```

## Why

By step 12, one agent had six tools and a prompt full of rules for orders, catalogue, policies, citations
and refunds. Every new job makes that prompt longer, every model call more expensive, and the choice of
tool harder. Teams of people solve this with specialists; agents can too:

```text
customer -> front_desk ─┬─ ask_orders_specialist -> orders_specialist (orders, products, stock)
                        ├─ ask_policy_specialist -> policy_specialist (handbook search)
                        └─ issue_refund (a human approves)
```

Each specialist has a short, focused prompt and only the tools it needs. The front desk talks to the
customer, decides who to ask, and combines the answers. Anything that moves money stays at the front
desk, behind step 12's human review: **specialists can only read**.

## Key concepts

- **Sub-agents as tools (supervisor pattern).** A specialist is a normal `create_agent(...)`. Wrap a call
  to it in a `@tool`, and the front desk uses it like any tool. Its docstring tells the front desk when to
  delegate. This is the simplest and most common multi-agent pattern.
- **Only the result comes back.** The tool returns the specialist's final answer, not its whole
  conversation, so the front desk's context stays small. The specialist starts fresh on each call.
- **Context flows down.** `ask_orders_specialist` gets the `ToolRuntime` and passes `runtime.context` to
  the specialist, so its tools still know who's logged in.
- **`response_format` on an agent.** The agent version of step 03's `with_structured_output`. The agent
  works as usual (here, searching the handbook), then ends with a `PolicyAnswer` in
  `result["structured_response"]`. Code can check `found_in_handbook` instead of parsing text.
- **`name`.** Names an agent; its replies carry the name. `print_updates` uses it to label lines.
- **`subgraphs=True`.** Streams the specialists' steps too, so you can watch them work. Without it you'd
  see only the front desk's tool calls and results.

## Key code

```python
orders_agent = create_agent(
    model=model,
    tools=[list_my_orders, get_order_status, search_products, check_stock],
    system_prompt="You are the orders specialist of Bean Street Coffee. ...",
    context_schema=CustomerContext,
    name="orders_specialist",
)


class PolicyAnswer(BaseModel):
    answer: str = Field(description="The answer, using only what the handbook says.")
    sources: list[str] = Field(
        description='Where it came from, like "shipping.md > Shipping charges".'
    )
    found_in_handbook: bool = Field(description="False if the handbook does not answer it.")


policy_agent = create_agent(
    model=model,
    tools=[search_handbook],
    system_prompt="You are the policy specialist of Bean Street Coffee. ...",
    response_format=PolicyAnswer,
    name="policy_specialist",
)


@tool
def ask_orders_specialist(request: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """Ask the orders specialist about the customer's orders, products, prices or stock. ..."""
    result = orders_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        context=runtime.context,
    )
    return result["messages"][-1].text


@tool
def ask_policy_specialist(question: str) -> dict:
    """Ask the policy specialist about shipping, returns, refunds, warranty, Bean Points or brewing. ..."""
    result = policy_agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["structured_response"].model_dump()


agent = create_agent(
    model=model,
    tools=[ask_orders_specialist, ask_policy_specialist, issue_refund],
    middleware=[personalised_prompt, *guardrails(model), HumanInTheLoopMiddleware(...)],
    context_schema=CustomerContext,
    checkpointer=InMemorySaver(),
    name="front_desk",
)
```

| Part | What it does |
| --- | --- |
| Specialist prompts | Short and single-purpose, and they say "you are talking to another agent", so answers are terse facts, not greetings. |
| `request: str` | The front desk writes the request. It should include order numbers and names; the specialist doesn't see the chat. |
| `context=runtime.context` | Passes the logged-in customer on. (A sub-agent run inside a tool inherits the run's context anyway; passing it explicitly makes the data flow visible.) |
| `result["messages"][-1].text` | Only the specialist's final answer goes back. |
| `response_format=PolicyAnswer` | The specialist must finish with a `PolicyAnswer`. Gemini does this with a hidden tool named after the schema, which is why you'll see `-> calls PolicyAnswer(...)`. |
| No checkpointer on the specialists | They don't need memory; each request is complete in itself. |

## Run it

```bash
python steps/step13_multi_agent/app.py
```

When the refund pauses, type `a` to approve (or try `e` and `r`, as in step 12).

## Try these prompts

1. As Meera: `Do you have decaf in stock, and how do I make cold brew with it?` The front desk calls
   **both specialists in one turn**. Their steps are interleaved in the output because they run at the same
   time. The policy specialist ends with `PolicyAnswer(...)`; the front desk combines both answers.
2. As Asha: `Is the grinder in my order BS-1002 still covered if its burrs go dull?` Orders specialist:
   it's the Flat Burr Electric Grinder. Policy specialist: dull burrs are wear parts, not covered. The front
   desk joins the facts and cites `(warranty.md > What is not covered)`.
3. As Asha: `One bag of beans in order BS-1001 arrived torn and half empty. Please refund that bag.` Both
   specialists check (order and price; damaged-beans policy), then the front desk calls `issue_refund` and
   **pauses for you**, exactly as in step 12.

**The limit:** more agents means more model calls. When we ran prompt 3, it took nine model calls across three
agents; the same request in step 12 took four. You pay for focus with tokens and time. Use
specialists when one agent is genuinely overloaded, not by default.

## Look at the output

```text
[front_desk] -> calls ask_orders_specialist({'request': 'Do you have decaf coffee in stock?'})
[front_desk] -> calls ask_policy_specialist({'question': 'How do I make cold brew coffee?'})
[policy_specialist] -> calls search_handbook({'query': 'cold brew coffee'})
[orders_specialist] -> calls search_products({'query': 'decaf'})
[orders_specialist] <- search_products returned [{"product_id": "BEAN-DCF", ...}]
[policy_specialist] <- search_handbook returned [brewing_guide.md > Cold brew] ...
[orders_specialist] -> calls check_stock({'product_id': 'BEAN-DCF'})
[policy_specialist] -> calls PolicyAnswer({'answer': 'To make cold brew coffee: ...', 'sources': [...], 'found_in_handbook': True})
[front_desk] <- ask_policy_specialist returned {"answer": "...", "sources": ["brewing_guide.md > Cold brew"], "found_in_handbook": true}
[front_desk] <- ask_orders_specialist returned * Product: Swiss Water Decaf beans, 250 g ...
[front_desk] Hi Meera! Yes, we have Swiss Water Decaf beans (250 g) in stock ...
```

In LangSmith (step 06's tip), each specialist appears as a nested run inside the front desk's tool call.

## Break it

Delete `response_format=PolicyAnswer` from `policy_agent` and ask
`python steps/step13_multi_agent/app.py "How do I make cold brew?"`. The specialist answers in plain text,
and `ask_policy_specialist` crashes with `KeyError: 'structured_response'`: there's only a
`structured_response` when the agent has a `response_format`. Structured output is a contract; when code
depends on it, keep it.

## Recap

- Split an overloaded agent into specialists with short prompts and few tools.
- Wrap each specialist in a `@tool`; the front desk delegates by calling it. Return only the final answer.
- Pass the runtime context down; keep risky actions (and their human review) at the top.
- `response_format` gives an agent a structured final answer in `result["structured_response"]`.
- More agents cost more calls. Use them when focus pays for itself.

## Learn more

- [Multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
- [Structured output with agents](https://docs.langchain.com/oss/python/langchain/structured-output)
