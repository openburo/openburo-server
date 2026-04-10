import { servers } from './config';

export interface ServiceConfig {
	id: string;
	name: string;
	capabilities: string[];
	endpoints: {
		drive: string;
	};
}

export interface OpenBUROConfig {
	version: string;
	name: string;
	services?: ServiceConfig[];
	// Legacy single-service format
	capabilities?: string[];
	endpoints?: {
		drive: string;
	};
}

export interface DriveHandle {
	id: string;
	name: string;
	capabilities: string[];
	serverUrl: string;
	driveBase: string;
}

export interface FileEntry {
	id: string;
	name: string;
	type: 'file' | 'directory';
	mime_type: string;
	path: string;
	last_modified: string;
	creation_date: string;
	owner: string;
	size: number;
}

export interface ShareLink {
	url: string;
}

async function fetchConfig(serverUrl: string): Promise<OpenBUROConfig> {
	const res = await fetch(`${serverUrl}/.well-known/openburo/config.json`);
	return res.json();
}

export async function discoverDrives(): Promise<DriveHandle[]> {
	const drives: DriveHandle[] = [];

	for (const server of servers) {
		try {
			const config = await fetchConfig(server.url);

			if (config.services && config.services.length > 0) {
				// Multi-service format: each service has its own endpoints
				for (const svc of config.services) {
					drives.push({
						id: `${server.url}::${svc.id}`,
						name: `${svc.name} (${server.name || config.name})`,
						capabilities: svc.capabilities,
						serverUrl: server.url,
						driveBase: `${server.url}${svc.endpoints.drive}`,
					});
				}
			} else if (config.endpoints?.drive) {
				// Single-service format — try listing sub-drives
				const driveBase = `${server.url}${config.endpoints.drive}`;
				try {
					const res = await fetch(driveBase);
					if (res.ok) {
						const subDrives = await res.json();
						if (Array.isArray(subDrives) && subDrives.length > 0) {
							for (const d of subDrives) {
								drives.push({
									id: `${server.url}::${d.id}`,
									name: `${d.name || d.id} (${server.name || config.name})`,
									capabilities: config.capabilities || [],
									serverUrl: server.url,
									driveBase: `${driveBase}/${d.id}`,
								});
							}
							continue;
						}
					}
				} catch { /* fall through to single drive */ }

				// Truly single drive
				drives.push({
					id: `${server.url}::direct`,
					name: server.name || config.name,
					capabilities: config.capabilities || [],
					serverUrl: server.url,
					driveBase: driveBase,
				});
			}
		} catch {
			console.warn(`Failed to discover ${server.url}`);
		}
	}

	return drives;
}

export async function listFiles(handle: DriveHandle): Promise<FileEntry[]> {
	const res = await fetch(`${handle.driveBase}/files?deep=0`);
	return res.json();
}

export async function listFolder(handle: DriveHandle, folderId: string): Promise<FileEntry[]> {
	const res = await fetch(`${handle.driveBase}/files/${folderId}/children?deep=0`);
	return res.json();
}

export async function getFile(handle: DriveHandle, fileId: string): Promise<FileEntry> {
	const res = await fetch(`${handle.driveBase}/files/${fileId}`);
	return res.json();
}

export function getContentUrl(handle: DriveHandle, fileId: string): string {
	return `${handle.driveBase}/files/${fileId}/content`;
}

export async function getShareLink(handle: DriveHandle, fileId: string): Promise<ShareLink> {
	const res = await fetch(`${handle.driveBase}/files/${fileId}/share`);
	return res.json();
}
