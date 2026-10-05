import type { UploadedFile } from '@/types';
import { BASE_URL, USE_MOCK } from './api';

export type UploadProgressCallback = (percent: number) => void;

const MAX_FILE_SIZE = 50 * 1024 * 1024;
const ALLOWED_EXTENSIONS = ['.csv', '.json', '.xlsx', '.parquet'];
const ALLOWED_MIME_TYPES = [
  'text/csv',
  'application/csv',
  'application/json',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
  'application/parquet',
];

export function validateFileSize(file: File): { valid: boolean; error?: string } {
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: `File too large. Maximum size is 50MB.`,
    };
  }
  return { valid: true };
}

export function validateFileType(file: File): { valid: boolean; error?: string } {
  const name = file.name.toLowerCase();
  const extMatch = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext));
  const mimeMatch = ALLOWED_MIME_TYPES.includes(file.type);

  if (!extMatch && !mimeMatch) {
    return {
      valid: false,
      error: `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`,
    };
  }
  return { valid: true };
}

function generateId(): string {
  return `FILE-${Date.now()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

export async function uploadFile(
  file: File,
  onProgress?: UploadProgressCallback
): Promise<UploadedFile> {
  const sizeCheck = validateFileSize(file);
  if (!sizeCheck.valid) {
    throw new Error(sizeCheck.error);
  }

  const typeCheck = validateFileType(file);
  if (!typeCheck.valid) {
    throw new Error(typeCheck.error);
  }

  const fileId = generateId();
  const uploadedAt = new Date().toISOString();

  if (USE_MOCK) {
    return new Promise((resolve) => {
      const totalDuration = 2000;
      const steps = 20;
      const stepInterval = totalDuration / steps;
      let currentStep = 0;

      const interval = setInterval(() => {
        currentStep += 1;
        const percent = Math.min(100, Math.round((currentStep / steps) * 100));

        if (onProgress) {
          onProgress(percent);
        }

        if (currentStep >= steps) {
          clearInterval(interval);
          resolve({
            id: fileId,
            name: file.name,
            size: file.size,
            type: file.type || 'application/octet-stream',
            uploadedAt,
            status: 'ready',
            percent: 100,
          });
        }
      }, stepInterval);
    });
  }

  const formData = new FormData();
  formData.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve({
            id: response?.id || fileId,
            name: response?.name || file.name,
            size: response?.size || file.size,
            type: response?.type || file.type || 'application/octet-stream',
            uploadedAt: response?.uploadedAt || uploadedAt,
            status: response?.status || 'processing',
            percent: 100,
          });
        } catch {
          resolve({
            id: fileId,
            name: file.name,
            size: file.size,
            type: file.type || 'application/octet-stream',
            uploadedAt,
            status: 'processing',
            percent: 100,
          });
        }
      } else {
        let message = `Upload failed: ${xhr.status}`;
        try {
          const err = JSON.parse(xhr.responseText);
          if (err?.message) message = err.message;
        } catch {
          // ignore parse error
        }
        reject(new Error(message));
      }
    };

    xhr.onerror = () => {
      reject(new Error('Network error during upload.'));
    };

    xhr.open('POST', `${BASE_URL}/datasets/upload`);

    const token = localStorage.getItem('ml-auth-token');
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.send(formData);
  });
}

export function createFilePreviewUrl(file: File): string {
  const name = file.name.toLowerCase();

  const isTextType =
    name.endsWith('.csv') ||
    name.endsWith('.json') ||
    file.type.startsWith('text/') ||
    file.type === 'application/json';

  if (isTextType) {
    return URL.createObjectURL(file);
  }

  return '';
}
