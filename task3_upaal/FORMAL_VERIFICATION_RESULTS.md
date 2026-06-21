# Formal UPPAAL Verification Results

## Result

The final CARLA ADAS timed-automata model was formally verified using UPPAAL 5.0.0 `verifyta`.

**Result: 20 of 20 properties satisfied.**

## Verified property groups

| Group | Result |
|---|---|
| Complete composed model is deadlock-free | Satisfied |
| Brake and throttle are never active simultaneously | Satisfied |
| Emergency override applies full brake and zero throttle | Satisfied |
| Controlled override applies partial brake and zero throttle | Satisfied |
| Manual-driving mode applies no command | Satisfied |
| Green notification applies no control command | Satisfied |
| Pedestrian detection leads to emergency override | Satisfied |
| Red-light detection leads to controlled override | Satisfied |
| Green-light detection leads to notification-only behavior | Satisfied |
| Emergency response remains within the configured deadline | Satisfied |
| Controlled-braking response remains within the configured deadline | Satisfied |
| Notification response remains within the configured deadline | Satisfied |
| Fast red-light scenario applies brake `90` | Satisfied |
| Slow red-light scenario applies brake `60` | Satisfied |
| Fast yellow-light scenario applies brake `45` | Satisfied |
| Close-vehicle scenario applies brake `35` | Satisfied |
| Low-confidence scenario remains under human control | Satisfied |
| Emergency override is reachable | Satisfied |
| Controlled override is reachable | Satisfied |
| Notification-only behavior is reachable | Satisfied |

The complete verifier console output is saved in `verifyta_results.txt`.

