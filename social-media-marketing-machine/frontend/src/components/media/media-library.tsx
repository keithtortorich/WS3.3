"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiFetch } from "@/lib/api-client";
import type { Media, Page } from "@/types/media";

interface UseMediaLibraryParams {
  postId?: string;
  page?: number;
  pageSize?: number;
  token?: string;
}

/**
 * Fetches paginated media metadata from GET /api/v1/media.
 */
export function useMediaLibrary({
  postId,
  page = 1,
  pageSize = 20,
  token,
}: UseMediaLibraryParams = {}) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (postId) params.set("post_id", postId);

  return useQuery<Page<Media>>({
    queryKey: ["media", { page, pageSize, postId }],
    queryFn: () => apiFetch<Page<Media>>(`/api/v1/media?${params.toString()}`, { token }),
  });
}

function formatBytes(value: number | null | undefined) {
  if (!value && value !== 0) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export function MediaLibrary({ token }: { token?: string }) {
  const { data, isLoading, isError, error } = useMediaLibrary({ token });
  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Media library ({data?.total ?? 0})</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <p className="text-sm text-destructive">Failed to load media: {error instanceof Error ? error.message : "Unknown error"}</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No media assets yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>MIME</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Dimensions</TableHead>
                <TableHead>URL</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.media_type}</TableCell>
                  <TableCell className="text-muted-foreground">{item.mime_type}</TableCell>
                  <TableCell className="text-muted-foreground">{formatBytes(item.size_bytes)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.width && item.height ? `${item.width}×${item.height}` : "—"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {item.url ? (
                      <a className="text-blue-600 underline" href={item.url} target="_blank" rel="noreferrer">
                        Open
                      </a>
                    ) : (
                      "—"
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
