import { Component, Input, Output, EventEmitter } from '@angular/core';
import { trigger, transition, style, animate } from '@angular/animations';

export interface ErrorInfo {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info' | 'network';
  code?: string | number;
  retryable?: boolean;
}

@Component({
  selector: 'app-error-handler',
  template: `
    <div class="error-container" [ngClass]="'error-' + error.type" @fadeIn>
      <div class="error-icon">
        <mat-icon>{{ getIcon() }}</mat-icon>
      </div>
      
      <div class="error-content">
        <h3 class="error-title">{{ error.title }}</h3>
        <p class="error-message">{{ error.message }}</p>
        
        <div class="error-code" *ngIf="error.code">
          Error Code: {{ error.code }}
        </div>
      </div>

      <div class="error-actions">
        <button mat-raised-button color="primary" *ngIf="error.retryable" (click)="onRetry()">
          <mat-icon>refresh</mat-icon>
          Retry
        </button>
        <button mat-button (click)="onDismiss()">
          Dismiss
        </button>
      </div>
    </div>
  `,
  styles: [`
    .error-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 40px 20px;
      text-align: center;
      background: white;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
      max-width: 500px;
      margin: 20px auto;
    }

    :host-context(.dark-theme) .error-container {
      background: #424242;
    }

    .error-icon {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 20px;
    }

    .error-icon mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: white;
    }

    .error-error .error-icon {
      background: linear-gradient(135deg, #f44336, #d32f2f);
    }

    .error-warning .error-icon {
      background: linear-gradient(135deg, #ff9800, #f57c00);
    }

    .error-info .error-icon {
      background: linear-gradient(135deg, #2196f3, #1976d2);
    }

    .error-network .error-icon {
      background: linear-gradient(135deg, #9c27b0, #7b1fa2);
    }

    .error-title {
      margin: 0 0 10px 0;
      font-size: 1.5rem;
      color: #333;
    }

    :host-context(.dark-theme) .error-title {
      color: #fff;
    }

    .error-message {
      margin: 0 0 15px 0;
      color: #666;
      line-height: 1.5;
    }

    :host-context(.dark-theme) .error-message {
      color: #bbb;
    }

    .error-code {
      font-family: monospace;
      font-size: 0.9rem;
      color: #999;
      padding: 5px 10px;
      background: #f5f5f5;
      border-radius: 4px;
      margin-bottom: 20px;
    }

    :host-context(.dark-theme) .error-code {
      background: #333;
      color: #aaa;
    }

    .error-actions {
      display: flex;
      gap: 10px;
    }

    .error-actions button mat-icon {
      margin-right: 5px;
    }
  `],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.95)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'scale(1)' }))
      ])
    ])
  ]
})
export class ErrorHandlerComponent {
  @Input() error: ErrorInfo = {
    title: 'Something went wrong',
    message: 'An unexpected error occurred. Please try again.',
    type: 'error',
    retryable: true
  };

  @Output() retry = new EventEmitter<void>();
  @Output() dismiss = new EventEmitter<void>();

  getIcon(): string {
    const icons: { [key: string]: string } = {
      'error': 'error_outline',
      'warning': 'warning_amber',
      'info': 'info_outline',
      'network': 'wifi_off'
    };
    return icons[this.error.type] || 'error_outline';
  }

  onRetry(): void {
    this.retry.emit();
  }

  onDismiss(): void {
    this.dismiss.emit();
  }
}
