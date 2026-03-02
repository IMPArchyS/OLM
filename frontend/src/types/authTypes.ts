export interface User {
    id: number;
    username: string;
    name: string;
    admin: boolean;
    role_id: number;
}

export interface Role {
    id: number;
    name: string;
    description: string;
    permissions: Permision[];
}

export interface Permision {
    id: number;
    name: string;
    description: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    refresh_token_expires_at: string;
}

export interface OauthCredentials {
    provider: string;
    redirect: string;
}

export interface OauthProvider {
    id: number;
    name: string;
    display_name: string;
    logo_url: string;
}
