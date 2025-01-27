#!/bin/bash
set -e  # Exit on any error

# Script configuration
PYTHON_VERSION="3.11"
VENV_DIR="create_layer"
OUTPUT_ZIP="site_packages_layer.zip"
LAYER_DIR="python/lib/python${PYTHON_VERSION}/site-packages"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

# Clean up any existing files
rm -rf python "${OUTPUT_ZIP}" "${VENV_DIR}"

# Create and activate virtual environment
python${PYTHON_VERSION} -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

# Install packages from requirements file
pip install --upgrade pip
pip install -r "${REQUIREMENTS_FILE}"

# Create the layer directory structure
mkdir -p "${LAYER_DIR}"

# Copy only the contents of site-packages
cp -r "${VENV_DIR}/lib/python${PYTHON_VERSION}/site-packages/"* "${LAYER_DIR}/"

# Create the zip file with the correct structure
zip -r "${OUTPUT_ZIP}" python/

# Clean up
deactivate
rm -rf "${VENV_DIR}" python

echo "Layer creation complete: ${OUTPUT_ZIP}"



# ------------------------------------------------------------------------------------------------------------------
# Export the environment variables in the .env file so that Terraform collects them when deploying.
# Need to name the variables as TF_VAR_<variable_name>

# The .env file is up one directory, in the project root
ENV_FILE="../.env"

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: .env file not found at $ENV_FILE!"
  exit 1
fi

# Ensure the file has a trailing newline. This is essential to be able to read the last env variable in the .env
# file. The shell tool requires a trailing newline to be able to process the file
if [ -n "$(tail -c 1 "$ENV_FILE")" ]; then
  echo "" >> "$ENV_FILE"
fi

# Loop through each line in the .env file
while IFS='=' read -r key value; do
  # Skip empty lines and comments
  if [[ -z "$key" || "$key" =~ ^# ]]; then
    continue
  fi
  
  # Prefix the key with TF_VAR_
  export "TF_VAR_${key}=${value}"

done < "$ENV_FILE"

echo "Environment variables prefixed with TF_VAR_ have been exported from $ENV_FILE."