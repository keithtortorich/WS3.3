import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function MediaAIStudioPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">AI Studio / Media Library</h1>
        <p className="text-muted-foreground">
          Generate and manage AI content and media assets for your campaigns.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Media library</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Wire this page to GET /api/v1/media and the prompt-template-driven
            generation endpoints backed by app/services/prompt_template_service.py.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
