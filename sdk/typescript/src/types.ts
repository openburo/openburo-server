export interface Service {
  id: string;
  name: string;
}

export interface File {
  id: string;
  name: string;
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
