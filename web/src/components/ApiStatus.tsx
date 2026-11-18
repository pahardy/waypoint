"use client";

import { useEffect, useState } from "react";

type Status = "checking" | "ok" | "unreachable";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Shows whether the Waypoint API answers its health check. */
export default function ApiStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => response.json())
      .then((body) => setStatus(body.status === "ok" ? "ok" : "unreachable"))
      .catch(() => setStatus("unreachable"));
  }, []);

  const label = {
    checking: "API: checking...",
    ok: "API: connected",
    unreachable: "API: unreachable",
  }[status];

  return <p role="status">{label}</p>;
}
