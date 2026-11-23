import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { act, cleanup, render, screen } from "@testing-library/react";
import Timer from "@/components/Timer";
import { clockText } from "@/lib/practice";

const NOW = new Date("2026-11-23T12:00:00Z");

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(NOW);
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function deadlineIn(seconds: number): string {
  return new Date(NOW.getTime() + seconds * 1000).toISOString();
}

test("the timer counts down each second", () => {
  render(<Timer deadline={deadlineIn(90 * 60)} onExpire={() => {}} />);
  const timer = screen.getByRole("timer", { name: "Time remaining" });
  expect(timer.textContent).toBe("1:30:00");
  act(() => vi.advanceTimersByTime(1000));
  expect(timer.textContent).toBe("1:29:59");
});

test("the timer calls onExpire once at zero", () => {
  const onExpire = vi.fn();
  render(<Timer deadline={deadlineIn(2)} onExpire={onExpire} />);
  act(() => vi.advanceTimersByTime(1000));
  expect(onExpire).not.toHaveBeenCalled();
  act(() => vi.advanceTimersByTime(1000));
  expect(onExpire).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("timer").textContent).toBe("0:00");
  act(() => vi.advanceTimersByTime(5000));
  expect(onExpire).toHaveBeenCalledTimes(1);
});

test("clock text formats minutes and hours", () => {
  expect(clockText(59)).toBe("0:59");
  expect(clockText(600)).toBe("10:00");
  expect(clockText(3600)).toBe("1:00:00");
  expect(clockText(-3)).toBe("0:00");
});
