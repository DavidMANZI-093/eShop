---
name: planner
description: Collect thorough specifications for new features and produce a clear, sequenced implementation plan before any code is written. Apply at the start of every new feature, regardless of perceived size. A feature that seems small often touches more than expected. A plan that seems unnecessary is the one that prevents the most rework.
---

# Planner

## Purpose

Planning is not overhead. It is the work that makes implementation faster, more predictable, and less likely to require undoing. An agent that starts coding before understanding the full scope of a feature will produce code that solves the surface problem while creating subsurface problems.

This skill governs how features are scoped, detailed, and sequenced. No implementation begins until the plan produced by this process is complete.

---

## Feature Intake

When a new feature is described, the first step is to ask enough questions to understand it completely. The description given is always a starting point, not a specification.

Work through the following dimensions for every feature. Some will be brief. None should be skipped.

### What the feature does

Describe the feature in one sentence from the user's perspective. If this sentence cannot be written without ambiguity, the feature is not yet understood.

Then describe: what does the user see, what can they do, and what changes as a result?

### Who uses it

Is this feature for all users, a subset of users, or only authenticated users? Are there permission levels that affect what different users can see or do within this feature?

### Where it lives in the application

What existing pages or sections does this feature connect to? Is it a new page, a new section within an existing page, or a new capability on an existing element? Does it introduce new navigation?

### What it depends on

What existing data does it read? What new data does it create or modify? What other features must be in place before this one can function? Are there any external dependencies (email sending, file storage, third-party data)?

### What the server must do

List every new or modified endpoint required. For each endpoint:
- HTTP method and path
- What input it accepts
- What it does with that input
- What it returns on success
- What it returns on each failure case
- What authentication and authorization it requires

### What the database must change

List every new table, column, index, or constraint required. For each:
- Name and type
- Whether it is nullable
- Whether it has a default
- What it relates to (foreign key relationships)
- Whether any existing data requires migration

### What the frontend must do

List every new page, component, or interaction required. For each:
- What data it displays and where that data comes from
- What actions are available and what they trigger
- What states it must handle (loading, empty, error, populated)
- How it behaves on mobile and constrained viewports
- Any validation that must happen on the client side

### What flows this feature introduces or modifies

Does this feature introduce a multi-step user journey? Does it modify an existing one? If so, a complete flow design (per the FLOWS skill) is part of the plan before implementation.

### What can go wrong

List every failure case: validation errors, missing data, permission violations, external service failures, concurrent access issues. Each failure case has a defined user-facing response.

### What this feature does not include

State explicitly what is out of scope for this iteration. This prevents scope from expanding during implementation and makes the boundary of the feature clear to any agent executing it.

---

## Plan Structure

Once intake is complete, produce a plan with the following structure.

### Summary

One paragraph: what this feature is, who it is for, and what it achieves. Written as if for someone who has not read the intake.

### Preconditions

List everything that must be true before implementation begins:
- Schema changes that must land first
- Other features that must be complete
- Configuration or environment requirements
- Design decisions that are still open (if any — open decisions block implementation until resolved)

### Implementation sequence

Break the feature into discrete, ordered tasks. Each task:
- Is small enough to be completed in a single working session
- Can be committed as one or more atomic commits upon completion
- Has a clear definition of done
- Is ordered such that no task depends on a task that comes later in the list

A task is not "implement the user profile page." A task is "add the `bio` column to the `users` table and update the schema file" or "render the profile page with static data from the session." Granularity prevents ambiguity.

### Data model changes

List all schema changes with the exact SQL required to implement them. If data migration is required, it is a separate task with its own SQL.

### API contract

For each new or modified endpoint, define the contract completely:

```
POST /users/profile/update
Auth: required
Body: { bio: string (max 500 chars), display_name: string (max 80 chars) }
Success: 200 { updated: true }
Validation error: 400 { field: string, message: string }
Unauthorized: 401
```

### Frontend requirements

For each new page or component, specify:
- The route or location
- The data it requires and how it fetches it
- Every state and what triggers each state
- Interaction behaviors
- Validation rules

### Testing checkpoints

For each task in the implementation sequence, define what must be manually verified before moving to the next task. These are not automated tests — they are the minimum verification that the completed task works as specified.

---

## Scope Control

### The single-iteration rule

A plan covers one iteration. Features that would benefit from being shipped incrementally are split into separate plans, each delivering value on its own. A plan that begins with the intent to ship in three weeks is a plan that will never be complete.

### Deferred scope is tracked, not forgotten

When a decision is made to exclude something from the current iteration, it is recorded in a "deferred" section at the end of the plan. This prevents the exclusion from being treated as a permanent decision while also preventing it from creeping into the current iteration.

### No plan is approved with open design questions

An open design question is a question about what the feature should do that has not been answered. Open questions about *how* to implement something are acceptable — they are engineering decisions. Open questions about *what* the feature does block the plan until answered. Proceeding with an open design question produces code that will likely need to be changed once the question is resolved.

---

## Revision Protocol

A plan may need to be revised when implementation reveals something the plan did not account for. When this happens:

1. Stop implementation.
2. Document what was discovered.
3. Revise the plan to account for it.
4. Resume implementation from the revised plan.

Do not continue implementing against a plan that is known to be incorrect. The rework cost of implementing incorrectly is always higher than the cost of pausing to revise the plan.
