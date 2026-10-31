 CrewSignal – Astronaut Health Monitoring System

A data-driven health monitoring and anomaly detection prototype for astronauts during space missions.

CrewSignal is a Python-based application designed to monitor astronaut health indicators, identify unusual patterns, and provide evidence-based warning flags. It simulates sensor readings, establishes individual health baselines, detects persistent deviations, and visualizes health trends through an interactive dashboard.

The system also explores offline monitoring and data synchronization for environments where connectivity may be unreliable.



 Problem Statement

Astronauts operate in challenging environments where continuous health monitoring is important. Changes in vital health indicators may go unnoticed when monitoring relies only on fixed thresholds or periodic manual reviews.

CrewSignal explores an approach that combines individual health baselines, anomaly detection, trend visualization and offline data handling to support astronaut health monitoring.

Our Solution

CrewSignal provides a centralized monitoring dashboard that processes simulated health readings and identifies unusual patterns.

Instead of relying exclusively on fixed thresholds, it evaluates deviations from individual baselines and checks whether unusual readings persist over time.

 Key Features

 1. Health Monitoring
- Heart rate monitoring
- Blood oxygen (SpO₂) monitoring
- Systolic and diastolic blood pressure
- Sleep duration tracking
- Physical activity monitoring

 2. Baseline Calculation
- Establishes individual health baselines.
- Uses median and Median Absolute Deviation (MAD).
- Evaluates deviations relative to baseline values.

 3. Anomaly Detection
- Detects moderate and strong deviations.
- Checks persistence across recent readings.
- Generates warning flags with supporting evidence.
- Includes a fixed SpO₂ threshold demonstration.

 4. Mission Simulation
- Generates synthetic astronaut health readings.
- Supports scenario-based simulations.
- Models gradual changes in health indicators.
- Supports missing readings and sensor conflicts.
- Includes mission-day replay.

 5. Offline Monitoring
- Supports offline mode.
- Retains readings locally.
- Tracks pending synchronization.
- Attempts synchronization when connectivity returns.

 6. Interactive Dashboard
- Astronaut profile
- Health trend charts
- Flags and evidence
- Symptoms and workflow tracking
- Mission timeline

 7. Access Management
- Separate crew and medical access roles.
- PIN-based authentication.
- Failed-attempt lockout.
- Session timeout and manual session locking.

 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive dashboard |
| Pandas | Data processing |
| NumPy | Numerical calculations |
| SQLite | Local database |
| JSON | Scenario configuration |
| Pytest | Testing |

 Project Architecture

```text
CrewSignal/
│
├── core/
│   ├── simulator.py
│   ├── baseline.py
│   ├── anomaly.py
│   └── sync.py
│
├── db/
│   └── database.py
│
├── docs/
│
├── scenarios/
│   ├── normal.json
│   ├── sleep_decline.json
│   └── spo2_drop.json
│
├── tests/
│
├── ui/
│   ├── profile.py
│   ├── charts.py
│   ├── flags.py
│   ├── symptoms.py
│   └── workflow.py
│
├── app.py
├── test_pipeline.py
├── requirements.txt
└── README.md
```

 How It Works

```text
Synthetic Sensor Readings
          |
          v
    Scenario Simulator
          |
          v
   Data Processing
          |
          v
   Baseline Calculation
          |
          v
    Anomaly Detection
          |
          v
   Evidence-Based Flags
          |
          v
   Streamlit Dashboard
          |
          v
     SQLite Storage
```

 Installation and Setup

 Prerequisites

- Python 3.10 or later
- Git
- pip

 1. Clone the repository

```bash
git clone https://github.com/Kapilprajapat234/CrewSignal.git
```

 2. Navigate to the project directory

```bash
cd CrewSignal
```

 3. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

Windows:
bash
venv\Scripts\activate


Linux/macOS:
```bash
source venv/bin/activate
'''

4. Install dependencies

```bash
pip install -r requirements.txt
```

 5. Configure access PINs

Set your own PINs using environment variables.

PowerShell:
```powershell
$env:CREW_PIN="your_crew_pin"
$env:MEDIC_PIN="your_medical_pin"
```

Do not use the built-in demonstration PIN defaults in a real deployment.

### 6. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

 Testing

Run the test suite using:

```bash
pytest -q
```

 Important Disclaimer

CrewSignal is an experimental prototype developed using synthetic health data.

- It is not connected to real astronaut medical devices.
- It does not provide medical diagnoses.
- Its anomaly detection results are intended for demonstration and decision-support research.
- It is not validated for clinical or operational use.

 Future Improvements

- Integration with real-time wearable sensors.
- More advanced anomaly detection models.
- Improved connectivity and synchronization mechanisms.
- More comprehensive historical health analytics.
- Enhanced authentication and access management.
- Deployment-ready infrastructure.

Contributors

Developed collaboratively as a hackathon project.

Repository:
https://github.com/Kapilprajapat234/CrewSignal

---

 If you find this project interesting, consider giving the repository a star!

Built with Python, teamwork and a passion for solving real-world problems.
