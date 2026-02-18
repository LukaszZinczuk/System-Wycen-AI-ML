import { Component, OnInit, OnDestroy, ViewChild, AfterViewInit } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { FormControl } from '@angular/forms';
import { Subject } from 'rxjs';
import { takeUntil, debounceTime, distinctUntilChanged, catchError } from 'rxjs/operators';
import { ApiService, Offer } from '../../services/api.service';
import { trigger, transition, style, animate, stagger, query } from '@angular/animations';

@Component({
  selector: 'app-offers-list',
  templateUrl: './offers-list.component.html',
  styleUrls: ['./offers-list.component.scss'],
  animations: [
    trigger('tableAnimation', [
      transition('* => *', [
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(-10px)' }),
          stagger(50, [
            animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
          ])
        ], { optional: true })
      ])
    ]),
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 }))
      ])
    ])
  ]
})
export class OffersListComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  displayedColumns: string[] = ['id', 'company', 'employees', 'region', 'base_price', 'final_price', 'ai_score', 'priority', 'actions'];
  dataSource = new MatTableDataSource<Offer>([]);

  // Filters
  searchControl = new FormControl('');
  priorityFilter = new FormControl('all');
  regionFilter = new FormControl('all');

  // State
  loading = true;
  errorMessage: string | null = null;

  // Stats
  totalOffers = 0;
  avgAiScore = 0;
  vipCount = 0;

  regions = ['Mazowieckie', 'Śląskie', 'Małopolskie', 'Inne'];
  priorities = ['LOW', 'STANDARD', 'VIP'];

  private destroy$ = new Subject<void>();

  constructor(private api: ApiService) { }

  ngOnInit(): void {
    this.loadOffers();
    this.setupFilters();
  }

  ngAfterViewInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;

    this.dataSource.sortingDataAccessor = (item: Offer, property: string) => {
      switch (property) {
        case 'priority':
          const priorityOrder: { [key: string]: number } = { 'VIP': 3, 'STANDARD': 2, 'LOW': 1 };
          return priorityOrder[item.priority_level] || 0;
        default:
          return (item as any)[property];
      }
    };
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadOffers(): void {
    this.loading = true;
    this.errorMessage = null;

    this.api.getOffers().pipe(
      takeUntil(this.destroy$),
      catchError(err => {
        this.errorMessage = err.message || 'Unable to fetch offers';
        this.loading = false;
        return [];
      })
    ).subscribe(offers => {
      this.dataSource.data = offers;
      this.calculateStats(offers);
      this.loading = false;
    });
  }

  private setupFilters(): void {
    this.searchControl.valueChanges.pipe(
      takeUntil(this.destroy$),
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(value => {
      this.dataSource.filter = value?.trim().toLowerCase() || '';
    });

    this.dataSource.filterPredicate = (data: Offer, filter: string) => {
      const searchMatch = !filter ||
        data.region.toLowerCase().includes(filter) ||
        data.priority_level.toLowerCase().includes(filter) ||
        data.id.toString().includes(filter);

      const priorityMatch = this.priorityFilter.value === 'all' ||
        data.priority_level === this.priorityFilter.value;

      const regionMatch = this.regionFilter.value === 'all' ||
        data.region === this.regionFilter.value;

      return searchMatch && priorityMatch && regionMatch;
    };

    this.priorityFilter.valueChanges.pipe(takeUntil(this.destroy$))
      .subscribe(() => this.dataSource.filter = this.searchControl.value || ' ');

    this.regionFilter.valueChanges.pipe(takeUntil(this.destroy$))
      .subscribe(() => this.dataSource.filter = this.searchControl.value || ' ');
  }

  private calculateStats(offers: Offer[]): void {
    this.totalOffers = offers.length;
    this.avgAiScore = offers.length > 0
      ? Math.round(offers.reduce((sum, o) => sum + o.ai_score, 0) / offers.length)
      : 0;
    this.vipCount = offers.filter(o => o.priority_level === 'VIP').length;
  }

  onRetry(): void {
    this.loadOffers();
  }

  clearFilters(): void {
    this.searchControl.setValue('');
    this.priorityFilter.setValue('all');
    this.regionFilter.setValue('all');
  }

  exportToCSV(): void {
    const headers = ['ID', 'Company ID', 'Employees', 'Region', 'Base Price', 'Final Price', 'AI Score', 'Priority'];
    const rows = this.dataSource.filteredData.map(o => [
      o.id, o.company_id, o.employees_count, o.region, o.base_price, o.final_price, o.ai_score, o.priority_level
    ]);

    const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `offers_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  }

  getPriorityClass(priority: string): string {
    return `badge-${priority.toLowerCase()}`;
  }

  getScoreColor(score: number): string {
    if (score >= 70) return '#4caf50';
    if (score >= 40) return '#ff9800';
    return '#f44336';
  }
}
