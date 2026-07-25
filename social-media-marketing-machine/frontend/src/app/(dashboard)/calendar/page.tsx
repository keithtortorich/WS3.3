import { CalendarView } from "@/components/calendar/calendar-view";

export default function CalendarPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Content Calendar</h1>
        <p className="text-muted-foreground">Scheduled posts across all platforms.</p>
      </div>
      <CalendarView />
    </div>
  );
}
