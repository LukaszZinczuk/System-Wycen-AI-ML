import { Component, OnInit, OnDestroy } from '@angular/core';
import { ApiService } from '../services/api.service';
import { Chart, registerables } from 'chart.js';
import { Subject } from 'rxjs';
import { takeUntil, catchError } from 'rxjs/operators';
import { trigger, transition, style, animate, stagger, query } from '@angular/animations';

Chart.register(...registerables);

interface DashboardStats {
  companies_count: number;
  offers_count: number;
  avg_offer_value: number;
  industry_distribution: { [key: string]: number };
  top_5_companies: string[];
  total_revenue?: number;
  vip_clients?: number;
}

@Component({
  selector: 'app-dashboard',
  template: `
    <div class="dashboard-container" @staggerAnimation>
      <!-- Welcome section -->
      <div class="welcome-section" @fadeIn>
        <h1>Welcome back! 👋</h1>
        <p>Here's what's happening with your pricing system today.</p>
      </div>

      <!-- Loading state -->
      <div class="loading-container" *ngIf="loading">
        <mat-spinner diameter="50"></mat-spinner>
        <p>Loading dashboard...</p>
      </div>

      <!-- Error state -->
      <mat-card class="error-card" *ngIf="errorMessage">
        <mat-icon>error_outline</mat-icon>
        <p>{{ errorMessage }}</p>
        <button mat-raised-button color="primary" (click)="loadStats()">Retry</button>
      </mat-card>

      <!-- Stats cards -->
      <div class="stats-grid" *ngIf="stats && !loading">
        <mat-card class="stat-card" @fadeIn>
          <div class="stat-icon blue">
            <mat-icon>business</mat-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.companies_count }}</span>
            <span class="stat-label">Companies</span>
          </div>
          <mat-icon class="stat-trend up">trending_up</mat-icon>
        </mat-card>

        <mat-card class="stat-card" @fadeIn>
          <div class="stat-icon green">
            <mat-icon>receipt_long</mat-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.offers_count }}</span>
            <span class="stat-label">Total Offers</span>
          </div>
          <mat-icon class="stat-trend up">trending_up</mat-icon>
        </mat-card>

        <mat-card class="stat-card" @fadeIn>
          <div class="stat-icon orange">
            <mat-icon>payments</mat-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.avg_offer_value | currency:'PLN':'symbol':'1.0-0' }}</span>
            <span class="stat-label">Avg Offer Value</span>
          </div>
        </mat-card>

        <mat-card class="stat-card" @fadeIn>
          <div class="stat-icon purple">
            <mat-icon>star</mat-icon>
          </div>
          <div class="stat-content">
            <span class="stat-value">{{ stats.vip_clients || 0 }}</span>
            <span class="stat-label">VIP Clients</span>
          </div>
        </mat-card>
      </div>

      <!-- Quick actions -->
      <mat-card class="quick-actions-card" *ngIf="!loading" @fadeIn>
        <mat-card-header>
          <mat-card-title>Quick Actions</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="actions-grid">
            <button mat-raised-button color="primary" routerLink="/calculator">
              <mat-icon>calculate</mat-icon>
              New Calculation
            </button>
            <button mat-stroked-button routerLink="/offers">
              <mat-icon>list_alt</mat-icon>
              View All Offers
            </button>
            <button mat-stroked-button routerLink="/companies">
              <mat-icon>business</mat-icon>
              Manage Companies
            </button>
            <button mat-stroked-button (click)="recalculateScores()" [disabled]="recalculating">
              <mat-icon>refresh</mat-icon>
              {{ recalculating ? 'Recalculating...' : 'Recalc AI Scores' }}
            </button>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Charts section -->
      <div class="charts-grid" *ngIf="stats && !loading">
        <mat-card class="chart-card" @fadeIn>
          <mat-card-header>
            <mat-card-title>Industries Distribution</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="chart-container">
              <canvas id="industryChart"></canvas>
            </div>
          </mat-card-content>
        </mat-card>

        <mat-card class="top-companies-card" @fadeIn>
          <mat-card-header>
            <mat-card-title>Top 5 Offers (AI Score)</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="top-list">
              <div class="top-item" *ngFor="let company of stats.top_5_companies; let i = index">
                <span class="rank" [ngClass]="'rank-' + (i + 1)">{{ i + 1 }}</span>
                <span class="name">{{ company }}</span>
                <mat-icon *ngIf="i < 3">emoji_events</mat-icon>
              </div>
              <div class="no-data" *ngIf="!stats.top_5_companies?.length">
                <mat-icon>info</mat-icon>
                <span>No offers yet</span>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      max-width: 1400px;
      margin: 0 auto;
    }

    .welcome-section {
      margin-bottom: 30px;

      h1 {
        margin: 0 0 8px 0;
        font-size: 2rem;
        font-weight: 500;
      }

      p {
        margin: 0;
        color: #666;
        font-size: 1.1rem;
      }
    }

    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px;
      
      p { margin-top: 16px; color: #666; }
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px;
      text-align: center;

      mat-icon { font-size: 64px; width: 64px; height: 64px; color: #f44336; }
      p { margin: 16px 0; color: #666; }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      display: flex;
      align-items: center;
      padding: 24px;
      border-radius: 16px !important;
      transition: transform 0.2s ease, box-shadow 0.2s ease;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.12);
      }
    }

    .stat-icon {
      width: 56px;
      height: 56px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 20px;

      mat-icon { font-size: 28px; width: 28px; height: 28px; color: white; }

      &.blue { background: linear-gradient(135deg, #2196f3, #1976d2); }
      &.green { background: linear-gradient(135deg, #4caf50, #388e3c); }
      &.orange { background: linear-gradient(135deg, #ff9800, #f57c00); }
      &.purple { background: linear-gradient(135deg, #9c27b0, #7b1fa2); }
    }

    .stat-content {
      flex: 1;
      display: flex;
      flex-direction: column;
    }

    .stat-value {
      font-size: 1.8rem;
      font-weight: 600;
      line-height: 1.2;
    }

    .stat-label {
      font-size: 0.9rem;
      color: #666;
      margin-top: 4px;
    }

    .stat-trend {
      &.up { color: #4caf50; }
      &.down { color: #f44336; }
    }

    .quick-actions-card {
      margin-bottom: 30px;
      border-radius: 16px !important;
    }

    .actions-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 16px;

      button {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .charts-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }

    .chart-card, .top-companies-card {
      border-radius: 16px !important;
    }

    .chart-container {
      height: 300px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .top-list {
      margin-top: 16px;
    }

    .top-item {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      border-radius: 8px;
      margin-bottom: 8px;
      background: #f5f5f5;
      transition: background 0.2s ease;

      &:hover { background: #eeeeee; }

      .rank {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
        margin-right: 12px;
        background: #e0e0e0;

        &.rank-1 { background: linear-gradient(135deg, #ffd700, #ffb300); color: white; }
        &.rank-2 { background: linear-gradient(135deg, #c0c0c0, #9e9e9e); color: white; }
        &.rank-3 { background: linear-gradient(135deg, #cd7f32, #a0522d); color: white; }
      }

      .name { flex: 1; font-weight: 500; }

      mat-icon { color: #ffc107; font-size: 20px; width: 20px; height: 20px; }
    }

    .no-data {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 40px;
      color: #999;

      mat-icon { font-size: 24px; width: 24px; height: 24px; }
    }

    @media (max-width: 768px) {
      .charts-grid {
        grid-template-columns: 1fr;
      }

      .welcome-section h1 { font-size: 1.5rem; }
      .stat-value { font-size: 1.5rem; }
    }
  `],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('staggerAnimation', [
      transition(':enter', [
        query(':enter', [
          style({ opacity: 0, transform: 'translateY(20px)' }),
          stagger(100, [
            animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
          ])
        ], { optional: true })
      ])
    ])
  ]
})
export class DashboardComponent implements OnInit, OnDestroy {
  stats: DashboardStats | null = null;
  chart: Chart | null = null;
  loading = true;
  errorMessage: string | null = null;
  recalculating = false;

  private destroy$ = new Subject<void>();

  constructor(private api: ApiService) { }

  ngOnInit(): void {
    this.loadStats();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.chart) {
      this.chart.destroy();
    }
  }

  loadStats(): void {
    this.loading = true;
    this.errorMessage = null;

    this.api.getDashboardStats().pipe(
      takeUntil(this.destroy$),
      catchError(err => {
        this.errorMessage = err.message || 'Failed to load dashboard';
        this.loading = false;
        return [];
      })
    ).subscribe((res: any) => {
      this.stats = res;
      this.loading = false;
      setTimeout(() => this.createChart(), 100);
    });
  }

  recalculateScores(): void {
    this.recalculating = true;
    this.api.recalculateScores().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.recalculating = false;
        this.loadStats();
      },
      error: () => {
        this.recalculating = false;
      }
    });
  }

  createChart(): void {
    if (!this.stats?.industry_distribution) return;

    const ctx = document.getElementById('industryChart') as HTMLCanvasElement;
    if (!ctx) return;

    if (this.chart) {
      this.chart.destroy();
    }

    const labels = Object.keys(this.stats.industry_distribution);
    const data = Object.values(this.stats.industry_distribution);

    this.chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: [
            'rgba(63, 81, 181, 0.8)',
            'rgba(233, 30, 99, 0.8)',
            'rgba(0, 188, 212, 0.8)',
            'rgba(255, 152, 0, 0.8)',
            'rgba(76, 175, 80, 0.8)',
            'rgba(156, 39, 176, 0.8)',
          ],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true
            }
          }
        },
        cutout: '60%'
      }
    });
  }
}
