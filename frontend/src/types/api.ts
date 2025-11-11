export interface Device {
    id: number
    name: string
    software?: Software[]
    device_type?: DeviceType
}

export interface DeviceType {
    id: number
    name: string
}

export interface Software {
    id: number
    name: string
}

export interface Reservation {
    id: number
    start: string
    end: string
    device_id: number
    queued: boolean
    username?: string
}

export interface Experiment {
    id: number
    name: string
    description?: string
    device_id: number
    software_id: number
    has_schema?: boolean
    commands?: Record<string, CommandSpec>
    experiment_commands?: Record<string, CommandSpec>
}

export interface Command {
    cmd: string
}

export interface CommandSpec {
    type: 'number' | 'select' | 'expression' | 'string'
    value?: number | string | null
    unit?: string | null
}

export interface Schema {
    id: number
    name: string
    description?: string
}

export interface ApiError {
    message: string
    code?: string
}

export interface Server {
    id: number
    name: string
    ip_address: string
    api_domain: string
    websocket_port: number
    available?: boolean
    production?: boolean
    enabled?: boolean
    deleted_at?: string
}
