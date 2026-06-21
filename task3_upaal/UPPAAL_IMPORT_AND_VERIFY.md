# UPPAAL Import and Verification

## Open the model

1. Start UPPAAL.
2. Click **File > Open System**.
3. Select `Carla_ADAS_Task3_UPPAAL.xml`.
4. The project tree should show seven templates:
   - `ScenarioGenerator`
   - `PerceptionAgent`
   - `ObjectDetectionRole`
   - `TrafficLightRole`
   - `DecisionRole`
   - `ControlAgent`
   - `ResponseMonitor`

## Run the verifier

1. Open the **Verifier** tab.
2. The queries are embedded in the XML.
3. If queries do not appear, open `Carla_ADAS_Task3_Verifier_Queries.q` and paste its queries into the verifier.
4. Click **Check All**.
5. All properties are designed to be satisfied.

Do not submit only the XML. Capture screenshots of the model templates and the verifier results because Task 3 requires evidence of verification.

## Demonstrate behavior in the simulator

Open the **Symbolic Simulator** and follow transitions for these cases:

| Scenario | Expected behavior |
|---|---|
| `Pedestrian` | `EmergencyOverride`, brake `100` |
| `RedFast` | `ControlledOverride`, brake `90` |
| `RedSlow` | `ControlledOverride`, brake `60` |
| `YellowFast` | `ControlledOverride`, brake `45` |
| `YellowSlow` | `StandbyHumanControl` |
| `CloseVehicle` | `ControlledOverride`, brake `35` |
| `FarVehicle` | `StandbyHumanControl` |
| `Green` | `DriverNotification`, brake `0` |
| `LowConfidence` | `StandbyHumanControl` |

## Important accuracy note

The model uses the actual final-code thresholds:

- pedestrian: `70%`
- vehicle: `50%`
- traffic light: `75%`

The `40%` threshold visible in the other team's screenshots is not used.

