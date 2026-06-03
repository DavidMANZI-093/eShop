---
name: code-style
description: Enforce clean, self-documenting code structure across the entire codebase. Apply when writing new modules, refactoring existing code, reviewing structure, naming identifiers, or organizing files. The standard is zero cognitive overhead for any reader approaching the code cold.
---

# Code Style

## Core Principle

Code is read far more than it is written. Every naming and structural decision must serve the next reader, whether that is a collaborator, an agent, or the author returning after two weeks. The standard is not "this works" but "this is immediately obvious."

Comments are a failure mode, not a documentation strategy. If a block of code requires a comment to explain what it does, the code needs to be rewritten until it does not. The only acceptable exception is a comment explaining *why* a non-obvious external constraint exists — a platform quirk, a deliberate workaround for a third-party limitation, or a regulatory requirement. Even then, a single sentence is the ceiling.

---

## File and Module Organization

### One concern per file

Each file owns exactly one responsibility. A file handling database access for users does not also define routes. A file defining a reusable UI component does not also manage application state. When a file starts doing two things, split it.

### Directory structure reflects domain, not file type

Do not organize by `models/`, `views/`, `controllers/` as a flat top-level scheme when the project grows beyond a handful of files. Organize by domain first, then by role within that domain.

```
project/
  auth/
    routes.py
    service.py
    validators.py
  users/
    routes.py
    service.py
    queries.py
  static/
    css/
      base.css
      components/
        form.css
        modal.css
    js/
      auth.js
      users.js
  templates/
    auth/
      login.html
      reset.html
    users/
      profile.html
```

### Entry points stay thin

`app.py` or equivalent entry points register things. They do not contain logic. A reader opening the entry point should understand the shape of the application in under thirty seconds.

---

## Naming

### Be precise, not verbose

A name should say exactly what something is or does — no more, no less. Avoid filler words that add length without adding meaning.

| Avoid | Prefer |
|---|---|
| `get_all_user_data_from_database` | `fetch_users` |
| `process_and_handle_the_request` | `handle_request` |
| `is_the_user_currently_logged_in` | `is_authenticated` |
| `temp`, `data`, `result`, `obj` | names that say what the value represents |
| `helper.py`, `utils.py` | `formatting.py`, `validators.py`, `transforms.py` |

### Naming by role

- **Functions and methods**: verb phrases that describe what they do. `send_verification_email`, `validate_form`, `build_query`.
- **Booleans**: `is_`, `has_`, `can_`, `should_` prefixes. `is_verified`, `has_permission`, `can_submit`.
- **Classes**: noun phrases that name the entity. `UserSession`, `EmailQueue`, `QueryBuilder`.
- **Constants**: uppercase snake case. `MAX_RETRIES`, `TOKEN_EXPIRY_SECONDS`.
- **Files**: lowercase snake case throughout. `user_queries.py`, `session_store.js`.

### Do not abbreviate unless universal

`req`, `res`, `db`, `id` are universally understood in their contexts. `usr`, `msg`, `cfg`, `tmp` are not. When in doubt, spell it out.

---

## Function Design

### Functions do one thing

A function that validates input, writes to the database, and sends an email is three functions. Each should be callable independently, testable independently, and understandable independently.

### Keep functions short

Not as a rule for its own sake, but because a function that requires scrolling is usually doing too much. When a function grows long, ask what can be extracted into a named sub-function. The name of the sub-function is part of the documentation.

### Argument discipline

Avoid positional argument ambiguity. A function call like `create_user("Alice", True, False, 3)` is not readable. When a function takes more than two or three arguments, prefer a structured input or keyword arguments.

Functions should not accept arguments they silently ignore. Do not pass a full object into a function that only uses one field of it.

### Return values are honest

A function either returns a value or it does not. A function that sometimes returns a value and sometimes returns `None` silently is a source of bugs. Make the contract explicit. If absence is a valid return, the caller must handle it explicitly.

---

## Python-Specific Standards

### Flask route handlers are thin

Route handlers in Flask receive a request, delegate to a service function, and return a response. They do not contain business logic. Query construction, data transformation, and decision making belong in service or query modules.

```python
@app.route("/users/<int:user_id>")
def get_user(user_id):
    user = user_service.fetch_by_id(user_id)
    if not user:
        return not_found("User not found")
    return jsonify(user)
```

### Imports are ordered and intentional

Standard library imports first, third-party second, local imports third, each group separated by a blank line. No wildcard imports. No unused imports.

### No mutable default arguments

```python
# Wrong
def append_item(item, target=[]):
    target.append(item)

# Right
def append_item(item, target=None):
    if target is None:
        target = []
    target.append(item)
```

### SQLite3 queries live in query modules

Raw SQL does not appear in route handlers or service functions. Every database interaction is a named function in a `queries.py` file within its domain. The function name describes what the query retrieves or modifies.

```python
# users/queries.py
def fetch_by_email(db, email):
    row = db.execute(
        "SELECT id, name, email, is_verified FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    return dict(row) if row else None
```

---

## JavaScript-Specific Standards

### No inline event handlers in HTML

All behavior lives in `.js` files. HTML is structure only.

### Functions over anonymous callbacks where the operation is non-trivial

```js
// Acceptable for trivial cases
button.addEventListener("click", () => modal.close());

// Required when the logic has a name
button.addEventListener("click", submitLoginForm);
```

### No global state unless unavoidable

State scoped to a module or a closure is preferable to state hanging on `window`. When global state is required, it is named explicitly and documented with a single-line `why`.

### DOM queries are cached

Do not query the DOM inside loops or event handlers that fire repeatedly. Query once, store the reference.

---

## CSS-Specific Standards

### No inline styles

All styles live in `.css` files. The only acceptable exception is a dynamic value that cannot be expressed any other way, applied via JavaScript at runtime.

### CSS custom properties for all repeated values

Colors, spacing scales, font sizes, and border radii are defined as custom properties on `:root` and referenced everywhere they are used. No magic numbers scattered through the stylesheet.

### Class names describe what an element is, not how it looks

`.card`, `.nav-link`, `.form-field` — not `.red-box`, `.padded-container`, `.bold-text`.

### Flat selector hierarchy

Nesting beyond two levels is a signal that structure should be flatter. Deep nesting creates specificity problems and makes styles hard to override.

---

## What Never Appears in This Codebase

- Commented-out code. If it is not running, it is deleted. Version control holds history.
- TODO comments left in committed code. Either it is done or it is a tracked issue.
- Dead code paths. Functions that are not called are removed.
- Redundant type-checking that duplicates what the language or a validator already enforces.
- Logic duplicated across files. If the same logic appears twice, it belongs in one place with a name.
