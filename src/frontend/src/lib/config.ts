export interface ServerConfig {
	url: string;
	name?: string;
}

export const servers: ServerConfig[] = [
	{ url: 'http://localhost:8000', name: 'OpenBURO Router' },
	{ url: 'https://mytwake-drive.10.3.0.227.nip.io', name: 'Twake Direct' },
];
