"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useApprovals } from "@/hooks/useApprovals";
import type { Approval } from "@/types/approval";

type PostStatus = "draft" | "internal_review" | "client_review" | "approved" | "scheduled" | "published" | "archived" | "rejected";

const TRANSITIONS: Record<PostStatus, PostStatus[]> = {
  draft: ["internal_review", "archived"],
  internal_review: ["client_review", "rejected", "draft"],
  client_review: ["approved", "rejected", "draft"],
  approved: ["scheduled", "archived"],
  scheduled: ["published", "draft", "archived"],
  published: ["archived"],
  archived: [],
  rejected: ["draft", "archived"],
};

export function ApprovalsTable({ token }: { token?: string }) {
  const [postId, setPostId] = useState("");
  const [targetStatus, setTargetStatus] = useState<PostStatus>("internal_review");
  const [reason, setReason] = useState("");
  const [transitionStatus, setTransitionStatus] = useState<string | null>(null);

  const { data, isLoading, isError, error, refetch } = useApprovals({ postId, token });

  const availableTargets = postId.trim().length > 0 ? (TRANSITIONS[data?.items?.[0]?.status ?? "draft"] ?? []) : (TRANSITIONS.draft ?? []);

  const uniqueStatuses = Array.from(new Set((data?.items ?? []).map((item) => item.status)));

  useEffect(() => {
    if (uniqueStatuses.length > 0) {
      const first = uniqueStatuses[0].toLowerCase().replace(" ", "_") as PostStatus;
      if (first in TRANSITIONS) {
        setTargetStatus(first);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [uniqueStatuses.join("|")]);

  const submitTransition = async () => {
    if (!postId.trim()) return;
    setTransitionStatus("loading");
    try {
      const baseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");
      const response = await fetch(`${baseUrl}/api/v1/approvals/posts/${postId}/transition`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ target_status: targetStatus, reason: reason || null }),
      });
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(text || `Transition failed with status ${response.status}`);
      }
      setTransitionStatus("success");
      setReason("");
      await refetch();
    } catch (submitError) {
      setTransitionStatus("error");
      console.error(submitError);
    } finally {
      setTimeout(() => setTransitionStatus(null), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Approvals</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Post ID</label>
            <input
              value={postId}
              onChange={(event) => setPostId(event.target.value)}
              placeholder="UUID of the post to inspect"
              className="w-full rounded-md border bg-background p-2 text-sm"
            />
            <p className="text-xs text-muted-foreground">Required. Use a Post ID from your data to load its approval history.</p>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">Transition post</label>
            <select
              value={targetStatus}
              onChange={(event) => setTargetStatus(event.target.value as PostStatus)}
              className="rounded-md border bg-background p-2 text-sm"
            >
              {(availableTargets.length > 0 ? availableTargets : Object.keys(TRANSITIONS)).map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
            <Textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Optional reason for this transition"
              className="min-h-[80px]"
            />
            <Button onClick={submitTransition} disabled={!postId.trim() || transitionStatus === "loading"}>
              {transitionStatus === "loading" ? "Submitting..." : "Submit transition"}
            </Button>
            {transitionStatus === "success" ? (
              <p className="text-xs text-green-600">Transition submitted. Approval history refreshing.</p>
            ) : null}
            {transitionStatus === "error" ? (
              <p className="text-xs text-destructive">Transition failed. Check the post ID and try again.</p>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Approval history {postId.trim().length > 0 ? `for ${postId}` : ""}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          ) : isError ? (
            <p className="text-sm text-destructive">Failed to load approvals: {error instanceof Error ? error.message : "Unknown error"}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Status</TableHead>
                  <TableHead>Stage</TableHead>
                  <TableHead>Feedback</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(data?.items ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4}>
                      <p className="text-sm text-muted-foreground">No approvals found for this post yet.</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  (data?.items ?? []).map((approval: Approval) => (
                    <TableRow key={approval.id}>
                      <TableCell>
                        <Badge variant="outline">{approval.status}</Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{approval.stage}</TableCell>
                      <TableCell className="text-muted-foreground">{approval.feedback ?? "—"}</TableCell>
                      <TableCell className="text-muted-foreground">{approval.created_at}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
