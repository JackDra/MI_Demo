# Region 3D View

## Purpose

The 3D region view should let an operator inspect the infrastructure behind a regional alert.

The goal is not physical accuracy. The goal is to make infrastructure state understandable by presenting water, gates, sensors, and surrounding conditions as spatial objects.

## Entry Transition

When an operator clicks a regional overlay on the dashboard, the interface should transition into the selected region's 3D view.

The transition should preserve context:

- selected region name
- selected alert severity
- active notifications
- return path back to the dashboard

The transition can be simple for the first demo, such as a fade or camera movement from the map into the scene.

## Scene Model

The first 3D scene should represent a stylised irrigation channel.

Core scene elements:

- a half-cylinder or basin-like channel shape
- animated water surface flowing through the channel
- one or more water gates
- several sensor devices mounted near the channel
- vegetation markers along the banks
- simple ground plane or terrain context

The water channel can be abstract and clean. It should look like an operational model, not a photorealistic simulation.

## Water Representation

The water should communicate flow direction and activity.

Acceptable PoC techniques:

- animated water texture
- moving shader pattern
- simple particle flow
- directional arrows or subtle surface movement

The first PoC does not need computational fluid dynamics or accurate hydraulic modelling.

## Infrastructure Components

### Water Gates

Gates should be visible mechanical structures placed across or beside the channel.

They should support states such as:

- open
- closed
- partially open
- scheduled to open
- scheduled to close
- maintenance required

### Sensors

Sensors should be visible as small devices near the channel or attached to infrastructure.

Example sensor types:

- water level sensor
- flow sensor
- gate position sensor
- temperature sensor
- evaporation or weather sensor

### Vegetation

Vegetation can be represented with simple clusters or markers.

The PoC should use vegetation to show environmental or maintenance context, such as overgrowth near the channel or a planned inspection zone.

## Navigation Controls

Operators should be able to inspect the scene in 3D space.

Expected controls:

- orbit camera around the region
- pan camera
- zoom in and out
- select components by clicking
- reset camera to default view
- return to dashboard

The controls should be simple and familiar. The scene should not require game-like movement unless a later design specifically calls for it.

## Context Panel

The right-side control panel should remain available in the 3D view.

When no component is selected, it should show:

- selected region name
- active notifications
- current water summary
- listed infrastructure components
- scheduled actions

When a component is selected, the panel should switch to that component's inspection details.
