import { describe, it, expect, beforeEach, vi } from "vitest";
import { OpenBuroClient } from "../src/client.js";

function mockFetch(data: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: () => Promise.resolve(data),
  });
}

describe("OpenBuroClient", () => {
  let client: OpenBuroClient;

  beforeEach(() => {
    client = new OpenBuroClient({
      baseUrl: "https://api.example.com",
      token: "test-token",
    });
  });

  it("getDrive returns a service", async () => {
    vi.stubGlobal("fetch", mockFetch({ id: "drive1", name: "My Drive" }));
    const service = await client.getDrive("drive1");
    expect(service).toEqual({ id: "drive1", name: "My Drive" });
    expect(fetch).toHaveBeenCalledWith("https://api.example.com/drive/drive1", {
      headers: { Authorization: "Bearer test-token" },
    });
  });

  it("listFiles returns files", async () => {
    const files = [
      {
        id: "file-001",
        name: "hello.txt",
        mime_type: "text/plain",
        path: "/hello.txt",
        last_modified: "2026-01-15T10:30:00Z",
        creation_date: "2026-01-10T08:00:00Z",
        owner: "alice",
        size: 12,
      },
    ];
    vi.stubGlobal("fetch", mockFetch(files));
    const result = await client.listFiles("drive1");
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("hello.txt");
  });

  it("listFiles passes deep parameter", async () => {
    vi.stubGlobal("fetch", mockFetch([]));
    await client.listFiles("drive1", 2);
    expect(fetch).toHaveBeenCalledWith(
      "https://api.example.com/drive/drive1/files?deep=2",
      expect.any(Object)
    );
  });

  it("getFile returns a file", async () => {
    const file = {
      id: "file-001",
      name: "hello.txt",
      mime_type: "text/plain",
      path: "/hello.txt",
      last_modified: "2026-01-15T10:30:00Z",
      creation_date: "2026-01-10T08:00:00Z",
      owner: "alice",
      size: 12,
    };
    vi.stubGlobal("fetch", mockFetch(file));
    const result = await client.getFile("drive1", "file-001");
    expect(result.id).toBe("file-001");
  });

  it("getShareLink returns a share link", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch({ url: "https://example.com/share/abc123" })
    );
    const link = await client.getShareLink("drive1", "file-001");
    expect(link.url).toContain("abc123");
  });

  it("throws on API error", async () => {
    vi.stubGlobal("fetch", mockFetch(null, 500));
    await expect(client.getDrive("drive1")).rejects.toThrow(
      "OpenBURO API error: 500"
    );
  });

  it("sends no auth header when no token", async () => {
    const noAuthClient = new OpenBuroClient({
      baseUrl: "https://api.example.com",
    });
    vi.stubGlobal("fetch", mockFetch({ id: "d1", name: "Drive" }));
    await noAuthClient.getDrive("d1");
    expect(fetch).toHaveBeenCalledWith("https://api.example.com/drive/d1", {
      headers: {},
    });
  });
});
