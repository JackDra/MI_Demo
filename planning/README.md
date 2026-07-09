# MI Control Panel PoC Planning

This folder captures the first product and experience planning for a Murrumbidgee Irrigation control panel proof of concept.

The current idea is intentionally exploratory: a visual-first operator dashboard that starts with a geographic overview of the irrigation region, highlights operational alerts directly on the map, and lets an operator drill into a 3D model of local infrastructure.

## Document Map

- [Product Concept](product-concept.md): PoC vision, intended users, goals, non-goals, and working assumptions.
- [Dashboard Overview](dashboard-overview.md): geographic dashboard, region overlays, severity model, and right-side control panel.
- [Region 3D View](region-3d-view.md): 3D canal scene, navigation, transitions, and visual infrastructure model.
- [Component Inspection](component-inspection.md): click behavior and detail panels for gates, water, sensors, and vegetation.
- [Demo Scope](demo-scope.md): what the first demo should prove, what can be mocked, and what remains out of scope.

## Current Status

This is the first planning pass. It defines the operator experience and demo intent, but it does not yet define:

- domain models
- data contracts
- persistence
- backend services
- frontend framework
- deployment architecture
- integration with real MI systems

Those topics should be added in later planning documents after the concept direction is stable.

## Planning Principles

- Make the PoC understandable at a glance.
- Prioritise an operator workflow over a technical showcase.
- Use realistic mocked data where real operational data is unavailable.
- Keep the first implementation visually compelling but bounded.
- Avoid committing to exact MI geography, assets, or infrastructure locations until reliable source material is available.
