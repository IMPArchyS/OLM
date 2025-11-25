export interface Device {
    id: number
    name: string
    maintenance_start: string
    maintenance_end: string
    software?: Software[]
    device_type?: DeviceType
}

export interface DeviceType {
    id: number
    name: string
    experiments: Array<{
        output_arguments: Array<{
            name: string
        }>
    }>
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

export interface OptionInput {
    name: string
    value: string
    output_value: string
}

export interface ArgumentInput {
    name: string
    label: string
    default_value: string | null
    row?: number
    order?: number
    options?: OptionInput[]
}

export interface SchemaBasic {
    id: number
    name: string
    schema: string | null
    preview: string | null
    deviceType: {
        name: string
    }
    software: {
        name: string
    }
    deleted_at: string | null
}

export interface SchemaExtended {
    id: number
    name: string
    type: string
    availableTypes: string[]
    note: string | null
    schema: string | null
    preview: string | null
    deviceType: {
        id: number
        name: string
    }
    software: {
        id: number
        name: string
    }
    arguments: ArgumentInput[]
}

export interface CreateSchemaInput {
    name: string
    type: string

    device_type_id: number
    software_id: number
    note?: string | null
    arguments: ArgumentInput[]
    schema: File | null
    preview?: File | null
}

export interface UpdateSchemaInput extends CreateSchemaInput {
    id: number
}

export enum Trashed {
    Only = 'only',
    With = 'with',
    Without = 'without',
}
