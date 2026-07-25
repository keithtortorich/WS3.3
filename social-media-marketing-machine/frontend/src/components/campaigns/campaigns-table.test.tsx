import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { CampaignsTable } from "@/components/campaigns/campaigns-table";
import type { Campaign, Page } from "@/types/campaign";

const mockCampaign: Campaign = {
  id: "11111111-1111-1111-1111-111111111111",
  organization_id: "22222222-2222-2222-2222-222222222222",
  client_id: "33333333-3333-3333-3333-333333333333",
  brand_id: null,
  name: "Summer Launch",
  goal: "Drive signups",
  status: "active",
  start_date: "2026-07-01",
  end_date: "2026-08-01",
  budget_cents: 500000,
  created_at: "2026-07-01T00:00:00Z",
  updated_at: "2026-07-01T00:00:00Z",
};

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("CampaignsTable", () => {
  it("renders campaign rows once data loads", async () => {
    const page: Page<Campaign> = {
      items: [mockCampaign],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => page,
      })
    );

    renderWithClient(<CampaignsTable />);

    await waitFor(() => expect(screen.getByText("Summer Launch")).toBeInTheDocument());
    expect(screen.getByText("active")).toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("renders an error state when the fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        text: async () => "boom",
      })
    );

    renderWithClient(<CampaignsTable />);

    await waitFor(() => expect(screen.getByText(/Failed to load campaigns/i)).toBeInTheDocument());

    vi.unstubAllGlobals();
  });
});
