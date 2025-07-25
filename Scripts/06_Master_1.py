import subprocess

# List of zones
zones = ["North", "Middle", "South"]

# List of scripts to execute
scripts = [
    "01_Extend_faults.py",
    "02_Calculate_apparent_dip.py",
    "03_Add_faults.py",
    "04_Add_original_sections.py",
    "05_process_interfaces.py"
]

# Loop through each zone
for zone in zones:
    print(f"=== Running scripts for zone: {zone} ===")
    
    # Loop through each script
    for script in scripts:
        print(f" -> Running {script} with zone {zone}")
        
        # Run the script with the zone name as an argument
        subprocess.run(["python", script, zone])
