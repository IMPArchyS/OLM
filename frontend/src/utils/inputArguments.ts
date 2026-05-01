import type { InputArgSpec } from '@/types/api';

export interface InputArgumentRow {
    key: string;
    type: InputArgSpec['type'];
    value: number | string;
    unit: string;
}

export type BuildInputArgumentsError = 'duplicate' | 'invalid_number';

export type BuildInputArgumentsResult =
    | { data: Record<string, InputArgSpec>; error: null }
    | { data: null; error: BuildInputArgumentsError };

export function buildInputArguments(rows: InputArgumentRow[]): BuildInputArgumentsResult {
    const inputArguments: Record<string, InputArgSpec> = {};

    for (const row of rows) {
        const key = row.key.trim();
        if (!key) continue;

        if (inputArguments[key]) {
            return { data: null, error: 'duplicate' };
        }

        if (row.type === 'number') {
            const numericValue = Number(row.value);
            if (Number.isNaN(numericValue)) {
                return { data: null, error: 'invalid_number' };
            }
            inputArguments[key] = { type: row.type, value: numericValue, unit: row.unit.trim() };
            continue;
        }

        inputArguments[key] = { type: row.type, value: String(row.value ?? ''), unit: row.unit.trim() };
    }

    return { data: inputArguments, error: null };
}
