-- ============================================================
-- SMM + GTM Bridge SQL Support Package — Refined
-- ============================================================
-- Grounded in the verified schema:
--   Campaigns, Posts, PostVersions, Approvals, AuditLogs,
--   Schedules, PublishJobs, PlatformAccounts, Analytics
-- Existing enums: CampaignStatus, PostStatus, ApprovalStatus,
--                  PublishJobStatus, AuditAction, PlatformName
--
-- NOTE: execution_nodes does NOT exist yet in this codebase.
-- The block below includes a proposed schema + query patterns,
-- clearly marked so implementation can land it explicitly.
-- ============================================================

-- ============================================================
-- 1. Bridge: ingest GTM skill output into SMM tables
-- ============================================================

-- Assumed JSON contract from the GTM skill:
-- {
--   "campaign": {
--     "client_id": "<uuid>",
--     "brand_id": "<uuid>|null",
--     "name": "string",
--     "goal": "string|null",
--     "status": "draft|active|...",
--     "start_date": "YYYY-MM-DD|null",
--     "end_date": "YYYY-MM-DD|null",
--     "budget_cents": 0|null
--   },
--   "post_drafts": [
--     {
--       "platform": "linkedin|facebook|instagram|...",
--       "post_type": "standard|carousel|reel|...",
--       "caption": "string",
--       "hashtags": ["string"],
--       "variant": "trust_authority|problem_solution|speed_convenience|value_price|social_proof_urgency",
--       "media_refs": ["<media_id>|<presigned_ref>"]
--     }
--   ],
--   "schedule_intent": {
--     "mode": "now|scheduled",
--     "scheduled_at": "timestamptz|null",
--     "platform_account_id": "<uuid>|null"
--   },
--   "approval_notes": "string|null"
-- }

-- 1a. Create campaign from GTM output. [Refinements in this version]
INSERT INTO campaigns (
    id, organization_id, client_id, brand_id, name, goal, status,
    start_date, end_date, budget_cents, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    :organization_id,
    (gtm.campaign->>'client_id')::uuid,
    NULLIF(gtm.campaign->>'brand_id', '')::uuid,
    gtm.campaign->>'name',
    NULLIF(gtm.campaign->>'goal', ''),
    COALESCE((gtm.campaign->>'status')::campaign_status, 'draft'),
    (gtm.campaign->>'start_date')::date,
    (gtm.campaign->>'end_date')::date,
    (gtm.campaign->>'budget_cents')::bigint,
    now(), now()
FROM jsonb_to_recordset(:gtm_json::jsonb) AS gtm(campaign jsonb)
RETURNING id, name, status;

-- 1b. Create post rows from post_drafts. [Refinements in this version]
INSERT INTO posts (
    id, organization_id, campaign_id, created_by_user_id, platform, post_type, caption, hashtags, status, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    :organization_id,
    :campaign_id,
    :actor_user_id,
    draft->>'platform',
    COALESCE(NULLIF(draft->>'post_type', ''), 'standard'),
    draft->>'caption',
    COALESCE(
        ARRAY(SELECT jsonb_array_elements_text(NULLIF(draft->'hashtags', 'null'::jsonb))),
        ARRAY[]::text[]
    ),
    'draft'::post_status,
    now(),
    now()
FROM jsonb_to_recordset(:post_drafts::jsonb) AS drafts(draft jsonb)
RETURNING id, platform, status;

-- 1c. Record first PostVersion for each created post.
INSERT INTO post_versions (
    id, post_id, version_number, caption, hashtags, edited_by_user_id, change_summary, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    p.id,
    1,
    p.caption,
    p.hashtags,
    :actor_user_id,
    COALESCE(:approval_notes, 'GTM skill intake'),
    now(),
    now()
FROM posts p
WHERE p.campaign_id = :campaign_id
  AND p.created_by_user_id = :actor_user_id
  AND p.organization_id = :organization_id
  AND NOT EXISTS (
      SELECT 1 FROM post_versions pv WHERE pv.post_id = p.id
  );

-- 1d. Bootstrap approval chain for each new post.
INSERT INTO approvals (
    id, organization_id, post_id, reviewer_user_id, stage, status, feedback, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    :organization_id,
    p.id,
    NULL,
    'internal',
    'pending'::approval_status,
    NULL,
    now(),
    now()
FROM posts p
WHERE p.campaign_id = :campaign_id
  AND p.organization_id = :organization_id;

-- 1e. Audit: GTM bridge intake event.
INSERT INTO audit_logs (
    id, organization_id, actor_user_id, action, entity_type, entity_id, description, metadata_json, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    :organization_id,
    :actor_user_id,
    'create'::audit_action,
    'Campaign',
    :campaign_id,
    'GTM campaign intent ingested via marketing-director-gtm bridge.',
    jsonb_build_object(
        'gtm_bridge',
        true,
        'variant_count',
        (SELECT jsonb_array_length(:post_drafts::jsonb)),
        'source',
        'marketing-director-gtm'
    ),
    now(),
    now()
);


-- ============================================================
-- 2. Approval state machine: reusable SQL helpers
-- ============================================================

-- 2a. Core transition helper.
-- Call this only after YOUR application code validates the transition.
-- Returns the previous status for audit trail.
CREATE OR REPLACE FUNCTION smm.transition_post_status(
    p_post_id uuid,
    p_organization_id uuid,
    p_target_status post_status,
    p_actor_user_id uuid,
    p_reason text DEFAULT NULL
)
RETURNS post_status
LANGUAGE plpgsql
AS $$
DECLARE
    v_previous_status post_status;
BEGIN
    SELECT status INTO v_previous_status
    FROM posts
    WHERE id = p_post_id
      AND organization_id = p_organization_id
    FOR UPDATE;

    IF v_previous_status IS NULL THEN
        RAISE EXCEPTION 'Post % not found in org %', p_post_id, p_organization_id;
    END IF;

    UPDATE posts
    SET status = p_target_status, updated_at = now()
    WHERE id = p_post_id;

    INSERT INTO audit_logs (
        id, organization_id, actor_user_id, action, entity_type, entity_id,
        description, metadata_json, created_at, updated_at
    )
    VALUES (
        gen_random_uuid(),
        p_organization_id,
        p_actor_user_id,
        'state_transition'::audit_action,
        'Post',
        p_post_id,
        format('Post transitioned from %s to %s%s', v_previous_status, p_target_status,
               CASE WHEN p_reason IS NULL THEN '' ELSE ': ' || p_reason END),
        jsonb_build_object('from', v_previous_status, 'to', p_target_status, 'reason', p_reason),
        now(),
        now()
    );

    RETURN v_previous_status;
END;
$$;

-- 2b. Record an approval decision + optional post status advancement.
CREATE OR REPLACE FUNCTION smm.record_approval_decision(
    p_post_id uuid,
    p_organization_id uuid,
    p_reviewer_user_id uuid,
    p_stage text,
    p_decision approval_status,
    p_feedback text DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
AS $$
DECLARE
    v_approval_id uuid;
BEGIN
    INSERT INTO approvals (
        id, organization_id, post_id, reviewer_user_id, stage, status, feedback, created_at, updated_at
    )
    VALUES (
        gen_random_uuid(),
        p_organization_id,
        p_post_id,
        p_reviewer_user_id,
        p_stage,
        p_decision,
        p_feedback,
        now(),
        now()
    )
    RETURNING id INTO v_approval_id;

    IF p_decision = 'approved'::approval_status AND p_stage = 'internal' THEN
        PERFORM smm.transition_post_status(p_post_id, p_organization_id, 'client_review'::post_status, p_reviewer_user_id,
            format('Approval decision approved at stage %s', p_stage));
    ELSIF p_decision = 'approved'::approval_status AND p_stage = 'client' THEN
        PERFORM smm.transition_post_status(p_post_id, p_organization_id, 'approved'::post_status, p_reviewer_user_id,
            format('Approval decision approved at stage %s', p_stage));
    ELSIF p_decision = 'rejected'::approval_status THEN
        PERFORM smm.transition_post_status(p_post_id, p_organization_id, 'rejected'::post_status, p_reviewer_user_id,
            format('Approval decision rejected at stage %s', p_stage));
    ELSIF p_decision = 'changes_requested'::approval_status THEN
        PERFORM smm.transition_post_status(p_post_id, p_organization_id, 'draft'::post_status, p_reviewer_user_id,
            format('Approval decision changes requested at stage %s', p_stage));
    END IF;

    RETURN v_approval_id;
END;
$$;

-- 2c. Create a new PostVersion snapshot on edit.
CREATE OR REPLACE FUNCTION smm.snapshot_post_version(
    p_post_id uuid,
    p_organization_id uuid,
    p_edited_by_user_id uuid,
    p_change_summary text DEFAULT 'Content edited'
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    v_next_version int;
BEGIN
    SELECT COALESCE(MAX(version_number), 0) + 1 INTO v_next_version
    FROM post_versions
    WHERE post_id = p_post_id;

    INSERT INTO post_versions (
        id, post_id, version_number, caption, hashtags, edited_by_user_id, change_summary, created_at, updated_at
    )
    SELECT
        gen_random_uuid(),
        p.id,
        v_next_version,
        p.caption,
        p.hashtags,
        p_edited_by_user_id,
        p_change_summary,
        now(),
        now()
    FROM posts p
    WHERE p.id = p_post_id
      AND p.organization_id = p_organization_id;
END;
$$;

-- 2d. Transition guard view for reporting / debugging.
-- Source of truth remains the application state machine.
CREATE OR REPLACE VIEW smm.post_transition_rules AS
SELECT *
FROM (VALUES
    ('draft',            ARRAY['internal_review','archived']::post_status[]),
    ('internal_review',  ARRAY['client_review','rejected','draft']::post_status[]),
    ('client_review',    ARRAY['approved','rejected','draft']::post_status[]),
    ('approved',         ARRAY['scheduled','archived']::post_status[]),
    ('rejected',         ARRAY['draft','archived']::post_status[]),
    ('scheduled',        ARRAY['published','draft','archived']::post_status[]),
    ('published',        ARRAY['archived']::post_status[]),
    ('archived',         ARRAY[]::post_status[])
) AS t(current_status, allowed_next);

-- 2e. Approval chain summary per post.
CREATE OR REPLACE VIEW smm.post_approval_chain AS
SELECT
    p.id AS post_id,
    p.status AS post_status,
    a.id AS approval_id,
    a.stage,
    a.status AS approval_status,
    a.feedback,
    a.created_at AS decided_at
FROM posts p
JOIN approvals a ON a.post_id = p.id
ORDER BY p.id, a.created_at;


-- ============================================================
-- 3. Execution graph / workflow orchestration
-- ============================================================
-- Status: NOT yet present in the repo.
-- Proposed addition so bridges and recovery are deterministic.

CREATE TABLE IF NOT EXISTS execution_nodes (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id     uuid NOT NULL,
    workflow_instance_id uuid NOT NULL,
    parent_node_id      uuid NULL,
    node_type           text NOT NULL CHECK (node_type IN (
                           'intake','campaign','post','publish_job','approval','integration_event'
                       )),
    status              text NOT NULL DEFAULT 'pending' CHECK (status IN (
                           'pending','running','succeeded','failed','cancelled'
                       )),
    ref_id              uuid NULL,
    ref_type            text NULL CHECK (ref_type IN (
                           'campaign','post','schedule','publish_job','approval','audit_log'
                       )),
    failure_reason      text NULL,
    created_at          timestamptz NOT NULL DEFAULT now(),
    completed_at        timestamptz NULL
);

CREATE INDEX IF NOT EXISTS ix_execution_nodes_org
    ON execution_nodes (organization_id);
CREATE INDEX IF NOT EXISTS ix_execution_nodes_workflow
    ON execution_nodes (workflow_instance_id);
CREATE INDEX IF NOT EXISTS ix_execution_nodes_parent
    ON execution_nodes (parent_node_id);
CREATE INDEX IF NOT EXISTS ix_execution_nodes_ref
    ON execution_nodes (ref_id, ref_type);
CREATE INDEX IF NOT EXISTS ix_execution_nodes_status
    ON execution_nodes (status, created_at);

ALTER TABLE execution_nodes
    ADD CONSTRAINT fk_execution_nodes_org
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE;

-- 3a. Create workflow instance root node helper. [Refinements in this version]
CREATE OR REPLACE FUNCTION smm.create_workflow_instance(
    p_organization_id uuid,
    p_root_ref_id uuid,
    p_root_ref_type text,
    p_node_type text DEFAULT 'campaign'
)
RETURNS uuid
LANGUAGE plpgsql AS $$
DECLARE
    v_workflow_id uuid := gen_random_uuid();
BEGIN
    INSERT INTO execution_nodes (
        organization_id, workflow_instance_id, parent_node_id,
        node_type, status, ref_id, ref_type
    )
    VALUES (
        p_organization_id, v_workflow_id, NULL,
        p_node_type, 'succeeded', p_root_ref_id, p_root_ref_type
    );
    RETURN v_workflow_id;
END;
$$;

-- Usage:
-- SELECT smm.create_workflow_instance(:org_id, :campaign_id, 'campaign');

-- 3b. Append approval/publish child nodes for a post. [Refinements in this version]
-- Intended to run in the same transaction as the workflow bootstrap.
INSERT INTO execution_nodes (
    id, organization_id, workflow_instance_id, parent_node_id, node_type, status, ref_id, ref_type, created_at
)
SELECT gen_random_uuid(), :organization_id, :workflow_instance_id, :parent_node_id, 'approval', 'pending', a.id, 'approval', now()
FROM approvals a
WHERE a.post_id = :post_id
  AND a.organization_id = :organization_id;

INSERT INTO execution_nodes (
    id, organization_id, workflow_instance_id, parent_node_id, node_type, status, ref_id, ref_type, created_at
)
SELECT gen_random_uuid(), :organization_id, :workflow_instance_id, :parent_node_id, 'publish_job', 'pending', j.id, 'publish_job', now()
FROM publish_jobs j
WHERE j.post_id = :post_id
  AND j.organization_id = :organization_id;

-- 3c. Mark node completed/failed.
UPDATE execution_nodes
SET status = 'succeeded', completed_at = now()
WHERE workflow_instance_id = :workflow_instance_id
  AND ref_id = :ref_id
  AND ref_type = :ref_type;

UPDATE execution_nodes
SET status = 'failed', failure_reason = :failure_reason, completed_at = now()
WHERE workflow_instance_id = :workflow_instance_id
  AND ref_id = :ref_id
  AND ref_type = :ref_type;


-- ============================================================
-- 4. Read model / operational queries
-- ============================================================

-- 4a. Campaign + latest post status view for SMM agent intake routing.
CREATE OR REPLACE VIEW smm.campaign_post_status AS
SELECT
    c.organization_id,
    c.id AS campaign_id,
    c.name,
    c.status AS campaign_status,
    p.id AS post_id,
    p.platform,
    p.status AS post_status,
    a.stage AS approval_stage,
    a.status AS approval_status,
    s.scheduled_at,
    pj.status AS publish_job_status
FROM campaigns c
JOIN posts p ON p.campaign_id = c.id
LEFT JOIN approvals a ON a.post_id = p.id
LEFT JOIN schedules s ON s.post_id = p.id
LEFT JOIN LATERAL (
    SELECT status, scheduled_at
    FROM publish_jobs
    WHERE post_id = p.id
    ORDER BY created_at DESC
    LIMIT 1
) pj ON TRUE;

-- 4b. Weekly KPI summary per campaign from analytics snapshots.
SELECT
    c.organization_id,
    c.id AS campaign_id,
    p.id AS post_id,
    p.platform,
    date_trunc('week', an.captured_at)::date AS week_start,
    SUM(an.impressions) AS impressions,
    SUM(an.likes) AS likes,
    SUM(an.comments_count) AS comments,
    SUM(an.shares) AS shares,
    SUM(an.clicks) AS clicks,
    MAX(an.engagement_rate) AS engagement_rate
FROM campaigns c
JOIN posts p ON p.campaign_id = c.id
JOIN analytics an ON an.post_id = p.id
WHERE c.organization_id = :organization_id
  AND an.captured_at BETWEEN :week_start AND :week_end
GROUP BY 1,2,3,4,5
ORDER BY week_start, post_id;

-- 4c. Publish queue for scheduler/polling.
SELECT
    p.id AS post_id,
    p.platform,
    pa.id AS platform_account_id,
    s.scheduled_at,
    pj.status,
    pj.next_attempt_at,
    pj.last_error
FROM schedules s
JOIN posts p ON p.id = s.post_id
JOIN platform_accounts pa ON pa.id = s.platform_account_id
LEFT JOIN LATERAL (
    SELECT status, next_attempt_at, last_error
    FROM publish_jobs
    WHERE post_id = p.id
    ORDER BY created_at DESC
    LIMIT 1
) pj ON TRUE
WHERE s.organization_id = :organization_id
  AND s.is_cancelled = false
  AND s.scheduled_at <= now()
ORDER BY s.scheduled_at;

-- 4d. GTM-bridge ingestion summary for a campaign.
SELECT
    c.id AS campaign_id,
    p.id AS post_id,
    p.platform,
    p.caption,
    a.stage,
    a.status AS approval_status,
    jsonb_agg(DISTINCT jsonb_build_object('variant', pv.change_summary, 'version', pv.version_number)) AS gtm_variant_notes
FROM campaigns c
JOIN posts p ON p.campaign_id = c.id
LEFT JOIN approvals a ON a.post_id = p.id
LEFT JOIN post_versions pv ON pv.post_id = p.id
WHERE c.id = :campaign_id
GROUP BY c.id, p.id, a.stage, a.status;


-- ============================================================
-- 5. Index recommendations
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_approvals_post_stage
    ON approvals (post_id, stage, status);

CREATE INDEX IF NOT EXISTS ix_analytics_post_captured
    ON analytics (post_id, captured_at DESC);

CREATE INDEX IF NOT EXISTS ix_publish_jobs_status_next
    ON publish_jobs (status, next_attempt_at)
    WHERE status IN ('queued','retrying');

CREATE INDEX IF NOT EXISTS ix_posts_org_status_platform
    ON posts (organization_id, status, platform);

CREATE INDEX IF NOT EXISTS ix_campaigns_org_brand_status
    ON campaigns (organization_id, brand_id, status);

CREATE INDEX IF NOT EXISTS ix_execution_nodes_org_status_created
    ON execution_nodes (organization_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_created
    ON audit_logs (entity_type, entity_id, created_at DESC);
