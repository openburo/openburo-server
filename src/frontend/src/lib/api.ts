import { servers, type ServerConfig } from './config';

export interface OpenBUROConfig {
	version: string;
	name: string;
	capabilities: string[];
	endpoints: {
		drive: string;
	};
}

export interface DriveHandle {
	id: string;
	name: string;
	serverUrl: string;
	driveBase: string; // full URL to the drive endpoint
	driveId: string | null; // null for direct certified services (they ARE the drive)
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
			const driveBase = `${server.url}${config.endpoints.drive}`;

			// Try to list sub-drives (router pattern)
			const res = await fetch(driveBase);
			if (res.ok) {
				const subDrives = await res.json();
				if (Array.isArray(subDrives) && subDrives.length > 0) {
					for (const d of subDrives) {
						drives.push({
							id: `${server.url}::${d.id}`,
							name: `${d.name || d.id} (${server.name || config.name})`,
							serverUrl: server.url,
							driveBase,
							driveId: d.id,
						});
					}
					continue;
				}
			}

			// Single drive (certified service pattern)
			drives.push({
				id: `${server.url}::direct`,
				name: server.name || config.name,
				serverUrl: server.url,
				driveBase,
				driveId: null,
			});
		} catch {
			console.warn(`Failed to discover ${server.url}`);
		}
	}

	return drives;
}

function drivePath(handle: DriveHandle): string {
	if (handle.driveId) {
		return `${handle.driveBase}/${handle.driveId}`;
	}
	return handle.driveBase;
}

export async function listFiles(handle: DriveHandle): Promise<FileEntry[]> {
	const res = await fetch(`${drivePath(handle)}/files?deep=0`);
	return res.json();
}

export async function listFolder(handle: DriveHandle, folderId: string): Promise<FileEntry[]> {
	const res = await fetch(`${drivePath(handle)}/files/${folderId}/children?deep=0`);
	return res.json();
}

export async function getFile(handle: DriveHandle, fileId: string): Promise<FileEntry> {
	const res = await fetch(`${drivePath(handle)}/files/${fileId}`);
	return res.json();
}

export function getContentUrl(handle: DriveHandle, fileId: string): string {
	return `${drivePath(handle)}/files/${fileId}/content`;
}

export async function getShareLink(handle: DriveHandle, fileId: string): Promise<ShareLink> {
	const res = await fetch(`${drivePath(handle)}/files/${fileId}/share`);
	return res.json();
}
