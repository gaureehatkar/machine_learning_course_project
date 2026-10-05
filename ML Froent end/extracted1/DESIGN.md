---
name: Rigorous Algorithmic Credit Engine
colors:
  surface: '#f7f9ff'
  surface-dim: '#c1ddfb'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#edf4ff'
  surface-container: '#e3efff'
  surface-container-high: '#d8eaff'
  surface-container-highest: '#cee5ff'
  on-surface: '#001d32'
  on-surface-variant: '#3d4949'
  inverse-surface: '#16334a'
  inverse-on-surface: '#e8f2ff'
  outline: '#6d7979'
  outline-variant: '#bcc9c9'
  surface-tint: '#00696b'
  primary: '#006768'
  on-primary: '#ffffff'
  primary-container: '#008284'
  on-primary-container: '#f3fffe'
  inverse-primary: '#69d7d9'
  secondary: '#49607c'
  on-secondary: '#ffffff'
  secondary-container: '#c7dfff'
  on-secondary-container: '#4b637e'
  tertiary: '#2a5ba6'
  on-tertiary: '#ffffff'
  tertiary-container: '#4774c1'
  on-tertiary-container: '#fefcff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#87f4f5'
  primary-fixed-dim: '#69d7d9'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#004f51'
  secondary-fixed: '#d1e4ff'
  secondary-fixed-dim: '#b0c9e8'
  on-secondary-fixed: '#011d35'
  on-secondary-fixed-variant: '#314863'
  tertiary-fixed: '#d7e2ff'
  tertiary-fixed-dim: '#acc7ff'
  on-tertiary-fixed: '#001a40'
  on-tertiary-fixed-variant: '#054590'
  background: '#f7f9ff'
  on-background: '#001d32'
  surface-variant: '#cee5ff'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 2.25rem
    fontWeight: '700'
    lineHeight: 2.75rem
    letterSpacing: -0.025em
  headline-lg:
    fontFamily: Inter
    fontSize: 1.75rem
    fontWeight: '600'
    lineHeight: 2.25rem
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 1.25rem
    fontWeight: '600'
    lineHeight: 1.75rem
    letterSpacing: -0.015em
  body-lg:
    fontFamily: Inter
    fontSize: 1rem
    fontWeight: '400'
    lineHeight: 1.5rem
  body-md:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '400'
    lineHeight: 1.375rem
  body-sm:
    fontFamily: Inter
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.125rem
  metric-display:
    fontFamily: Inter
    fontSize: 2rem
    fontWeight: '700'
    lineHeight: 2.25rem
    letterSpacing: -0.03em
  metric-unit:
    fontFamily: Inter
    fontSize: 0.875rem
    fontWeight: '500'
    lineHeight: 1rem
  label-uppercase:
    fontFamily: Inter
    fontSize: 0.6875rem
    fontWeight: '700'
    lineHeight: 1rem
    letterSpacing: 0.08em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 0.8125rem
    fontWeight: '400'
    lineHeight: 1.25rem
  code-inspector:
    fontFamily: JetBrains Mono
    fontSize: 0.75rem
    fontWeight: '400'
    lineHeight: 1.2rem
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  margin: 2rem
  margin-sm: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style
The design system delivers an institutional, high-integrity decisioning environment tailored for evaluating thin-file, volatile earnings profiles in the gig economy. The design aesthetic is clinical, transparent, and authoritative—borrowing from medical diagnostic tooling, safety-critical telemetry, and high-tier algorithmic underwriting consoles. 

Every visual decision prioritizes evidentiary auditability: models must not appear as "black boxes," but rather as structured logic trees backed by concrete transactional signals. Visual noise is stripped away in favor of high-contrast micro-typography, explicit status cues that never rely solely on hue, and structured multi-layered panels. The emotional resonance is calm, uncompromisingly fair, and scientifically precise, reassuring underwriters, regulatory auditors, and platform operations teams.

## Colors
The palette balances institutional gravitas with functional semantic zoning:

- **Foundation**:
  - `page-bg`: `#F4F8FB` (cool, sterile off-white)
  - `surface-card`: `#FFFFFF`
  - `border-subtle`: `#D9E2EC` (slate-200 equivalent)
  - `text-primary`: `#102A43` (deep ink navy for optimal legibility)
  - `text-secondary`: `#486581`
  - `text-muted`: `#627D98`

- **Interactive Primary**:
  - `action-primary`: `#159A9C` (deep clinical teal)
  - `action-primary-hover`: `#117B7D`
  - `action-primary-contrast`: `#FFFFFF`

- **Domain Layer Accents**:
  - `domain-risk`: `#2E5EAA` (surface tint: `#F0F4FA`, border: `#BCD0EE`)
  - `domain-evidence`: `#B9770E` (surface tint: `#FDF8F0`, border: `#F4DCB1`)
  - `domain-policy`: `#6B4C9A` (surface tint: `#F6F3FA`, border: `#DACFE7`)

- **Decision Outcomes (Strict Icon + Label Requirement)**:
  - `status-approve`: `#1B7F37` (contrast-safe emerald, dark text pairing `#0A3615`)
  - `status-review`: `#946200` (deep ochre amber, dark text pairing `#412900`)
  - `status-decline`: `#CF222E` (coral crimson, dark text pairing `#5C0B11`)

- **Regulatory Banner**:
  - Background `#FFF8E6`, border `#F0C000`, text `#533F03` for synthetic prototype notices.

## Typography
Typographic clarity anchors the credibility of decision audits. We employ **Inter** for all narrative and structural interfaces, configured with OpenType features `tnum` (tabular numbers) and `cv05` activated system-wide to ensure financial amounts and ratios align vertically across tabular scans.

**JetBrains Mono** is reserved strictly for algorithmic rules, raw transaction telemetry, payload inspectors, and confidence score thresholds. 

All category badges, table headers, and structural domain tags utilize `label-uppercase` with explicit tracking (`0.08em`) to enforce distinct perceptual separation between interface metadata and dynamic underwriter data.

## Layout & Spacing
The layout adheres to an asymmetric workspace model split into:
1. **Primary Evaluation Column (65%)**: Contains input profiles, gate flow pipelines, and decision rationales.
2. **Reactive Evidence Rail (35%)**: Persistent inspector containing income stream telemetry, platform stability indexes, and code/policy trace payloads.

On viewports below 1024px, the layout reflows into a single-column stacked format with the Evidence Rail collapsable into a bottom sheet drawer. Grid alignment relies on a 4px baseline sub-grid with structural standard spacing tokens (`space-sm` to `space-xl`) preserving strict alignment between disparate data columns.

## Elevation & Depth
Depth is strictly structured to denote interactive and analytical hierarchy, rejecting arbitrary drop shadows in favor of crisp architectural boundaries:

- **Flat/Canvas**: `#F4F8FB` serves as the neutral bedrock.
- **Card Tier**: Pure white (`#FFFFFF`) with a mandatory `1px solid #D9E2EC` stroke. Elevation is soft and diffused: `box-shadow: 0 1px 3px rgba(16, 42, 67, 0.05), 0 1px 2px rgba(16, 42, 67, 0.03)`.
- **Raised Interactive Panes & Live Reactive Cards**: Retain the `1px` border, paired with an elevation lift on focus/hover: `box-shadow: 0 4px 6px -1px rgba(16, 42, 67, 0.07), 0 2px 4px -1px rgba(16, 42, 67, 0.04)`.
- **Modal / Technical Audit Drawers**: Elevated to `box-shadow: -4px 0 24px rgba(16, 42, 67, 0.12)` over a solid `rgba(16, 42, 67, 0.4)` backdrop blur overlay (`4px`).

## Shapes
Base interactive surfaces, primary cards, and review containers utilize an exact radius of **12px** (`rounded-lg`), delivering a tailored, contemporary institutional feel that softens analytical rigidity without losing structural discipline. 

Internal micro-elements such as form fields, rule pill indicators, data tags, and code blocks adopt a tighter radius of **6px** (`rounded-sm`). Pills for verification statuses use fully rounded profiles (`9999px`) to distinguish categorical metadata from analytical data boxes.

## Components

### 1. Decision Status Badges
- **Requirement**: Must never be color alone. Always composed of: [Icon] + [Bold Label] + [Score/Threshold].
- **Approved**: Surface `#EAF5EC`, Border `#3FB950`, Icon `check-circle`, Text `#0A3615`.
- **Review**: Surface `#FDF8E8`, Border `#E3B341`, Icon `alert-triangle`, Text `#412900`.
- **Declined**: Surface `#FDF0EF`, Border `#F85149`, Icon `x-octagon`, Text `#5C0B11`.

### 2. Domain Layer Cards
Each domain card utilizes a 3px vertical accent border on its left edge matching its domain token:
- **Risk Metrics Card**: Left border `#2E5EAA`, surface tint `#FAFCFF`.
- **Evidence & Stability Card**: Left border `#B9770E`, confidence progress bars styled in warm ochre.
- **Policy Enforcement Card**: Left border `#6B4C9A`, monospace rule ID tokens.

### 3. Gate Flow Indicators
Linear stepping nodes showing algorithm progression (e.g., Identity Check -> Platform Income Gate -> Volatility Stress -> Final Policy).
- **Passed Gate**: Filled `#159A9C` ring with solid check icon.
- **Blocked/Failed Gate**: Outlined `#CF222E` ring with solid cross icon and error tag.
- **Pending Evaluation**: Dashed `#D9E2EC` ring.

### 4. Interactive & Form Controls
- **Segmented History Controller**: `#E2E8F0` pill track, active segment rendered in `#FFFFFF` with `box-shadow: 0 1px 2px rgba(0,0,0,0.08)` and `#102A43` bold text.
- **Inputs**: 1px `#CBD5E1` border, `#FFFFFF` surface. Active focus rings: `2px solid #159A9C` with 2px offset. Monospace support for routing, earnings, and API keys.

### 5. Persistent Research Prototype Notice
Fixed top banner with a 1px border. Styled with `#FFF8E6` background, `#F0C000` border, `#533F03` text, displaying a prominent `beaker` icon and tracking text: `NOTICE: SYNTHETIC RESEARCH DATA — NOT FOR REAL-WORLD SOLVENCY EXECUTION`.

### 6. Technical Audit Drawer
Slides from right (width: 480px) on monospace inspector triggers. Background `#0B1A28` (deep code navy), syntax highlight colors matching Risk (`#6FA4F8`), Evidence (`#F5BA58`), and Policy (`#B89CE0`) to trace algorithmic execution line-by-line.