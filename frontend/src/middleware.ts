import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

/** Public routes that don't require authentication. Everything else under
 * `(dashboard)` is protected — see CLERK_SIGN_IN_URL / CLERK_SIGN_UP_URL in
 * .env.example for where unauthenticated users get redirected. */
const isPublicRoute = createRouteMatcher([
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks(.*)",
]);

export default clerkMiddleware((auth, req) => {
  if (!isPublicRoute(req)) {
    auth().protect();
  }
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
