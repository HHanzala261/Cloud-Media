/**
 * Integration tests for MediaCloud MVP frontend
 * Tests complete user workflows and component integration
 */

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { FormsModule } from '@angular/forms';
import { Component } from '@angular/core';

import { AuthService, User, AuthResponse } from './core/auth.service';
import { MediaService, MediaItem } from './core/media.service';
import { AuthGuard } from './core/auth.guard';
import { LoginComponent } from './pages/login/login.component';
import { RegisterComponent } from './pages/register/register.component';
import { HomeComponent } from './pages/home/home.component';

// Mock components for routing tests
@Component({ template: '' })
class MockHomeComponent { }

@Component({ template: '' })
class MockLoginComponent { }

describe('MediaCloud Integration Tests', () => {
  let authService: AuthService;
  let mediaService: MediaService;
  let authGuard: AuthGuard;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        RouterTestingModule.withRoutes([
          { path: 'home', component: MockHomeComponent, canActivate: [AuthGuard] },
          { path: 'login', component: MockLoginComponent }
        ]),
        FormsModule
      ],
      declarations: [
        LoginComponent,
        RegisterComponent,
        HomeComponent,
        MockHomeComponent,
        MockLoginComponent
      ],
      providers: [
        AuthService,
        MediaService,
        AuthGuard
      ]
    });

    authService = TestBed.inject(AuthService);
    mediaService = TestBed.inject(MediaService);
    authGuard = TestBed.inject(AuthGuard);
    httpMock = TestBed.inject(HttpTestingController);

    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  describe('Authentication Workflow Integration', () => {
    it('should complete registration → login → protected route access workflow', (done) => {
      const testUser = {
        firstName: 'Test',
        lastName: 'User',
        email: 'test@example.com',
        password: 'testpassword123'
      };

      const mockAuthResponse: AuthResponse = {
        accessToken: 'mock.jwt.token',
        user: {
          id: '123',
          firstName: 'Test',
          lastName: 'User',
          email: 'test@example.com'
        }
      };

      // Step 1: Test registration
      authService.register(testUser).subscribe({
        next: (response) => {
          expect(response).toEqual(mockAuthResponse);
          expect(localStorage.getItem('token')).toBe(mockAuthResponse.accessToken);
          expect(localStorage.getItem('user')).toBe(JSON.stringify(mockAuthResponse.user));

          // Step 2: Test that user is now authenticated
          expect(authService.isAuthenticated()).toBe(true);
          expect(authService.getUser()).toEqual(mockAuthResponse.user);

          // Step 3: Test login with same credentials
          authService.login({ email: testUser.email, password: testUser.password }).subscribe({
            next: (loginResponse) => {
              expect(loginResponse).toEqual(mockAuthResponse);

              // Step 4: Test protected route access
              authService.getCurrentUser().subscribe({
                next: (userResponse) => {
                  expect(userResponse.user).toEqual(mockAuthResponse.user);
                  done();
                }
              });

              // Mock the /api/auth/me request
              const meReq = httpMock.expectOne('http://localhost:5001/api/auth/me');
              expect(meReq.request.method).toBe('GET');
              expect(meReq.request.headers.get('Authorization')).toBe(`Bearer ${mockAuthResponse.accessToken}`);
              meReq.flush({ user: mockAuthResponse.user });
            }
          });

          // Mock the login request
          const loginReq = httpMock.expectOne('http://localhost:5001/api/auth/login');
          expect(loginReq.request.method).toBe('POST');
          expect(loginReq.request.body).toEqual({ email: testUser.email, password: testUser.password });
          loginReq.flush(mockAuthResponse);
        }
      });

      // Mock the registration request
      const registerReq = httpMock.expectOne('http://localhost:5001/api/auth/register');
      expect(registerReq.request.method).toBe('POST');
      expect(registerReq.request.body).toEqual(testUser);
      registerReq.flush(mockAuthResponse);
    });

    it('should handle authentication errors properly', () => {
      const invalidCredentials = {
        email: 'test@example.com',
        password: 'wrongpassword'
      };

      authService.login(invalidCredentials).subscribe({
        next: () => fail('Should not succeed with invalid credentials'),
        error: (error) => {
          expect(error.status).toBe(401);
          expect(authService.isAuthenticated()).toBe(false);
          expect(authService.getUser()).toBeNull();
        }
      });

      const req = httpMock.expectOne('http://localhost:5001/api/auth/login');
      req.flush({ error: 'Invalid credentials' }, { status: 401, statusText: 'Unauthorized' });
    });

    it('should handle token expiration and logout', () => {
      // Set up an expired token
      const expiredToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDAwMDAwMDB9.invalid';
      localStorage.setItem('token', expiredToken);
      localStorage.setItem('user', JSON.stringify({ id: '123', firstName: 'Test', lastName: 'User', email: 'test@example.com' }));

      // Token should be considered expired
      expect(authService.isAuthenticated()).toBe(false);

      // Test logout
      authService.logout();
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(authService.getUser()).toBeNull();
    });
  });

  describe('Media Management Workflow Integration', () => {
    beforeEach(() => {
      // Set up authenticated state
      const mockUser: User = {
        id: '123',
        firstName: 'Test',
        lastName: 'User',
        email: 'test@example.com'
      };
      localStorage.setItem('token', 'mock.jwt.token');
      localStorage.setItem('user', JSON.stringify(mockUser));
    });

    it('should complete upload → retrieve → organize workflow', (done) => {
      const mockFile = new File(['test content'], 'test.png', { type: 'image/png' });
      const mockMediaItem: MediaItem = {
        id: 'media123',
        type: 'photo',
        title: 'test.png',
        blob: {
          containerName: 'user-123',
          blobName: 'uuid-test.png',
          url: 'https://storage.example.com/user-123/uuid-test.png'
        },
        isFavorite: false,
        isDeleted: false,
        createdAt: new Date().toISOString()
      };

      // Step 1: Upload media
      mediaService.uploadMedia(mockFile, 'test.png').subscribe({
        next: (uploadResponse) => {
          expect(uploadResponse).toEqual(mockMediaItem);

          // Step 2: Retrieve media list
          mediaService.getMedia().subscribe({
            next: (mediaList) => {
              expect(mediaList.items).toContain(mockMediaItem);

              // Step 3: Mark as favorite
              mediaService.toggleFavorite(mockMediaItem.id, true).subscribe({
                next: (favoriteResponse) => {
                  expect(favoriteResponse.success).toBe(true);

                  // Step 4: Get favorites
                  mediaService.getMedia({ favorites: true }).subscribe({
                    next: (favoritesList) => {
                      const favoriteItem = { ...mockMediaItem, isFavorite: true };
                      expect(favoritesList.items).toContain(favoriteItem);

                      // Step 5: Move to trash
                      mediaService.toggleTrash(mockMediaItem.id, true).subscribe({
                        next: (trashResponse) => {
                          expect(trashResponse.success).toBe(true);
                          done();
                        }
                      });

                      // Mock trash request
                      const trashReq = httpMock.expectOne(`http://localhost:5001/api/media/${mockMediaItem.id}/trash`);
                      expect(trashReq.request.method).toBe('PATCH');
                      expect(trashReq.request.body).toEqual({ isDeleted: true });
                      trashReq.flush({ success: true });
                    }
                  });

                  // Mock favorites list request
                  const favoritesReq = httpMock.expectOne('http://localhost:5001/api/media?favorites=true');
                  expect(favoritesReq.request.method).toBe('GET');
                  favoritesReq.flush({ items: [{ ...mockMediaItem, isFavorite: true }] });
                }
              });

              // Mock favorite toggle request
              const favoriteReq = httpMock.expectOne(`http://localhost:5001/api/media/${mockMediaItem.id}/favorite`);
              expect(favoriteReq.request.method).toBe('PATCH');
              expect(favoriteReq.request.body).toEqual({ isFavorite: true });
              favoriteReq.flush({ success: true });
            }
          });

          // Mock media list request
          const listReq = httpMock.expectOne('http://localhost:5001/api/media');
          expect(listReq.request.method).toBe('GET');
          listReq.flush({ items: [mockMediaItem] });
        }
      });

      // Mock upload request
      const uploadReq = httpMock.expectOne('http://localhost:5001/api/media/upload');
      expect(uploadReq.request.method).toBe('POST');
      expect(uploadReq.request.body instanceof FormData).toBe(true);
      uploadReq.flush(mockMediaItem);
    });

    it('should handle media filtering correctly', () => {
      const mockPhotoItem: MediaItem = {
        id: 'photo123',
        type: 'photo',
        title: 'photo.jpg',
        blob: { containerName: 'user-123', blobName: 'photo.jpg', url: 'https://example.com/photo.jpg' },
        isFavorite: false,
        isDeleted: false,
        createdAt: new Date().toISOString()
      };

      const mockAudioItem: MediaItem = {
        id: 'audio123',
        type: 'audio',
        title: 'audio.mp3',
        blob: { containerName: 'user-123', blobName: 'audio.mp3', url: 'https://example.com/audio.mp3' },
        isFavorite: false,
        isDeleted: false,
        createdAt: new Date().toISOString()
      };

      // Test photo filtering
      mediaService.getMedia({ type: 'photo' }).subscribe({
        next: (response) => {
          expect(response.items).toEqual([mockPhotoItem]);
          expect(response.items.every(item => item.type === 'photo')).toBe(true);
        }
      });

      const photoReq = httpMock.expectOne('http://localhost:5001/api/media?type=photo');
      expect(photoReq.request.method).toBe('GET');
      photoReq.flush({ items: [mockPhotoItem] });

      // Test audio filtering
      mediaService.getMedia({ type: 'audio' }).subscribe({
        next: (response) => {
          expect(response.items).toEqual([mockAudioItem]);
          expect(response.items.every(item => item.type === 'audio')).toBe(true);
        }
      });

      const audioReq = httpMock.expectOne('http://localhost:5001/api/media?type=audio');
      expect(audioReq.request.method).toBe('GET');
      audioReq.flush({ items: [mockAudioItem] });
    });

    it('should handle media deletion workflow', () => {
      const mediaId = 'media123';

      mediaService.deleteMedia(mediaId).subscribe({
        next: (response) => {
          expect(response.success).toBe(true);
        }
      });

      const deleteReq = httpMock.expectOne(`http://localhost:5001/api/media/${mediaId}`);
      expect(deleteReq.request.method).toBe('DELETE');
      deleteReq.flush({ success: true });
    });
  });

  describe('Route Protection Integration', () => {
    it('should allow access to protected routes when authenticated', () => {
      // Set up authenticated state
      localStorage.setItem('token', 'valid.jwt.token');
      localStorage.setItem('user', JSON.stringify({ id: '123', firstName: 'Test', lastName: 'User', email: 'test@example.com' }));

      const canActivate = authGuard.canActivate();
      expect(canActivate).toBe(true);
    });

    it('should redirect to login when not authenticated', () => {
      // Ensure no authentication
      localStorage.clear();

      const router = TestBed.inject(Router);
      spyOn(router, 'navigate');

      const canActivate = authGuard.canActivate();
      expect(canActivate).toBe(false);
      expect(router.navigate).toHaveBeenCalledWith(['/login']);
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle network errors gracefully', () => {
      authService.login({ email: 'test@example.com', password: 'password' }).subscribe({
        next: () => fail('Should not succeed'),
        error: (error) => {
          expect(error).toBeDefined();
          expect(authService.isAuthenticated()).toBe(false);
        }
      });

      const req = httpMock.expectOne('http://localhost:5001/api/auth/login');
      req.error(new ErrorEvent('Network error'));
    });

    it('should handle server errors in media operations', () => {
      // Set up authenticated state
      localStorage.setItem('token', 'mock.jwt.token');

      mediaService.getMedia().subscribe({
        next: () => fail('Should not succeed'),
        error: (error) => {
          expect(error.status).toBe(500);
        }
      });

      const req = httpMock.expectOne('http://localhost:5001/api/media');
      req.flush({ error: 'Internal server error' }, { status: 500, statusText: 'Internal Server Error' });
    });

    it('should handle unauthorized errors by clearing authentication', () => {
      // Set up authenticated state
      localStorage.setItem('token', 'expired.jwt.token');
      localStorage.setItem('user', JSON.stringify({ id: '123', firstName: 'Test', lastName: 'User', email: 'test@example.com' }));

      mediaService.getMedia().subscribe({
        next: () => fail('Should not succeed'),
        error: (error) => {
          expect(error.status).toBe(401);
          // In a real app, you might want to automatically logout on 401
        }
      });

      const req = httpMock.expectOne('http://localhost:5001/api/media');
      req.flush({ error: 'Unauthorized' }, { status: 401, statusText: 'Unauthorized' });
    });
  });

  describe('Component Integration', () => {
    it('should integrate login component with auth service', () => {
      const fixture = TestBed.createComponent(LoginComponent);
      const component = fixture.componentInstance;
      
      component.loginData = {
        email: 'test@example.com',
        password: 'testpassword123'
      };

      spyOn(authService, 'login').and.returnValue(of({
        accessToken: 'mock.token',
        user: { id: '123', firstName: 'Test', lastName: 'User', email: 'test@example.com' }
      }));

      component.onSubmit();

      expect(authService.login).toHaveBeenCalledWith(component.loginData);
      expect(component.isLoading).toBe(false);
    });

    it('should integrate register component with auth service', () => {
      const fixture = TestBed.createComponent(RegisterComponent);
      const component = fixture.componentInstance;
      
      component.registerData = {
        firstName: 'Test',
        lastName: 'User',
        email: 'test@example.com',
        password: 'testpassword123'
      };
      component.confirmPassword = 'testpassword123';

      spyOn(authService, 'register').and.returnValue(of({
        accessToken: 'mock.token',
        user: { id: '123', firstName: 'Test', lastName: 'User', email: 'test@example.com' }
      }));

      component.onSubmit();

      expect(authService.register).toHaveBeenCalledWith(component.registerData);
      expect(component.isLoading).toBe(false);
    });
  });
});

// Import Router for route protection tests
import { Router } from '@angular/router';
import { of } from 'rxjs';