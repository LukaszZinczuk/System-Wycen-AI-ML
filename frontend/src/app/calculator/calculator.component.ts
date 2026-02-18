import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService, Company, Offer, OfferCreate } from '../services/api.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, Observable, BehaviorSubject } from 'rxjs';
import {
  takeUntil,
  debounceTime,
  distinctUntilChanged,
  switchMap,
  tap,
  catchError,
  finalize,
  map
} from 'rxjs/operators';

@Component({
  selector: 'app-calculator',
  templateUrl: './calculator.component.html',
  styleUrls: ['./calculator.component.scss']
})
export class CalculatorComponent implements OnInit, OnDestroy {
  pricingForm!: FormGroup;
  result: Offer | null = null;
  regions = ['Mazowieckie', 'Śląskie', 'Małopolskie', 'Inne'];
  companies: Company[] = [];
  loading = false;

  // RxJS subjects for reactive patterns
  private destroy$ = new Subject<void>();
  private calculateSubject$ = new Subject<OfferCreate>();

  // Observable for loading state from API service
  loading$: Observable<boolean>;

  // Price preview (calculated locally before submission)
  estimatedPrice$ = new BehaviorSubject<number>(0);

  constructor(
    private fb: FormBuilder,
    private api: ApiService,
    private snackBar: MatSnackBar
  ) {
    this.loading$ = this.api.loading$;
  }

  ngOnInit(): void {
    this.initForm();
    this.loadCompanies();
    this.setupCalculateStream();
    this.setupPricePreview();
  }

  ngOnDestroy(): void {
    // Clean up all subscriptions
    this.destroy$.next();
    this.destroy$.complete();
  }

  private initForm(): void {
    this.pricingForm = this.fb.group({
      company_id: [null, Validators.required],
      employees_count: [100, [Validators.required, Validators.min(1), Validators.max(10000)]],
      region: ['Mazowieckie', Validators.required],
      premium_48h: [false],
      ml_feature_avg_order_value: [20000, [Validators.required, Validators.min(0)]],
      ml_feature_offers_count: [0, [Validators.required, Validators.min(0)]]
    });
  }

  private loadCompanies(): void {
    this.api.getCompanies()
      .pipe(
        takeUntil(this.destroy$),
        catchError(error => {
          this.snackBar.open('Error loading companies', 'Close', { duration: 3000 });
          return [];
        })
      )
      .subscribe(companies => {
        this.companies = companies;
      });
  }

  /**
   * Setup reactive stream for calculations
   * Uses switchMap to cancel previous requests when new one comes in
   */
  private setupCalculateStream(): void {
    this.calculateSubject$.pipe(
      takeUntil(this.destroy$),
      tap(() => this.loading = true),
      debounceTime(300), // Prevent rapid-fire submissions
      switchMap(offerData =>
        this.api.calculateOffer(offerData).pipe(
          catchError(error => {
            this.snackBar.open(
              error.message || 'Error calculating offer',
              'Close',
              { duration: 3000 }
            );
            return [];
          }),
          finalize(() => this.loading = false)
        )
      )
    ).subscribe({
      next: (result) => {
        if (result && !Array.isArray(result)) {
          this.result = result;
          this.showSuccessMessage(result);
        }
      }
    });
  }

  /**
   * Setup real-time price preview based on form changes
   * Uses distinctUntilChanged to prevent unnecessary recalculations
   */
  private setupPricePreview(): void {
    this.pricingForm.valueChanges.pipe(
      takeUntil(this.destroy$),
      debounceTime(200),
      distinctUntilChanged((prev, curr) =>
        prev.employees_count === curr.employees_count &&
        prev.region === curr.region &&
        prev.premium_48h === curr.premium_48h
      ),
      map(values => this.calculateLocalEstimate(values))
    ).subscribe(estimate => {
      this.estimatedPrice$.next(estimate);
    });
  }

  /**
   * Local price estimation (simplified version of backend logic)
   */
  private calculateLocalEstimate(values: any): number {
    const basePrice = values.employees_count * 100;

    // Quantity discount
    let discountRate = 0;
    if (values.employees_count > 200) discountRate = 0.15;
    else if (values.employees_count > 50) discountRate = 0.10;
    else if (values.employees_count > 10) discountRate = 0.05;

    let price = basePrice * (1 - discountRate);

    // Region multiplier
    const regionMultipliers: Record<string, number> = {
      'Mazowieckie': 1.2,
      'Śląskie': 1.1,
      'Małopolskie': 1.05,
      'Inne': 1.0
    };
    price *= regionMultipliers[values.region] || 1.0;

    // Premium
    if (values.premium_48h) {
      price *= 1.20;
    }

    return Math.round(price * 100) / 100;
  }

  /**
   * Show success message based on priority level
   */
  private showSuccessMessage(result: Offer): void {
    let message = 'Offer calculated & saved!';
    let panelClass = '';

    if (result.priority_level === 'VIP') {
      message = '🌟 VIP Offer created! 5% discount applied.';
      panelClass = 'snackbar-vip';
    } else if (result.priority_level === 'LOW') {
      message = 'Offer created with LOW priority.';
      panelClass = 'snackbar-warning';
    }

    this.snackBar.open(message, 'Close', {
      duration: 4000,
      panelClass: panelClass ? [panelClass] : undefined
    });
  }

  /**
   * Trigger calculation through the reactive stream
   */
  calculate(): void {
    if (this.pricingForm.invalid) {
      // Mark all fields as touched to show validation errors
      Object.keys(this.pricingForm.controls).forEach(key => {
        this.pricingForm.get(key)?.markAsTouched();
      });
      return;
    }

    this.calculateSubject$.next(this.pricingForm.value as OfferCreate);
  }

  /**
   * Get score class for styling
   */
  getScoreClass(score: number): string {
    if (score >= 70) return 'score-high';
    if (score >= 40) return 'score-medium';
    return 'score-low';
  }

  /**
   * Reset form to initial state
   */
  resetForm(): void {
    this.pricingForm.reset({
      company_id: null,
      employees_count: 100,
      region: 'Mazowieckie',
      premium_48h: false,
      ml_feature_avg_order_value: 20000,
      ml_feature_offers_count: 0
    });
    this.result = null;
  }

  /**
   * Get error message for form field
   */
  getErrorMessage(fieldName: string): string {
    const control = this.pricingForm.get(fieldName);

    if (control?.hasError('required')) {
      return 'This field is required';
    }
    if (control?.hasError('min')) {
      return `Minimum value is ${control.errors?.['min'].min}`;
    }
    if (control?.hasError('max')) {
      return `Maximum value is ${control.errors?.['max'].max}`;
    }

    return '';
  }

  /**
   * Track by function for ngFor optimization
   */
  trackByCompanyId(index: number, company: Company): number {
    return company.id;
  }
}
