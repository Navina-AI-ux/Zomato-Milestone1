---
name: Zomato AI Recommender
colors:
  surface: '#fbf9f8'
  surface-dim: '#dbd9d9'
  surface-bright: '#fbf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f3'
  surface-container: '#efeded'
  surface-container-high: '#eae8e7'
  surface-container-highest: '#e4e2e2'
  on-surface: '#1b1c1c'
  on-surface-variant: '#57423b'
  inverse-surface: '#303030'
  inverse-on-surface: '#f2f0f0'
  outline: '#8b7169'
  outline-variant: '#dec0b6'
  surface-tint: '#a43c12'
  primary: '#a43c12'
  on-primary: '#ffffff'
  primary-container: '#ff7f50'
  on-primary-container: '#6c2000'
  inverse-primary: '#ffb59c'
  secondary: '#715c00'
  on-secondary: '#ffffff'
  secondary-container: '#feda57'
  on-secondary-container: '#745f00'
  tertiary: '#4e6072'
  on-tertiary: '#ffffff'
  tertiary-container: '#93a6ba'
  on-tertiary-container: '#293c4c'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbcf'
  primary-fixed-dim: '#ffb59c'
  on-primary-fixed: '#380c00'
  on-primary-fixed-variant: '#822800'
  secondary-fixed: '#ffe179'
  secondary-fixed-dim: '#e6c443'
  on-secondary-fixed: '#231b00'
  on-secondary-fixed-variant: '#554500'
  tertiary-fixed: '#d1e5fa'
  tertiary-fixed-dim: '#b5c9de'
  on-tertiary-fixed: '#091d2d'
  on-tertiary-fixed-variant: '#36495a'
  background: '#fbf9f8'
  on-background: '#1b1c1c'
  surface-variant: '#e4e2e2'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 24px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  gutter: 24px
  margin: 48px
---

## Brand & Style
The design system for this application is built on a "Modern-Retro Playful" aesthetic. It balances the nostalgia of vintage diners and pop-art with a clean, high-energy SaaS interface. The target audience is food enthusiasts looking for curated, AI-driven suggestions without the friction of traditional search.

The UI should evoke a sense of appetite and excitement. We achieve this by mixing a warm, creamy background with high-saturation accent colors. The style utilizes **Modern-Retro** influences: bold typography, thick rounded shapes, and vibrant gradients that suggest motion and energy. It avoids the coldness of standard tech platforms by leaning into tactile, friendly geometry.

## Colors
This design system uses a high-contrast, warm palette designed to stimulate visual interest and appetite. 

- **Primary (Coral):** Used for main actions, brand identifiers, and active states.
- **Accent (Canary Yellow):** Used for highlighting AI-generated insights, ratings, and "spark" moments.
- **Dark Surface (Midnight Navy):** Reserved for high-contrast navigation bars, footers, and deep-contextual overlays to provide a grounded "retro" feel.
- **Background (Cream Beige):** The canvas for all content. It softens the interface compared to a pure white, making long browsing sessions more comfortable.
- **Text (Charcoal):** Provides high legibility while remaining softer than pure black to maintain the warm brand tone.

**Gradients:**
- **Hero Gradient:** Linear from Coral to Canary Yellow (90deg).
- **Card Accent:** Linear Vertical Stripe (Coral to Cream Beige) used as a decorative left-border indicator.

## Typography
The system utilizes **Plus Jakarta Sans** (as a high-quality alternative to Poppins that offers better variable weights and a more modern feel while retaining the requested circular, friendly geometry).

- **Headings:** Use Heavy (800) or Bold (700) weights. They should feel impactful and "chunky."
- **Body:** Use Regular (400) for long-form text and Medium (500) for emphasis within paragraphs.
- **Labels:** Use SemiBold (600) for navigation and UI controls to ensure they pop against vibrant backgrounds.

For desktop, headlines should maintain tight line-heights to emphasize their presence. On mobile, scale `headline-xl` down to 32px to avoid excessive wrapping.

## Layout & Spacing
The design system follows a **Fluid Grid** philosophy with a 12-column structure on desktop. The base spacing unit is **24px**, ensuring generous breathing room that contributes to the "approachable" brand personality.

- **Desktop (1440px+):** 12 columns, 24px gutters, 48px outer margins.
- **Tablet (768px - 1024px):** 8 columns, 24px gutters, 24px outer margins.
- **Mobile (Below 768px):** 4 columns, 16px gutters, 16px outer margins.

Spacing should always be multiples of 4px or 8px, but the primary rhythm is driven by the 24px base unit to create a consistent, open feel.

## Elevation & Depth
This system uses **Ambient Shadows** to create a soft, floating effect that feels modern and approachable. Depth is not meant to be "realistic" but rather to separate the interactive cards from the cream background.

- **Level 1 (Cards):** `0 4px 20px rgba(23, 42, 58, 0.08)`. This uses the Midnight Navy color for the shadow tint to keep it grounded and organic rather than a harsh grey.
- **Level 2 (Hover States/Modals):** `0 8px 30px rgba(23, 42, 58, 0.12)`.
- **Navigation:** The Dark Surface (Midnight Navy) is treated as a "floor" or "anchor." It does not use shadows; it relies on its deep color to establish hierarchy.

## Shapes
The shape language is purposefully exaggerated and friendly. 

- **Cards:** Use a 16px radius. This provides a soft, containerized look for food imagery and restaurant details.
- **Inputs & Form Elements:** Use a 10px radius. This is slightly sharper than the cards to denote utility and precision.
- **Interactive Elements:** Buttons, Chips, and Pills must use a **999px (Pill)** radius. This reinforces the "playful/energetic" tone and makes buttons feel very touchable and distinct from structural containers.

## Components

### Buttons
- **Primary:** Pill-shaped, Coral background, White text. Bold 16px font.
- **Secondary:** Pill-shaped, Canary Yellow background, Charcoal text.
- **Ghost:** Pill-shaped, Transparent background, Coral border (2px), Coral text.

### Cards
- **Restaurant Card:** 16px rounded corners, Level 1 shadow. Features a 4px vertical gradient stripe (Coral to Cream) on the far-left edge to signify AI "Match" status.
- **Image Treatment:** Images within cards should have a 12px inner radius to create a nested, "frame-within-frame" look.

### Input Fields
- **Search Bar:** 10px rounded corners, Cream Beige background with a thin 1px Charcoal border (20% opacity). Focus state uses a 2px Coral border.

### Chips & Pills
- **Cuisine Tags:** Pill-shaped, Midnight Navy background, White text, 12px Bold uppercase labels.
- **AI Badges:** Pill-shaped, Canary Yellow background with a small "sparkle" icon.

### Lists
- Standard lists should use 16px padding between items with a thin `rgba(74, 74, 74, 0.1)` divider.

### AI Chat Interface
- To lean into the "Recommender" aspect, the chat bubbles should follow the card styling (16px radius) but use the Midnight Navy for AI responses and the Coral for User responses to maintain clear visual distinction.