import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);

    // Mock localStorage
    const mockUser = { token: 'test-token' };
    spyOn(localStorage, 'getItem').and.returnValue(JSON.stringify(mockUser));
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('calculateOffer', () => {
    it('should POST offer data and return result', () => {
      const mockOfferData = {
        company_id: 1,
        employees_count: 100,
        region: 'Mazowieckie',
        premium_48h: false,
        ml_feature_avg_order_value: 20000,
        ml_feature_offers_count: 3
      };

      const mockResponse = {
        id: 1,
        base_price: 10000,
        final_price: 9500,
        ai_score: 75.5,
        priority_level: 'VIP'
      };

      service.calculateOffer(mockOfferData).subscribe(result => {
        expect(result).toEqual(mockResponse);
        expect(result.ai_score).toBeGreaterThan(0);
        expect(result.priority_level).toBeTruthy();
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/offers/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(mockOfferData);
      expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
      req.flush(mockResponse);
    });
  });

  describe('getCompanies', () => {
    it('should GET list of companies', () => {
      const mockCompanies = [
        { id: 1, name: 'Company A', industry_id: 1 },
        { id: 2, name: 'Company B', industry_id: 2 }
      ];

      service.getCompanies().subscribe(companies => {
        expect(companies.length).toBe(2);
        expect(companies[0].name).toBe('Company A');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/companies/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockCompanies);
    });
  });

  describe('getOffers', () => {
    it('should GET list of offers', () => {
      const mockOffers = [
        { id: 1, final_price: 9500, ai_score: 75 },
        { id: 2, final_price: 8000, ai_score: 60 }
      ];

      service.getOffers().subscribe(offers => {
        expect(offers.length).toBe(2);
        expect(offers[0].ai_score).toBe(75);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/offers/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockOffers);
    });
  });

  describe('getDashboardStats', () => {
    it('should GET dashboard statistics', () => {
      const mockStats = {
        companies_count: 10,
        offers_count: 50,
        avg_offer_value: 12500,
        top_5_companies: ['Company A (95)', 'Company B (88)'],
        industry_distribution: { IT: 5, Production: 3 },
        avg_score_per_region: { Mazowieckie: 72.5, Śląskie: 68.3 }
      };

      service.getDashboardStats().subscribe(stats => {
        expect(stats.companies_count).toBe(10);
        expect(stats.offers_count).toBe(50);
        expect(stats.top_5_companies.length).toBeLessThanOrEqual(5);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/admin/dashboard`);
      expect(req.request.method).toBe('GET');
      req.flush(mockStats);
    });
  });

  describe('createCompany', () => {
    it('should POST new company data', () => {
      const newCompany = { name: 'New Company', industry_id: 1 };
      const mockResponse = { id: 3, ...newCompany, created_at: '2024-01-01T00:00:00Z' };

      service.createCompany(newCompany).subscribe(company => {
        expect(company.id).toBe(3);
        expect(company.name).toBe('New Company');
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/companies/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(newCompany);
      req.flush(mockResponse);
    });
  });

  describe('error handling', () => {
    it('should handle HTTP errors gracefully', () => {
      service.getCompanies().subscribe({
        next: () => fail('should have failed'),
        error: (error) => {
          expect(error.status).toBe(401);
        }
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/api/companies/`);
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });
    });
  });
});
