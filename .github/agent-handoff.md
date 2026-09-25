# Agent Handoff Workflow

This repository uses small, evidence-driven handoffs for the local Garmin MVP. Every child issue and pull request must make ownership, scope, validation, and limitations explicit.

## Issue Handoff Contract

Each implementation issue must identify:

- **Owner agent:** the role responsible for the first implementation pass.
- **Dependencies:** prerequisite issues, decisions, data, or tools.
- **Inputs:** source data, APIs, configuration, fixtures, and assumptions.
- **Outputs:** files, interfaces, user-visible behavior, or documentation expected from the work.
- **Validation commands:** focused commands that prove the acceptance criteria, without requiring real Garmin credentials.
- **Acceptance criteria:** observable behavior and failure conditions.

When an issue is unclear, the owner records the missing decision as a blocker instead of guessing. A child issue may begin only after its dependencies are either complete or explicitly mocked.

## Pull Request Handoff Contract

Every pull request must use the repository PR template. The author records changed files, tests and commands, acceptance evidence, and known limitations. Reviewers should be able to verify the ticket without relying on an unrecorded local state.

The PR must also confirm that:

- no Garmin credentials, tokens, or raw personal activity data are committed;
- local services bind to localhost unless a ticket explicitly documents another boundary;
- Garmin access remains read-only and no write tool is called for the MVP;
- failures, unavailable data, and privacy-sensitive assumptions are visible.

## Epic and Child-Issue Workflow

The six project epics are the planning parents for child issues:

1. #1 Garmin data integration
2. #2 Local storage and processing
3. #3 Multisport analytics and planning
4. #4 Local nutrition analysis
5. #5 Local web interface
6. #6 Local infrastructure and agent workflow

For each child issue:

1. Define the requirement, acceptance criteria, owner agent, dependencies, inputs, outputs, and validation commands.
2. Implement on a feature branch based on `development`.
3. Open a pull request targeting `development` and include the ticket link and acceptance evidence.
4. Run code review and QA checks against the ticket, including privacy and local-only constraints.
5. Resolve findings and update the evidence before marking the issue complete.

Cross-cutting work belongs in the relevant epic and should link affected child issues rather than duplicating requirements. A blocked child issue stays blocked until its dependency or clarification is recorded.

## Review Checklist

- Requirements and acceptance criteria are testable.
- The implementation stays within local-only scope.
- Services and development servers use localhost by default.
- Credentials, tokens, and raw personal data stay outside Git.
- Garmin integrations allow only read operations for the MVP.
- Tests cover success, failure, missing data, and retry or idempotency behavior where relevant.
- The PR describes known limitations and evidence for every acceptance criterion.