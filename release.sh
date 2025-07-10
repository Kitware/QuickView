#!/bin/bash

# Function to print output
print_status() {
    echo "[INFO] $1" >&2
}

print_success() {
    echo "[SUCCESS] $1" >&2
}

print_warning() {
    echo "[WARNING] $1" >&2
}

print_error() {
    echo "[ERROR] $1" >&2
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [patch|minor|major]"
    echo ""
    echo "This script will:"
    echo "  1. Bump the version using bump2version"
    echo "  2. Commit the changes to main"
    echo "  3. Create a release PR from main to release branch"
    echo ""
    echo "Examples:"
    echo "  $0 patch   # 0.1.0 -> 0.1.1"
    echo "  $0 minor   # 0.1.0 -> 0.2.0"
    echo "  $0 major   # 0.1.0 -> 1.0.0"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."

    # Check if bump2version is installed
    if ! command -v bump2version &> /dev/null; then
        print_error "bump2version is not installed. Install it with: pip install bump2version"
        exit 1
    fi

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI is not installed. Install it from: https://cli.github.com/"
        exit 1
    fi

    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        print_error "Not in a git repository"
        exit 1
    fi

    # Check if we're on main/master branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" && "$current_branch" != "master" ]]; then
        print_error "Must be on main or master branch. Currently on: $current_branch"
        exit 1
    fi

    # Check if working directory is clean
    if ! git diff-index --quiet HEAD --; then
        print_error "Working directory is not clean. Please commit or stash your changes."
        exit 1
    fi

    print_success "All prerequisites met"
}

# Function to get current version from pyproject.toml
get_current_version() {
    python -c "import tomllib; f=open(\"pyproject.toml\",\"rb\"); data=tomllib.load(f); f.close(); print(data[\"project\"][\"version\"])"
}

# Function to get previous version from git tags
get_previous_version() {
    git describe --tags --abbrev=0 2>/dev/null | sed "s/^v//" || echo "0.0.0"
}

# Function to generate changelog
generate_changelog() {
    local prev_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    if [ -z "$prev_tag" ]; then
        echo "- Initial release"
    else
        # Get commits since last tag, excluding merge commits
        git log --oneline --pretty=format:"- %s" --no-merges ${prev_tag}..HEAD | head -15
    fi
}

# Function to bump version
bump_version() {
    local version_type=$1

    print_status "Getting current version..."
    local old_version=$(get_current_version)
    print_status "Current version: v$old_version"

    print_status "Bumping $version_type version..."
    # Redirect all bump2version output to stderr to avoid capturing it
    bump2version $version_type --verbose >&2
    if [ $? -ne 0 ]; then
        print_error "Failed to bump version"
        exit 1
    fi

    local new_version=$(get_current_version)
    print_success "Version bumped: v$old_version -> v$new_version"

    # Debug: show what we're returning
    print_status "Returning version: $new_version" >&2

    echo "$new_version"
}

# Function to commit and push changes
commit_and_push() {
    local version=$1
    local branch=$(git branch --show-current)

    # Debug: show what version we received
    print_status "Received version for push: '$version'" >&2

    print_status "Pushing changes to $branch..."
    if ! git push origin $branch; then
        print_error "Failed to push changes"
        exit 1
    fi

    # Push the new tag (bump2version already created it)
    print_status "Pushing new tag v${version}..."
    if ! git push origin v${version}; then
        # Check if tag already exists on remote
        if git ls-remote --tags origin | grep -q "refs/tags/v${version}$"; then
            print_warning "Tag v${version} already exists on remote"
        else
            print_error "Failed to push tag v${version}"
            exit 1
        fi
    fi

    print_success "Changes and tags pushed to $branch"
}

# Function to create release PR
create_release_pr() {
    local current_version=$1
    local previous_version=$(get_previous_version)

    # Determine release type
    IFS="." read -ra CURRENT <<< "$current_version"
    IFS="." read -ra PREVIOUS <<< "$previous_version"

    if [ "${CURRENT[0]}" != "${PREVIOUS[0]}" ]; then
        release_type="major"
    elif [ "${CURRENT[1]}" != "${PREVIOUS[1]}" ]; then
        release_type="minor"
    else
        release_type="patch"
    fi

    print_status "Generating changelog..."
    local changelog=$(generate_changelog)

    print_status "Creating release PR..."

    # Create PR using GitHub CLI
    gh pr create \
        --base release \
        --head $(git branch --show-current) \
        --title "Release v${current_version}" \
        --body "$(cat << EOF
## Release v${current_version}

This pull request contains all changes for the **v${current_version}** release.

### Release Information
- **Previous version**: v${previous_version}
- **New version**: v${current_version}
- **Release type**: ${release_type}
- **Release date**: $(date +%Y-%m-%d)

### What Changed

${changelog}

### Release Checklist
- [x] Version bumped in all files
- [ ] All tests passing
- [ ] Documentation updated (if needed)
- [ ] Breaking changes documented (if any)
- [ ] Ready for production deployment

### Files Updated
- quickview/__init__.py - Version updated to ${current_version}
- pyproject.toml - Version updated to ${current_version}
- src-tauri/tauri.conf.json - Version updated to ${current_version}
- src-tauri/Cargo.toml - Version updated to ${current_version}

### Post-Merge Actions
After merging this PR:
1. Git tag v${current_version} will be available
2. Tauri build will trigger automatically
3. Draft release will be created with distributables
4. Release will be published automatically with release notes

### Important Notes
- This is a **${release_type}** release
- Review all changes carefully before merging
- Ensure all CI checks pass before merging

---

**Release prepared by**: @$(git config user.name)
**Release type**: ${release_type}
**Target branch**: release
**Commit count**: $(git rev-list --count HEAD ^$(git merge-base HEAD release) 2>/dev/null || echo "N/A")
EOF
)" \
        --assignee @me \
        --label "release,${release_type}" || {
        print_error "Failed to create PR"
        exit 1
    }

    print_success "Release PR created successfully!"
}

# Main function
main() {
    # Check if version type is provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi

    local version_type=$1

    # Validate version type
    if [[ ! "$version_type" =~ ^(patch|minor|major)$ ]]; then
        print_error "Invalid version type: $version_type"
        show_usage
        exit 1
    fi

    echo "QuickView Release Tool"
    echo "======================"

    # Run checks
    check_prerequisites

    # Bump version
    local new_version=$(bump_version $version_type)

    # Commit and push changes
    commit_and_push $new_version

    # Create release PR
    create_release_pr $new_version

    echo ""
    print_success "Release process completed!"
    echo "Version: v$new_version ($version_type)"
    echo "Review and merge the PR to trigger the release pipeline"
    echo "PR URL: $(gh pr view --json url --jq .url 2>/dev/null || echo Check GitHub for PR link)"
}

# Run main function
main "$@"
