# Validation Notes

## Completed locally

- Formal UPPAAL `verifyta` execution: **PASS**
- Formal properties satisfied: **20 of 20**
- Deadlock-freedom query: **SATISFIED**
- XML parsing: **PASS**
- Template count: **7**
- Query count: **20**
- Initial-location reference check: **PASS**
- Transition source/target reference check: **PASS**
- Required-template-name check: **PASS**
- Generator Python syntax check: **PASS**
- Independent decision truth-table check: **PASS**

Truth-table cases checked:

- no hazard -> manual control
- valid pedestrian -> emergency brake `100`
- red above `15 km/h` -> controlled brake `90`
- red at/below `15 km/h` -> controlled brake `60`
- yellow above `10 km/h` -> controlled brake `45`
- yellow at/below `10 km/h` -> manual control
- valid green -> notification only
- close vehicle above `20 km/h` -> controlled brake `35`
- far vehicle -> manual control
- low-confidence detection -> manual control

## Formal verification result

The final model was checked using UPPAAL 5.0.0 `verifyta`. All twenty properties were reported as:

```text
Formula is satisfied.
```

The complete command-line output is saved in `verifyta_results.txt`. Open the final XML in the UPPAAL GUI and use **Verifier > Check All** to capture graphical evidence for submission.
