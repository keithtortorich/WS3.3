import Link from "next/link";
import { UserButton } from "@clerk/nextjs";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/clients", label: "Clients" },
  { href: "/campaigns", label: "Campaigns" },
  { href: "/calendar", label: "Calendar" },
  { href: "/media", label: "AI Studio" },
  { href: "/approvals", label: "Approvals" },
  { href: "/analytics", label: "Analytics" },
  { href: "/settings", label: "Settings" },
  { href: "/billing", label: "Billing" },
  { href: "/profile", label: "Profile" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r p-4">
        <div className="mb-6 text-lg font-bold">SMM Machine</div>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <div className="flex-1">
        <header className="flex items-center justify-end border-b p-4">
          <UserButton afterSignOutUrl="/" />
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
