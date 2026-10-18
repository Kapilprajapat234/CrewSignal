   CrewSignal: Slide Notes

  Code  E  Manipal 2.0 | Track 02 HealthTech | PS 09 | Software / Simulation | Synthetic data only  

      

     1. Problem (2 lines)

On long missions, crew members cannot get quick medical advice, and a fixed population threshold (for example "heart rate above 100") either misses a real change in one person or raises repeated false alarms for another.
CrewSignal learns each astronaut's own normal, flags persistent deviations, states how sure it is, and keeps working offline, without ever diagnosing.

      

     2. Architecture: one sentence per layer

| Layer | File | One sentence |
|      |      |      |
| Data contract | `core/__init__.py` | Shared `Reading` and `Flag` types and the list of metrics, so every layer speaks the same language. |
| Simulator | `core/simulator.py` | Generates reproducible synthetic sensor streams (heart rate, SpO2, sleep and more) from scenario JSON files, including noise, dropouts, late arrivals and conflicting records. |
| Storage | `db/database.py` | Stores everything locally in SQLite with both `measured_at` and `recorded_at` timestamps and no duplicate rows. |
| Baseline | `core/baseline.py` | Builds a personal baseline for each astronaut and metric from a calibration window, using median and MAD, and says "not established" when there is too little data. |
| Anomaly | `core/anomaly.py` | Compares new readings with the personal baseline and flags only deviations that persist, or several moderate changes that happen together. |
| Uncertainty | `core/uncertainty.py` | Gives every flag a confidence level and a plain  language evidence list, and returns "insufficient evidence" when the data cannot support a conclusion. |
| Sync | `core/sync.py` | Records and alerts without connectivity, then reconciles late and conflicting records by sorting on measurement time and keeping both sides of a conflict visible. |
| Workflow | `ui/workflow.py` | Guides the crew member through repeat measurement, symptom logging, or escalation via an approved protocol, and records each action with a timestamp. |
| Interface | `app.py`, `ui/ ` | Shows the astronaut profile, mission timeline, trend charts with the personal normal band, flags with evidence, and the symptom log. |
| Tests | `tests/test_failure_cases.py` | Proves the system behaves safely when data is missing, late, duplicated, impossible or in conflict. |

      

     3. The safety rule: observed vs. suspected vs. confirmed

CrewSignal keeps three things strictly separate:

| Level | Meaning | Who can set it | Example wording |
|      |      |      |      |
|      Observed   | A raw measurement | The sensor | "SpO2 = 94%" |
|   Suspected concern   | A pattern that differs from this person's normal | CrewSignal | "SpO2 has been below this astronaut's normal in 4 of the last 5 readings" |
|   Confirmed diagnosis   | A medical conclusion | A medical professional only | The system has no way to set this |

   The code has   no diagnosis status  , so the system cannot produce one.
   Every flag card carries the banner:   "Not a diagnosis. Decision support only."  
   The system never recommends treatment. It only suggests repeating a measurement, logging a symptom, or escalating through an approved protocol.
   A person always confirms an escalation.
   Weak data produces   "insufficient evidence"  , not a guess.

      

     4. Demo order

Keep the demo to about 3 minutes. Say the   bold   line at each step.

1.   normal  
      Show: the trend chart stays inside the normal band and no flags appear.
      Say:   "With a healthy astronaut, CrewSignal stays quiet. No false alarms."  

2.   sleep_decline  
      Show: sleep slowly falls and heart rate rises a little. Neither change is alarming alone.
      Show: a flag appears with its evidence list and a confidence level.
      Say:   "Two moderate changes together, persisting over days, become a suspected concern."  

3.   spo2_drop  
      Show: the fixed population rule stays silent, while the personal baseline raises a flag.
      Say:   "This value would look fine to a fixed threshold. For this person, it is a real drop."  
      Make sure the numbers in `spo2_drop.json` produce this exact effect before the demo.

4.   offline  
      Show: turn connectivity off. Readings keep arriving locally and the flag still appears.
      Show: walk the flag through repeat measurement, log a symptom, escalate via the protocol card.
      Say:   "No connection does not mean no monitoring."  

5.   reconcile  
      Show: turn connectivity back on. Late readings slot into the correct time order.
      Show: one conflicting pair appears with both values kept and marked as a conflict.
      Say:   "We never silently overwrite data. Conflicts stay visible, and nothing is duplicated."  

6.   test results  
      Show: run the failure  case tests and show the pass count.
      Say:   "We tested the failure cases, not just the happy path."  

      

     5. Fill in before the demo

   [ ] Test results: `__ passed / __ total` (run `pytest tests/test_failure_cases.py`)
   [ ] Scenario used for the fixed  vs  personal comparison: `spo2_drop` (day flagged: `__`, fixed rule triggers on day: `__` or never)
   [ ] Baseline window length: `__ days`
   [ ] Persistence rule: `__ of the last __ readings`
   [ ] Conflict rule (one sentence): `__`

      

     6. Likely judge questions

     Why not a fixed threshold?   One person's normal is another person's warning sign. A personal baseline catches change relative to the individual and cuts false alarms.
     How do you avoid false alarms?   A flag needs persistence over several readings, and the `normal` scenario is a test that must raise zero flags.
     What if data is missing or conflicting?   The system lowers confidence or returns "insufficient evidence", and conflicting records are both kept and shown.
     Does it diagnose?   No. It has no diagnosis state and only supports a decision about the next step.
     Is any of this real patient data?   No. All data is synthetic and reproducible from a fixed seed.