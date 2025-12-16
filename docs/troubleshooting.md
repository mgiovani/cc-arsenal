# Troubleshooting Guide

Comprehensive solutions for common issues with Claude Code Arsenal installation, configuration, and usage.

## Quick Diagnostics

### System Check

```bash
# Run comprehensive system check
make info

# Check specific components
make validate-structure
make status

# Verify dependencies
uv --version
python3 --version
claude --version
```

### Installation Verification

```bash
# Check what's installed
ls ~/.claude/commands/
ls ~/.claude/skills/

# Test basic functionality
make dry-run
make test
```

## Installation Issues

### UV Package Manager Problems

#### UV Not Found
```bash
# Error: command not found: uv
# Solution: Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc for zsh
```

#### UV Installation Fails
```bash
# Error: Installation script fails
# Solution: Manual installation
pip install uv

# Or use package manager
# macOS: brew install uv
# Ubuntu: sudo apt install uv
```

#### Permission Denied During UV Install
```bash
# Error: Permission denied writing to /usr/local/bin
# Solution: Install to user directory
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --user

# Or use sudo for system install
curl -LsSf https://astral.sh/uv/install.sh | sudo sh
```

### Python Version Issues

#### Python 3.12+ Not Available
```bash
# Error: Python 3.12 not found
# Solution: Install Python 3.12+

# macOS with Homebrew
brew install python@3.12

# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv

# CentOS/RHEL
sudo dnf install python3.12

# Windows
# Download from python.org or use pyenv
```

#### Multiple Python Versions Conflict
```bash
# Error: Wrong Python version used
# Solution: Specify Python version explicitly

# Use specific Python version
uv sync --python python3.12

# Set UV to use specific Python
export UV_PYTHON=python3.12
```

### Claude Code Issues

#### Claude Code Not Installed
```bash
# Error: claude command not found
# Solution: Install Claude Code
# Visit: https://claude.ai/code

# Verify installation
which claude
claude --version
```

#### Claude Code Not in PATH
```bash
# Error: Command not found after installation
# Solution: Add to PATH

# Add to shell profile
echo 'export PATH="$PATH:/path/to/claude"' >> ~/.bashrc
source ~/.bashrc
```

### Repository Clone Issues

#### Git Clone Fails
```bash
# Error: Repository not found or access denied
# Solution: Check repository URL and access

# Use HTTPS instead of SSH
git clone https://github.com/mgiovani/cc-arsenal.git

# Check network connectivity
ping github.com

# Try with verbose output
git clone --verbose https://github.com/mgiovani/cc-arsenal.git
```

#### Slow Clone Due to Large Repository
```bash
# Error: Clone takes too long
# Solution: Shallow clone

# Clone only recent history
git clone --depth 1 https://github.com/mgiovani/cc-arsenal.git

# Clone specific branch
git clone -b main --single-branch https://github.com/mgiovani/cc-arsenal.git
```

## Configuration Issues

### Permission Problems

#### Cannot Write to ~/.claude Directory
```bash
# Error: Permission denied writing to ~/.claude
# Solution: Fix directory permissions

# Create directory with correct permissions
mkdir -p ~/.claude
chmod 755 ~/.claude

# Fix ownership if needed
sudo chown -R $USER:$USER ~/.claude
```

### Configuration File Issues

#### Invalid YAML Syntax
```bash
# Error: YAML parsing error in configuration
# Solution: Validate and fix YAML

# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('~/.claude/hook-config.yaml'))"

# Use YAML validator online or install yamllint
pip install yamllint
yamllint ~/.claude/hook-config.yaml
```

#### Missing Configuration Files
```bash
# Error: Configuration file not found
# Solution: Generate default configuration

# Generate default configurations
make configure

# Or create manually
make install  # Creates default configs
```

### Skill Issues

#### Skills Not Available in Claude Code
```bash
# Error: Skills not showing up
# Solution: Verify installation and restart

# Check skill installation
ls -la ~/.claude/skills/

# Verify skill file format
head -20 ~/.claude/skills/skill-creator/SKILL.md

# Restart Claude Code completely
# Close all Claude Code windows and restart
```

#### Skill File Format Errors
```bash
# Error: Invalid skill file format
# Solution: Validate skill YAML frontmatter

# Check YAML frontmatter
python3 -c "
import yaml
with open('SKILL.md') as f:
    content = f.read()
    if '---' in content:
        yaml_part = content.split('---')[1]
        yaml.safe_load(yaml_part)
        print('YAML is valid')
"
```

#### Skill Permissions
```bash
# Error: Cannot read skill files
# Solution: Fix file permissions

# Fix skill file permissions
find ~/.claude/skills -name "*.md" -exec chmod 644 {} \;

# Fix directory permissions
find ~/.claude/skills -type d -exec chmod 755 {} \;
```

## Runtime Issues

### Command Execution Problems

#### Commands Not Found
```bash
# Error: Claude commands not available
# Solution: Verify command installation

# Check command installation
ls ~/.claude/commands/

# Test command syntax in Claude Code
# /help to see available commands

# Verify command file format
head -10 ~/.claude/commands/security/security-scan.md
```

#### Command Permission Denied
```bash
# Error: Cannot execute commands
# Solution: Check permissions and dependencies

# Fix command permissions
chmod +x ~/.claude/commands/**/*.sh

# Check if required tools are installed
which git npm pytest ruff
```


### Performance Issues

#### Slow Skill Response
```bash
# Error: Skills take too long to load
# Solution: Optimize usage and check resources

# Check system resources
top
df -h

# Monitor Claude Code process
ps aux | grep claude

# Check network connectivity
ping claude.ai
```

#### High Memory Usage
```bash
# Error: High memory consumption
# Solution: Optimize configuration

# Clear caches
make clean

# Restart Claude Code
```

#### Token Limit Issues
```bash
# Error: Running out of tokens quickly
# Solution: Optimize token usage

# Check token usage
# Enhanced statusline shows usage patterns

# Use smart scheduling
make claude-hi-setup

# Monitor usage patterns
tail ~/.claude/logs/usage.log
```

## Component-Specific Issues

### Smart Session Scheduler (Claude Hi)

#### Cron Jobs Not Working
```bash
# Error: Hi messages not sent automatically
# Solution: Debug cron configuration

# Check cron jobs
crontab -l | grep send_hi

# Check cron service
sudo systemctl status cron  # Linux
# or check launchd on macOS

# Test manual execution
~/.claude/send_hi.sh
```

#### Hi Messages Not Triggering Sessions
```bash
# Error: Hi sent but session doesn't start
# Solution: Check Claude Code connectivity

# Test manual hi
echo "hi" | claude

# Check Claude Code authentication
claude auth status

# Verify network connectivity
ping claude.ai
```

#### Schedule Not Matching Expectations
```bash
# Error: Wrong timing for hi messages
# Solution: Verify and adjust schedule

# Check current schedule
make claude-hi-status

# Remove and recreate
make claude-hi-remove
make claude-hi-setup
```

### Enhanced Statusline

#### Statusline Not Showing
```bash
# Error: Statusline not visible
# Solution: Check installation and shell integration

# Verify statusline installation
ls ~/.claude/statusline/

# Check shell integration
grep claude ~/.bashrc ~/.zshrc

# Reinstall statusline
make statusline-install
```

#### Incorrect Usage Data
```bash
# Error: Statusline shows wrong information
# Solution: Debug data sources

# Check data files
ls ~/.claude/logs/

# Test statusline script
~/.claude/statusline/statusline.sh --debug

# Reset usage tracking
rm ~/.claude/logs/usage.json
```

## Development Environment Issues

### Testing Problems

#### Tests Fail
```bash
# Error: Test suite failures
# Solution: Debug test environment

# Run tests with verbose output
make test -v

# Check test dependencies
uv sync --group dev

# Run specific test
uv run pytest tests/test_specific.py -v
```

#### Coverage Issues
```bash
# Error: Low test coverage
# Solution: Identify missing tests

# Generate coverage report
make coverage

# View detailed coverage
open htmlcov/index.html

# Check uncovered lines
uv run pytest --cov-report=term-missing
```

### Linting and Formatting Issues

#### Ruff Errors
```bash
# Error: Linting failures
# Solution: Fix code style issues

# Show all issues
make lint

# Auto-fix issues
make format

# Check specific rules
uv run ruff check --explain E501
```

#### Type Checking Failures
```bash
# Error: MyPy type errors
# Solution: Fix type annotations

# Run type checking
make type-check

# Show detailed errors
uv run mypy --show-error-codes src/

# Ignore specific errors temporarily
# Add # type: ignore comment
```

## Network and Connectivity Issues

### Claude API Problems

#### Authentication Errors
```bash
# Error: API authentication failed
# Solution: Check Claude Code authentication

# Check auth status
claude auth status

# Re-authenticate
claude auth login

# Check credentials
cat ~/.claude/credentials  # Be careful with sensitive data
```

#### Network Timeouts
```bash
# Error: Request timeouts
# Solution: Check network and proxy settings

# Test connectivity
curl -I https://claude.ai

# Check proxy settings
echo $HTTP_PROXY $HTTPS_PROXY

# Configure proxy if needed
export HTTPS_PROXY=http://proxy.company.com:8080
```

### Update Issues

#### Update Failures
```bash
# Error: Cannot update repository
# Solution: Clean update process

# Clean and update
git clean -fd
git reset --hard HEAD
git pull origin main

# Force reinstall
make clean
make install
```

#### Version Conflicts
```bash
# Error: Version compatibility issues
# Solution: Check version requirements

# Check current versions
git describe --tags
claude --version
python3 --version

# Update to compatible versions
git checkout v1.0.0  # or latest stable tag
```

## Logging and Debugging

### Enable Debug Logging

```bash
# Enable verbose logging
export CC_ARSENAL_DEBUG=1

# Enable component-specific debugging
export CC_ARSENAL_DEBUG_SKILLS=1
export CC_ARSENAL_DEBUG_HOOKS=1
export CC_ARSENAL_DEBUG_COMMANDS=1
```

### Log Locations

```bash
# Main logs
~/.claude/logs/arsenal.log      # Main application log
~/.claude/logs/skills.log       # Skill execution log
~/.claude/logs/commands.log     # Command execution log

# Component logs
~/.claude/logs/statusline.log   # Statusline debug info
~/.claude/logs/claude-hi.log    # Session scheduler log
~/.claude/logs/usage.log        # Token usage tracking
```

### Debug Commands

```bash
# Component status
make info                       # Overall status
make validate-structure         # Structural validation
make claude-hi-status          # Session scheduler status

# Test components
make test                      # Run test suite
make dry-run                   # Preview installation
```

## Getting Help

### Self-Service Resources

1. **Documentation**: Check docs/ directory for detailed guides
2. **Examples**: Review examples/ directory for working configurations
3. **Test Suite**: Run tests to verify installation
4. **Logs**: Check log files for error details

### Community Support

1. **GitHub Issues**: https://github.com/mgiovani/cc-arsenal/issues
2. **GitHub Discussions**: https://github.com/mgiovani/cc-arsenal/discussions
3. **Documentation**: Browse all documentation in docs/

### Reporting Issues

When reporting issues, include:

```bash
# System information
make info

# Error logs
tail -50 ~/.claude/logs/arsenal.log

# Configuration
ls -la ~/.claude/

# Reproduction steps
# Clear description of what you were trying to do
# Exact commands that failed
# Complete error messages
```

### Emergency Recovery

#### Complete Reset
```bash
# Backup current configuration
cp -r ~/.claude ~/.claude.backup.$(date +%Y%m%d)

# Remove all Arsenal components
rm -rf ~/.claude/skills ~/.claude/commands

# Reinstall clean
make install
```

#### Restore from Backup
```bash
# Restore previous configuration
mv ~/.claude ~/.claude.broken
mv ~/.claude.backup.YYYYMMDD ~/.claude

# Restart Claude Code
```

## Prevention

### Regular Maintenance

```bash
# Weekly maintenance routine
make clean                     # Clean temporary files
git pull origin main          # Get latest updates
make install                   # Update installation
make test                      # Verify functionality
```

### Monitoring

```bash
# Monitor system health
make status                    # Check component status
tail -f ~/.claude/logs/arsenal.log  # Monitor activity

# Check for updates
git fetch origin
git status
```

### Best Practices

1. **Regular Updates**: Keep the arsenal updated to latest stable version
2. **Backup Configuration**: Backup ~/.claude before major changes
3. **Test Changes**: Use dry-run before installing updates
4. **Monitor Logs**: Regularly check logs for warnings or errors
5. **Resource Monitoring**: Monitor system resources during heavy usage

---

For additional help:
- [Getting Started](getting-started.md)
- [Skill Development](skill-development.md)
- [Contributing](../CONTRIBUTING.md)
