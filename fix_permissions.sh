#!/bin/bash
# fix_permissions.sh - Fix permissions for the drehteller configuration

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Drehteller Configuration Permission Fixer${NC}"
echo "==========================================="

# Get current user
CURRENT_USER=$(whoami)
echo -e "Current user: ${GREEN}${CURRENT_USER}${NC}"

# Check if script is being run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Note: Not running as root. Some operations might fail.${NC}"
  echo "Consider running with sudo if permission issues persist."
fi

# Project directory
PROJECT_DIR="/home/alex/Dokumente/drehteller_360_grad_fotos"
echo -e "Project directory: ${GREEN}${PROJECT_DIR}${NC}"

# Find the config file
CONFIG_FILE="${PROJECT_DIR}/config.json"

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo -e "Config file exists: ${GREEN}${CONFIG_FILE}${NC}"
    echo -e "Current permissions: $(ls -la ${CONFIG_FILE})"
else
    echo -e "${YELLOW}Config file does not exist yet: ${CONFIG_FILE}${NC}"
    echo -e "Directory permissions: $(ls -la $(dirname ${CONFIG_FILE}))"
fi

# Fix permissions for the project directory and all files
echo -e "\n${YELLOW}Fixing permissions for project directory and files...${NC}"
chown -R alex:alex "${PROJECT_DIR}"
chmod -R 755 "${PROJECT_DIR}"
echo "Directory permissions updated."

# Explicitly set permissions for the config file or its parent directory
if [ -f "$CONFIG_FILE" ]; then
    chmod 644 "${CONFIG_FILE}"
    echo -e "Config file permissions set to: ${GREEN}644${NC}"
else
    chmod 755 "$(dirname ${CONFIG_FILE})"
    echo -e "Config directory permissions set to: ${GREEN}755${NC}"
fi

# Create an empty config file if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "\n${YELLOW}Creating empty config file...${NC}"
    echo "{}" > "${CONFIG_FILE}"
    chown alex:alex "${CONFIG_FILE}"
    chmod 644 "${CONFIG_FILE}"
    echo -e "Empty config file created: ${GREEN}${CONFIG_FILE}${NC}"
fi

# Restart the service
echo -e "\n${YELLOW}Would you like to restart the drehteller360 service? (y/n)${NC}"
read -r answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo "Restarting drehteller360 service..."
    systemctl restart drehteller360.service
    echo "Service restarted."
    echo "You can check the service status with: sudo systemctl status drehteller360.service"
else
    echo "Service not restarted. Remember to restart it manually with:"
    echo "sudo systemctl restart drehteller360.service"
fi

echo -e "\n${GREEN}Done!${NC}"
