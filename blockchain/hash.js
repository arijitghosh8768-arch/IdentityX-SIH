import crypto from 'crypto';

/**
 * Generates a SHA-256 hex hash of a file buffer (prefixed with 0x).
 * @param {Buffer} fileBuffer 
 * @returns {string} SHA-256 hash hex string
 */
export function hashFile(fileBuffer) {
  if (!fileBuffer) return '';
  return '0x' + crypto.createHash('sha256').update(fileBuffer).digest('hex');
}

/**
 * Generates a deterministic SHA-256 hex hash of a report object (prefixed with 0x).
 * @param {Object} reportData 
 * @returns {string} SHA-256 hash hex string
 */
export function hashReport(reportData) {
  if (!reportData) return '';
  // Sort keys to produce deterministic JSON string representation
  const sortedKeys = Object.keys(reportData).sort();
  const reportString = JSON.stringify(reportData, sortedKeys);
  return '0x' + crypto.createHash('sha256').update(reportString).digest('hex');
}
