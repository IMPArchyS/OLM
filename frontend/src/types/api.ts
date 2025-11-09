export interface Device {
    id: number
    name: string
}

export interface Reservation {
    id: number
    start: string
    end: string
    device_id: number
    username?: string
}

export interface Experiment {
    id: number
    name: string
    description?: string
    device_id: number
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
