#!/bin/bash

# Script to create GitHub repository and sync code

echo "Setting up GitHub repository: compare-city-sizes"

# Navigate to the project directory
cd /Users/urikogan/code/city-compare

# Initialize git repository
git init

# Create .gitignore file
cat > .gitignore << EOF
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Editor directories and files
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log

# Temporary files
*.tmp
EOF

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: City Size Comparison Tool

🗺️ Features:
- Interactive city boundary comparison tool
- Real NYC 5-borough and LA city boundaries
- Overlay with transparency and transformations
- Rotation and translation controls
- High-resolution GeoJSON boundary data

🛠️ Tech Stack:
- Pure HTML/CSS/JavaScript
- Leaflet.js for mapping
- Real boundary data from NYC Open Data & LA GeoHub

🎯 Usage:
- Select two cities to compare
- Use transformation controls to rotate and move overlay
- Compare actual city shapes and sizes

🤖 Generated with Claude Code (https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Create GitHub repository (requires GitHub CLI)
gh repo create compare-city-sizes --public --description "Interactive tool to compare city sizes by overlaying actual boundary data with transformation controls"

# Add remote and push
git branch -M main
git remote add origin https://github.com/$(gh api user --jq .login)/compare-city-sizes.git
git push -u origin main

echo "✅ Repository created and code synced to: https://github.com/$(gh api user --jq .login)/compare-city-sizes"
echo "🌐 GitHub Pages will be available at: https://$(gh api user --jq .login).github.io/compare-city-sizes/accurate-city-comparison.html"

# Enable GitHub Pages
gh api --method POST /repos/$(gh api user --jq .login)/compare-city-sizes/pages \
  --field source='{"branch":"main","path":"/"}'

echo "🎉 Setup complete! Your city comparison tool is now on GitHub."