import { describe, it, expect } from "vitest";
import Home from "../page";

describe("Home page", () => {
  it("is a function component", () => {
    expect(typeof Home).toBe("function");
  });
});