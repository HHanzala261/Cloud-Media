import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Router } from '@angular/router';

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
}

export interface AuthResponse {
  accessToken: string;
  user: User;
}

export interface RegisterRequest {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly API_BASE = 'http://localhost:5001/api';
  private readonly TOKEN_KEY = 'token';
  private readonly USER_KEY = 'user';
  
  private currentUserSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
  public currentUser$ = this.currentUserSubject.asObservable();
  
  private isLoggingOut = false; // Flag to prevent race conditions

  constructor(private http: HttpClient, private router: Router) { }

  register(userData: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_BASE}/auth/register`, userData)
      .pipe(
        tap(response => this.handleAuthSuccess(response))
      );
  }

  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.API_BASE}/auth/login`, credentials)
      .pipe(
        tap(response => this.handleAuthSuccess(response))
      );
  }

  logout(): void {
    if (this.isLoggingOut) {
      console.log('AuthService: Logout already in progress, skipping');
      return;
    }
    
    this.isLoggingOut = true;
    console.log('AuthService: Logging out user');
    
    // Clear all authentication data
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.currentUserSubject.next(null);
    
    // Navigate to login page immediately
    this.router.navigate(['/login']).then(() => {
      this.isLoggingOut = false;
      console.log('AuthService: Logout complete, redirected to login');
    });
  }

  getCurrentUser(): Observable<{user: User}> {
    return this.http.get<{user: User}>(`${this.API_BASE}/auth/me`);
  }

  isAuthenticated(): boolean {
    if (this.isLoggingOut) {
      console.log('AuthService: Logout in progress, returning false');
      return false;
    }
    
    const token = this.getToken();
    if (!token) {
      console.log('AuthService: No token found');
      return false;
    }
    
    const isExpired = this.isTokenExpired(token);
    if (isExpired) {
      console.log('AuthService: Token is expired');
      // Clear expired token
      this.logout();
      return false;
    }
    
    console.log('AuthService: Token is valid');
    return true;
  }

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getUser(): User | null {
    return this.currentUserSubject.value;
  }

  private handleAuthSuccess(response: AuthResponse): void {
    localStorage.setItem(this.TOKEN_KEY, response.accessToken);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.currentUserSubject.next(response.user);
  }

  private getUserFromStorage(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (e) {
        console.error('Error parsing user from localStorage:', e);
        localStorage.removeItem(this.USER_KEY);
      }
    }
    return null;
  }

  private isTokenExpired(token: string): boolean {
    try {
      // JWT tokens have 3 parts separated by dots
      const parts = token.split('.');
      if (parts.length !== 3) {
        console.log('AuthService: Invalid token format - not 3 parts');
        return true;
      }
      
      // Decode the payload (second part)
      const payload = JSON.parse(atob(parts[1]));
      
      // Check if exp claim exists
      if (!payload.exp) {
        console.log('AuthService: Token missing exp claim');
        return true;
      }
      
      const currentTime = Math.floor(Date.now() / 1000);
      const isExpired = payload.exp < currentTime;
      
      if (isExpired) {
        console.log('AuthService: Token expired', {
          exp: payload.exp,
          current: currentTime,
          expiredBy: currentTime - payload.exp
        });
      }
      
      return isExpired;
    } catch (e) {
      console.error('AuthService: Error validating token:', e);
      return true;
    }
  }
}