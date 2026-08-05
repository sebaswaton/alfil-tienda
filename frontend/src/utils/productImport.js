export function canImportValidatedFile(file, preview, busy) {
  return Boolean(
    file
    && preview?.can_import
    && preview.total_rows > 0
    && preview.invalid_rows === 0
    && !busy
  );
}


export function canUploadValidatedZip(file, preview, busy) {
  return Boolean(
    file
    && preview?.can_upload
    && preview.total_files > 0
    && preview.invalid_files === 0
    && !busy
  );
}


export function formatFileSize(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
