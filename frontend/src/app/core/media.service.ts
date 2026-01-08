import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface MediaItem {
  id: string;
  type: 'photo' | 'video' | 'audio';
  title: string;
  blob: {
    containerName: string;
    blobName: string;
    url: string;
  };
  sizeBytes: number;
  status: 'active' | 'trashed' | 'deleted_permanent';
  isFavorite: boolean;
  isDeleted: boolean;
  createdAt: string;
  trashedAt?: string;
}

export interface MediaListResponse {
  items: MediaItem[];
}

export interface StorageSummary {
  usedBytes: number;
  quotaBytes: number;
  availableBytes: number;
  usagePercentage: number;
  updatedAt: string;
}

@Injectable({
  providedIn: 'root'
})
export class MediaService {
  private readonly API_BASE = 'http://localhost:5001/api';

  constructor(private http: HttpClient) { }

  uploadMedia(file: File, title: string): Observable<MediaItem> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    return this.http.post<MediaItem>(`${this.API_BASE}/media/upload`, formData);
  }

  getMedia(filters?: {
    type?: 'photo' | 'video' | 'audio';
    favorites?: boolean;
    trash?: boolean;
    limit?: number;
    skip?: number;
  }): Observable<MediaListResponse> {
    let params: any = {};
    
    if (filters) {
      if (filters.type) params.type = filters.type;
      if (filters.favorites !== undefined) params.favorites = filters.favorites.toString();
      if (filters.trash !== undefined) params.trash = filters.trash.toString();
      if (filters.limit) params.limit = filters.limit.toString();
      if (filters.skip) params.skip = filters.skip.toString();
    }

    return this.http.get<MediaListResponse>(`${this.API_BASE}/media`, { params });
  }

  toggleFavorite(mediaId: string, isFavorite: boolean): Observable<{success: boolean}> {
    return this.http.patch<{success: boolean}>(`${this.API_BASE}/media/${mediaId}/favorite`, {
      isFavorite
    });
  }

  toggleTrash(mediaId: string, isDeleted: boolean): Observable<{success: boolean}> {
    return this.http.patch<{success: boolean}>(`${this.API_BASE}/media/${mediaId}/trash`, {
      isDeleted
    });
  }

  deleteMedia(mediaId: string): Observable<{success: boolean}> {
    return this.http.delete<{success: boolean}>(`${this.API_BASE}/media/${mediaId}`);
  }

  getStorageSummary(): Observable<StorageSummary> {
    return this.http.get<StorageSummary>(`${this.API_BASE}/media/storage`);
  }

  formatBytes(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }

  getPlanDisplayName(quotaBytes: number): string {
    const gb = quotaBytes / (1024 * 1024 * 1024);
    if (gb <= 5) return 'Free Plan';
    if (gb <= 100) return 'Pro Plan';
    return 'Enterprise Plan';
  }
}