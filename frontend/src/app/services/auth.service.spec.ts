import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        AuthService,
        { provide: Router, useValue: routerSpy }
      ]
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);

    // Clear localStorage before each test
    localStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('login', () => {
    it('should login successfully and store user data', () => {
      const mockResponse = {
        access_token: 'test-jwt-token',
        token_type: 'bearer'
      };

      service.login('test@example.com', 'password123').subscribe(response => {
        expect(response.access_token).toBe('test-jwt-token');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/auth/login`);
      expect(req.request.method).toBe('POST');
      req.flush(mockResponse);
    });

    it('should handle login failure', () => {
      service.login('wrong@example.com', 'wrongpassword').subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(401);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/auth/login`);
      req.flush('Invalid credentials', { status: 401, statusText: 'Unauthorized' });
    });
  });

  describe('logout', () => {
    it('should clear user data and navigate to login', () => {
      // Set up initial logged-in state
      localStorage.setItem('currentUser', JSON.stringify({ token: 'test-token' }));

      service.logout();

      expect(localStorage.getItem('currentUser')).toBeNull();
      expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
    });
  });

  describe('isLoggedIn', () => {
    it('should return true when user is logged in', () => {
      localStorage.setItem('currentUser', JSON.stringify({ token: 'test-token' }));
      expect(service.isLoggedIn()).toBeTrue();
    });

    it('should return false when user is not logged in', () => {
      localStorage.removeItem('currentUser');
      expect(service.isLoggedIn()).toBeFalse();
    });
  });

  describe('getToken', () => {
    it('should return token when user is logged in', () => {
      const mockUser = { token: 'test-jwt-token', email: 'test@example.com' };
      localStorage.setItem('currentUser', JSON.stringify(mockUser));

      expect(service.getToken()).toBe('test-jwt-token');
    });

    it('should return null when user is not logged in', () => {
      localStorage.removeItem('currentUser');
      expect(service.getToken()).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should return current user data', () => {
      const mockUser = { token: 'test-token', email: 'test@example.com', role: 'admin' };
      localStorage.setItem('currentUser', JSON.stringify(mockUser));

      const user = service.getCurrentUser();
      expect(user?.email).toBe('test@example.com');
      expect(user?.role).toBe('admin');
    });

    it('should return null when no user is logged in', () => {
      localStorage.removeItem('currentUser');
      expect(service.getCurrentUser()).toBeNull();
    });
  });

  describe('isAdmin', () => {
    it('should return true for admin users', () => {
      const mockUser = { token: 'test-token', role: 'admin' };
      localStorage.setItem('currentUser', JSON.stringify(mockUser));

      expect(service.isAdmin()).toBeTrue();
    });

    it('should return false for regular users', () => {
      const mockUser = { token: 'test-token', role: 'user' };
      localStorage.setItem('currentUser', JSON.stringify(mockUser));

      expect(service.isAdmin()).toBeFalse();
    });
  });
});
