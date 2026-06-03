---
name: flows
description: Design and implement any multi-step user journey to industry-level completeness. Apply when building or reviewing any feature that involves more than one screen, more than one state, or more than one actor. Every flow must handle the full surface area: happy path, failure paths, edge cases, re-entry, and recovery — not just the case where everything goes right.
---

# Flows

## What a Flow Is

A flow is any user journey that involves state changing across more than one interaction. Submitting a form is a single interaction. A journey that spans multiple screens, involves intermediate states, or can be interrupted and resumed is a flow.

Flows must be designed completely before implementation begins. A flow that is only designed for the happy path will be patched with inconsistent error handling later, produce confusing states in production, and cost significantly more to correct than to design right initially.

---

## Flow Design Protocol

Before a single line of implementation is written, a flow must answer every question in this protocol. The answers become the implementation specification.

### 1. Define the entry points

Where can a user begin this flow? From a navigation link? From an inline action on a list item? From a notification? From a direct URL? Each entry point must be handled. A flow that assumes the user always begins from the same place will fail for users who arrive through a different path.

### 2. Define the terminal states

What are all the ways this flow ends?

- Successful completion
- User-initiated cancellation
- Session expiry mid-flow
- Validation failure at each step
- Server-side failure at each step
- External dependency failure (email not delivered, third-party timeout)

Each terminal state has a defined outcome: where the user ends up, what message they see, what state is preserved or discarded, and whether a retry is possible.

### 3. Map every screen and state

List each screen or view in the flow. For each screen:

- What data does the user see?
- What actions are available?
- What can go wrong on this screen?
- What does the back action do?
- What does abandonment (closing the tab, navigating away) do?

### 4. Define re-entry behavior

If a user starts a flow, stops, and returns later — what happens?

- Is the previous state recoverable?
- Does a partially completed flow expire?
- Is there a way to resume, or does the user restart?
- Is the user informed of their previous state?

### 5. Define concurrent access behavior

If the same user opens the flow in two tabs, what happens? If two users interact with the same resource simultaneously, what happens? Define the resolution.

### 6. Define the session and permission requirements

Can the flow be started without being authenticated? At what point does authentication become required? What happens when a user attempts to enter a step without having completed a prerequisite step?

---

## State Machine Discipline

Every non-trivial flow is a state machine. The states and transitions are defined explicitly before implementation.

### States are named and finite

A flow has a defined set of states. "In progress" is not a state — "awaiting email confirmation" is a state. "Error" is not a state — "submission failed due to duplicate email" is a state.

### Transitions are events, not conditions

A transition is triggered by an event: a button click, a server response, a timer expiry, a user navigation. It is not triggered by a condition being checked at render time. The flow moves because something happened, not because the interface re-evaluated state.

### Invalid transitions are blocked

A user cannot reach step 3 without completing step 2. A user cannot submit a form while a previous submission is still pending. A user cannot trigger a destructive action twice by double-clicking. These are not edge cases — they are standard user behaviors that the flow must handle.

---

## Interruption and Recovery

Every flow can be interrupted. Design the recovery before the happy path is finalized.

### Network failure

An action that depends on a network request can fail mid-flight. The user must know:
1. That the operation is pending (immediate loading feedback)
2. That it failed (specific error, not a generic message)
3. Whether it is safe to retry (idempotent operations: yes; non-idempotent: explain)
4. What their current state is (was the record saved? was the email sent?)

### Session expiry

If a session expires while a user is mid-flow, the flow must:
1. Preserve any input the user has not yet submitted
2. Redirect to re-authentication
3. Return the user to the point in the flow where they left off, with their data intact where possible

A flow that discards half-completed work when a session expires is a frustrating and avoidable failure.

### Partial completion

A flow that involves multiple server-side operations (write a record, send a notification, update a related resource) must account for partial failure. If the record writes but the notification fails, what does the user see? What is the recovery path? Is the operation retryable? Idempotency must be considered at every step where partial failure is possible.

---

## Feedback at Every Transition

The user must always know where they are and what is happening.

### Progress indication

For multi-step flows with a defined number of steps, show the current position. Not just a step counter — the user should understand what steps remain and roughly what each involves.

### Loading states begin immediately

The moment an action is initiated, the UI reflects that something is in progress. Do not wait for a timeout or a slow response to show a loading state. The delay between click and feedback must be imperceptible.

### Completion confirmation

Successful completion of a flow is confirmed explicitly. The user should not have to infer that something worked. The confirmation:
- States clearly what happened
- Summarizes the result (what was created, sent, or changed)
- Offers the natural next action

### Failure recovery keeps the user's context

When a step fails, the user is not returned to the beginning. They are shown the error at the step where the failure occurred, with their input preserved, and with a clear path to correct and retry.

---

## Edge Case Inventory

For every flow, systematically work through the following cases before considering the flow complete:

- What happens if a required external service is unavailable?
- What happens if the user submits the same action twice rapidly?
- What happens if the user navigates back using the browser's back button?
- What happens if the user closes the browser and reopens the URL?
- What happens if the user's data changes on the server while they are mid-flow?
- What happens if the user has already completed this flow and attempts it again?
- What happens if the user has insufficient permissions partway through?
- What happens if the data they entered is valid at step 2 but invalid by the time step 4 executes?

These are not hypotheticals — they are standard user behaviors. A flow that cannot answer all of them is not complete.

---

## Flow Consistency Across the Application

Flows within the same application share behavioral patterns. Users build a mental model of how the application works. Violating that mental model with an inconsistent flow introduces confusion.

- Confirmation dialogs use the same visual pattern.
- Error messages use the same placement and format.
- Loading states use the same indicator.
- Success confirmations use the same visual treatment.
- Step indicators use the same component.

When adding a new flow, review existing flows for the patterns already in use and match them unless there is a specific, documented reason to diverge.

---

## Security Considerations Within Flows

Any flow that handles sensitive operations must address:

- **CSRF protection** on state-changing requests.
- **Rate limiting** on flows that could be abused by repetition (submission, verification, retry).
- **Token expiry** on any time-limited link or code issued as part of the flow.
- **Invalidation** of tokens once used — a single-use token must not be reusable.
- **Authorization checks at every step**, not only at the entry point. Do not assume that reaching step 3 implies the user was authorized at step 1.
- **Sensitive data** is not persisted in the URL, browser history, or session beyond the point where it is needed.
