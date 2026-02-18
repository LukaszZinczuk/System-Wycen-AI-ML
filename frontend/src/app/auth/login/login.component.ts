import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-login',
  template: `
    <div class="login-container">
      <div class="login-background">
        <div class="bg-shape shape-1"></div>
        <div class="bg-shape shape-2"></div>
        <div class="bg-shape shape-3"></div>
      </div>

      <mat-card class="login-card" @fadeIn>
        <div class="login-header">
          <div class="logo">
            <mat-icon>analytics</mat-icon>
          </div>
          <h1>AI Pricing System</h1>
          <p>Sign in to your account</p>
        </div>

        <mat-card-content>
          <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
            <mat-form-field appearance="outline">
              <mat-label>Email</mat-label>
              <input matInput formControlName="username" type="email" placeholder="Enter your email">
              <mat-icon matSuffix>email</mat-icon>
              <mat-error *ngIf="loginForm.get('username')?.hasError('required')">Email is required</mat-error>
              <mat-error *ngIf="loginForm.get('username')?.hasError('email')">Invalid email format</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline">
              <mat-label>Password</mat-label>
              <input matInput formControlName="password" [type]="hidePassword ? 'password' : 'text'" placeholder="Enter your password">
              <button mat-icon-button matSuffix (click)="hidePassword = !hidePassword" type="button">
                <mat-icon>{{ hidePassword ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
              <mat-error *ngIf="loginForm.get('password')?.hasError('required')">Password is required</mat-error>
            </mat-form-field>

            <div class="form-options">
              <mat-checkbox color="primary">Remember me</mat-checkbox>
              <a href="#" class="forgot-link">Forgot password?</a>
            </div>

            <button mat-raised-button color="primary" type="submit" class="login-btn" [disabled]="loginForm.invalid || loading">
              <mat-spinner diameter="20" *ngIf="loading"></mat-spinner>
              <span *ngIf="!loading">Sign In</span>
            </button>
          </form>

          <mat-divider></mat-divider>

          <div class="demo-credentials">
            <p><strong>Demo Credentials:</strong></p>
            <code>admin@example.com / admin123</code>
          </div>
        </mat-card-content>
      </mat-card>

      <p class="footer-text">© 2024 AI Pricing System. Portfolio Project.</p>
    </div>
  `,
  styles: [`
    .login-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
      position: relative;
      overflow: hidden;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .login-background {
      position: absolute;
      inset: 0;
      overflow: hidden;
    }

    .bg-shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.1;
    }

    .shape-1 {
      width: 400px;
      height: 400px;
      background: white;
      top: -100px;
      left: -100px;
      animation: float 8s ease-in-out infinite;
    }

    .shape-2 {
      width: 300px;
      height: 300px;
      background: white;
      bottom: -50px;
      right: -50px;
      animation: float 6s ease-in-out infinite reverse;
    }

    .shape-3 {
      width: 200px;
      height: 200px;
      background: white;
      top: 50%;
      right: 20%;
      animation: float 10s ease-in-out infinite;
    }

    @keyframes float {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-20px) rotate(5deg); }
    }

    .login-card {
      width: 100%;
      max-width: 420px;
      padding: 40px;
      border-radius: 24px !important;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
      position: relative;
      z-index: 1;
    }

    .login-header {
      text-align: center;
      margin-bottom: 32px;

      .logo {
        width: 70px;
        height: 70px;
        margin: 0 auto 16px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;

        mat-icon {
          font-size: 36px;
          width: 36px;
          height: 36px;
          color: white;
        }
      }

      h1 {
        margin: 0 0 8px 0;
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
      }

      p {
        margin: 0;
        color: #666;
      }
    }

    form {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    mat-form-field {
      width: 100%;
    }

    .form-options {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 8px 0 16px 0;

      .forgot-link {
        color: #667eea;
        text-decoration: none;
        font-size: 0.9rem;

        &:hover {
          text-decoration: underline;
        }
      }
    }

    .login-btn {
      width: 100%;
      padding: 12px;
      font-size: 1rem;
      border-radius: 12px !important;
      margin-bottom: 24px;

      mat-spinner {
        display: inline-block;
        margin-right: 8px;
      }
    }

    mat-divider {
      margin: 24px 0;
    }

    .demo-credentials {
      text-align: center;
      padding: 16px;
      background: #f5f5f5;
      border-radius: 12px;

      p {
        margin: 0 0 8px 0;
        font-size: 0.85rem;
        color: #666;
      }

      code {
        display: block;
        font-family: monospace;
        font-size: 0.9rem;
        color: #333;
        background: #e0e0e0;
        padding: 8px 16px;
        border-radius: 8px;
      }
    }

    .footer-text {
      margin-top: 24px;
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.85rem;
      position: relative;
      z-index: 1;
    }
  `],
  animations: [
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('400ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class LoginComponent implements OnInit {
  loginForm!: FormGroup;
  loading = false;
  hidePassword = true;

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private snackBar: MatSnackBar
  ) { }

  ngOnInit(): void {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.loading = true;
    this.auth.login(this.loginForm.value.username, this.loginForm.value.password).subscribe({
      next: () => {
        this.loading = false;
        this.snackBar.open('Login successful!', 'Close', { duration: 2000 });
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.snackBar.open(err.message || 'Login failed', 'Close', { duration: 3000 });
      }
    });
  }
}
