---
name: engineering
description: Guide architectural and implementation decisions across the Flask + SQLite3 + vanilla JS stack. Apply when choosing data structures, designing query patterns, structuring modules, evaluating tradeoffs between performance and extensibility, or orienting to an existing codebase before making changes.
---

# Engineering

## Stack Orientation Protocol

Before writing or modifying any code, read the existing codebase to understand what patterns are already in use. Do not introduce a new pattern when an existing one already handles the case. Consistency within the project outweighs marginal improvements from mixing approaches.

When orienting to an existing codebase, establish:

1. How Flask is initialized and configured — factory function, direct instantiation, or otherwise.
2. How database connections are managed — per-request, pooled, or global.
3. Where and how environment configuration is loaded.
4. How routes are organized — blueprints, a single file, or by domain.
5. How errors are handled — custom handlers, exceptions, or inline checks.
6. What conventions exist in the frontend — how JS files are structured, how forms submit, how the server and client exchange data.

Do not assume. Read, then act.

---

## Performance vs. Adaptability

The goal is never raw performance at all costs. The goal is decisions that are efficient enough to not create friction today and structured well enough to not become a wall tomorrow.

### The tradeoff framed correctly

Micro-optimized code that is tightly coupled to a specific data shape, a specific query structure, or a specific execution path is fast until requirements change — then it is expensive. Generic, fully abstracted code that handles every possible case is adaptable until it becomes indistinguishable magic that nobody can debug.

The correct position is: use straightforward, well-understood patterns with clean interfaces. Optimize only when a concrete performance problem is identified and measured.

### When to optimize

Optimize when:
- A measured bottleneck exists, not when one is suspected.
- The operation runs on every request, not occasionally.
- The data volume is known to be large or growing.

Do not optimize:
- For hypothetical scale.
- At the cost of readability.
- Before the feature is working correctly.

---

## Flask Patterns

### Application factory

Use the application factory pattern. It makes testing possible, configuration explicit, and avoids circular import issues.

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or DefaultConfig)
    register_blueprints(app)
    register_error_handlers(app)
    init_db(app)
    return app
```

### Blueprints for domain separation

Each domain owns a Blueprint. Blueprints are registered in the factory. A route defined in the users Blueprint does not know about the auth Blueprint's internals.

### Request lifecycle is not for business logic

`before_request`, `after_request`, and `teardown_request` hooks handle cross-cutting concerns: database connection setup and teardown, authentication checks, logging. They do not contain feature logic.

### Configuration is environment-driven

Secrets, database paths, mail server credentials, and environment flags come from environment variables or a `.env` file, never from committed code. A `config.py` maps those variables to typed, named constants with sensible defaults for development.

---

## SQLite3 Patterns

### Connection management

Use Flask's `g` object to hold the database connection per request. Open on first use, close on teardown.

```python
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

### Always use `sqlite3.Row`

Row factory set to `sqlite3.Row` allows column access by name, not by index. Code that accesses `row["email"]` is readable. Code that accesses `row[2]` is fragile.

### Parameterized queries only

No string formatting or concatenation to build SQL. Every dynamic value is a parameter.

```python
# Wrong
db.execute(f"SELECT * FROM users WHERE email = '{email}'")

# Right
db.execute("SELECT * FROM users WHERE email = ?", (email,))
```

### Schema lives in one place

The database schema is defined in a single `schema.sql` file. An `init_db` function applies it. Migrations, when needed, are numbered SQL files applied in order — not applied programmatically by scrambling the schema file.

### Query results are normalized before leaving the query layer

A query function returns a plain dict, a list of dicts, or `None`. It does not return a raw `sqlite3.Row` object. The rest of the application does not know about the database layer's return types.

---

## Data Structure Choices

### Use the simplest structure that is correct

A plain dict is appropriate for passing related values between functions. A class is appropriate when the data has behavior attached to it or when the structure is complex enough that a dict's keys need to be enforced. Do not use a class purely to group data.

### Lists vs. generators

Return a list when the caller needs random access, multiple passes, or a known count. Return a generator when the data is large and the caller processes it once sequentially. In practice, for this stack and expected data volumes, lists are almost always correct.

### Avoid deep nesting in data structures

A dict of dicts of lists of dicts is a signal that the data model needs to be flatter or that the responsibility for structuring it needs to move somewhere else.

---

## Frontend Engineering

### JavaScript is behavioral, HTML is structural, CSS is presentational

No logic in HTML. No styles in JavaScript unless the value is dynamic and cannot be expressed in CSS. No layout decisions in JavaScript when CSS can handle them.

### Fetch-based communication with the server

Forms that require partial updates, validations, or non-navigation submissions use `fetch`. Full-page forms that perform a simple action and redirect use standard HTML form submission. Do not reach for fetch just to avoid a page reload when a page reload is appropriate.

```js
async function submitForm(endpoint, payload) {
    const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    return response.json();
}
```

### Error handling is never silent

Every async operation has a failure path. Network errors, non-200 responses, and malformed data are handled explicitly — not swallowed or ignored.

### Progressive enhancement where applicable

Core functionality works without JavaScript where feasible. JavaScript enhances the experience — adds inline validation, prevents unnecessary page loads, enables dynamic UI — but the baseline is functional HTML and server-rendered responses.

---

## Extensibility Decisions

### Do not pre-abstract

Write the code for the problem at hand. Extract an abstraction when the same pattern appears in a second place. Extract it into a named, well-placed module when it appears in a third. Do not build a framework before you have a problem.

### Interfaces between layers are narrow

The route handler does not reach into the query layer directly. The service layer does not know about HTTP. The query layer does not know about business rules. Each layer communicates through a narrow, named interface. This is what makes individual layers replaceable.

### Configuration over hardcoding

Any value that might vary between environments, deployments, or feature flags belongs in configuration. Any value that defines application behavior rather than application code belongs in configuration. Names, thresholds, limits, and external endpoints are never literals scattered through the code.
