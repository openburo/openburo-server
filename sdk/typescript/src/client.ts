import type { Service, File, ShareLink } from "./types.js";

export interface OpenBuroClientOptions {
  baseUrl: string;
  token?: string;
}

export class OpenBuroClient {
  private baseUrl: string;
  private headers: Record<string, string>;

  constructor(options: OpenBuroClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.headers = {};
    if (options.token) {
      this.headers["Authorization"] = `Bearer ${options.token}`;
    }
  }

  async getDrive(driveId: string): Promise<Service> {
    return this.get<Service>(`/drive/${driveId}`);
  }

  async listFiles(driveId: string, deep: number = 0): Promise<File[]> {
    const params = new URLSearchParams({ deep: String(deep) });
    return this.get<File[]>(`/drive/${driveId}/files?${params}`);
  }

  async getFile(driveId: string, fileId: string): Promise<File> {
    return this.get<File>(`/drive/${driveId}/files/${fileId}`);
  }

  async getShareLink(driveId: string, fileId: string): Promise<ShareLink> {
    return this.get<ShareLink>(`/drive/${driveId}/files/${fileId}/share`);
  }

  private async get<T>(path: string): Promise<T> {
    const resp = await fetch(`${this.baseUrl}${path}`, {
      headers: this.headers,
    });
    if (!resp.ok) {
      throw new Error(`OpenBURO API error: ${resp.status} ${resp.statusText}`);
    }
    return resp.json() as Promise<T>;
  }
}
