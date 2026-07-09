# Component Inspection

## Interaction Model

In the 3D region view, operators should be able to click infrastructure and environmental objects to inspect them.

Selection should not navigate away from the 3D scene. Instead, the right-side panel should update with details for the selected component.

The selected component should be visually highlighted in the scene so the operator can see which object the panel refers to.

## Water Gate Details

Clicking a water gate should show operational and maintenance information.

Expected information:

- gate name
- asset ID
- current position
- planned position change
- time of next scheduled action
- related notifications
- maintenance status
- next scheduled inspection
- model or device type
- installation date, if available
- last command timestamp

Example notifications:

- Gate scheduled to open from 40 percent to 65 percent at 14:30.
- Inspection due within 7 days.
- Position sensor reporting delayed updates.

## Water Details

Clicking the water surface should show water metrics for the selected channel or region.

Expected information:

- current flow rate
- target flow rate
- water level
- absorption estimate for the region
- evaporation estimate
- recent trend
- upstream influence
- downstream delivery status
- related water quality or flow notifications

Example notifications:

- Flow below target by 8 percent.
- Evaporation estimate elevated for current weather conditions.
- Downstream delivery expected to normalise within 30 minutes.

## Sensor Details

Clicking a sensor should show live or mocked telemetry and device metadata.

Expected information:

- sensor name
- sensor type
- sensor ID
- current reading
- reading unit
- last updated timestamp
- health status
- battery or power status, if relevant
- calibration date
- next inspection date
- related notifications

Example notifications:

- Water level sensor has not reported for 12 minutes.
- Flow reading outside expected range.
- Calibration due next month.

## Vegetation Details

Clicking vegetation should show environmental or maintenance context.

Expected information:

- vegetation zone name
- inspection status
- risk level
- last inspection date
- next scheduled inspection
- maintenance notes
- related channel or asset

Example notifications:

- Vegetation encroachment inspection due.
- Potential obstruction risk near sensor access path.
- Recent maintenance completed, monitor for regrowth.

## Panel Behaviour

The component detail panel should include:

- component title
- component type
- severity or health indicator
- active notifications first
- current data or metadata
- scheduled actions
- clear selection action

The most time-sensitive information should appear at the top of the panel.

## Mock Data Boundaries

All component information can be mocked for the first PoC.

Mock values should be plausible, internally consistent, and labelled in the implementation or demo notes as non-production data.

The first version should avoid implying real operational authority. For example, planned gate changes can be shown as scheduled information, but the PoC should not include real command execution.
