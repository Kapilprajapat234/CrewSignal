
from core.simulator import load_scenario, generate_readings
from core.baseline import compute_all_baselines
from core.anomaly import detect
from core.uncertainty import evaluate, missing_ratio


def run_scenario(name: str):
    print(f"\n{'='*60}")
    print(f"SCENARIO: {name.upper()}")
    print('='*60)

    scenario = load_scenario(name)
    df = generate_readings(scenario)
    astronaut_id = scenario["astronaut_id"]

    print(f"Total readings generated : {len(df)}")
    print(f"Astronaut ID             : {astronaut_id}")

    baselines = compute_all_baselines(df)
    print("\nBaselines:")
    for m, b in baselines.items():
        status = b["status"]
        med = b["median"]
        print(f"  {m:15} → {status:15} median={med}")

    flags = detect(df, baselines, astronaut_id)

    
    final_flags = []
    for f in flags:
        missing = missing_ratio(df)
        f = evaluate(f, df, baselines, missing)
        final_flags.append(f)

    print(f"\nFlags found: {len(final_flags)}")
    if not final_flags:
        print("→ No flags (expected for normal scenario)")
    else:
        for i, flag in enumerate(final_flags, 1):
            print(f"\n--- Flag {i} ---")
            print(f"Status     : {flag.status}")
            print(f"Metrics    : {flag.metrics}")
            print(f"Confidence : {flag.confidence}")
            print("Evidence   :")
            for e in flag.evidence:
                print(f"  • {e}")


if __name__ == "__main__":
    for scenario_name in ["normal", "sleep_decline", "spo2_drop"]:
        try:
            run_scenario(scenario_name)
        except Exception as e:
            print(f"\nERROR in {scenario_name}: {e}")