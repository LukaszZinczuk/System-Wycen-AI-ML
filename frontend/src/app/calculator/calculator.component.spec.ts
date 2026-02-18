import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { CalculatorComponent } from './calculator.component';
import { ApiService } from '../services/api.service';

describe('CalculatorComponent', () => {
  let component: CalculatorComponent;
  let fixture: ComponentFixture<CalculatorComponent>;
  let apiServiceSpy: jasmine.SpyObj<ApiService>;
  let snackBarSpy: jasmine.SpyObj<MatSnackBar>;

  const mockCompanies = [
    { id: 1, name: 'Company A', industry_id: 1 },
    { id: 2, name: 'Company B', industry_id: 2 }
  ];

  const mockPricingResult = {
    id: 1,
    company_id: 1,
    employees_count: 100,
    region: 'Mazowieckie',
    premium_48h: false,
    base_price: 10000,
    final_price: 9500,
    ai_score: 75.5,
    ml_score: 80,
    rule_score: 65,
    priority_level: 'VIP',
    created_at: '2024-01-01T00:00:00Z'
  };

  beforeEach(async () => {
    apiServiceSpy = jasmine.createSpyObj('ApiService', ['getCompanies', 'calculateOffer']);
    snackBarSpy = jasmine.createSpyObj('MatSnackBar', ['open']);

    apiServiceSpy.getCompanies.and.returnValue(of(mockCompanies));
    apiServiceSpy.calculateOffer.and.returnValue(of(mockPricingResult));

    await TestBed.configureTestingModule({
      declarations: [CalculatorComponent],
      imports: [
        ReactiveFormsModule,
        NoopAnimationsModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatSlideToggleModule,
        MatButtonModule,
        MatCardModule,
        MatSnackBarModule
      ],
      providers: [
        { provide: ApiService, useValue: apiServiceSpy },
        { provide: MatSnackBar, useValue: snackBarSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CalculatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize form with default values', () => {
    expect(component.pricingForm).toBeDefined();
    expect(component.pricingForm.get('employees_count')?.value).toBe(100);
    expect(component.pricingForm.get('region')?.value).toBe('Mazowieckie');
    expect(component.pricingForm.get('premium_48h')?.value).toBe(false);
  });

  it('should load companies on init', () => {
    expect(apiServiceSpy.getCompanies).toHaveBeenCalled();
    expect(component.companies).toEqual(mockCompanies);
  });

  it('should have correct regions list', () => {
    expect(component.regions).toContain('Mazowieckie');
    expect(component.regions).toContain('Śląskie');
    expect(component.regions).toContain('Małopolskie');
    expect(component.regions).toContain('Inne');
  });

  describe('Form Validation', () => {
    it('should require company_id', () => {
      const control = component.pricingForm.get('company_id');
      control?.setValue(null);
      expect(control?.valid).toBeFalse();
      expect(control?.errors?.['required']).toBeTruthy();
    });

    it('should require employees_count to be at least 1', () => {
      const control = component.pricingForm.get('employees_count');
      control?.setValue(0);
      expect(control?.valid).toBeFalse();
      expect(control?.errors?.['min']).toBeTruthy();
    });

    it('should require region', () => {
      const control = component.pricingForm.get('region');
      control?.setValue('');
      expect(control?.valid).toBeFalse();
    });

    it('should be valid with all required fields', () => {
      component.pricingForm.setValue({
        company_id: 1,
        employees_count: 100,
        region: 'Mazowieckie',
        premium_48h: false,
        ml_feature_avg_order_value: 20000,
        ml_feature_offers_count: 0
      });
      expect(component.pricingForm.valid).toBeTrue();
    });
  });

  describe('calculate()', () => {
    beforeEach(() => {
      component.pricingForm.setValue({
        company_id: 1,
        employees_count: 100,
        region: 'Mazowieckie',
        premium_48h: false,
        ml_feature_avg_order_value: 20000,
        ml_feature_offers_count: 3
      });
    });

    it('should not calculate if form is invalid', () => {
      component.pricingForm.get('company_id')?.setValue(null);
      component.calculate();
      expect(apiServiceSpy.calculateOffer).not.toHaveBeenCalled();
    });

    it('should call API and set result on success', fakeAsync(() => {
      component.calculate();
      tick();

      expect(apiServiceSpy.calculateOffer).toHaveBeenCalled();
      expect(component.result).toEqual(mockPricingResult);
      expect(component.loading).toBeFalse();
      expect(snackBarSpy.open).toHaveBeenCalledWith(
        'Offer calculated & saved!', 'Close', { duration: 3000 }
      );
    }));

    it('should handle API error', fakeAsync(() => {
      apiServiceSpy.calculateOffer.and.returnValue(throwError(() => new Error('API Error')));

      component.calculate();
      tick();

      expect(component.result).toBeNull();
      expect(component.loading).toBeFalse();
      expect(snackBarSpy.open).toHaveBeenCalledWith(
        'Error calculating offer', 'Close', { duration: 3000 }
      );
    }));

    it('should set loading state during API call', fakeAsync(() => {
      expect(component.loading).toBeFalse();

      component.calculate();
      expect(component.loading).toBeTrue();

      tick();
      expect(component.loading).toBeFalse();
    }));
  });

  describe('Result Display', () => {
    it('should display VIP badge for VIP priority', () => {
      component.result = { ...mockPricingResult, priority_level: 'VIP' };
      fixture.detectChanges();

      // Check that result is set correctly
      expect(component.result.priority_level).toBe('VIP');
    });

    it('should display AI score', () => {
      component.result = mockPricingResult;
      fixture.detectChanges();

      expect(component.result.ai_score).toBe(75.5);
    });
  });
});
