const API_BASE = 'http://localhost:8000';

export interface Service {
	id: string;
	name: string;
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

export async function listDrives(): Promise<Service[]> {
	const res = await fetch(`${API_BASE}/drive`);
	return res.json();
}

export async function getDrive(id: string): Promise<Service> {
	const res = await fetch(`${API_BASE}/drive/${id}`);
	return res.json();
}

export async function listFiles(driveId: string): Promise<FileEntry[]> {
	const res = await fetch(`${API_BASE}/drive/${driveId}/files?deep=0`);
	return res.json();
}

export async function listFolder(driveId: string, folderId: string): Promise<FileEntry[]> {
	const res = await fetch(`${API_BASE}/drive/${driveId}/files/${folderId}/children?deep=0`);
	return res.json();
}

export async function getFile(driveId: string, fileId: string): Promise<FileEntry> {
	const res = await fetch(`${API_BASE}/drive/${driveId}/files/${fileId}`);
	return res.json();
}

export async function getShareLink(driveId: string, fileId: string): Promise<ShareLink> {
	const res = await fetch(`${API_BASE}/drive/${driveId}/files/${fileId}/share`);
	return res.json();
}
