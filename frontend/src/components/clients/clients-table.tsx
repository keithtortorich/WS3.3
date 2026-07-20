"use client";

import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useClients } from "@/hooks/useClients";
import type { Client } from "@/types/client";

export function ClientsTable({ token }: { token?: string }) {
  const { data, isLoading, isError, error } = useClients({ token });

  const [selected, setSelected] = useState<Client | null>(null);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Clients</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full animate-pulse rounded bg-muted" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Clients</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load clients: {error instanceof Error ? error.message : "Unknown error"}</p>
        </CardContent>
      </Card>
    );
  }

  const clients = data?.items ?? [];

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Clients ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {clients.length === 0 ? (
            <p className="text-sm text-muted-foreground">No clients yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Industry</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Website</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {clients.map((client) => (
                  <TableRow
                    key={client.id}
                    className="cursor-pointer"
                    onClick={() => setSelected(client)}
                  >
                    <TableCell className="font-medium">{client.name}</TableCell>
                    <TableCell className="text-muted-foreground">{client.industry ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{client.contact_name ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{client.website_url ?? "—"}</TableCell>
                    <TableCell>
                      <span className={`text-xs ${client.is_active ? "text-green-600" : "text-muted-foreground"}`}>
                        {client.is_active ? "Active" : "Inactive"}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {selected ? (
        <Card>
          <CardHeader>
            <CardTitle>Client detail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            <p><span className="font-medium">Name:</span> {selected.name}</p>
            <p><span className="font-medium">Industry:</span> {selected.industry ?? "—"}</p>
            <p><span className="font-medium">Contact:</span> {selected.contact_name ?? "—"} {selected.contact_email ? `&lt;${selected.contact_email}&gt;` : ""}</p>
            <p><span className="font-medium">Website:</span> {selected.website_url ? <a className="text-blue-600 underline" href={selected.website_url} target="_blank" rel="noreferrer">{selected.website_url}</a> : "—"}</p>
            <p><span className="font-medium">Notes:</span> {selected.notes ?? "—"}</p>
            <p className="text-xs text-muted-foreground">Created {selected.created_at} · Updated {selected.updated_at}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
