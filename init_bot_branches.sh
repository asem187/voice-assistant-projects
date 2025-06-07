# !/bin/bash
# Initialize git branches for each bot
# Run this script once after cloning the repository

branches=(
  part01_setup
  part02_database
  part03_stt
  part04_tts
  part05_openai
  part06_cli
  part07_dashboard
  part08_realtime
  part09_testing
  part10_deploy
)

for b in "${branches[@]}"; do
  git branch "$b" 2>/dev/null && echo "Created branch $b" || echo "Branch $b already exists"
done

echo "\nSwitch to a branch with: git checkout <branch-name>"
