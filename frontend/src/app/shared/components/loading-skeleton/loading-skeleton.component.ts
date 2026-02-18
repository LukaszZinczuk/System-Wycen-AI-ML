import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-loading-skeleton',
  template: `
    <div class="skeleton-container" [ngStyle]="containerStyle">
      <!-- Card skeleton -->
      <ng-container *ngIf="type === 'card'">
        <div class="skeleton-card" *ngFor="let item of items">
          <div class="skeleton-header">
            <div class="skeleton skeleton-avatar"></div>
            <div class="skeleton-title-group">
              <div class="skeleton skeleton-title"></div>
              <div class="skeleton skeleton-subtitle"></div>
            </div>
          </div>
          <div class="skeleton skeleton-content"></div>
          <div class="skeleton skeleton-content short"></div>
        </div>
      </ng-container>

      <!-- Table skeleton -->
      <ng-container *ngIf="type === 'table'">
        <div class="skeleton-table">
          <div class="skeleton-row header">
            <div class="skeleton skeleton-cell" *ngFor="let col of columnsArray"></div>
          </div>
          <div class="skeleton-row" *ngFor="let row of items">
            <div class="skeleton skeleton-cell" *ngFor="let col of columnsArray"></div>
          </div>
        </div>
      </ng-container>

      <!-- Text skeleton -->
      <ng-container *ngIf="type === 'text'">
        <div class="skeleton skeleton-text" *ngFor="let item of items" [ngStyle]="{ width: getRandomWidth() }"></div>
      </ng-container>

      <!-- Chart skeleton -->
      <ng-container *ngIf="type === 'chart'">
        <div class="skeleton-chart">
          <div class="skeleton skeleton-chart-area"></div>
        </div>
      </ng-container>

      <!-- Form skeleton -->
      <ng-container *ngIf="type === 'form'">
        <div class="skeleton-form">
          <div class="skeleton-form-field" *ngFor="let item of items">
            <div class="skeleton skeleton-label"></div>
            <div class="skeleton skeleton-input"></div>
          </div>
          <div class="skeleton skeleton-button"></div>
        </div>
      </ng-container>
    </div>
  `,
  styles: [`
    .skeleton-container {
      width: 100%;
    }

    .skeleton {
      background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
      border-radius: 4px;
    }

    :host-context(.dark-theme) .skeleton {
      background: linear-gradient(90deg, #3a3a3a 25%, #4a4a4a 50%, #3a3a3a 75%);
      background-size: 200% 100%;
    }

    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* Card skeleton */
    .skeleton-card {
      padding: 20px;
      margin-bottom: 15px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    :host-context(.dark-theme) .skeleton-card {
      background: #424242;
    }

    .skeleton-header {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
    }

    .skeleton-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin-right: 15px;
    }

    .skeleton-title-group {
      flex: 1;
    }

    .skeleton-title {
      height: 18px;
      width: 60%;
      margin-bottom: 8px;
    }

    .skeleton-subtitle {
      height: 14px;
      width: 40%;
    }

    .skeleton-content {
      height: 14px;
      width: 100%;
      margin-bottom: 10px;
    }

    .skeleton-content.short {
      width: 70%;
    }

    /* Table skeleton */
    .skeleton-table {
      width: 100%;
    }

    .skeleton-row {
      display: flex;
      gap: 15px;
      padding: 15px 0;
      border-bottom: 1px solid #eee;
    }

    :host-context(.dark-theme) .skeleton-row {
      border-bottom-color: #555;
    }

    .skeleton-row.header {
      background: #fafafa;
    }

    :host-context(.dark-theme) .skeleton-row.header {
      background: #383838;
    }

    .skeleton-cell {
      flex: 1;
      height: 20px;
    }

    /* Text skeleton */
    .skeleton-text {
      height: 16px;
      margin-bottom: 10px;
    }

    /* Chart skeleton */
    .skeleton-chart {
      padding: 20px;
    }

    .skeleton-chart-area {
      height: 300px;
      width: 100%;
    }

    /* Form skeleton */
    .skeleton-form {
      max-width: 400px;
    }

    .skeleton-form-field {
      margin-bottom: 20px;
    }

    .skeleton-label {
      height: 14px;
      width: 30%;
      margin-bottom: 8px;
    }

    .skeleton-input {
      height: 40px;
      width: 100%;
    }

    .skeleton-button {
      height: 40px;
      width: 120px;
      margin-top: 20px;
    }
  `]
})
export class LoadingSkeletonComponent {
  @Input() type: 'card' | 'table' | 'text' | 'chart' | 'form' = 'card';
  @Input() count = 3;
  @Input() columns = 5;
  @Input() containerStyle: { [key: string]: string } = {};

  get items(): number[] {
    return Array(this.count).fill(0).map((_, i) => i);
  }

  get columnsArray(): number[] {
    return Array(this.columns).fill(0).map((_, i) => i);
  }

  getRandomWidth(): string {
    const widths = ['100%', '90%', '80%', '95%', '85%'];
    return widths[Math.floor(Math.random() * widths.length)];
  }
}
