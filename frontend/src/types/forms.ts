import type { Command, InputArgSpec, SoftwareName, StepSequence } from './api';

export interface LoginForm {
    username: string;
    password: string;
}

export interface RegisterForm {
    name: string;
    username: string;
    password: string;
}

export interface ReservationForm {
    deviceId: number;
    startDate: string;
    endDate: string;
}

export interface CreateServerForm {
    name?: string;
    ip_address?: string;
    api_domain?: string;
    port?: number;
}

export interface EditServerForm {
    id?: number;
    name?: string;
    ip_address?: string;
    api_domain?: string;
    port?: number;
    production?: boolean;
    enabled?: boolean;
}

export interface QueueFormData {
    user_id: number | null;
    id: number | null;
    server_id: number | null;
    command: Command | null;
    input_arguments: Record<string, InputArgSpec>;
    output_arguments: string[];
    setpoint_changes: StepSequence | Record<string, never>;
    schema_id: number | null;
    simulation_time: number;
    device_id: number | null;
    software_name: SoftwareName | null;
    sample_rate: number;
}
