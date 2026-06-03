# ADR 0001: Use LangGraph Document AI Platform

## Status

Accepted

## Context

Power Web OS requires an AI-agent system and must use `mudrezzz/langgraph-document-ai-platform`. The product also needs evidence provenance, auditability, HITL review, async batch processing, and typed workflow contracts.

## Decision

Use `mudrezzz/langgraph-document-ai-platform` as the AI workflow/runtime layer for agentic flows:

- Access Planning workflow.
- Account Radar batch workflow.
- evidence retrieval and canonical ingestion.
- HITL review for sensitive recommendations.
- tool execution audit for CRM and source connectors.

## Consequences

- Product domain logic remains separate from the framework.
- First domain behavior can be implemented and tested deterministically.
- Future workflow slices must follow the framework extension model.
