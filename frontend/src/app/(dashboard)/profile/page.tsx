import { UserProfile } from "@clerk/nextjs";

export default function ProfilePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Profile</h1>
        <p className="text-muted-foreground">Manage your account.</p>
      </div>
      <UserProfile routing="hash" />
    </div>
  );
}
