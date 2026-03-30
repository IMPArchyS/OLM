export interface Server {
    id: number;
    name: string;
    ip_address: string;
    api_domain: string;
    port: number;
    available?: boolean;
    production?: boolean;
    enabled?: boolean;
    deleted_at?: string;
}

export interface ServerStatus {
    id: number;
    available: boolean;
}

export interface Reservation {
    id: number;
    start: string;
    end: string;
    device_id: number;
    user_id: number;
    username?: string;
}

export interface Device {
    id: number;
    name: string;
    maintenance_start: string;
    maintenance_end: string;
    softwares?: Software[];
    device_type?: DeviceType;
    deleted_at?: string;
}

export interface DeviceType {
    id: number;
    name: string;
}

export interface Software {
    id: number;
    name: SoftwareName;
}

export interface Experiment {
    id: number;
    commands: Command[];
    setpoint_changes?: StepSequence;
    input_arguments: Record<string, InputArgSpec>;
    output_arguments: string[];
    simulation_time: number;
    sample_rate: number;
    devices: Device[];
    software: Software;
    schema_id?: number;
}

export interface ExperimentLog {
    id: number;
    server_id: number;
    device_id: number;
    software_name: SoftwareName;
    run: ExperimentRun;
    started_at: string;
    finished_at?: string;
    stopped_at?: string;
    timedout_at?: string;
}

export interface ExperimentRun {
    input_history: ExperimentHistoryItem[];
    output_history: Record<string, any>[];
}

export interface ExperimentHistoryItem {
    command: Command;
    input_args: Record<string, any>;
}

export interface Step {
    duration: number;
    value: number;
}

export interface StepSequence {
    start_value: number;
    steps: Step[];
}

export interface InputArgSpec {
    type: 'number' | 'string';
    value: number | string;
    unit: string;
}

export enum SoftwareName {
    OPENLOOP = 'openloop',
    MATLAB = 'matlab',
    SCILAB = 'scilab',
    OPENMODELICA = 'openmodelica',
}

export enum Command {
    INIT = 'init',
    START = 'start',
    CHANGE = 'change',
    STOP = 'stop',
}
