import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { BehaviorSubject, Observable, throwError, timer, of } from 'rxjs';
import {
  tap,
  catchError,
  map,
  shareReplay,
  switchMap,
  retry,
  finalize
} from 'rxjs/operators';
import { environment } from 'src/environments/environment';

export interface User {
  token: string;
  email?: string;
  role: string;
  expiresAt?: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/api/auth`;
  private currentUserSubject: BehaviorSubject<User | null>;
  public currentUser$: Observable<User | null>;

  // Cache for role checking - prevents multiple localStorage reads
  private roleCache$ = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient, private router: Router) {
    const storedUser = this.getStoredUser();
    this.currentUserSubject = new BehaviorSubject<User | null>(storedUser);
    this.currentUser$ = this.currentUserSubject.asObservable().pipe(
      shareReplay(1) // Share subscription and replay last value
    );

    if (storedUser) {
      this.roleCache$.next(storedUser.role);
    }
  }

  /**
   * Get stored user from localStorage with error handling
   */
  private getStoredUser(): User | null {
    try {
      const stored = localStorage.getItem('currentUser');
      if (!stored) return null;

      const user = JSON.parse(stored) as User;

      // Check if token is expired (if we have expiry info)
      if (user.expiresAt && Date.now() > user.expiresAt) {
        this.clearStorage();
        return null;
      }

      return user;
    } catch (e) {
      this.clearStorage();
      return null;
    }
  }

  private clearStorage(): void {
    localStorage.removeItem('currentUser');
  }

  public get currentUserValue(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Login with retry logic and error handling
   */
  login(username: string, password: string): Observable<LoginResponse> {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    return this.http.post<LoginResponse>(`${this.apiUrl}/token`, formData).pipe(
      // Retry once on network errors (not on 4xx errors)
      retry({
        count: 1,
        delay: (error, retryCount) => {
          if (error.status >= 400 && error.status < 500) {
            return throwError(() => error); // Don't retry client errors
          }
          return timer(1000 * retryCount); // Exponential backoff
        }
      }),
      tap(res => {
        if (res && res.access_token) {
          // Parse JWT to extract role and expiry (simplified)
          const payload = this.parseJwt(res.access_token);
          const user: User = {
            token: res.access_token,
            email: payload?.sub,
            role: payload?.role || 'user',
            expiresAt: payload?.exp ? payload.exp * 1000 : undefined
          };

          localStorage.setItem('currentUser', JSON.stringify(user));
          this.currentUserSubject.next(user);
          this.roleCache$.next(user.role);
        }
      }),
      catchError(this.handleError.bind(this))
    );
  }

  /**
   * Parse JWT token payload
   */
  private parseJwt(token: string): any {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(window.atob(base64));
    } catch (e) {
      return null;
    }
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      switch (error.status) {
        case 401:
          errorMessage = 'Invalid credentials';
          break;
        case 403:
          errorMessage = 'Access forbidden';
          break;
        case 429:
          errorMessage = 'Too many requests. Please try again later.';
          break;
        case 500:
          errorMessage = 'Server error. Please try again later.';
          break;
        default:
          errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      }
    }

    console.error('Auth error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  logout(): void {
    this.clearStorage();
    this.currentUserSubject.next(null);
    this.roleCache$.next(null);
    this.router.navigate(['/login']);
  }

  /**
   * Check if user is logged in
   */
  isLoggedIn(): boolean {
    const user = this.currentUserValue;
    if (!user || !user.token) return false;

    // Check expiry
    if (user.expiresAt && Date.now() > user.expiresAt) {
      this.logout();
      return false;
    }

    return true;
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.currentUserValue?.token || null;
  }

  /**
   * Get current user (alias for compatibility)
   */
  getCurrentUser(): User | null {
    return this.currentUserValue;
  }

  /**
   * Check if user is admin - uses cached value
   */
  isAdmin(): boolean {
    return this.roleCache$.value === 'admin';
  }

  /**
   * Observable stream of admin status - useful for async pipe
   */
  isAdmin$(): Observable<boolean> {
    return this.roleCache$.pipe(
      map(role => role === 'admin')
    );
  }

  /**
   * Refresh token if needed (placeholder for future implementation)
   */
  refreshToken(): Observable<LoginResponse> {
    // In a real implementation, this would call a refresh endpoint
    return throwError(() => new Error('Token refresh not implemented'));
  }
}
