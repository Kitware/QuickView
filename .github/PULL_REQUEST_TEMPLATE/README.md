# Pull Request Templates

This directory contains templates for different types of pull requests in the
QuickView project.

## Available Templates

### 1. Default Template (`../pull_request_template.md`)

- Use for general pull requests
- Automatically loaded when creating a PR without specifying a template

### 2. Release Branch Template (`release_branch.md`)

- Use when creating a PR for a new release
- Includes comprehensive release checklist
- Access via: `?template=release_branch.md` in PR URL

### 3. Feature Branch Template (`feature_branch.md`)

- Use when adding new features
- Focuses on user stories and implementation details
- Access via: `?template=feature_branch.md` in PR URL

### 4. Bug Fix Template (`bugfix_branch.md`)

- Use when fixing bugs
- Emphasizes root cause analysis and testing
- Access via: `?template=bugfix_branch.md` in PR URL

## How to Use Templates

1. **Via GitHub Web Interface**:

   - Click "New Pull Request"
   - Add `?template=TEMPLATE_NAME.md` to the URL
   - Example:
     `https://github.com/E3SM-Project/QuickView/compare/main...feature-branch?template=feature_branch.md`

2. **Via GitHub CLI**:

   ```bash
   gh pr create --template .github/PULL_REQUEST_TEMPLATE/feature_branch.md
   ```

3. **Via URL Parameters**:
   - Feature: `?template=feature_branch.md`
   - Bug Fix: `?template=bugfix_branch.md`
   - Release: `?template=release_branch.md`

## Best Practices

1. **Choose the Right Template**: Select the template that best matches your PR
   type
2. **Fill Out Completely**: Don't skip sections - mark as N/A if not applicable
3. **Be Specific**: Provide detailed information to help reviewers
4. **Update as Needed**: Keep the PR description updated as changes are made
5. **Link Issues**: Always link related issues using GitHub's linking syntax

## Template Guidelines

- **Description**: Be concise but comprehensive
- **Testing**: Document all testing performed
- **Screenshots**: Include for UI changes
- **Checklist**: Complete all items before requesting review
- **Breaking Changes**: Clearly highlight any breaking changes

## Contributing to Templates

If you need to modify these templates:

1. Consider the impact on existing workflows
2. Discuss changes with the team first
3. Update this README if adding new templates
4. Ensure templates remain clear and actionable
