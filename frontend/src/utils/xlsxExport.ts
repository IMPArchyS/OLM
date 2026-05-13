import * as XLSX from 'xlsx';
import type { ExperimentLog } from '@/types/api';
import { estimateSampleInterval, estimateSimulationTime, formatFinishReason } from '@/utils/reportFormatters';

type Translator = (key: string) => string;
type Row = Array<string | number>;

const sanitizePart = (value: string | null | undefined): string => {
    if (!value) return '';
    return value.replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, '_');
};

const formatDateForFilename = (locale: string, date: Date): string => {
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const yyyy = String(date.getFullYear());
    return locale === 'sk' ? `${dd}-${mm}-${yyyy}` : `${yyyy}-${mm}-${dd}`;
};

const formatCellDateTime = (value: string | null | undefined): string => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
};

const buildMetadataRows = (log: ExperimentLog, t: Translator, showUserName: boolean): Row[] => {
    const simTime = estimateSimulationTime(log);
    const sampleInterval = estimateSampleInterval(log);
    const rows: Row[] = [
        [t('reports.export.metadataSheet')],
        [t('reports.export.field'), t('reports.export.value')],
        [t('reports.export.server'), log.server_name ?? ''],
        [t('reports.export.device'), log.device_name ?? ''],
        [t('reports.export.software'), log.software_name ?? ''],
    ];
    if (showUserName) rows.push([t('reports.export.username'), log.username ?? '']);
    rows.push(
        [t('reports.started'), formatCellDateTime(log.started_at)],
        [t('reports.finished'), formatCellDateTime(log.finished_at)],
        [t('reports.finishReason'), formatFinishReason(log.finish_reason, t)],
        [t('reports.simulationTime'), simTime !== null ? `${simTime} s` : ''],
        [t('reports.sampleInterval'), sampleInterval !== null ? `${sampleInterval} s` : ''],
    );
    return rows;
};

const buildInputRows = (log: ExperimentLog, t: Translator): Row[] => {
    const rows: Row[] = [
        [t('reports.inputHistory')],
        [
            t('reports.export.entry'),
            t('reports.export.command'),
            t('reports.export.argument'),
            t('reports.export.value'),
            t('reports.unit'),
        ],
    ];
    const entries = log.run?.input_history ?? [];
    if (entries.length === 0) {
        rows.push([t('reports.noInputHistory')]);
        return rows;
    }
    entries.forEach((entry, index) => {
        const args = Object.entries(entry.input_args ?? {});
        if (args.length === 0) {
            rows.push([index + 1, String(entry.command ?? ''), '', '', '']);
            return;
        }
        args.forEach(([key, rawValue]) => {
            let cellValue: string | number = '';
            let unit = '';
            if (rawValue !== null && rawValue !== undefined) {
                if (typeof rawValue === 'object' && !Array.isArray(rawValue)) {
                    const obj = rawValue as { value?: unknown; unit?: unknown };
                    if (obj.value !== undefined) {
                        cellValue = typeof obj.value === 'number' ? obj.value : String(obj.value);
                    } else {
                        cellValue = JSON.stringify(rawValue);
                    }
                    if (typeof obj.unit === 'string') unit = obj.unit;
                } else if (typeof rawValue === 'number') {
                    cellValue = rawValue;
                } else {
                    cellValue = String(rawValue);
                }
            }
            rows.push([index + 1, String(entry.command ?? ''), key, cellValue, unit]);
        });
    });
    return rows;
};

const buildOutputRows = (log: ExperimentLog, t: Translator): Row[] => {
    const rows: Row[] = [[t('reports.outputHistoryTitle')]];
    const output = log.run?.output_history ?? [];
    if (output.length === 0) {
        rows.push([t('reports.noRunData')]);
        return rows;
    }
    const columnSet = new Set<string>();
    output.forEach((row) => Object.keys(row).forEach((k) => columnSet.add(k)));
    const columns = ['time', ...Array.from(columnSet).filter((c) => c !== 'time')];
    rows.push(columns);
    output.forEach((row) => {
        rows.push(
            columns.map((col) => {
                const raw = (row as Record<string, unknown>)[col];
                if (raw === null || raw === undefined) return '';
                if (typeof raw === 'number' || typeof raw === 'string') return raw;
                return JSON.stringify(raw);
            }),
        );
    });
    return rows;
};

export const exportLogToXlsx = (log: ExperimentLog, t: Translator, locale: string, showUserName: boolean): void => {
    const allRows: Row[] = [
        ...buildMetadataRows(log, t, showUserName),
        [],
        ...buildInputRows(log, t),
        [],
        ...buildOutputRows(log, t),
    ];

    const sheet = XLSX.utils.aoa_to_sheet(allRows);
    sheet['!cols'] = [{ wch: 22 }, { wch: 20 }, { wch: 20 }, { wch: 18 }, { wch: 10 }];

    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, sheet, t('reports.export.sheetName'));

    const datePart = formatDateForFilename(locale, log.started_at ? new Date(log.started_at) : new Date());
    const parts = [
        t('reports.export.filenamePrefix'),
        sanitizePart(log.server_name),
        sanitizePart(log.device_name),
        sanitizePart(log.software_name),
        datePart,
    ].filter((p) => p.length > 0);
    const filename = `${parts.join('-')}.xlsx`;

    XLSX.writeFile(workbook, filename);
};
