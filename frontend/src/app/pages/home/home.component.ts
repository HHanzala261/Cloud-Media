import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthService, User } from '../../core/auth.service';
import { MediaService, MediaItem, StorageSummary } from '../../core/media.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit, OnDestroy {
  currentUser: User | null = null;
  mediaItems: MediaItem[] = [];
  filteredItems: MediaItem[] = [];
  activeTab: string = 'photos';
  searchQuery: string = '';
  isLoading = false;
  nowPlaying: MediaItem | null = null;
  uploadingFiles: Set<string> = new Set();
  operatingItems: Set<string> = new Set();
  uploadProgress: Map<string, number> = new Map();
  uploadError: string | null = null;
  
  // Storage tracking
  storageSummary: StorageSummary | null = null;
  storageLoading = false;
  
  // Subscription management
  private userSubscription: Subscription = new Subscription();

  constructor(
    private authService: AuthService,
    private mediaService: MediaService
  ) {}

  ngOnInit(): void {
    // Subscribe to current user changes for immediate UI updates
    this.userSubscription = this.authService.currentUser$.subscribe(user => {
      this.currentUser = user;
      console.log('HomeComponent: Current user updated:', user);
    });
    
    this.loadMedia();
    this.loadStorageSummary();
  }

  ngOnDestroy(): void {
    // Clean up subscription to prevent memory leaks
    this.userSubscription.unsubscribe();
  }

  setActiveTab(tab: string): void {
    console.log('HomeComponent: Setting active tab to:', tab);
    this.activeTab = tab;
    this.loadMedia();
  }

  loadMedia(): void {
    this.isLoading = true;
    
    let filters: any = {};
    
    switch (this.activeTab) {
      case 'photos':
        filters.type = 'photo';
        break;
      case 'videos':
        filters.type = 'video';
        break;
      case 'audio':
        filters.type = 'audio';
        break;
      case 'favorites':
        filters.favorites = true;
        break;
      case 'trash':
        filters.trash = true;
        break;
    }

    console.log('HomeComponent: Loading media with filters:', filters);

    this.mediaService.getMedia(filters).subscribe({
      next: (response) => {
        console.log('HomeComponent: Media loaded successfully:', response);
        this.mediaItems = response.items;
        this.applySearch();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('HomeComponent: Error loading media:', error);
        
        // Handle authentication errors
        if (error.status === 401) {
          console.log('HomeComponent: 401 error - clearing auth and redirecting to login');
          this.authService.logout();
          // Note: Don't manually navigate here, let the AuthGuard handle it
        }
        
        this.isLoading = false;
      }
    });
  }

  onSearch(): void {
    this.applySearch();
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.applySearch();
  }

  applySearch(): void {
    if (!this.searchQuery.trim()) {
      this.filteredItems = this.mediaItems;
    } else {
      const query = this.searchQuery.toLowerCase().trim();
      this.filteredItems = this.mediaItems.filter(item =>
        item.title.toLowerCase().includes(query)
      );
    }
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      // Clear any previous upload error
      this.uploadError = null;
      
      // Validate file size (100MB limit)
      const maxSize = 100 * 1024 * 1024; // 100MB
      if (file.size > maxSize) {
        this.uploadError = 'File too large. Maximum size is 100MB.';
        return;
      }
      
      // Validate file type
      const allowedTypes = ['image/', 'video/', 'audio/'];
      const isValidType = allowedTypes.some(type => file.type.startsWith(type));
      if (!isValidType) {
        this.uploadError = 'Invalid file type. Please select an image, video, or audio file.';
        return;
      }
      
      this.uploadFile(file);
    }
    
    // Reset the file input
    event.target.value = '';
  }

  uploadFile(file: File): void {
    const title = file.name;
    const fileId = `${file.name}-${Date.now()}`;
    this.uploadingFiles.add(fileId);
    this.uploadProgress.set(fileId, 0);
    this.uploadError = null;
    
    this.mediaService.uploadMedia(file, title).subscribe({
      next: (response) => {
        console.log('Upload successful:', response);
        this.uploadingFiles.delete(fileId);
        this.uploadProgress.delete(fileId);
        
        // Update storage summary if included in response
        if ((response as any).storage) {
          this.storageSummary = (response as any).storage;
        } else {
          this.loadStorageSummary(); // Fallback: reload storage summary
        }
        
        this.loadMedia(); // Refresh the list
      },
      error: (error) => {
        console.error('Upload failed:', error);
        this.uploadingFiles.delete(fileId);
        this.uploadProgress.delete(fileId);
        
        // Set user-friendly error message
        if (error.status === 413) {
          if (error.error?.error?.includes('quota')) {
            this.uploadError = error.error.error; // Use server's quota message
          } else {
            this.uploadError = 'File too large. Maximum size is 100MB.';
          }
        } else if (error.status === 400) {
          this.uploadError = error.error?.error || 'Invalid file. Please check the file type and try again.';
        } else if (error.status === 401) {
          this.uploadError = 'Authentication failed. Please log in again.';
        } else {
          this.uploadError = 'Upload failed. Please try again.';
        }
      }
    });
  }

  toggleFavorite(item: MediaItem): void {
    if (this.operatingItems.has(item.id)) return;
    
    this.operatingItems.add(item.id);
    const newFavoriteStatus = !item.isFavorite;
    
    this.mediaService.toggleFavorite(item.id, newFavoriteStatus).subscribe({
      next: () => {
        item.isFavorite = newFavoriteStatus;
        this.operatingItems.delete(item.id);
        // If we're viewing favorites and item is no longer favorite, remove it
        if (this.activeTab === 'favorites' && !newFavoriteStatus) {
          this.loadMedia();
        }
      },
      error: (error) => {
        console.error('Error toggling favorite:', error);
        this.operatingItems.delete(item.id);
        alert('Failed to update favorite status. Please try again.');
      }
    });
  }

  toggleTrash(item: MediaItem): void {
    if (this.operatingItems.has(item.id)) return;
    
    this.operatingItems.add(item.id);
    const newTrashStatus = !item.isDeleted;
    
    this.mediaService.toggleTrash(item.id, newTrashStatus).subscribe({
      next: (response) => {
        item.isDeleted = newTrashStatus;
        this.operatingItems.delete(item.id);
        
        // Update storage summary if included in response
        if ((response as any).storage) {
          this.storageSummary = (response as any).storage;
        }
        
        // If we're not viewing trash and item is now deleted, remove it
        if (this.activeTab !== 'trash' && newTrashStatus) {
          this.loadMedia();
        }
      },
      error: (error) => {
        console.error('Error toggling trash:', error);
        this.operatingItems.delete(item.id);
        alert('Failed to move item to trash. Please try again.');
      }
    });
  }

  deleteMedia(item: MediaItem): void {
    if (this.operatingItems.has(item.id)) return;
    
    if (confirm('Are you sure you want to permanently delete this item?')) {
      this.operatingItems.add(item.id);
      
      this.mediaService.deleteMedia(item.id).subscribe({
        next: (response) => {
          this.operatingItems.delete(item.id);
          
          // Update storage summary if included in response
          if ((response as any).storage) {
            this.storageSummary = (response as any).storage;
          } else {
            this.loadStorageSummary(); // Fallback: reload storage summary
          }
          
          this.loadMedia(); // Refresh the list
        },
        error: (error) => {
          console.error('Error deleting media:', error);
          this.operatingItems.delete(item.id);
          alert('Failed to delete item. Please try again.');
        }
      });
    }
  }

  playAudio(item: MediaItem): void {
    if (item.type === 'audio') {
      // If the same audio is clicked, don't restart it
      if (this.nowPlaying?.id === item.id) {
        return;
      }
      this.nowPlaying = item;
    }
  }

  stopAudio(): void {
    this.nowPlaying = null;
  }

  logout(): void {
    console.log('HomeComponent: Logout button clicked');
    this.authService.logout();
  }

  isOperating(itemId: string): boolean {
    return this.operatingItems.has(itemId);
  }

  isCurrentlyPlaying(item: MediaItem): boolean {
    return this.nowPlaying?.id === item.id;
  }

  loadStorageSummary(): void {
    this.storageLoading = true;
    this.mediaService.getStorageSummary().subscribe({
      next: (summary) => {
        this.storageSummary = summary;
        this.storageLoading = false;
      },
      error: (error) => {
        console.error('Error loading storage summary:', error);
        this.storageLoading = false;
      }
    });
  }

  formatBytes(bytes: number): string {
    return this.mediaService.formatBytes(bytes);
  }

  getPlanDisplayName(): string {
    if (!this.storageSummary) return '';
    return this.mediaService.getPlanDisplayName(this.storageSummary.quotaBytes);
  }

  getStoragePercentage(): number {
    if (!this.storageSummary || this.storageSummary.quotaBytes === 0) return 0;
    return Math.min(100, (this.storageSummary.usedBytes / this.storageSummary.quotaBytes) * 100);
  }

  getStorageBarColor(): string {
    const percentage = this.getStoragePercentage();
    if (percentage >= 90) return '#dc3545'; // Red
    if (percentage >= 75) return '#fd7e14'; // Orange  
    if (percentage >= 50) return '#ffc107'; // Yellow
    return '#28a745'; // Green
  }
}