#!/bin/bash

# GitHub Token Generator Script
# This script helps generate a GitHub Personal Access Token with the required scopes

# Required scopes for the DevOps Researcher tool
SCOPES=(
  "public_repo"    # Access public repositories
  "repo"           # Full control of private repositories (if needed)
  "read:org"       # Read org and team membership
  "read:user"      # Read user profile data
  "user:email"     # Access user email addresses
)

# Function to display help
show_help() {
  echo "GitHub Token Generator"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -h, --help    Show this help message"
  echo "  -s, --scopes  Show available scopes and exit"
  echo ""
  echo "The token will be generated with the following scopes:"
  printf "  - %s\n" "${SCOPES[@]}"
  echo ""
  echo "Note: You'll need to have 'gh' (GitHub CLI) installed and authenticated."
  echo "      If not installed, you can get it from: https://cli.github.com/"
}

# Check for help or scopes flags
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  show_help
  exit 0
fi

if [[ "$1" == "-s" || "$1" == "--scopes" ]]; then
  echo "Available scopes that will be requested:"
  printf "  - %s\n" "${SCOPES[@]}"
  exit 0
fi

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
  echo "Error: GitHub CLI (gh) is not installed."
  echo "Please install it from: https://cli.github.com/"
  exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
  echo "Error: jq is required but not installed."
  echo "Please install it with: sudo apt-get install jq"
  exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
  echo "You need to authenticate with GitHub first."
  echo "Running: gh auth login"
  gh auth login
fi

# Generate a token with the specified scopes
echo "Generating a new GitHub Personal Access Token with the following scopes:"
printf "  - %s\n" "${SCOPES[@]}"
echo ""

# Join scopes with comma
SCOPES_STR=$(IFS=,; echo "${SCOPES[*]}")

# Generate token with 30-day expiration
TOKEN_INFO=$(gh auth token -h github.com -s "$SCOPES_STR" -e "30d" -n "DevOps Researcher Token" --json token,expiresAt 2>&1)

# Check for errors in token generation
if [ $? -ne 0 ]; then
  echo "Error generating token: $TOKEN_INFO"
  echo "Please check your GitHub authentication and try again."
  exit 1
fi

# Extract token and expiration
TOKEN=$(echo "$TOKEN_INFO" | jq -r '.token' 2>/dev/null)
EXPIRES_AT=$(echo "$TOKEN_INFO" | jq -r '.expiresAt' 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "Error: Failed to generate token. Response was:"
  echo "$TOKEN_INFO"
  exit 1
fi

# Display the token information
echo ""
echo "✅ Successfully generated GitHub Personal Access Token"
echo "====================================================="
echo "Token:        $TOKEN"
echo "Expires at:   $EXPIRES_AT"
echo "Scopes:       $SCOPES_STR"
echo "===================================================="
echo ""
echo "Important: Copy this token now. You won't be able to see it again!"
echo ""

# Ask if user wants to update .env file
read -p "Do you want to update the .env file with this token? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Escape special characters in token for sed
  ESCAPED_TOKEN=$(printf '%s\n' "$TOKEN" | sed -e 's/[\/&]/\\&/g')
  
  # Check if .env exists
  if [ -f .env ]; then
    # Create backup
    cp .env .env.bak
    # Update existing .env file
    if grep -q "^GITHUB_TOKEN=" .env; then
      # Update existing token
      sed -i.bak "s/^GITHUB_TOKEN=.*/GITHUB_TOKEN=$ESCAPED_TOKEN/" .env
    else
      # Add new token
      echo "GITHUB_TOKEN=$TOKEN" >> .env
    fi
    echo "✅ Updated .env file with the new token"
  else
    # Create new .env file
    echo "GITHUB_TOKEN=$TOKEN" > .env
    echo "✅ Created new .env file with the token"
  fi
fi

echo ""
echo "To use this token in the current shell session, run:"
echo "export GITHUB_TOKEN=\"$TOKEN\""
echo ""
echo "Note: This token has been saved to your GitHub account and will expire on $EXPIRES_AT"
