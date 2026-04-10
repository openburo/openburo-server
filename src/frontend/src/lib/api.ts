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
	token?: string;
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

function authHeaders(handle: DriveHandle): HeadersInit {
	if (handle.token) {
		return { Authorization: `Bearer ${handle.token}` };
	}
	return {};
}

async function fetchConfig(serverUrl: string, token?: string): Promise<OpenBUROConfig> {
	const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
	const res = await fetch(`${serverUrl}/.well-known/openburo/config.json`, { headers });
	return res.json();
}

function serviceToHandle(
	serverUrl: string,
	serverName: string,
	svc: ServiceConfig,
	token?: string,
): DriveHandle {
	return {
		id: `${serverUrl}::${svc.id}`,
		name: `${svc.name} (${serverName})`,
		capabilities: svc.capabilities,
		serverUrl,
		driveBase: `${serverUrl}${svc.endpoints.drive}`,
		token,
	};
}

export async function discoverDrives(): Promise<DriveHandle[]> {
	const drives: DriveHandle[] = [];

	for (const server of servers) {
		try {
			const config = await fetchConfig(server.url, server.token);
			const serverName = server.name || config.name || server.url;

			if (config.services && config.services.length > 0) {
				for (const svc of config.services) {
					drives.push(serviceToHandle(server.url, serverName, svc, server.token));
				}
			} else if (config.service) {
				drives.push(serviceToHandle(server.url, serverName, config.service, server.token));
			}
		} catch {
			console.warn(`Failed to discover ${server.url}`);
		}
	}

	return drives;
}

export async function listFiles(handle: DriveHandle): Promise<FileEntry[]> {
	const res = await fetch(`${handle.driveBase}/files?deep=0`, { headers: authHeaders(handle) });
	return res.json();
}

export async function listFolder(handle: DriveHandle, folderId: string): Promise<FileEntry[]> {
	const res = await fetch(`${handle.driveBase}/files/${folderId}/children?deep=0`, { headers: authHeaders(handle) });
	return res.json();
}

export async function getFile(handle: DriveHandle, fileId: string): Promise<FileEntry> {
	const res = await fetch(`${handle.driveBase}/files/${fileId}`, { headers: authHeaders(handle) });
	return res.json();
}

export function getContentUrl(handle: DriveHandle, fileId: string): string {
	return `${handle.driveBase}/files/${fileId}/content`;
}

export async function fetchContentBlob(handle: DriveHandle, fileId: string): Promise<string> {
	const res = await fetch(`${handle.driveBase}/files/${fileId}/content`, { headers: authHeaders(handle) });
	const blob = await res.blob();
	return URL.createObjectURL(blob);
}

export async function getShareLink(handle: DriveHandle, fileId: string): Promise<ShareLink> {
	const res = await fetch(`${handle.driveBase}/files/${fileId}/share`, { headers: authHeaders(handle) });
	return res.json();
}
