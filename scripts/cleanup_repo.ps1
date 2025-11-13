<#
Cleanup script for preparing repository before pushing to GitHub.
Usage: Open PowerShell in the project root and run:
  .\scripts\cleanup_repo.ps1

This script removes common local files from the git index (does not delete them locally):
it will attempt to untrack `venv`, `.env`, `.cache`, and `.vscode` if they were committed.
After running the script, review `git status` and commit the changes, then push.
NOTE: this script requires `git` to be installed and the folder to be a git repository.
#>
if (-not (Test-Path .git)) {
    Write-Host "No .git directory found. Initialize git before running this script." -ForegroundColor Yellow
    exit 1
}

# Untrack typical local files
$targets = @('venv', '.venv', '.env', '.cache', 'node_modules', '.vscode', '.idea')
foreach ($t in $targets) {
    if (Test-Path $t) {
        Write-Host "Attempting to untrack: $t"
        git rm -r --cached $t 2>$null
    }
}

Write-Host "Review the git changes. If they look correct, commit them:"
Write-Host "  git add .gitignore"
Write-Host "  git commit -m 'Remove local files from repo and update .gitignore'"
Write-Host "Then push to remote with: git push -u origin main"