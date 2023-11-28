import subprocess
from pathlib import Path

# Set the path to the aviatrix resources directory
aviatrix_resources_dir = Path("resources/aviatrix")

# Function to run the submit.py script for a given resource
def submit_resource(resource_dir):
    # Convert dashes in resource directory names to two colons
    resource_name = resource_dir.name.replace('-', '::')
    try:
        # Run the submit.py script with the modified resource name
        subprocess.run(['python3', 'submit.py', resource_name], check=True)
        print(f"Successfully submitted {resource_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to submit {resource_name}: {e}")

# List all resource directories in the aviatrix resources directory
resource_dirs = [f for f in aviatrix_resources_dir.iterdir() if f.is_dir()]

# # Limit the number of resources to submit
# max_resources = 50
# limited_resource_dirs = resource_dirs[:max_resources]

# Loop through the limited list of resource directories and submit each one
for resource_dir in resource_dirs:
    submit_resource(resource_dir)