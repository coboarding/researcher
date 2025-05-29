import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print GitHub token (will be empty if not set)
print(f"GITHUB_TOKEN from .env: {os.environ.get('GITHUB_TOKEN')}")

# Check if the token is set
if not os.environ.get('GITHUB_TOKEN'):
    print("\nWarning: GITHUB_TOKEN is not set in the environment variables!")
    print("Please make sure to set it in the .env file.")
else:
    print("\nGitHub token is set and loaded successfully!")
