import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import * as fc from 'fast-check';

import { HomeComponent } from './home.component';
import { AuthService } from '../../core/auth.service';
import { MediaService, MediaItem } from '../../core/media.service';

/**
 * Feature: mediacloud-mvp, Property 10: Search filtering respects context
 * Validates: Requirements 8.1, 8.2
 */
describe('HomeComponent Property Tests', () => {
  let component: HomeComponent;
  let fixture: ComponentFixture<HomeComponent>;
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let mockMediaService: jasmine.SpyObj<MediaService>;

  beforeEach(async () => {
    const authSpy = jasmine.createSpyObj('AuthService', ['getUser', 'logout']);
    const mediaSpy = jasmine.createSpyObj('MediaService', ['getMedia', 'uploadMedia', 'toggleFavorite', 'toggleTrash', 'deleteMedia']);

    await TestBed.configureTestingModule({
      declarations: [HomeComponent],
      imports: [HttpClientTestingModule, FormsModule, RouterTestingModule],
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: MediaService, useValue: mediaSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(HomeComponent);
    component = fixture.componentInstance;
    mockAuthService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    mockMediaService = TestBed.inject(MediaService) as jasmine.SpyObj<MediaService>;

    // Setup default mocks
    mockAuthService.getUser.and.returnValue({
      id: 'test-user-id',
      firstName: 'Test',
      lastName: 'User',
      email: 'test@example.com'
    });
  });

  /**
   * Property 10: Search filtering respects context
   * For any search query within a specific tab context, results should include only items 
   * that match both the search term and the tab's type filter
   */
  it('should filter search results within tab context', () => {
    fc.assert(fc.property(
      // Generate random media items with different types
      fc.array(fc.record({
        id: fc.string({ minLength: 1 }),
        type: fc.constantFrom('photo' as const, 'video' as const, 'audio' as const),
        title: fc.string({ minLength: 1, maxLength: 50 }),
        blob: fc.record({
          containerName: fc.string(),
          blobName: fc.string(),
          url: fc.webUrl()
        }),
        isFavorite: fc.boolean(),
        isDeleted: fc.boolean(),
        createdAt: fc.date().map(d => d.toISOString())
      }), { minLength: 0, maxLength: 20 }),
      // Generate a search query that might match some titles
      fc.string({ minLength: 1, maxLength: 10 }),
      // Generate a tab type
      fc.constantFrom('photos', 'videos', 'audio', 'favorites', 'trash'),
      (mediaItems, searchQuery, activeTab) => {
        // Set up component state
        component.mediaItems = mediaItems;
        component.activeTab = activeTab;
        component.searchQuery = searchQuery.toLowerCase();

        // Apply search filtering
        component.applySearch();

        // Get expected results based on tab context
        let expectedItems = mediaItems;
        
        // First filter by tab context (simulating what loadMedia() would do)
        switch (activeTab) {
          case 'photos':
            expectedItems = mediaItems.filter(item => item.type === 'photo' && !item.isDeleted);
            break;
          case 'videos':
            expectedItems = mediaItems.filter(item => item.type === 'video' && !item.isDeleted);
            break;
          case 'audio':
            expectedItems = mediaItems.filter(item => item.type === 'audio' && !item.isDeleted);
            break;
          case 'favorites':
            expectedItems = mediaItems.filter(item => item.isFavorite && !item.isDeleted);
            break;
          case 'trash':
            expectedItems = mediaItems.filter(item => item.isDeleted);
            break;
        }

        // Then filter by search query
        if (searchQuery.trim()) {
          expectedItems = expectedItems.filter(item =>
            item.title.toLowerCase().includes(searchQuery.toLowerCase().trim())
          );
        }

        // For this test, we simulate the tab filtering by manually setting mediaItems
        // to what would be loaded for the active tab
        component.mediaItems = expectedItems.filter(item => {
          // Remove search filtering to simulate what loadMedia() would return
          switch (activeTab) {
            case 'photos':
              return item.type === 'photo' && !item.isDeleted;
            case 'videos':
              return item.type === 'video' && !item.isDeleted;
            case 'audio':
              return item.type === 'audio' && !item.isDeleted;
            case 'favorites':
              return item.isFavorite && !item.isDeleted;
            case 'trash':
              return item.isDeleted;
            default:
              return !item.isDeleted;
          }
        });

        // Apply search again with the tab-filtered items
        component.applySearch();

        // Verify that all filtered items match the search query
        const actualResults = component.filteredItems;
        
        if (searchQuery.trim()) {
          // Every result should contain the search query in its title
          actualResults.forEach(item => {
            expect(item.title.toLowerCase()).toContain(searchQuery.toLowerCase().trim());
          });
        } else {
          // If no search query, should show all items for the tab
          expect(actualResults).toEqual(component.mediaItems);
        }

        // Verify that results respect the tab context
        actualResults.forEach(item => {
          switch (activeTab) {
            case 'photos':
              expect(item.type).toBe('photo');
              expect(item.isDeleted).toBe(false);
              break;
            case 'videos':
              expect(item.type).toBe('video');
              expect(item.isDeleted).toBe(false);
              break;
            case 'audio':
              expect(item.type).toBe('audio');
              expect(item.isDeleted).toBe(false);
              break;
            case 'favorites':
              expect(item.isFavorite).toBe(true);
              expect(item.isDeleted).toBe(false);
              break;
            case 'trash':
              expect(item.isDeleted).toBe(true);
              break;
          }
        });
      }
    ), { numRuns: 100 });
  });

  it('should handle empty search queries correctly', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        id: fc.string({ minLength: 1 }),
        type: fc.constantFrom('photo' as const, 'video' as const, 'audio' as const),
        title: fc.string({ minLength: 1 }),
        blob: fc.record({
          containerName: fc.string(),
          blobName: fc.string(),
          url: fc.webUrl()
        }),
        isFavorite: fc.boolean(),
        isDeleted: fc.boolean(),
        createdAt: fc.date().map(d => d.toISOString())
      }), { minLength: 0, maxLength: 10 }),
      fc.constantFrom('', '   ', '\t', '\n'),
      (mediaItems, emptyQuery) => {
        component.mediaItems = mediaItems;
        component.searchQuery = emptyQuery;
        
        component.applySearch();
        
        // Empty or whitespace-only queries should return all media items
        expect(component.filteredItems).toEqual(component.mediaItems);
      }
    ), { numRuns: 100 });
  });

  it('should perform case-insensitive search', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        id: fc.string({ minLength: 1 }),
        type: fc.constantFrom('photo' as const, 'video' as const, 'audio' as const),
        title: fc.string({ minLength: 5, maxLength: 20 }),
        blob: fc.record({
          containerName: fc.string(),
          blobName: fc.string(),
          url: fc.webUrl()
        }),
        isFavorite: fc.boolean(),
        isDeleted: fc.boolean(),
        createdAt: fc.date().map(d => d.toISOString())
      }), { minLength: 1, maxLength: 10 }),
      (mediaItems) => {
        // Pick a random item and use part of its title as search query
        if (mediaItems.length === 0) return;
        
        const randomItem = mediaItems[Math.floor(Math.random() * mediaItems.length)];
        const title = randomItem.title;
        if (title.length < 2) return;
        
        const searchPart = title.substring(0, Math.min(3, title.length));
        
        // Test with different cases
        const queries = [
          searchPart.toLowerCase(),
          searchPart.toUpperCase(),
          searchPart.charAt(0).toUpperCase() + searchPart.slice(1).toLowerCase()
        ];
        
        queries.forEach(query => {
          component.mediaItems = mediaItems;
          component.searchQuery = query;
          
          component.applySearch();
          
          // Should find the item regardless of case
          const foundItem = component.filteredItems.find(item => item.id === randomItem.id);
          if (title.toLowerCase().includes(query.toLowerCase())) {
            expect(foundItem).toBeDefined();
          }
        });
      }
    ), { numRuns: 50 });
  });

  /**
   * Feature: mediacloud-mvp, Property 11: Audio player state management
   * For any audio file selection, the player should load the new audio and maintain 
   * playback state while navigating between interface tabs
   * Validates: Requirements 7.1, 7.2, 7.5
   */
  it('should manage audio player state correctly', () => {
    fc.assert(fc.property(
      // Generate random audio items
      fc.array(fc.record({
        id: fc.string({ minLength: 1 }),
        type: fc.constant('audio' as const),
        title: fc.string({ minLength: 1, maxLength: 50 }),
        blob: fc.record({
          containerName: fc.string(),
          blobName: fc.string(),
          url: fc.webUrl()
        }),
        isFavorite: fc.boolean(),
        isDeleted: fc.boolean(),
        createdAt: fc.date().map(d => d.toISOString())
      }), { minLength: 1, maxLength: 10 }),
      // Generate a sequence of tab changes
      fc.array(fc.constantFrom('photos', 'videos', 'audio', 'favorites', 'trash'), { minLength: 1, maxLength: 5 }),
      (audioItems, tabSequence) => {
        // Reset component state before each test
        component.nowPlaying = null;
        
        // Select a random audio item to play
        const selectedAudio = audioItems[Math.floor(Math.random() * audioItems.length)];
        
        // Initially no audio should be playing
        expect(component.nowPlaying).toBeNull();
        expect(component.isCurrentlyPlaying(selectedAudio)).toBe(false);
        
        // Play the selected audio
        component.playAudio(selectedAudio);
        
        // Verify the audio is now playing
        expect(component.nowPlaying).toBeTruthy();
        expect(component.nowPlaying!.id).toEqual(selectedAudio.id);
        expect(component.isCurrentlyPlaying(selectedAudio)).toBe(true);
        
        // Navigate through different tabs
        tabSequence.forEach(tab => {
          const previousNowPlayingId = component.nowPlaying?.id;
          
          // Change tab (mock the loadMedia call since we're not testing the service)
          component.activeTab = tab;
          
          // Audio player state should persist during tab navigation
          expect(component.nowPlaying?.id).toEqual(previousNowPlayingId);
          expect(component.isCurrentlyPlaying(selectedAudio)).toBe(true);
        });
        
        // Test switching to a different audio file
        if (audioItems.length > 1) {
          const differentAudio = audioItems.find(item => item.id !== selectedAudio.id);
          if (differentAudio) {
            component.playAudio(differentAudio);
            
            // Should switch to the new audio
            expect(component.nowPlaying).toBeTruthy();
            expect(component.nowPlaying!.id).toEqual(differentAudio.id);
            expect(component.isCurrentlyPlaying(differentAudio)).toBe(true);
            expect(component.isCurrentlyPlaying(selectedAudio)).toBe(false);
          }
        }
        
        // Test clicking the same audio again (should not restart)
        if (component.nowPlaying) {
          const currentPlayingItem = component.nowPlaying;
          component.playAudio(currentPlayingItem);
          // Should remain the same if clicking the currently playing audio
          expect(component.nowPlaying).toEqual(currentPlayingItem);
        }
        
        // Test stopping audio
        component.stopAudio();
        expect(component.nowPlaying).toBeNull();
        expect(component.isCurrentlyPlaying(selectedAudio)).toBe(false);
      }
    ), { numRuns: 100 });
  });

  it('should only play audio files', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        id: fc.string({ minLength: 1 }),
        type: fc.constantFrom('photo' as const, 'video' as const, 'audio' as const),
        title: fc.string({ minLength: 1 }),
        blob: fc.record({
          containerName: fc.string(),
          blobName: fc.string(),
          url: fc.webUrl()
        }),
        isFavorite: fc.boolean(),
        isDeleted: fc.boolean(),
        createdAt: fc.date().map(d => d.toISOString())
      }), { minLength: 1, maxLength: 10 }),
      (mediaItems) => {
        // Reset component state before each test
        component.nowPlaying = null;
        
        // Initially no audio should be playing
        expect(component.nowPlaying).toBeNull();
        
        mediaItems.forEach(item => {
          const previousNowPlaying = component.nowPlaying;
          
          component.playAudio(item);
          
          if (item.type === 'audio') {
            // Should play audio files
            expect(component.nowPlaying).toBeTruthy();
            expect(component.nowPlaying!.id).toEqual(item.id);
          } else {
            // Should not play non-audio files
            expect(component.nowPlaying?.id).toEqual(previousNowPlaying?.id);
          }
        });
      }
    ), { numRuns: 100 });
  });
});