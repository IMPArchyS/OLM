export interface ReservationForm {
    deviceId: number;
    startDate: string;
    endDate: string;
}

export interface CreateServerForm {
    name?: string;
    ip_address?: string;
    api_domain?: string;
    websocket_port?: number;
}

export interface EditServerForm {
    id?: number;
    name?: string;
    ip_address?: string;
    api_domain?: string;
    websocket_port?: number;
    production?: boolean;
    enabled?: boolean;
}
