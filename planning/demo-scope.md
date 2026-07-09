# Demo Scope

## What The First PoC Should Prove

The first PoC should prove that a spatial, visual operator interface can communicate irrigation operations more clearly than a purely tabular or alarm-list experience.

It should demonstrate:

- a regional geographic overview
- severity-based region overlays
- a right-side contextual control panel
- selection of regions from the dashboard
- transition from a region into a 3D infrastructure model
- clickable 3D components
- contextual detail panels for gates, water, sensors, and vegetation
- mocked operational notifications and metrics

## What Can Be Mocked

The following can be mocked for the first demo:

- geographic map or region image
- region names and boundaries
- alert locations
- alert severity
- notification content
- infrastructure positions
- water flow rate
- water level
- absorption rate
- evaporation rate
- gate metadata
- gate schedules
- sensor readings
- sensor health
- vegetation inspection data
- timestamps

Mock data should be coherent enough to support a believable operator journey.

## Out Of Scope For The First PoC

The first PoC should not attempt to deliver:

- real GIS accuracy
- real-time data ingestion
- real control commands
- production SCADA integration
- user authentication
- role-based permissions
- audit logging
- production reporting
- mobile-specific workflows
- full asset lifecycle management
- detailed hydraulic simulation
- alert acknowledgement workflows
- incident management workflows

These may become future planning topics once the demo concept is validated.

## Recommended First Demo Scenario

Use a single operator journey to make the PoC easy to understand:

1. The operator opens the dashboard.
2. The map shows several green, yellow, and red region overlays.
3. The operator selects a red or yellow region.
4. The right panel shows active notifications and a short operational summary.
5. The operator enters the 3D region view.
6. The operator sees a channel with flowing water, a gate, sensors, and vegetation.
7. The operator clicks the gate and reviews upcoming action and maintenance details.
8. The operator clicks the water and reviews flow, absorption, and evaporation metrics.
9. The operator clicks a sensor and reviews telemetry and metadata.
10. The operator returns to the dashboard.

## Acceptance Criteria

The planning documentation is sufficient when:

- the operator journey is clear from dashboard to component inspection
- visual elements and interactions are described without requiring implementation architecture
- mock data expectations are explicit
- real-data limitations are clearly stated
- future architecture planning can build on the documented experience

## Future Planning Topics

Likely next planning documents:

- implementation architecture
- frontend technology stack
- 3D rendering approach
- domain model
- mock data schema
- asset and scene data structure
- integration boundaries
- UX wireframes
- demo script
