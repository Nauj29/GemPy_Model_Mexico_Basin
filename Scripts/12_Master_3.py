import subprocess

# List of zones
zones = ["North", "Middle", "South"]

# List of scripts to execute
scripts = [
    "06_Master_1.py",
    "11_Master_2.py"
]

# Loop through each zone
for zone in zones:
    print(f"=== Running scripts for zone: {zone} ===")
    
    # Loop through each script
    for script in scripts:
        print(f" -> Running {script} with zone {zone}")
        
        # Run the script with the zone name as an argument
        subprocess.run(["python", script, zone])