"use client";

import { useEffect, useRef, useState } from "react";
import { clockText } from "@/lib/practice";

const WARNING_S = 5 * 60;

function remaining(deadline: string): number {
  return (Date.parse(deadline) - Date.now()) / 1000;
}

/** Counts down to the server's deadline and calls `onExpire` once at zero. */
export default function Timer({
  deadline,
  onExpire,
}: {
  deadline: string;
  onExpire: () => void;
}) {
  const [seconds, setSeconds] = useState(() => remaining(deadline));
  const expired = useRef(false);

  useEffect(() => {
    const tick = () => {
      const left = remaining(deadline);
      setSeconds(left);
      if (left <= 0 && !expired.current) {
        expired.current = true;
        onExpire();
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [deadline, onExpire]);

  const warning = seconds <= WARNING_S;
  return (
    <p
      role="timer"
      aria-label="Time remaining"
      className={`font-mono text-lg font-semibold ${warning ? "text-fail" : ""}`}
    >
      {clockText(seconds)}
    </p>
  );
}
