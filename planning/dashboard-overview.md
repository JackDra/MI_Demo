# Dashboard Overview

## Main Screen

The main dashboard should be dominated by a large geographic image representing the area managed by Murrumbidgee Irrigation.

For the first PoC, this image can be either:

- a real map or satellite-style image of the relevant region, if one is easy to source and use safely
- a fictional demo map that is clearly not claiming geographic accuracy

The image should act as the operational canvas. Alerts, region status, and selectable areas should be shown directly over the geography.

## Regional Alert Overlays

Key regions should be represented by transparent circular blobs overlaid on the geographic image.

Each blob represents a region or operational area with one or more notifications.

Severity colours:

- Green: normal status, informational, or low-priority notification.
- Yellow: attention required soon, planned action upcoming, or moderate risk.
- Red: urgent, time-sensitive, abnormal, or high-risk condition.

The overlays should be semi-transparent so the underlying region remains visible. They should feel like status heat markers rather than hard boundaries.

## Overlay Behaviour

Each region overlay should support:

- hover state showing the region name and short status summary
- click or tap to select the region
- visible selected state
- transition into the 3D regional infrastructure view

The PoC should include enough example regions to demonstrate contrast between normal, warning, and urgent operational conditions.

Example regions:

- Griffith West Channel: yellow, gate adjustment scheduled soon.
- Leeton Delivery Zone: red, abnormal downstream sensor reading.
- Yanco Main Channel: green, normal flow.
- Coleambally Edge Area: yellow, vegetation inspection due.

These names can be replaced later if better demo regions are chosen.

## Right-Side Control Panel

The dashboard should include a selectable control panel on the right side of the screen.

The panel should provide contextual information for the currently selected region or overall dashboard state.

Default dashboard panel content:

- current system status summary
- list of active notifications
- severity filters
- region list
- last updated timestamp

Selected region panel content:

- region name
- severity
- active notifications
- key water metrics
- upcoming planned actions
- button or command to enter the 3D region view

## Operator Workflow

The intended dashboard workflow is:

1. Operator opens the control panel and sees a regional overview.
2. Operator visually identifies red and yellow areas first.
3. Operator hovers or selects a region to understand the alert summary.
4. Operator reviews the right-side panel for details.
5. Operator clicks the region overlay or enters the 3D view from the panel.
6. Operator inspects local infrastructure in context.

## Data Expectations

Dashboard data can be mocked in the first PoC, but it should resemble plausible operational data:

- region status
- alert severity
- notification title and description
- timestamp or age
- related infrastructure type
- suggested operator action
- high-level water metrics
