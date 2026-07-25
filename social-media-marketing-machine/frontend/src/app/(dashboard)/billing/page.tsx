import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function BillingPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Billing</h1>
        <p className="text-muted-foreground">Subscription plan and usage.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Current plan</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Billing integration (e.g. Stripe) is out of scope for this scaffold.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
