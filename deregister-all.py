import subprocess
from pathlib import Path
import boto3
import sys

session = boto3.session.Session()
default_region = session.region_name
# Set the path to the aviatrix resources directory
aviatrix_resources_dir = Path("resources/aviatrix")

# Function to deregister a resource
def deregister_resource(resource_name, region):
    try:
        # Run the AWS CLI command to deregister the resource type
        subprocess.run(['aws', 'cloudformation', 'deregister-type', '--region', region, '--type-name', resource_name, '--type', 'RESOURCE'], check=True)
        print(f"Successfully deregistered {resource_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to deregister {resource_name}: {e}")

# Get the region from the command line argument or default to the AWS profile's default region
region = sys.argv[1] if len(sys.argv) > 1 else default_region

# Ensure there is a default region available
if not region:
    print("No default region found in AWS configuration and no region argument provided.")
    sys.exit(1)

# List all resource directories in the aviatrix resources directory
resource_dirs = [f for f in aviatrix_resources_dir.iterdir() if f.is_dir()]

# Loop through the resource directories and deregister each one
for resource_dir in resource_dirs:
    # Convert dashes in resource directory names to two colons
    # Ensure that 'TF::Aviatrix::' is not prefixed twice
    resource_name = resource_dir.name.replace('-', '::')
    if not resource_name.startswith('TF::Aviatrix::'):
        resource_name = f"TF::Aviatrix::{resource_name}"
    deregister_resource(resource_name, region)