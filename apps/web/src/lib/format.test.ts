import { describe, expect, it } from "vitest";
import { formatScoreGrade, onlineLabel } from "./format";

describe("format", () => {
  it("maps scores to grades", () => {
    expect(formatScoreGrade(95)).toBe("A");
    expect(formatScoreGrade(50)).toBe("F");
  });
  it("labels online state", () => {
    expect(onlineLabel(true)).toBe("online");
    expect(onlineLabel(false)).toBe("offline");
  });
});
