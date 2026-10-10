# Step 03 · Structured output

> **You'll learn:** how to make a model fill in a Python object with fixed fields, instead of writing free text you have to parse.
> **Time:** about 10 minutes · **Previous:** [Step 02 · Prompts and chains](../step02_prompts_chains/) · **Next:** [Step 04 · Composing chains](../step04_compose_chains/)

## What changed

Barista Bot stops chatting for a moment and does a back-office job: triaging the support inbox.

| Added | Changed | Removed |
| --- | --- | --- |
| `Ticket`: a Pydantic model with `category`, `priority`, `order_id`, `sentiment`, `summary` | The prompt asks for triage of `{email}`, not a reply to `{question}` | `StrOutputParser()` (the output is already an object) |
| `model.with_structured_output(Ticket)` in the chain | `ask()` prints the ticket as JSON and flags urgent ones | `.stream()` (you want the finished ticket, not pieces) |
| | Demo prompts are now customer emails | `SHOP` and the `{shop_name}` / `{tone}` variables |

```bash
git diff --no-index steps/step02_prompts_chains/app.py steps/step03_structured_output/app.py
```

## Why

Code can't act on "This seems like an urgent refund request about order BS-1001, the customer is upset".
It can act on `ticket.priority == "urgent"`. Asking the model to "reply in JSON" in the prompt mostly
works, until it adds a sentence before the JSON, or calls the field `orderId`, or invents a priority
called "high". Structured output makes the reply match a schema you define.

## Key concepts

- **Schema.** The shape you want back. A Pydantic `BaseModel` is the usual choice; a `TypedDict` or a JSON
  Schema dict also work.
- **`with_structured_output(Schema)`.** Wraps the model so it returns a `Schema` object instead of an
  `AIMessage`. LangChain uses the provider's native structured output (Gemini's JSON-schema mode here) or, for
  models without it, a tool call, and validates the result with Pydantic.
- **The schema is part of the prompt.** Field names, types, `Literal` choices and `Field(description=...)`
  are all sent to the model. Write them for the model to read.
- **`Literal[...]`** limits a field to fixed values. **`X | None = None`** makes a field optional, so the
  model can leave it empty.

## Key code

```python
class Ticket(BaseModel):
    """A support ticket created from one customer email."""

    category: Literal["order_status", "return_or_refund", "product_question", "complaint", "other"]
    priority: Literal["low", "normal", "urgent"] = Field(
        description="urgent: money lost, item broken or the customer is very upset. low: general questions."
    )
    order_id: str | None = Field(
        default=None, description='Order number like "BS-1002", only if the email mentions one.'
    )
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(description="One short sentence saying what the customer wants.")


chain = prompt | model.with_structured_output(Ticket)
ticket = chain.invoke({"email": email})  # a Ticket
if ticket.priority == "urgent":
    ...
```

| Part | What it does |
| --- | --- |
| The class docstring | Sent as the schema's description. |
| `Literal[...]` | The model must pick one of these strings. No "high", no "Urgent!!". |
| `Field(description=...)` | Explains a field: what counts as urgent, what an order id looks like. |
| `str \| None = None` | Optional. Without it, the model has to put *something* in the field (see Break it). |
| `with_structured_output(Ticket)` | Returns a new runnable whose output is a validated `Ticket`. |
| `ticket.priority == "urgent"` | From here on it's ordinary Python: attributes, not text parsing. |

## Run it

```bash
python steps/step03_structured_output/app.py
python steps/step03_structured_output/app.py "Your decaf gave me a headache. Do you sell anything milder?"
```

## Try these prompts

1. `Hi! Ordered an electric grinder last week (BS-1002). Any idea when it gets here? Thanks!`
   `order_status`, `low`, `order_id: "BS-1002"`, `positive`.
2. `This is the second time my beans arrived with a torn bag ... Order BS-1001. I want my money back NOW.`
   `return_or_refund`, `urgent`, `negative`, and the code flags it for a human.
3. `Do you have a decaf that works for cold brew?` `product_question`, and `order_id` is `null`: no order
   was mentioned, so the model left the optional field empty.
4. `Loved the Monsoon Malabar, best coffee I've had all year!` `other`, `positive`. **The limit:** the
   schema has no "praise" category, so it lands in `other`. The model can only choose from what you give it.
   Add `"feedback"` to the `Literal` and run it again.

## Look at the output

```text
[triage] {
  "category": "return_or_refund",
  "priority": "urgent",
  "order_id": "BS-1001",
  "sentiment": "negative",
  "summary": "The customer is demanding an immediate refund for a damaged coffee order."
}
[triage] -> urgent: send this one to a human straight away
```

Every run returns the same five keys, with values from the allowed lists.

## Break it

Make `order_id` required: change it to `order_id: str = Field(description=...)` (remove `| None` and
`default=None`) and run prompt 3. The model must fill the field, and there is no order to put in it, so it
returns `"order_id": ""` (or worse, an invented id). Optional fields are how you let a model say "not
mentioned".

## Recap

- Define the output as a Pydantic model; field names, types and descriptions are instructions to the model.
- `model.with_structured_output(Schema)` returns validated objects you can use in code.
- Use `Literal` for fixed choices, and make a field optional when the input may not contain it.

## Learn more

- [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Models: structured output](https://docs.langchain.com/oss/python/langchain/models#structured-output)
