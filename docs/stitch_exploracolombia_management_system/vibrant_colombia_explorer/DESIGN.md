---
name: Vibrant Colombia Explorer
colors:
  surface: '#f9f9fc'
  surface-dim: '#dadadc'
  surface-bright: '#f9f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f6'
  surface-container: '#eeeef0'
  surface-container-high: '#e8e8ea'
  surface-container-highest: '#e2e2e5'
  on-surface: '#1a1c1e'
  on-surface-variant: '#3f4941'
  inverse-surface: '#2f3133'
  inverse-on-surface: '#f0f0f3'
  outline: '#6f7a70'
  outline-variant: '#bec9be'
  surface-tint: '#006d3c'
  primary: '#00522c'
  on-primary: '#ffffff'
  primary-container: '#006d3c'
  on-primary-container: '#92ecae'
  inverse-primary: '#80d99d'
  secondary: '#7d5800'
  on-secondary: '#ffffff'
  secondary-container: '#ffb700'
  on-secondary-container: '#6b4b00'
  tertiary: '#3a4851'
  on-tertiary: '#ffffff'
  tertiary-container: '#526069'
  on-tertiary-container: '#cbdae5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9bf6b7'
  primary-fixed-dim: '#80d99d'
  on-primary-fixed: '#00210e'
  on-primary-fixed-variant: '#00522c'
  secondary-fixed: '#ffdea9'
  secondary-fixed-dim: '#ffba26'
  on-secondary-fixed: '#271900'
  on-secondary-fixed-variant: '#5e4100'
  tertiary-fixed: '#d6e5ef'
  tertiary-fixed-dim: '#bac9d3'
  on-tertiary-fixed: '#0f1d25'
  on-tertiary-fixed-variant: '#3b4951'
  background: '#f9f9fc'
  on-background: '#1a1c1e'
  surface-variant: '#e2e2e5'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 56px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg-mobile:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  metric-lg:
    fontFamily: Montserrat
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  table-data:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 64px
---

## Brand & Style

This design system captures the rhythmic energy and lush natural beauty of Colombia. It targets domestic and international travelers, as well as management stakeholders, balancing a professional administrative backbone with an adventurous, high-end editorial aesthetic.

The visual direction is **Modern Glassmorphism**. This style uses translucent layers to suggest the mist of the Cocora Valley or the crystal waters of Tayrona. By layering frosted surfaces over vibrant, high-saturation photography, the UI achieves depth without sacrificing legibility. The interface should feel expensive, trustworthy, and deeply connected to the Colombian landscape.

## Colors

The palette is rooted in the "Emerald and Gold" heritage of Colombia. 

- **Primary (Deep Emerald):** Used for navigation, primary branding elements, and deep-tinted overlays. It represents stability and the lush Andean forests.
- **Secondary (Colombian Gold):** Reserved for high-priority Call to Actions (CTAs) and accents. It provides a sun-drenched contrast against the deep green.
- **Background (Soft Sky Blue):** A very desaturated, airy blue used for page backgrounds to prevent "stark white" eye strain and maintain the tropical theme.
- **Semantic Colors:** Muted versions of the primary/secondary palette are used for status indicators (Success, Alert, Error) to ensure they remain functional without clashing with the brand's vibrant emerald core.

## Typography

The typography strategy employs **Montserrat** for its geometric, confident authority in headings and **Inter** for its unparalleled legibility in data-heavy management contexts.

- **Display & Headlines:** Use Montserrat Bold. For large hero sections, use `display-lg` with tight letter spacing to mimic high-end travel magazines.
- **Dashboard Metrics:** Use `metric-lg` for key performance indicators (KPIs) like "Total Bookings" or "Revenue."
- **Body & Data:** Use Inter for all long-form text and data tables. `table-data` is optimized for density and readability in the tourism management dashboard.

## Layout & Spacing

The design system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. 

- **Containers:** Content should be housed in containers with a maximum width of 1440px to ensure line lengths remain readable on ultra-wide monitors.
- **Rhythm:** An 8px base unit drives all padding and margins. 
- **Reflow:** On mobile devices, side margins shrink to 16px, and grid gutters reduce to 16px. Glassmorphic cards should transition from multi-column layouts to single-stack cards.

## Elevation & Depth

This system treats the UI as a series of physical layers floating over breathtaking imagery.

1.  **Background Layer:** High-definition photography of Colombian landscapes with a slight dark or emerald-tinted overlay (20-40% opacity).
2.  **Surface Layer (Glass):** UI containers use a background blur (16px to 24px) and a semi-transparent white fill (typically `rgba(255, 255, 255, 0.7)`).
3.  **Outlines:** Every glass element must have a 1px solid border at 20% white opacity on the top/left and 10% on the bottom/right to simulate light catching the edge of the glass.
4.  **Shadows:** Use large, diffused shadows with a slight emerald tint (`#006D3C` at 8% alpha) instead of pure black to maintain a vibrant, clean feel.

## Shapes

The shape language is friendly and approachable. 
- **Standard Radius:** 16px (represented by `rounded-lg` in this system) is the default for all cards and primary containers.
- **Interactive Elements:** Buttons and input fields should follow a slightly smaller radius (8px) to feel more precise, while badges and chips are fully rounded (pill-shaped) to distinguish them from clickable actions.

## Components

### Buttons
- **Primary:** Solid Colombian Gold (#FFB700) with Black or Deep Emerald text. Bold Montserrat, uppercase. Use a subtle lift shadow on hover.
- **Secondary:** Transparent background with a 2px Deep Emerald border. On hover, fills with a very light emerald tint.
- **Glass Action:** A white semi-transparent button used specifically when placed directly over photographs.

### Cards
- **Feature Cards:** Large image background with a glassmorphic footer containing the title and price. 16px corner radius.
- **Management Cards:** White/Glass background with emerald-tinted icons for dashboard metrics.

### Badges & Chips
- **Status Badges:** Use a pill shape with high-contrast text. For "Confirmed" tours, use Success Green; for "Pending," use Alert Yellow.
- **Category Chips:** Small, semi-transparent grey chips used to tag locations (e.g., "Beach", "Coffee Region").

### Input Fields
- **Search & Forms:** Use a subtle 1px border and a white background (90% opacity). Focus states should glow with a 4px soft emerald outer shadow.

### Data Tables
- Header rows should use a light emerald tint. Rows should have a subtle hover effect (5% emerald tint) to help users track data across wide screens.