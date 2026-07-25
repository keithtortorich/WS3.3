# Retained Graph Model — Post-Session State

Purpose: replace in-memory workflow state with a persisted graph that survives restarts and makes every campaign, post, publish job, and approval traceable.

## Node

```json
{
  "node_id": "node_001",
  "workflow_instance_id": "wf_123",
  "tenant_id": "acme-hvac",
  "type": "campaign",
  "status": "active",
  "payload_ref": "campaigns/campaign_001.json",
  "parent_node_id": null,
  "created_at": "2026-07-24T00:00:00Z",
  "completed_at": null,
  "failure_reason": null
}
```

## Allowed node types

- `intake`
- `campaign`
- `post`
- `publish_job`
- `approval`
- `integration_event`

## Status values

- `pending`
- `active`
- `awaiting_approval`
- `completed`
- `failed`
- `canceled`

## Rules

- Every new session or campaign creation writes a root node.
- Every publish attempt writes a child `publish_job` node under its campaign.
- Every approval request writes an `approval` node and links it to the triggering `post` or `campaign` node.
- Every SMM integration event writes an `integration_event` node with the raw payload hash for replay.
- Completion or failure must update `completed_at` or `failure_reason` in the same transaction as the child node write.

## Why this matters

This is the only way to recover from partial failures without manual state inspection. It also makes retries idempotent: if a publish job node already exists, reuse it instead of creating a duplicate.
