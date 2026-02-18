import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject, timer, of } from 'rxjs';
import {
  catchError,
  map,
  shareReplay,
  switchMap,
  retry,
  tap,
  debounceTime,
  distinctUntilChanged,
  finalize
} from 'rxjs/operators';
import { environment } from 'src/environments/environment';

// Interfaces for type safety
export interface Company {
  id: number;
  name: string;
  industry_id: number;
  created_at?: string;
}

export interface Offer {
  id: number;
  company_id: number;
  employees_count: number;
  region: string;
  premium_48h: boolean;
  base_price: number;
  final_price: number;
  ai_score: number;
  ml_score: number;
  rule_score: number;
  priority_level: 'LOW' | 'STANDARD' | 'VIP';
  created_at: string;
}

export interface OfferCreate {
  company_id: number;
  employees_count: number;
  region: string;
  premium_48h: boolean;
  ml_feature_avg_order_value: number;
  ml_feature_offers_count: number;
}

export interface DashboardStats {
  companies_count: number;
  offers_count: number;
  avg_offer_value: number;
  top_5_companies: string[];
  industry_distribution: Record<string, number>;
  avg_score_per_region: Record<string, number>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  // Cache for frequently accessed data
  private companiesCache$: Observable<Company[]> | null = null;
  private cacheExpiry = 5 * 60 * 1000; // 5 minutes cache
  private lastCacheTime = 0;

  // Loading state
  private loadingSubject = new BehaviorSubject<boolean>(false);
  public loading$ = this.loadingSubject.asObservable();

  constructor(private http: HttpClient) { }

  /**
   * Get authorization headers
   */
  private getHeaders(): HttpHeaders {
    const user = JSON.parse(localStorage.getItem('currentUser') || '{}');
    return new HttpHeaders({
      'Authorization': `Bearer ${user.token || ''}`,
      'Content-Type': 'application/json'
    });
  }

  /**
   * Handle HTTP errors with retry logic
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      switch (error.status) {
        case 400:
          errorMessage = 'Bad request. Please check your input.';
          break;
        case 401:
          errorMessage = 'Unauthorized. Please login again.';
          // Could trigger auto-logout here
          break;
        case 403:
          errorMessage = 'Forbidden. You do not have access.';
          break;
        case 404:
          errorMessage = 'Resource not found.';
          break;
        case 429:
          errorMessage = 'Too many requests. Please wait.';
          break;
        case 500:
          errorMessage = 'Server error. Please try again later.';
          break;
        default:
          errorMessage = `Error ${error.status}: ${error.message}`;
      }
    }

    console.error('API Error:', errorMessage, error);
    return throwError(() => ({ message: errorMessage, status: error.status }));
  }

  /**
   * Calculate offer with loading state management
   */
  calculateOffer(data: OfferCreate): Observable<Offer> {
    this.loadingSubject.next(true);

    return this.http.post<Offer>(
      `${this.apiUrl}/api/offers/`,
      data,
      { headers: this.getHeaders() }
    ).pipe(
      retry({
        count: 2,
        delay: (error, retryCount) => {
          if (error.status >= 400 && error.status < 500) {
            return throwError(() => error);
          }
          return timer(1000 * retryCount);
        }
      }),
      tap(() => {
        // Invalidate companies cache as offer creation might affect stats
        this.invalidateCache();
      }),
      catchError(this.handleError.bind(this)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Get dashboard stats with caching
   */
  getDashboardStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(
      `${this.apiUrl}/api/admin/dashboard`,
      { headers: this.getHeaders() }
    ).pipe(
      shareReplay({ bufferSize: 1, refCount: true }),
      catchError(this.handleError.bind(this))
    );
  }

  /**
   * Get companies with caching and auto-refresh
   */
  getCompanies(forceRefresh = false): Observable<Company[]> {
    const now = Date.now();

    // Return cached if valid and not forcing refresh
    if (!forceRefresh && this.companiesCache$ && (now - this.lastCacheTime) < this.cacheExpiry) {
      return this.companiesCache$;
    }

    this.companiesCache$ = this.http.get<Company[]>(
      `${this.apiUrl}/api/companies/`,
      { headers: this.getHeaders() }
    ).pipe(
      tap(() => this.lastCacheTime = Date.now()),
      shareReplay({ bufferSize: 1, refCount: true }),
      catchError(error => {
        this.companiesCache$ = null;
        return this.handleError(error);
      })
    );

    return this.companiesCache$;
  }

  /**
   * Invalidate cache
   */
  invalidateCache(): void {
    this.companiesCache$ = null;
    this.lastCacheTime = 0;
  }

  /**
   * Get offers with optional filtering
   */
  getOffers(filters?: { priority?: string; region?: string }): Observable<Offer[]> {
    let params = new HttpParams();

    if (filters?.priority) {
      params = params.set('priority', filters.priority);
    }
    if (filters?.region) {
      params = params.set('region', filters.region);
    }

    return this.http.get<Offer[]>(
      `${this.apiUrl}/api/offers/`,
      { headers: this.getHeaders(), params }
    ).pipe(
      catchError(this.handleError.bind(this))
    );
  }

  /**
   * Create company
   */
  createCompany(data: Partial<Company>): Observable<Company> {
    return this.http.post<Company>(
      `${this.apiUrl}/api/companies/`,
      data,
      { headers: this.getHeaders() }
    ).pipe(
      tap(() => this.invalidateCache()),
      catchError(this.handleError.bind(this))
    );
  }

  /**
   * Search companies with debouncing (useful for autocomplete)
   */
  searchCompanies(query$: Observable<string>): Observable<Company[]> {
    return query$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => {
        if (!query || query.length < 2) {
          return of([]);
        }
        return this.http.get<Company[]>(
          `${this.apiUrl}/api/companies/search`,
          {
            headers: this.getHeaders(),
            params: new HttpParams().set('q', query)
          }
        ).pipe(
          catchError(() => of([]))
        );
      })
    );
  }

  /**
   * Get single offer by ID
   */
  getOffer(id: number): Observable<Offer> {
    return this.http.get<Offer>(
      `${this.apiUrl}/api/offers/${id}`,
      { headers: this.getHeaders() }
    ).pipe(
      catchError(this.handleError.bind(this))
    );
  }

  /**
   * Batch calculate offers (for bulk operations)
   */
  batchCalculateOffers(offers: OfferCreate[]): Observable<Offer[]> {
    this.loadingSubject.next(true);

    return this.http.post<Offer[]>(
      `${this.apiUrl}/api/offers/batch`,
      { offers },
      { headers: this.getHeaders() }
    ).pipe(
      tap(() => this.invalidateCache()),
      catchError(this.handleError.bind(this)),
      finalize(() => this.loadingSubject.next(false))
    );
  }

  /**
   * Recalculate AI scores for all offers (admin only)
   */
  recalculateScores(): Observable<{ message: string; updated: number }> {
    this.loadingSubject.next(true);

    return this.http.post<{ message: string; updated: number }>(
      `${this.apiUrl}/api/admin/recalc_scores`,
      {},
      { headers: this.getHeaders() }
    ).pipe(
      tap(() => this.invalidateCache()),
      catchError(this.handleError.bind(this)),
      finalize(() => this.loadingSubject.next(false))
    );
  }
}
