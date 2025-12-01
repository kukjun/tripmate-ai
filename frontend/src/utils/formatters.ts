/**
 * Utility functions for formatting data
 */

/**
 * Format number with commas (Korean style)
 * @example formatNumber(1000000) => "1,000,000"
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('ko-KR');
}

/**
 * Format currency (Korean Won)
 * @example formatCurrency(1000000) => "1,000,000원"
 */
export function formatCurrency(amount: number): string {
  return `${formatNumber(amount)}원`;
}

/**
 * Format date to Korean format
 * @example formatDate("2024-12-20") => "12월 20일"
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('ko-KR', {
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format duration
 * @example formatDuration(3) => "3박 4일"
 */
export function formatDuration(nights: number): string {
  return `${nights}박 ${nights + 1}일`;
}

/**
 * Format travel style array
 * @example formatTravelStyle(["관광", "맛집"]) => "관광, 맛집"
 */
export function formatTravelStyle(styles: string[]): string {
  return styles.join(', ');
}

/**
 * Get option type label
 * @example getOptionLabel("budget") => "저가형"
 */
export function getOptionLabel(type: string): string {
  const labels: Record<string, string> = {
    budget: '저가형',
    standard: '추천',
    premium: '프리미엄',
  };
  return labels[type] || type;
}

/**
 * Get activity type emoji
 */
export function getActivityEmoji(type: string): string {
  const emojis: Record<string, string> = {
    transport: '🚗',
    sightseeing: '🏛️',
    food: '🍽️',
    shopping: '🛍️',
    rest: '😴',
  };
  return emojis[type] || '📍';
}
