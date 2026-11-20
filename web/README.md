# Waypoint Web

Next.js frontend. `/learn` is the instructor chat.

```
cp .env.example .env.local
npm install
npm run dev          # http://localhost:3000
npm test             # Vitest
npm run lint && npm run typecheck && npm run build
```

End-to-end tests (Playwright) start the built site and the API with a stub
model; they need a migrated database in `DATABASE_URL`:

```
npx playwright install chromium
npm run e2e
```
