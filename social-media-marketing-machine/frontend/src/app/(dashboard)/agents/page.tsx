"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useAgentTemplates } from "@/hooks/useAgentTemplates";

const CATEGORIES = [
  { slug: "all", label: "All Agents", description: "Explore every extracted marketing prompt." },
  { slug: "strategy", label: "Strategy", description: "Competitive, pricing, trend, and planning agents." },
  { slug: "content_marketing", label: "Content", description: "Content calendars, SEO, audits, and performance." },
  { slug: "social_media", label: "Social", description: "Social audits, listening, and influencer research." },
  { slug: "campaign_optimization", label: "Campaigns", description: "Email, conversion, journey, and attribution agents." },
  { slug: "lead_growth", label: "Lead Growth", description: "Lead scoring and pipeline-focused agents." },
  { slug: "messaging", label: "Messaging", description: "Brand voice, positioning, and feedback insights." },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <Button size="sm" variant="outline" onClick={handleCopy} className="shrink-0">
      {copied ? "Copied" : "Copy Prompt"}
    </Button>
  );
}

function CategoryPill({ active, label, description, onClick }: { active: boolean; label: string; description: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`w-full rounded-lg border p-4 text-left transition-colors ${
        active ? "border-primary bg-primary/10" : "hover:border-primary/60 hover:bg-muted/40"
      }`}
    >
      <span className="font-semibold">{label}</span>
      <span className="block text-sm text-muted-foreground">{description}</span>
    </button>
  );
}

export default function AgentsPage() {
  const search = useSearchParams();
  const activeCategory = search?.get("category") ?? "all";
  const { data, isLoading, isError, error } = useAgentTemplates({ category: activeCategory });
  const agents = data ?? [];
  const [selected, setSelected] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  const focusedAgent = useMemo(
    () => agents.find((item) => item.id === selected) ?? agents[0] ?? null,
    [agents, selected]
  );

  const handleSelect = (id: string) => setSelected(id);

  const handleCopyAll = async () => {
    if (!focusedAgent) return;
    const combined = `${focusedAgent.name} — ${focusedAgent.description ?? ""}

${focusedAgent.template_body}`;
    await navigator.clipboard.writeText(combined);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2200);
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">AI Marketing Agents</h1>
        <p className="text-muted-foreground">
          Use extracted marketing prompts as reusable agents. Open one, then copy its prompt back into ChatGPT or your provider.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col gap-3 lg:col-span-1">
          {CATEGORIES.map((category) => (
            <CategoryPill
              key={category.slug}
              active={activeCategory === category.slug}
              label={category.label}
              description={category.description}
              onClick={() => {
                const next = category.slug === "all" ? "/agents" : `/agents?category=${category.slug}`;
                window.location.href = next;
              }}
            />
          ))}
        </div>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              {agents.length}
              {" active "}
              {activeCategory === "all" ? "agents" : `${activeCategory.replace("_", " ")} agents`}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading && (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            )}

            {isError && (
              <p className="text-sm text-destructive">
                Failed to load agents: {error instanceof Error ? error.message : "Unknown error"}
              </p>
            )}

            {!isLoading && !isError && agents.length === 0 && (
              <p className="text-sm text-muted-foreground">No active agents are available yet.</p>
            )}

            {!isLoading && !isError && agents.length > 0 && (
              <div className="flex flex-col gap-2">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => handleSelect(agent.id)}
                    className={`w-full rounded-lg border p-3 text-left transition-colors ${
                      focusedAgent?.id === agent.id ? "border-primary bg-primary/10" : "hover:border-primary/50"
                    }`}
                  >
                    <span className="font-medium">{agent.name}</span>
                    <span className="block text-sm text-muted-foreground">{agent.description}</span>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {focusedAgent && (
        <Card>
          <CardHeader className="gap-3 md:flex md:items-center md:justify-between">
            <div>
              <CardTitle>{focusedAgent.name}</CardTitle>
              <p className="text-sm text-muted-foreground">{focusedAgent.description}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <CopyButton text={focusedAgent.template_body} />
              <Button size="sm" variant="ghost" onClick={handleCopyAll}>
                {copiedAll ? "Copied" : "Copy Card"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">v{focusedAgent.version}</Badge>
              {focusedAgent.category && <Badge>{focusedAgent.category.replace("_", " ")}</Badge>}
              <Badge variant="outline">{focusedAgent.is_active ? "Active" : "Inactive"}</Badge>
            </div>

            <Textarea readOnly value={focusedAgent.template_body} className="min-h-[180px] font-mono text-sm" />

            <div className="flex flex-col gap-1 text-sm text-muted-foreground">
              <span>Slug: {focusedAgent.slug}</span>
              <span>Works best in a chat provider with follow-up prompts for client-specific fields.</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
