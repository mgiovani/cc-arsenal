# Claude Code Arsenal Commands Reference

This document provides a comprehensive overview of all available Claude commands in the Claude Code Arsenal. Commands are security and quality workflow automations that orchestrate multiple agents and tasks to accomplish secure development objectives.

## Quick Start

1. **Installation**: Run `uv run scripts/setup/install.py` to symlink commands to your `~/.claude` directory
2. **Configuration**: Run `uv run scripts/setup/configure.py` to enable specific commands
3. **Usage**: Invoke commands in Claude Code using the slash syntax: `/command:name "arguments"`

## Command Categories

### 🔐 Security Workflow Commands
*Comprehensive security and quality automation for secure development*

*Note: Advanced workflow commands are available for enterprise users - contact for access*

#### security-scan
**Location**: `commands/security/security-scan.md`
**Description**: Automated security vulnerability scanning that analyzes code for common security issues, authentication flaws, and data exposure risks.
**Usage**: `/security:scan "code location or directory"`
**Features**:
- Vulnerability pattern detection
- Authentication security analysis
- Data protection validation
- Security report generation

#### quality-check
**Location**: `commands/security/quality-check.md`
**Description**: Comprehensive code quality validation that checks coding standards, security patterns, and compliance requirements.
**Usage**: `/quality:check "code location or directory"`
**Workflow**:
1. Code quality analysis (code-reviewer)
2. Security pattern validation (security-validator)
3. Compliance checking (compliance-checker)
4. Quality report generation (test-orchestrator)
5. Recommendations and fixes (security-validator)

#### compliance-audit
**Location**: `commands/security/compliance-audit.md`
**Description**: Regulatory compliance audit workflow that validates code against industry standards like HIPAA, SOX, and GDPR.
**Usage**: `/compliance:audit "--standard=HIPAA code_location"`
**Features**:
- Multi-standard compliance checking
- PII/PHI detection and validation
- Audit trail generation
- Compliance report generation

#### test-runner
**Location**: `commands/security/test-runner.md`
**Description**: Security-focused test execution workflow that runs comprehensive tests including security, performance, and compliance validation.
**Usage**: `/test:runner "--security --coverage test_location"`
**Workflow**:
1. Security requirements analysis (security-validator)
2. Architecture security review (code-reviewer)
3. Technology selection and setup
4. Initial implementation structure
5. Development environment configuration

#### legacy-scan
**Location**: `commands/security/legacy-scan.md`
**Description**: Existing project security enhancement workflow for adding security features or securing legacy codebases.
**Usage**: `/legacy:scan "codebase_location"`
**Workflow**:
1. Codebase analysis and understanding
2. Impact assessment and planning
3. Incremental implementation strategy
4. Legacy integration and testing
5. Documentation and knowledge transfer

### 🔄 Git Workflow Commands
*Git operations and repository management automation*

*Coming Soon - Git workflow commands will be added in future releases*

### 🧪 Testing Commands
*Test automation and quality assurance workflows*

*Coming Soon - Testing commands will be added in future releases*

### 🛠️ Utility Commands
*General-purpose development utilities and helpers*

*Coming Soon - Utility commands will be added in future releases*

## Command Usage Patterns

### Basic Command Invocation
```
/security:scan "User authentication system with JWT tokens"
```

### Command with Complex Requirements
```
/security:scan "E-commerce platform with React frontend, Node.js backend, PostgreSQL database"
```

### Sequential Command Workflows
```
1. /security:scan "Initial project security audit"
2. /security:scan "User authentication feature"
3. /compliance:audit "Authentication implementation"
4. /quality:check "Product catalog feature"
```

## Command Development Guidelines

### Command File Structure
```yaml
---
description: "Command description"
argument-hint: "<argument_format>"
allowed-tools: ["Tool1", "Tool2", "Tool3"]
---

# Command Title

Command description and purpose...

## Workflow Overview
Brief description of the command workflow...

## Implementation
Detailed step-by-step workflow...

## Usage Examples
Example invocations and use cases...
```

### Best Practices
- **Single Responsibility**: Each command should have a clear, focused purpose
- **Agent Coordination**: Use appropriate agents for each workflow step
- **Error Handling**: Include robust error handling and recovery
- **Documentation**: Provide clear usage examples and expected outcomes

## Security-First Integration

All security commands implement security-first development principles:

### Core Principles
- **Business-Focused**: Every decision considers business value and user impact
- **Quality-First**: Comprehensive testing and review at every step
- **Incremental**: Break large tasks into manageable, deliverable increments
- **Collaborative**: Multi-agent coordination mirrors team collaboration
- **Documentation**: Maintain comprehensive documentation throughout

### Quality Gates
Each security command includes multiple security gates:
- **Requirements Validation**: Ensure requirements are clear and testable
- **Architecture Review**: Validate technical decisions and system design
- **Implementation Quality**: Code review, testing, and performance validation
- **Integration Testing**: Ensure components work together correctly
- **Documentation**: Verify all artifacts are properly documented

## Advanced Usage

### Custom Workflows
Commands can be combined to create custom workflows:
```
1. Use security-scan to establish security baseline
2. Use quality-check iteratively for ongoing validation
3. Use compliance-audit for regulatory assurance at milestones
4. Use legacy-scan for major security improvement initiatives
```

### Environment-Specific Variations
Commands adapt to different development environments:
- **Development**: Full workflow with comprehensive testing
- **Staging**: Deployment-focused validation and integration testing
- **Production**: Safety-first approach with rollback capabilities

## Troubleshooting

### Command Not Found
- Verify command is symlinked correctly via installation script
- Check command file exists in expected category directory
- Ensure command is enabled in your configuration

### Command Execution Failures
- Review command syntax and argument format
- Check that required agents are available and functional
- Verify all necessary tools are accessible
- Monitor Claude Code logs for detailed error information

### Performance Optimization
- Use specific commands rather than general-purpose ones
- Monitor resource usage during complex workflows
- Consider breaking large workflows into smaller command sequences

## Contributing New Commands

1. **Identify Need**: Determine what workflow gap the command addresses
2. **Design Workflow**: Plan the agent coordination and step sequence
3. **Implement Command**: Create the command file with proper structure
4. **Test Thoroughly**: Validate with real-world scenarios
5. **Document Usage**: Provide clear examples and use cases
6. **Submit PR**: Include command in appropriate category directory

### Command Categories Guidelines
- **security/**: Security-first workflows and validation commands
- **git/**: Git operations, repository management, and version control
- **testing/**: Test automation, quality assurance, and validation workflows  
- **utility/**: General-purpose tools and development helpers

## Integration with Agents

Commands orchestrate agents but don't replace them:
- **Commands** provide structured workflows and process automation
- **Agents** provide specialized expertise and task execution
- **Together** they enable comprehensive development workflow automation

### Agent Selection in Commands
Commands should use appropriate agents for each task:
- **Security Analysis**: security-validator for vulnerability research and requirements
- **Code Review**: code-reviewer for security-focused system analysis
- **Quality Assurance**: test-orchestrator for comprehensive testing and validation
- **Compliance**: compliance-checker for regulatory requirement validation

## Support

For issues, questions, or contributions:
- **Issues**: Open an issue on GitHub with command-specific details
- **Discussions**: Use GitHub Discussions for workflow questions
- **Documentation**: Check the `docs/` directory for detailed workflow guides

---

*This document is auto-generated from command metadata. Last updated: $(date)*