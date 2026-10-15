from crewsignal import DataSimulator, create_sample_mission, generate_sample_data

# Generate sample data
data = generate_sample_data(num_days=7, num_astronauts=2)

# Full mission simulation
simulator = create_sample_mission(
    mission_id="mars_2024",
    num_astronauts=4,
    duration_days=90,
    seed=42
)
data = simulator.generate_all_data()

# Generate specific streams
hr_data = simulator.generate_stream("heart_rate", astronaut_id="astronaut_01")
co2_data = simulator.generate_stream("co2")