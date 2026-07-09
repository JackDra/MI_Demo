# Product Concept

## Vision

The MI Control Panel PoC is a demonstration of what a next-generation irrigation operations interface could feel like.

Instead of presenting operators with disconnected tables, alarms, and system pages, the PoC should organise operational awareness around the region itself. The main screen should show a large geographic image of the area Murrumbidgee Irrigation is responsible for, with status and alert information overlaid directly on meaningful areas.

From that regional view, an operator should be able to select a highlighted area and transition into a 3D view of the infrastructure in that region. The 3D view should make gates, channels, sensors, water movement, and local conditions understandable as physical things rather than abstract records.

## Target User

The primary user is an irrigation operator or control room user who needs to:

- understand which regions need attention
- quickly distinguish urgent issues from routine notifications
- inspect the infrastructure related to an alert
- see operational data in context
- understand upcoming actions such as gate changes, inspections, and repairs

The PoC does not need to support every real operator workflow. It should demonstrate the value of a spatial, visual, and interactive operations interface.

## Goals

- Present regional operational status on a large map-like dashboard.
- Use coloured transparent overlays to show notification severity by area.
- Support drill-down from a regional alert into a 3D infrastructure model.
- Allow clicking infrastructure components to inspect details and notifications.
- Use mocked but plausible operational data.
- Keep the experience polished enough to communicate the idea to stakeholders.

## Non-Goals

- Accurate GIS implementation.
- Real-time SCADA integration.
- Real MI asset registry integration.
- Authentication, permissions, or audit logging.
- Production-grade hydraulic simulation.
- A complete domain model or system architecture.
- Exact replication of MI infrastructure.

## Working Assumptions

- The first demo can use a fictional or stylised regional image if a real MI region map is not available.
- All operational data can be mocked.
- Alert locations, infrastructure positions, and water metrics can be invented for demonstration purposes.
- The first version should be visual-first and operator-facing.
- Later planning will define the implementation architecture, technology stack, data model, and integration approach.
