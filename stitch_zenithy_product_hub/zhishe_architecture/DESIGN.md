# Design System Documentation: Architectural Clarity

## 1. Overview & Creative North Star
### The Creative North Star: "The Precision Lens"
This design system is built to transform a high-density AI video analysis environment into a space of "Architectural Clarity." Unlike generic SaaS platforms that rely on cluttered grids and heavy borders, this system treats the UI as a physical workspace—a digital workbench where information is layered, not just placed.

The "Precision Lens" philosophy dictates that every element must serve the user's focus. We move beyond the "template" look by utilizing intentional asymmetry, expansive breathing room, and a hierarchy driven by tonal depth rather than structural lines. The atmosphere is serious and trustworthy, yet carries a creative soul through sophisticated glass textures and editorial typography.

---

## 2. Color & Tonal Architecture
The palette is rooted in professional neutrals to ensure the AI-generated video content remains the hero. The blue-cyan accent (`primary: #0058bc`) acts as a surgical tool—used only for high-priority actions and state indications.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define major sections. Layout boundaries must be achieved through:
- **Background Shifts:** Using `surface-container-low` against a `surface` background.
- **Tonal Transitions:** Defining the workspace through subtle color blocks rather than wireframe lines.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked sheets. Depth is created by "nesting" tokens:
- **Level 0 (Base):** `background (#f8f9ff)` for the overall canvas.
- **Level 1 (Sections):** `surface_container_low (#eff4ff)` for large sidebars or secondary panels.
- **Level 2 (Active Workspaces):** `surface_container_lowest (#ffffff)` for the primary video feed or analysis cards to provide maximum "pop."
- **Level 3 (Overlays):** `surface_container_highest (#d5e3fc)` for contextual menus or floating inspectors.

### The "Glass & Gradient" Rule
To elevate the "AI" aesthetic, use Glassmorphism for floating UI elements. Use semi-transparent `surface` colors with a `backdrop-blur` (minimum 20px). Main CTAs should utilize a subtle linear gradient from `primary (#0058bc)` to `primary_container (#0070eb)` at a 135-degree angle to provide a "lit from within" professional polish.

---

## 3. Typography: Editorial Authority
The typography system pairs the geometric precision of **Manrope** for high-level branding and headings with the functional clarity of **Inter** for data-heavy analysis.

- **Display & Headlines (Manrope):** Use `display-lg` and `headline-md` to create an "Editorial" feel. Bold weights should be used sparingly to anchor the page. The architectural nature of Manrope reinforces the sense of a professional tool.
- **Body & Labels (Inter):** All analytical data, timestamps, and tooltips use Inter. This ensures high legibility at small sizes (e.g., `label-sm: 0.6875rem`).
- **Identity through Scale:** We use high-contrast scales. A `display-lg` headline next to a `body-sm` metadata label creates a sophisticated, modern tension that feels custom-designed rather than "bootstrapped."

---

## 4. Elevation & Depth
In this system, depth is a functional tool for hierarchy, not a decorative choice.

### The Layering Principle
Achieve lift through "Tonal Layering." Instead of adding a shadow to every card, place a `surface_container_lowest` card on a `surface_container_low` background. This creates a soft, natural edge that is easier on the eyes during long analysis sessions.

### Ambient Shadows
When a component must "float" (e.g., a modal or a floating action bar), use **Ambient Shadows**:
- **Blur:** 32px to 64px.
- **Opacity:** 4% to 8%.
- **Color:** Use a tinted version of `on_surface (#0d1c2e)` rather than pure black to ensure the shadow feels like a natural part of the environment.

### The "Ghost Border" Fallback
If accessibility requirements demand a container boundary, use a **Ghost Border**:
- **Token:** `outline_variant (#c1c6d7)` at **20% opacity**.
- **Rule:** Never use 100% opaque borders for card containers.

---

## 5. Components
### High-Precision Cards
Cards should not have visible borders. Use the `xl (0.75rem)` or `lg (0.5rem)` roundedness scale. Content inside cards must follow a strict vertical rhythm using the spacing scale—forbid the use of horizontal divider lines. Use white space to separate the header from the body.

### Workflow Step Indicators
These are the "spine" of the AI analysis process.
- **Active State:** `primary` background with `on_primary` text.
- **Inactive State:** `surface_container_high` background.
- **Pathways:** Connect steps with a 2px `surface_variant` dashed line, never a solid dark line.

### Buttons & Interaction
- **Primary:** Gradient-filled (`primary` to `primary_container`) with `xl` rounding.
- **Secondary:** Transparent background with a `Ghost Border` and `primary` text.
- **Glass Action:** For overlaying on video content, use a `surface` background at 60% opacity with a heavy backdrop blur.

### Input Fields
Inputs should feel "architectural." Use `surface_container_lowest` with a subtle `outline_variant` (20% opacity). On focus, transition the border to `primary` and add a subtle 4px glow using the `primary` color at 10% opacity.

---

## 6. Do's and Don'ts

### Do:
- **Embrace Asymmetry:** Align primary analysis tools to a 12-column grid, but allow metadata inspectors to sit in offset, "floating" panels.
- **Use Tonal Nesting:** Always check if you can separate two areas with a background color shift before reaching for a border.
- **Respect the Content:** Video analysis is visually noisy. Keep the UI "quiet" so the AI detections (bounding boxes, heatmaps) are the most vibrant elements.

### Don't:
- **Don't use pure black (#000000):** Use `on_surface (#0d1c2e)` for all text and iconography to maintain a high-end, "Slate" feel.
- **Don't use standard drop shadows:** Avoid the "dirty" look of grey, high-opacity shadows.
- **Don't use Dividers:** Forbid the use of `<hr>` or 1px lines to separate list items. Use a 4px or 8px vertical gap instead.
- **Don't overcrowd:** If a screen feels full, increase the page height rather than shrinking the components. Architectural clarity requires room to breathe.