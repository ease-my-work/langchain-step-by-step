# Step 12 · Human in the loop

> **You'll learn:** how to pause an agent before a risky tool call, let a human approve, edit or reject it, and resume the run where it stopped.
> **Time:** about 15 minutes · **Previous:** [Step 11 · Middleware](../step11_middleware/) · **Next:** [Step 13 · A team of agents](../step13_multi_agent/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `issue_refund(order_id, amount_inr, reason, runtime)`: a tool that (pretends to) move money | `ask()` loops: stream, check for a pause, collect decisions, resume with `Command(resume=...)` | `show_what_model_sees` and `log_tool_calls` (they were only for learning hooks) |
| `HumanInTheLoopMiddleware(interrupt_on={"issue_refund": ...})` | `SYSTEM_PROMPT`: a refund rule and a line for `issue_refund` | Printing the thread's message count |
| `review(action)`: asks the human in the terminal | Step 11's built-in middleware moved to [`guardrails.py`](guardrails.py) | |

```bash
git diff --no-index steps/step11_middleware/app.py steps/step12_human_in_the_loop/app.py
```

## Why

Looking things up is safe. **Doing** things (refunds, cancellations, emails to customers) is not: a
misunderstanding or a manipulative customer could cost real money. The shop's own handbook says every
refund needs a second person. So Barista Bot may *propose* a refund, but a human decides. The agent has
to stop mid-run, wait (seconds or days), and then carry on exactly where it was.

## Key concepts

- **Interrupt.** A pause inside a run. The agent's state, including the tool call it was about to make, is
  saved by the **checkpointer**, so nothing is lost while it waits. That's why a checkpointer is required.
- **`HumanInTheLoopMiddleware(interrupt_on={...})`.** After the model asks for tool calls, it checks each
  one. Tools listed with a config pause for review; others run straight away.
- **Decisions.** For each paused tool call, the human sends one of:

  | Decision | Effect |
  | --- | --- |
  | `{"type": "approve"}` | Run the tool call as the model wrote it. |
  | `{"type": "edit", "edited_action": {"name": ..., "args": {...}}}` | Run it with your changes, for example a different amount. |
  | `{"type": "reject", "message": "..."}` | Don't run it. The message goes back to the model as the tool's result, so it can explain or try something else. |

  `allowed_decisions` limits which ones a reviewer may use for each tool.
- **Resume.** `agent.stream(Command(resume={"decisions": [...]}), config)` with the **same thread id**.
  The agent doesn't start over: it continues from the paused tool call.
- **Where the pause shows.** The stream yields an `__interrupt__` chunk, and
  `agent.get_state(config).interrupts` lists pending pauses. Each interrupt's `value["action_requests"]`
  holds the tool calls to review, with `name`, `args` and `description`.

## Key code

```python
agent = create_agent(
    ...,
    tools=[..., issue_refund],
    middleware=[
        personalised_prompt,
        *guardrails(model),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "issue_refund": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                    "description": "Refund requested. Check it against the refund policy.",
                }
            }
        ),
    ],
    checkpointer=InMemorySaver(),
)

while True:
    for chunk in agent.stream(agent_input, config, context=context, stream_mode="updates"):
        print_updates(chunk)

    interrupts = agent.get_state(config).interrupts
    if not interrupts:
        break
    decisions = [review(action) for action in interrupts[0].value["action_requests"]]
    agent_input = Command(resume={"decisions": decisions})
```

| Part | What it does |
| --- | --- |
| `interrupt_on={"issue_refund": {...}}` | Only refunds pause. `"issue_refund": True` would allow every decision type. |
| `checkpointer=InMemorySaver()` | Holds the paused run. In production, a database: the reviewer may answer tomorrow, from another server. |
| `agent.get_state(config).interrupts` | Empty when the run finished; otherwise the pause to handle. |
| `review(action)` | Your UI. Here, `input()` in the terminal; in a real app, Approve / Edit / Reject buttons in a dashboard. |
| `Command(resume={"decisions": [...]})` | One decision per action request, in the same order. |

`issue_refund` still checks ownership, status and the amount in code. Human review is an extra layer, not
a replacement for validation.

## Run it

```bash
python steps/step12_human_in_the_loop/app.py
```

When it pauses, type `a`, `e` or `r` and press Enter. The demo suggests one of each:

## Try these prompts

1. As Asha: `One bag of beans in order BS-1001 arrived torn and half empty. Please refund that bag.`
   The agent checks the order, searches the policy (damaged beans: full refund), finds the bag costs ₹650,
   and calls `issue_refund(BS-1001, 650, ...)`. It pauses. Type **`a`** to approve: the tool runs and
   Barista Bot confirms the refund.
2. As Asha: `The second bag in that order was torn too. Refund it as well.` It proposes another ₹650. Type
   **`r`**, then a reason such as `Please ask for a photo of the torn bag first, as the policy says.`
   The tool doesn't run; the model reads your reason and asks Asha for a photo.
3. As Rahul: `Please cancel my order BS-1003 and refund me.` The policy allows a full refund while an
   order is processing, so it proposes ₹1,470. Type **`e`** and a different amount (say `1000`): the tool
   runs with **your** amount, and the reply says ₹1,000.

**Limits you may spot:**

- In prompt 3, Barista Bot may say the order "has been cancelled". It has no cancel tool, so that's not
  true. It refunded, nothing more. The fix is a real `cancel_order` tool (behind the same review), and
  the rule "never claim an action you didn't take with a tool".
- One agent now has six tools and a long prompt covering orders, catalogue, policies and refunds. Each new
  job makes the prompt longer and the tool choice harder. Step 13 splits the work across specialist agents.

## Look at the output

```text
[barista_bot] -> calls issue_refund({'amount_inr': 650, 'order_id': 'BS-1001', 'reason': 'One bag ... arrived torn and half empty.'})
[barista_bot] ⏸ paused, waiting for a human decision

[review] Refund requested. Check it against the refund policy.
[review] issue_refund({'amount_inr': 650, 'order_id': 'BS-1001', 'reason': '...'})
[review] approve (a), edit the amount (e) or reject (r)? a

[barista_bot] · HumanInTheLoopMiddleware.after_model changed the messages
[barista_bot] <- issue_refund returned {"status": "refund issued", "order_id": "BS-1001", "amount_inr": 650, ...}
```

The `HumanInTheLoopMiddleware` line is the middleware recording your decision in the conversation before
the tool runs. After an **edit**, the tool's result starts with a note telling the model a human replaced
its call, so it reports the amount that was really refunded.

## Break it

Remove `checkpointer=InMemorySaver()` from `create_agent` and run prompt 1. The stream still shows the
pause, then `agent.get_state(config)` fails with `ValueError: No checkpointer set`. Without a checkpointer
there's nowhere to keep the paused run, so it can never be resumed. Human in the loop needs memory.

## Recap

- `HumanInTheLoopMiddleware` pauses before chosen tools; others run freely.
- The checkpointer holds the paused run; resume it with `Command(resume={"decisions": [...]})` on the same thread.
- Decisions: approve, edit (change the arguments), reject (with a message for the model).
- Keep validating inside the tool too. Review is a second line of defence.

## Learn more

- [Human-in-the-loop](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
- [Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
