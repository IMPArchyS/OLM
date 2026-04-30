export interface User {
    id: number;
    username: string;
    name: string;
}

export interface AuthResponse {
    access_token: string;
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
