# Final Formal-Acceptability Audit

## Verdict

The submitted UPPAAL model is formally acceptable for Task 3.

The final model:

- opens successfully in UPPAAL 5.0.0;
- contains seven cooperating timed-automata templates;
- contains twenty formal verification properties;
- passes all twenty properties in both the UPPAAL GUI and `verifyta`;
- explicitly verifies deadlock freedom;
- verifies safety, response behavior, exact braking commands, low-confidence rejection, and reachability;
- is traceable to the actual thresholds and control decisions in `my_adas.py`;
- is supported by MUML community, role, interaction, and state-behavior documentation.

## Task 3 Coverage

| Task 3 requirement | Evidence | Status |
|---|---|---|
| Refine the principle solution into a software model | Seven-template UPPAAL timed-automata network | Complete |
| Apply MUML techniques | Community, component, role, sequence, and behavior diagrams | Complete |
| Identify communities and role behavior | Perception, object detection, traffic-light detection, decision, control, environment, and monitor roles | Complete |
| Map role behavior to agents | Role-to-agent table in the Task 3 report | Complete |
| Specify overall agent behavior | `DecisionRole`, `ControlAgent`, diagrams, and interaction sequence | Complete |
| Refine requirements into checkable properties | Twenty UPPAAL queries | Complete |
| Verify correctness, including deadlock freedom | All twenty queries green; `A[] not deadlock` satisfied | Complete |
| Use UPPAAL to specify behavior | Importable and verified UPPAAL XML | Complete |

## Verification Evidence

- `evidence/UPPAAL_Verifier_Results_01.png`
- `evidence/UPPAAL_Verifier_Results_02.png`
- `verifyta_results.txt`
- `FORMAL_VERIFICATION_RESULTS.md`

## Formal Interpretation

The green UPPAAL results prove that every checked property holds for every possible execution represented by this abstract timed-automata model.

The verification does not prove:

- YOLO detection accuracy;
- correctness of unmodeled ROS 2 or CARLA implementation details;
- physical stopping distance;
- real-world sensor and actuator reliability.

This limitation is normal and should be stated during presentation. Formal verification establishes correctness relative to the explicitly documented abstraction and assumptions.

