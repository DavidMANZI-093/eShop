---
name: ui-ux
description: Design and implement interfaces that are visually clean, stable, accessible, and grounded in Human-Computer Interaction principles. Apply when building any UI component, page layout, interaction pattern, or visual system. The standard is a product that feels considered, responsive to user needs, and effortless to use — built entirely with vanilla HTML, CSS, and JavaScript.
---

# UI/UX

## Design Philosophy

An interface is not decoration applied over functionality. It is the product. Every visual decision — spacing, typography, color, motion, hierarchy — is a communication decision. Users should never have to think about the interface. They should be thinking about their task.

The governing standard is clarity under pressure. An interface that works when a user is calm and focused is a baseline. An interface that works when a user is hurried, distracted, or uncertain is the actual target.

---

## Visual Design Principles

### Hierarchy communicates priority

Every screen has one primary action. One. Secondary actions are visually subordinate. Tertiary actions are accessible but not visible. If everything on a screen appears equally important, nothing is important, and the user stops to figure out what to do.

Typography, size, weight, color, and spacing are the tools for establishing hierarchy — not icons, not labels, not decorative elements.

### Spacing is load-bearing

Adequate whitespace reduces cognitive load. Elements that are visually grouped are logically grouped. Cramped layouts signal disorder even when the underlying functionality is correct. When in doubt, add space.

Use a spacing scale, not arbitrary values. Define a base unit (8px is conventional) and express all spacing as multiples of it. Apply this scale through CSS custom properties.

```css
:root {
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 16px;
    --space-4: 24px;
    --space-5: 32px;
    --space-6: 48px;
    --space-7: 64px;
}
```

### Color serves function, not aesthetics alone

Color communicates state: default, hover, active, disabled, error, success, warning. These states must be distinguishable without relying on color alone (for accessibility). Every color in the interface is defined as a CSS custom property. No color values appear as literals in component styles.

Define a minimal palette: a neutral scale, one primary action color, and semantic colors for state.

```css
:root {
    --color-bg: #ffffff;
    --color-surface: #f5f5f4;
    --color-border: #e2e2e0;
    --color-text-primary: #1a1a18;
    --color-text-secondary: #6b6b68;
    --color-text-disabled: #a8a8a4;
    --color-accent: #2563eb;
    --color-accent-hover: #1d4ed8;
    --color-error: #dc2626;
    --color-success: #16a34a;
    --color-warning: #d97706;
}
```

### Typography is a system

Define a type scale and use it. Do not size text arbitrarily. Font choices reflect the product's register — not generic defaults.

```css
:root {
    --font-body: 'Your chosen body font', sans-serif;
    --font-display: 'Your chosen display font', sans-serif;
    --text-xs: 0.75rem;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
    --text-xl: 1.25rem;
    --text-2xl: 1.5rem;
    --text-3xl: 1.875rem;
}
```

Line height for body text: 1.5 to 1.6. Line height for headings: 1.1 to 1.3. Measure (line length) for body text: 60 to 75 characters.

---

## HCI Principles Applied

### Feedback for every action

A user action without feedback is a black box. The user does not know whether the action registered, succeeded, or failed. Every interactive element must communicate its state:

- **Buttons**: visual change on hover and active. A loading state when an async operation is pending. A disabled state with a visual reason when the action is unavailable.
- **Forms**: inline validation feedback as close to the field as possible, not summarized at the top. Error messages name the problem and what to do about it — not `Invalid input`, but `Email must include an @ symbol`.
- **Async operations**: loading indicators begin immediately, not after a delay. Completion and failure states are clearly communicated.
- **Destructive actions**: confirmation before execution. The confirmation must describe what will be destroyed. "Are you sure?" is not adequate — "Delete this account and all its data permanently?" is.

### Affordance and discoverability

Interactive elements must look interactive. Clickable elements have a cursor change. Inputs have visible boundaries. Hover states exist on anything that responds to interaction.

Nothing important should require discovery. Features hidden behind hover states, right-clicks, or invisible boundaries are invisible to most users.

### Error prevention over error recovery

The best error message is the one that never appears. Disable actions that would result in errors. Show constraints before a user violates them. Validate input as the user types, not only on submission. Prevent form submission of clearly invalid states.

When errors do occur, the message is:
1. Visible (not buried, not a console warning)
2. Specific (names the exact field and exact problem)
3. Constructive (tells the user what the valid input looks like)
4. Non-punishing (the user's other input is preserved)

### Recognition over recall

Do not make the user remember information from a previous screen to complete the current one. Surface the relevant context. Labels remain visible after a field is filled. The current state of a multi-step process is visible throughout.

### Consistency is trust

Elements that look the same behave the same. Buttons styled the same way are clicked for the same type of action. The same interaction pattern is used for the same type of task throughout the application. Inconsistency creates uncertainty, and uncertainty erodes confidence.

---

## Stability

An interface is stable when the layout does not shift as content loads, updates, or changes state.

### Reserve space for dynamic content

Elements that appear asynchronously should have their space reserved. Skeleton states or fixed dimensions prevent layout shift that disorienta the user's eye.

### Form and input stability

Fields do not change size when validation messages appear. The validation message occupies reserved space below the field, whether it is populated or not. Error states do not cause the form to reflow.

### Transition discipline

State changes that happen instantly feel abrupt. Transitions smooth the change — but only when the duration is short enough not to feel like waiting. 150ms to 250ms for most UI transitions. 300ms maximum for larger elements entering the viewport. Nothing beyond that for functional UI.

```css
.button {
    transition: background-color 150ms ease, box-shadow 150ms ease;
}
```

Motion is not decoration. Every animated property must have a reason.

---

## Accessibility Standards

Accessibility is not a compliance checklist appended at the end. It is a dimension of every design decision from the start.

### Keyboard navigation

Every interactive element is reachable and operable by keyboard. Tab order follows visual reading order. Focus states are visible — not suppressed with `outline: none` without a replacement. Modals trap focus while open. Focus returns to the trigger element when a modal closes.

### Color contrast

Text on background: minimum 4.5:1 contrast ratio for body text, 3:1 for large text (18px+ bold or 24px+). Do not rely solely on color to convey state. An error field outlined in red must also have an icon or text label indicating the error.

### Semantic HTML

Use the correct element for the purpose:
- `<button>` for actions, `<a>` for navigation.
- `<label>` associated with every form input via `for`/`id`.
- `<h1>` through `<h6>` for heading hierarchy, not for visual sizing.
- `<nav>` for navigation regions, `<main>` for primary content, `<aside>` for secondary content.
- `<ul>` and `<ol>` for lists, not for layout.

ARIA attributes supplement semantic HTML when native semantics are insufficient. They do not replace it.

### Images and icons

Every image has meaningful `alt` text, or `alt=""` if it is purely decorative. Icons that convey meaning have an accessible label. Icons that duplicate adjacent text are hidden from screen readers with `aria-hidden="true"`.

---

## Component Standards

### Forms

- Visible label on every field. Placeholder text is not a label.
- Required fields are marked explicitly.
- Submission triggers a loading state immediately.
- On success: the form either clears, shows a confirmation, or navigates — not all three ambiguously.
- On failure: the fields are preserved, the error is shown inline, the focus moves to the first invalid field.

### Buttons

Three visual tiers: primary (one per screen), secondary, ghost/tertiary. Destructive actions have their own visual treatment (typically red, after confirmation). Disabled state is visually distinct and does not accept interaction.

### Modals and dialogs

Used only for information or actions that require the user's full attention and cannot be completed in-context. Not used for confirmations that could be inline. Always closable with Escape. Always have a visible close action. Background is dimmed and non-interactive.

### Navigation

The current location is always indicated visually in the navigation. Navigation structure is consistent across pages. Navigation items are links, not JavaScript-navigated buttons, so they support standard browser behavior (open in new tab, browser history).

### Empty states

Every list, table, or collection view has an empty state design. Empty states explain why the view is empty and, where appropriate, offer a direct action to populate it. A blank area is not an acceptable empty state.

---

## What This Stack Prohibits

- No CSS resets or utility frameworks. The visual system is built from scratch using custom properties and purposeful rules.
- No inline styles except for values that are unavoidably dynamic (set by JavaScript at runtime).
- No JavaScript-driven layout. CSS handles layout. JavaScript handles behavior.
- No design decisions made in JavaScript that belong in CSS (`element.style.color = 'red'` for a static state is a stylesheet problem, not a scripting problem).
