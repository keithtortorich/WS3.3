import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ApprovalsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Approvals</h1>
        <p className="text-muted-foreground">Posts awaiting internal or client review.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Pending review</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Wire this page to GET /api/v1/approvals/posts/{"{post_id}"} and the
            transition/decision endpoints backed by the approval state machine.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
