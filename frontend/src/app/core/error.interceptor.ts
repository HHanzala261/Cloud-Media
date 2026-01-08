import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  intercept(req: HttpRequest<any>, next: HttpHandler) {
    return next.handle(req).pipe(
      catchError((error: HttpErrorResponse) => {
        console.log('ErrorInterceptor: HTTP error caught:', error);
        
        // Handle authentication errors
        if (error.status === 401) {
          console.log('ErrorInterceptor: 401 Unauthorized - checking if logout needed');
          
          // Only logout if we're not already logging out
          if (this.authService.isAuthenticated()) {
            console.log('ErrorInterceptor: Calling logout due to 401 error');
            this.authService.logout();
          } else {
            console.log('ErrorInterceptor: User already logged out, just redirecting');
            this.router.navigate(['/login']);
          }
        }
        
        // Re-throw the error so components can still handle it
        return throwError(() => error);
      })
    );
  }
}