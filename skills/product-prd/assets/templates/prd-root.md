<!-- template: prd-root: filled by the product-prd skill -->
---
title: "{{PRODUCT_NAME}}: Product Requirements Document"
status: "{{STATUS}}"  <!-- Draft | In Review | Approved -->
size: "{{SIZE_TIER}}"  <!-- small | medium | big -->
owner: "{{OWNER}}"
target_release: "{{TARGET_RELEASE}}"
last_updated: "{{LAST_UPDATED}}"
---

<!--
  ENTERPRISE INDEX ROOT. This template is used ONLY on the --enterprise
  multi-file path (scaffold.py --enterprise), where PRD.md is the index over a
  numbered prd/ document set. The lean default (a single PRD.md) is authored
  instead from the tier template (brief.md / one-pager.md / prfaq.md /
  prd-full.md) and does not use this index structure. Reach for --enterprise
  only when a single PRD.md has demonstrably outgrown itself.
-->

# {{PRODUCT_NAME}}

## Document Control

| Field | Value |
|---|---|
| Status | {{STATUS}} |
| Size tier | {{SIZE_TIER}} |
| Owner | {{OWNER}} |
| Contributors | {{CONTRIBUTORS}} |
| Target release | {{TARGET_RELEASE}} |
| Last updated | {{LAST_UPDATED}} |
| Alignment summary | {{ALIGNMENT_SUMMARY_REF}} |

## Product Summary

{{PRODUCT_SUMMARY}}

## Goals

{{GOALS_LIST}}

## Non-Goals

{{NON_GOALS_LIST}}

## Target Release

{{TARGET_RELEASE_DETAIL}}

## Reading Guide

{{READING_GUIDE}}

<!-- Small tier: note here that all sections are inline in this file. -->

## Document Index

<!-- medium/big only: small tier has no prd/ subdirectory -->

| # | Document | Summary |
|---|---|---|
| {{DOC_NUM}} | [{{DOC_TITLE}}]({{DOC_PATH}}) | {{DOC_SUMMARY}} |

## Requirement Index

| ID | Title | Priority | Release | Status |
|---|---|---|---|---|
| {{REQ_ID}} | {{REQ_TITLE}} | {{REQ_PRIORITY}} | {{REQ_RELEASE}} | {{REQ_STATUS}} |

## Key Decisions

See [{{DECISIONS_DOC_TITLE}}]({{DECISIONS_DOC_PATH}}) for the full decision ledger.

{{KEY_DECISIONS_SUMMARY}}

## Risks

{{RISKS_SUMMARY}}

## Approval Status

| Approver | Role | Status | Date |
|---|---|---|---|
| {{APPROVER_NAME}} | {{APPROVER_ROLE}} | {{APPROVAL_STATUS}} | {{APPROVAL_DATE}} |

## Change History

| Date | Version | Author | Change |
|---|---|---|---|
| {{CHANGE_DATE}} | {{CHANGE_VERSION}} | {{CHANGE_AUTHOR}} | {{CHANGE_DESCRIPTION}} |
