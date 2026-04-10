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
	name?: string;
	services?: ServiceConfig[];
	service?: ServiceConfig;
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

function serviceToHandle(serverUrl: string, serverName: string, svc: ServiceConfig): DriveHandle {
	return {
		id: `${serverUrl}::${svc.id}`,
		name: `${svc.name} (${serverName})`,
		capabilities: svc.capabilities,
		serverUrl,
		driveBase: `${serverUrl}${svc.endpoints.drive}`,
	};
}

export async function discoverDrives(): Promise<DriveHandle[]> {
	const drives: DriveHandle[] = [];

	for (const server of servers) {
		try {
			const config = await fetchConfig(server.url);
			const serverName = server.name || config.name || server.url;

			if (config.services && config.services.length > 0) {
				for (const svc of config.services) {
					drives.push(serviceToHandle(server.url, serverName, svc));
				}
			} else if (config.service) {
				drives.push(serviceToHandle(server.url, serverName, config.service));
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
