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

Please do not report security vulnerabilities through public GitHub issues.

If you discover a security vulnerability, please email us at e@giovani.dev.

Include the following information in your report:

- Type of vulnerability
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability
- Suggested fix (if you have one)

### What to expect

1. Acknowledgment: we'll respond within 48 hours to acknowledge receipt of your report
2. Investigation: we'll investigate the issue and keep you updated on our progress
3. Resolution: we'll work on a fix and coordinate a release timeline with you
4. Credit: we'll credit you in our security advisory (unless you prefer to remain anonymous)

### Disclosure policy

- Please give us reasonable time to fix the vulnerability before any public disclosure
- We'll coordinate the disclosure timeline with you
- We aim to release security patches as quickly as possible

## Security best practices

When using cc-arsenal, follow these practices depending on your role:

| Role | Practice | Detail |
| --- | --- | --- |
| Users | Keep updated | Always use the latest version to get security patches |
| Users | Environment variables | Never commit `.env` files or credentials |
| Contributors | No credentials in code | Never commit API keys, passwords, or tokens |
| Contributors | Pre-commit checks | Run pre-commit checks before pushing code |
| Contributors | Dependencies | Report outdated dependencies with known vulnerabilities |
| Contributors | Code review | Security-sensitive changes require thorough review |
| Contributors | Tests | Include security test cases for new features |

## Known security considerations

Two areas are worth understanding before you rely on cc-arsenal in a sensitive environment: automation and data handling.

Automation runs with real access, so review it before you enable it: custom agents have access to your codebase, so review agent configurations, and the Claude Hi scheduler creates cron jobs, so review scheduling before setup.

Data handling stays local by design: the statusline displays usage data locally with nothing sent to external services, git history is analyzed locally with no repository data leaving your machine, and all processing happens on your local system.

## Security updates and questions

We'll announce security updates through GitHub Security Advisories, release notes in CHANGELOG.md, and email to reporters who request notification.

If you have questions about this security policy, email e@giovani.dev.

---

*Last updated: October 2025*
