# {{PROJECT_NAME}} - Deployment Guide

**Last Updated:** {{DATE}}

## Overview

{{OVERVIEW}}

## Environments

<!-- One row per environment the codebase actually defines (env files, CI config,
     IaC). Delete rows for environments that don't exist. -->

| Environment | Configuration | Access |
|-------------|----------------|--------|
| {{ENV_NAME}} | {{ENV_CONFIG}} | {{ENV_ACCESS}} |

## CI/CD Pipeline

{{CICD_PIPELINE}}

[Describe the real pipeline found in .github/workflows, .gitlab-ci.yml, etc.
Build steps, test gate, deploy trigger.]

## Infrastructure

{{INFRASTRUCTURE}}

<!-- Include only the artifacts that actually exist in the repo (Dockerfile,
     k8s manifests, Terraform). Link to the real file instead of pasting it
     if it's long. -->

## Monitoring and Alerting

{{MONITORING_ALERTING}}

[Only tools with evidence in the repo: a Sentry/Datadog config, a
prometheus.yml, health-check routes.]

## Rollback Procedure

{{ROLLBACK_PROCEDURE}}

## Scaling

{{SCALING_STRATEGY}}

[Omit if nothing in the repo indicates a scaling strategy beyond defaults.]

## Troubleshooting

{{TROUBLESHOOTING}}

## References

- [Architecture Documentation](architecture.md)

---

*Keep this document updated with infrastructure and deployment changes.*
