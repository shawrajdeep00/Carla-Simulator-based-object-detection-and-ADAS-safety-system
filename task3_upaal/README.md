# CARLA ADAS Task 3 UPPAAL Package

Start with:

1. Open `Carla_ADAS_Task3_UPPAAL.xml` in UPPAAL.
2. Run all embedded queries in the **Verifier** tab.
3. Follow `UPPAAL_IMPORT_AND_VERIFY.md`.
4. Use `TASK3_MUML_UPPAAL_REPORT.md` as the Task 3 report content.
5. Use `TASK3_MUML_DIAGRAMS.md` for the community, sequence, and behavior diagrams.

The model is based on the final `my_adas.py` logic and uses confidence thresholds of `70%` for pedestrians, `50%` for vehicles, and `75%` for traffic lights.

## Final verification status

The model was formally checked using UPPAAL 5.0.0. All twenty verifier properties are satisfied. See:

- `FORMAL_VERIFICATION_RESULTS.md`
- `FINAL_ACCEPTABILITY_AUDIT.md`
- `verifyta_results.txt`
- `evidence/UPPAAL_Verifier_Results_01.png`
- `evidence/UPPAAL_Verifier_Results_02.png`
