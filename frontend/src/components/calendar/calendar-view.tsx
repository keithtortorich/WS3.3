"use client";

import { useMemo, useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useCalendar } from "@/hooks/useCalendar";
import type { CalendarEntry } from "@/types/calendar";

function formatDate(value: string) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function CalendarView({ token }: { token?: string }) {
  const { data, isLoading, isError, error } = useCalendar({ token });
  const entries: CalendarEntry[] = data ?? [];

  const grouped = useMemo(() => {
    const map = new Map<string, CalendarEntry[]>();
    for (const entry of entries) {
      const day = entry.scheduled_at?.slice(0, 10) ?? "unscheduled";
      const list = map.get(day) ?? [];
      list.push(entry);
      map.set(day, list);
    }
    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [entries]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Content Calendar</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Content Calendar</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load calendar: {error instanceof Error ? error.message : "Unknown error"}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Content Calendar ({entries.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <p className="text-sm text-muted-foreground">No scheduled posts in the current view.</p>
          ) : (
            <div className="space-y-6">
              {grouped.map(([day, items]) => (
                <div key={day} className="space-y-2">
                  <p className="text-xs font-medium uppercase text-muted-foreground">{day}</p>
                  <div className="space-y-2">
                    {items.map((item) => (
                      <div
                        key={item.schedule_id}
                        className="flex flex-col gap-1 rounded-md border p-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm font-medium">{formatDate(item.scheduled_at)}</span>
                          <Badge variant="outline">{item.platform}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-2">{item.caption_preview || "No caption preview."}</p>
                        <p className="text-xs text-muted-foreground">Post status: {item.post_status}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
