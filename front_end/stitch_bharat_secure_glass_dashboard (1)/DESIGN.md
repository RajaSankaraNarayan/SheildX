---
name: Bharat Secure Sentinel
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394e'
  surface-container-lowest: '#060d20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3e'
  surface-container-highest: '#2d3449'
  on-surface: '#dbe2fd'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dbe2fd'
  inverse-on-surface: '#283044'
  outline: '#8c909f'
  outline-variant: '#424753'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#ddb8ff'
  on-secondary: '#490080'
  secondary-container: '#6f00be'
  on-secondary-container: '#d6aaff'
  tertiary: '#5ddac7'
  on-tertiary: '#003731'
  tertiary-container: '#00a392'
  on-tertiary-container: '#00302a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004495'
  secondary-fixed: '#f0dbff'
  secondary-fixed-dim: '#ddb8ff'
  on-secondary-fixed: '#2c0051'
  on-secondary-fixed-variant: '#6800b3'
  tertiary-fixed: '#7cf7e3'
  tertiary-fixed-dim: '#5ddac7'
  on-tertiary-fixed: '#00201c'
  on-tertiary-fixed-variant: '#005047'
  background: '#0b1326'
  on-background: '#dbe2fd'
  surface-variant: '#2d3449'
  surface-deep: '#0b1326'
  input-bg: '#1e293b'
  glass-stroke: rgba(255, 255, 255, 0.1)
  neon-teal: '#00ffd9'
  neon-purple: '#a855f7'
  error-alert: '#ffb4ab'
typography:
  display-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '700'
    letterSpacing: -0.05em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-md:
    fontFamily: Outfit
    fontSize: 20px
    fontWeight: '600'
  numeric-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '700'
  numeric-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '700'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    letterSpacing: 0.1em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  gutter: 20px
  container-max: 1200px
---

## Brand & Style
Bharat Secure Sentinel is a high-assurance fintech identity that blends traditional banking stability with cutting-edge cybersecurity. The brand personality is "Cyber-Guardian"—authoritative, futuristic, and highly technical. 

The design style is a sophisticated **Glassmorphism** mixed with **Vaporwave-inspired neon accents**. It utilizes deep obsidian surfaces, vibrant light-source simulations (orbs), and translucent frosted layers to create a sense of infinite depth. The aesthetic is designed to make the user feel like they are operating within a secure, high-tech vault where data is protected by active, intelligent systems.

## Colors
The palette is rooted in a **Dark Mode** foundation using a deep midnight blue (`#0b1326`) for the base background.

- **Primary Action:** A high-vibrancy Electric Blue (`#4d8eff`) used for key interactions and focus states.
- **Security Accent:** A Royal Purple (`#6f00be`) is paired with the primary blue in gradients to represent encrypted or "hardened" states.
- **Safe State:** A Tertiary Teal (`#00a392`) signifies "Secure" or "Verified" statuses.
- **Danger State:** A high-contrast Coral Red (`#ffb4ab`) is reserved strictly for security intercepts and blocked transactions.
- **Surface Treatment:** Backgrounds use low-opacity whites (5-10%) over the base neutral to create the frosted glass effect.

## Typography
The system uses a dual-font approach to balance technical precision with modern flair.

- **Outfit** is the primary display face. It is used for branding, headers, and all currency/numeric values to provide a bold, geometric, and "tech" feel.
- **Inter** handles all functional and body text. Its high legibility and neutral tone provide clarity within complex data-driven layouts.
- **Numeric values** are prioritized with increased weight and font size (32px for main balances) to ensure immediate data recognition.
- **Labels** use uppercase with tracking (0.1em) to create a clear hierarchical distinction from body text.

## Layout & Spacing
The system employs a **Fixed Grid** philosophy for desktop (max-width 1200px) and a fluid, margin-based approach for mobile.

- **Grid:** A 12-column structure with 20px gutters.
- **Rhythm:** An 8px linear scale (referenced as `sm` through `xxl`) governs all padding and margins. 
- **Containers:** Content is grouped into "Glass Panels" with `lg` (24px) internal padding. 
- **Mobile:** Horizontal margins are set to `lg` (24px) to ensure content doesn't hit the screen edge, with a persistent bottom navigation bar for ergonomic access.

## Elevation & Depth
Depth is not communicated through traditional shadows but through **optical transparency and light simulation**:

- **Layer 0 (Base):** Deep obsidian (`#0b1326`) with dynamic WebGL-rendered orbs creating a "moving atmosphere."
- **Layer 1 (Standard Panels):** 5% white background with a 20px backdrop blur and a 1px border at 10% opacity.
- **Layer 2 (Modals/Overlays):** 10% white background with a 40px backdrop blur, creating a much stronger occlusion of the base layer.
- **Glow Effects:** Critical components (like the balance card) use a radial gradient "under-glow" (`rgba(77,142,255,0.15)`) to pull the element forward.
- **Interactive States:** Buttons use 0px blur but 20px outer glows of their own color on hover to simulate "powering on."

## Shapes
The shape language is consistently **Rounded**, communicating modern sophistication rather than organic softness or brutalist harshness.

- **Standard Containers:** Use 0.75rem (`rounded-xl`) to soften the large glass panels.
- **Inputs & Buttons:** Use 0.5rem (`rounded-lg`) for a more precise, structural feel.
- **Pills/Status:** Security badges and status indicators use `rounded-full` to stand out as distinct "tags."
- **Visual Contrast:** Borders are thin (1px) and translucent, ensuring the shapes feel like light-weight glass rather than heavy solid objects.

## Components

- **Buttons (Primary):** Features a 135-degree gradient from Primary Blue to Secondary Purple. On hover, apply a `20px` blue drop-shadow and a subtle `-1px` Y-axis translation.
- **Glass Panels:** The core container. Must include `backdrop-filter: blur(20px)`, a `1px` white border at `0.1` opacity, and an `inset` shadow of `1px` white at `0.05` opacity to simulate glass thickness.
- **Inputs:** Use the "Input-Dark" style—a solid slate-blue (`#1e293b`) background to provide better contrast for text entry against the translucent page background. Focus state triggers a primary blue border and a `15px` glow.
- **Security Overlays:** Full-screen blurs with an increased depth of `30px-40px`. Use a centered container with a red-tinted radial "alarm" glow at the top.
- **Toggle Switches:** Custom-styled with a primary blue background when active and a white circular "thumb" that slides with a 200ms transition.
- **Badges:** Small, pill-shaped tags with low-opacity backgrounds of the status color (e.g., 10% Teal for "Secure") to indicate attributes without overpowering the main content.