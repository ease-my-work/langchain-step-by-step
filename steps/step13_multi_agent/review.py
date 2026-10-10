"""The human reviewer from step 12 (unchanged).

It moved here to keep app.py about what is new in this step.
"""


# The human side. Shows the paused tool call and asks for a decision in the terminal.
# In a real app this would be a button in a support dashboard.
def review(action: dict) -> dict:
    print(f"\n[review] {action['description']}")
    print(f"[review] {action['name']}({action['args']})")
    choice = input("[review] approve (a), edit the amount (e) or reject (r)? ").strip().lower()
    print()

    if choice == "a":
        return {"type": "approve"}
    if choice == "e":
        amount = int(input("[review] new amount in ₹: "))
        new_args = {**action["args"], "amount_inr": amount}
        return {"type": "edit", "edited_action": {"name": action["name"], "args": new_args}}
    reason = input("[review] reason, for Barista Bot to pass on: ")
    return {"type": "reject", "message": reason}
