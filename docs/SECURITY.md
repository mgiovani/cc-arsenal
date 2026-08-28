# Security policy

## Our commitment

We take the security of cc-arsenal seriously. If you discover a security vulnerability, we appreciate your help in disclosing it to us responsibly.

## Supported versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please email us at:

**e@giovani.dev**

Include the following information in your report:

- Type of vulnerability
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability
- Suggested fix (if you have one)

### What to expect

1. **Acknowledgment** - We'll respond within 48 hours to acknowledge receipt of your report
2. **Investigation** - We'll investigate the issue and keep you updated on our progress
3. **Resolution** - We'll work on a fix and coordinate a release timeline with you
4. **Credit** - We'll credit you in our security advisory (unless you prefer to remain anonymous)

### Disclosure policy

- Please give us reasonable time to fix the vulnerability before any public disclosure
- We'll coordinate the disclosure timeline with you
- We aim to release security patches as quickly as possible

## Security best practices

When using cc-arsenal:

### For users

- **Keep Updated** - Always use the latest version to get security patches
- **Environment Variables** - Never commit `.env` files or credentials

### For contributors

- **No Credentials in Code** - Never commit API keys, passwords, or tokens
- **Pre-commit Checks** - Run pre-commit checks before pushing code
- **Dependencies** - Report outdated dependencies with known vulnerabilities
- **Code Review** - Security-sensitive changes require thorough review
- **Tests** - Include security test cases for new features

## Known security considerations

### Automation

- Custom agents have access to your codebase - review agent configurations
- Claude Hi scheduler creates cron jobs - review scheduling before setup

### Data handling

- Statusline displays usage data locally - no data is sent to external services
- Git history is analyzed locally - no repository data leaves your machine
- All processing happens on your local system

## Security updates

We'll announce security updates through:

- GitHub Security Advisories
- Release notes in CHANGELOG.md
- Email to reporters who request notification

## Questions

If you have questions about this security policy, email **e@giovani.dev**

---

*Last updated: October 2025*
