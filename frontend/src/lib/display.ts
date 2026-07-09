import type { Notification, Region, Severity } from './types';

export const severityRank: Record<Severity, number> = {
  green: 0,
  yellow: 1,
  red: 2
};

export const severityColor: Record<Severity, string> = {
  green: '#31c873',
  yellow: '#f2c94c',
  red: '#ff5a4f'
};

export function notificationSeverityForRegion(
  region: Region,
  notifications: Notification[]
): Severity {
  const regionNotifications = notifications.filter((item) => item.region_id === region.id);
  if (regionNotifications.length === 0) return 'green';
  return regionNotifications.reduce<Severity>((highest, item) =>
    severityRank[item.severity] > severityRank[highest] ? item.severity : highest
  , 'green');
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return 'Not scheduled';
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value));
}
