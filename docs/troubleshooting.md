# Troubleshooting guide

Comprehensive solutions for common issues with Claude Code Arsenal installation, configuration, and usage.

## Quick diagnostics

### System check

```bash
# Run comprehensive system check
make info

# Check specific components
make validate-structure

# Verify dependencies
uv --version
python3 --version
claude --version
```

### Installation verification

```bash
# Check what's installed
ls ~/.claude/skills/

# Test basic functionality
make dry-run
make test
```

## Installation issues

### UV package manager problems

#### UV not found
```bash
# Error: command not found: uv
# Solution: Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell configuration
source ~/.bashrc  # or ~/.zshrc for zsh
```

#### UV installation fails
```bash
# Error: Installation script fails
# Solution: Manual installation
pip install uv

# Or use package manager
# macOS: brew install uv
# Ubuntu: sudo apt install uv
```

#### Permission denied during UV install
```bash
# Error: Permission denied writing to /usr/local/bin
# Solution: Install to user directory
curl -LsSf https://astral.sh/uv/install.sh | sh -s -- --user

# Or use sudo for system install
curl -LsSf https://astral.sh/uv/install.sh | sudo sh
```

### Python version issues

#### Python 3.12+ not available
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

#### Multiple Python versions conflict
```bash
# Error: Wrong Python version used
# Solution: Specify Python version explicitly

# Use specific Python version
uv sync --python python3.12

# Set UV to use specific Python
export UV_PYTHON=python3.12
```

### Claude Code issues

#### Claude Code not installed
```bash
# Error: claude command not found
# Solution: Install Claude Code
# Visit: https://claude.ai/code

# Verify installation
which claude
claude --version
```

#### Claude Code not in PATH
```bash
# Error: Command not found after installation
# Solution: Add to PATH

# Add to shell profile
echo 'export PATH="$PATH:/path/to/claude"' >> ~/.bashrc
source ~/.bashrc
```

### Repository clone issues

#### Git clone fails
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

#### Slow clone due to large repository
```bash
# Error: Clone takes too long
# Solution: Shallow clone

# Clone only recent history
git clone --depth 1 https://github.com/mgiovani/cc-arsenal.git

# Clone specific branch
git clone -b main --single-branch https://github.com/mgiovani/cc-arsenal.git
```

## Configuration issues

### Permission problems

#### Cannot write to ~/.claude directory
```bash
# Error: Permission denied writing to ~/.claude
# Solution: Fix directory permissions

# Create directory with correct permissions
mkdir -p ~/.claude
chmod 755 ~/.claude

# Fix ownership if needed
sudo chown -R $USER:$USER ~/.claude
```

### Configuration file issues

#### Invalid YAML syntax
```bash
# Error: YAML parsing error in configuration
# Solution: Validate and fix YAML

# Check YAML syntax
python3 -c "import yaml; yaml.safe_load(open('~/.claude/hook-config.yaml'))"

# Use YAML validator online or install yamllint
pip install yamllint
yamllint ~/.claude/hook-config.yaml
```

#### Missing configuration files
```bash
# Error: Configuration file not found
# Solution: Generate default configuration

# Generate default configurations
make configure

# Or create manually
make install  # Creates default configs
```

### Skill issues

#### Skills not available in Claude Code
```bash
# Error: Skills not showing up
# Solution: Verify installation and restart

# Check skill installation
ls -la ~/.claude/skills/

# Verify skill file format
head -20 ~/.claude/skills/create-skill/SKILL.md

# Restart Claude Code completely
# Close all Claude Code windows and restart
```

#### Skill file format errors
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

#### Skill permissions
```bash
# Error: Cannot read skill files
# Solution: Fix file permissions

# Fix skill file permissions
find ~/.claude/skills -name "*.md" -exec chmod 644 {} \;

# Fix directory permissions
find ~/.claude/skills -type d -exec chmod 755 {} \;
```

## Runtime issues

### Skill execution problems

#### Skills not found
```bash
# Error: Claude skills not available
# Solution: Verify skill installation

# Check skill installation
ls ~/.claude/skills/

# Test in Claude Code: ask a question that should trigger the skill,
# or invoke a user-invoked skill directly, e.g. /git-commit

# Verify a skill's frontmatter
head -10 ~/.claude/skills/git-commit/SKILL.md
```

#### Permission denied running a skill's scripts
```bash
# Error: Cannot execute a skill's bundled script
# Solution: Check permissions and dependencies

# Fix script permissions
chmod +x ~/.claude/skills/**/scripts/*.sh

# Check if required tools are installed
which git npm pytest ruff
```


### Performance issues

#### Slow skill response
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

#### High memory usage
```bash
# Error: High memory consumption
# Solution: Optimize configuration

# Clear caches
make clean

# Restart Claude Code
```

#### Token limit issues
```bash
# Error: Running out of tokens quickly
# Solution: Optimize token usage

# Check token usage
# Enhanced statusline shows usage patterns

# Use smart scheduling
make -C integrations/claude-code/claude-hi setup

# Monitor usage patterns
tail ~/.claude/logs/usage.log
```

## Component-Specific issues

### Smart session scheduler (Claude Hi)

#### Cron jobs not working
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

#### Hi messages not triggering sessions
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

#### Schedule not matching expectations
```bash
# Error: Wrong timing for hi messages
# Solution: Verify and adjust schedule

# Check current schedule
make -C integrations/claude-code/claude-hi status

# Remove and recreate
make -C integrations/claude-code/claude-hi remove
make -C integrations/claude-code/claude-hi setup
```

### Enhanced statusline

#### Statusline not showing
```bash
# Error: Statusline not visible
# Solution: Check installation and shell integration

# Verify statusline installation
ls ~/.claude/scripts/claude/statusline/

# Check shell integration
grep claude ~/.bashrc ~/.zshrc

# Reinstall statusline
make install-statusline
```

#### Incorrect usage data
```bash
# Error: Statusline shows wrong information
# Solution: Debug with STATUSLINE_DEBUG and inspect the /tmp caches

# Test statusline script with debug logging
STATUSLINE_DEBUG=1 bash -c 'echo "{\"model\":{\"id\":\"test\"}}" | ~/.claude/scripts/claude/statusline/statusline.sh'
tail -20 /tmp/claude_statusline_debug.log

# Rate-limit/usage data is cached in /tmp, not ~/.claude/logs — clear it to force a refresh
# (default account; append .<hash> for a CLAUDE_CODE_OAUTH_TOKEN-scoped account)
rm -f /tmp/claude_rate_limits_cache.json /tmp/claude_oauth_usage_cache.json
```

Full reference, including every `STATUSLINE_*`/`CLAUDE_*` env var and multi-account cache layout: [Statusline Guide](../integrations/claude-code/statusline/STATUSLINE.md).

## Development environment issues

### Testing problems

#### Tests fail
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

#### Coverage issues
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

### Linting and formatting issues

#### Ruff errors
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

#### Type checking failures
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

## Network and connectivity issues

### Claude API problems

#### Authentication errors
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

#### Network timeouts
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

### Update issues

#### Update failures
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

#### Version conflicts
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

## Logging and debugging

### Enable debug logging

```bash
# Enable verbose logging
export CC_ARSENAL_DEBUG=1

# Enable component-specific debugging
export CC_ARSENAL_DEBUG_SKILLS=1
export CC_ARSENAL_DEBUG_HOOKS=1
export CC_ARSENAL_DEBUG_COMMANDS=1
```

### Log locations

```bash
# Main logs
~/.claude/logs/arsenal.log      # Main application log
~/.claude/logs/skills.log       # Skill execution log
~/.claude/logs/commands.log     # Command execution log

# Component logs
/tmp/claude_statusline_debug.log        # Statusline debug info (STATUSLINE_DEBUG=1)
/tmp/statusline_live_cache/oauth_errors.log  # Statusline OAuth usage fetch errors
~/.claude/logs/claude-hi.log    # Session scheduler log
~/.claude/logs/usage.log        # Token usage tracking
```

### Debug commands

```bash
# Component status
make info                       # Overall status
make validate-structure         # Structural validation
make -C integrations/claude-code/claude-hi status          # Session scheduler status

# Test components
make test                      # Run test suite
make dry-run                   # Preview installation
```

## Getting help

### Self-Service resources

1. **Documentation**: Check docs/ directory for detailed guides
2. **Examples**: Review examples/ directory for working configurations
3. **Test Suite**: Run tests to verify installation
4. **Logs**: Check log files for error details

### Community support

1. **GitHub Issues**: https://github.com/mgiovani/cc-arsenal/issues
2. **GitHub Discussions**: https://github.com/mgiovani/cc-arsenal/discussions
3. **Documentation**: Browse all documentation in docs/

### Reporting issues

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

### Emergency recovery

#### Complete reset
```bash
# Backup current configuration
cp -r ~/.claude ~/.claude.backup.$(date +%Y%m%d)

# Remove all Arsenal components
rm -rf ~/.claude/skills ~/.claude/commands

# Reinstall clean
make install
```

#### Restore from backup
```bash
# Restore previous configuration
mv ~/.claude ~/.claude.broken
mv ~/.claude.backup.YYYYMMDD ~/.claude

# Restart Claude Code
```

## Prevention

### Regular maintenance

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
make info                      # Check component status
tail -f ~/.claude/logs/arsenal.log  # Monitor activity

# Check for updates
git fetch origin
git status
```

### Best practices

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
