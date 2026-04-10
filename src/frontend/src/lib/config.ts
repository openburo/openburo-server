export interface ServerConfig {
	url: string;
	name?: string;
	token?: string;
}

export const servers: ServerConfig[] = [
	{ url: 'http://localhost:8000', name: 'OpenBURO Router' },
	{ url: 'https://mytwake-drive.10.3.0.227.nip.io', name: 'Twake Direct', token: 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJteXR3YWtlLjEwLjMuMC4yMjcubmlwLmlvIiwiYXVkIjpbImNsaSJdLCJpYXQiOjE3NzU4MTA2NjIsInNjb3BlIjoiaW8uY296eS5maWxlcyBpby5jb3p5LnBlcm1pc3Npb25zIn0.reoOuyx2p5sN7S8MVNiI3HFNfCAEkUiq19lUyfEsJB90jCVNZkvoLBRaGEXyamiltxBh7xNNV_VBMyeddk2KRQ' },
];
