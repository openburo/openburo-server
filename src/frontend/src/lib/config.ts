export interface ServerConfig {
	url: string;
	name?: string;
	token?: string;
}

export const servers: ServerConfig[] = [
	{ url: 'http://localhost:8000', name: 'OpenBURO Router' },
	{ url: 'https://mytwake-drive.10.3.0.227.nip.io', name: 'Twake Direct', token: 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJteXR3YWtlLjEwLjMuMC4yMjcubmlwLmlvIiwiYXVkIjpbImNsaSJdLCJpYXQiOjE3NzU4MjcyOTQsInNjb3BlIjoiaW8uY296eS5maWxlcyBpby5jb3p5LnNldHRpbmdzIn0.RGaOjC5h_k4JME2LRWnbM9aJ8s-YHiVSuIcwmC1KXQ_XqtrdFJwbbKVQhgKOux-_--hy89UNT5ks1lGv3iiXAg' },
];
