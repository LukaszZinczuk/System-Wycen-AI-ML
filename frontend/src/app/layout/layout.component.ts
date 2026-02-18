import { Component, OnInit, OnDestroy, ViewChild } from '@angular/core';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { MatSidenav } from '@angular/material/sidenav';
import { Router, NavigationEnd } from '@angular/router';
import { Subject, Observable } from 'rxjs';
import { takeUntil, filter, map, shareReplay } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { ThemeService } from '../services/theme.service';
import { trigger, transition, style, animate } from '@angular/animations';

@Component({
  selector: 'app-layout',
  template: `
    <mat-sidenav-container class="sidenav-container" [class.dark-theme]="isDarkMode$ | async">
      <!-- Sidenav -->
      <mat-sidenav
        #sidenav
        [mode]="(isHandset$ | async) ? 'over' : 'side'"
        [opened]="!(isHandset$ | async)"
        class="sidenav"
        [class.dark-theme]="isDarkMode$ | async">
        
        <div class="sidenav-header">
          <div class="logo">
            <mat-icon>analytics</mat-icon>
            <span>AI Pricing</span>
          </div>
        </div>

        <mat-nav-list>
          <a mat-list-item routerLink="/dashboard" routerLinkActive="active" (click)="closeSidenavOnMobile()">
            <mat-icon matListItemIcon>dashboard</mat-icon>
            <span matListItemTitle>Dashboard</span>
          </a>
          <a mat-list-item routerLink="/calculator" routerLinkActive="active" (click)="closeSidenavOnMobile()">
            <mat-icon matListItemIcon>calculate</mat-icon>
            <span matListItemTitle>Calculator</span>
          </a>
          <a mat-list-item routerLink="/offers" routerLinkActive="active" (click)="closeSidenavOnMobile()">
            <mat-icon matListItemIcon>list_alt</mat-icon>
            <span matListItemTitle>Offers</span>
          </a>
          <a mat-list-item routerLink="/companies" routerLinkActive="active" (click)="closeSidenavOnMobile()">
            <mat-icon matListItemIcon>business</mat-icon>
            <span matListItemTitle>Companies</span>
          </a>
        </mat-nav-list>

        <div class="sidenav-footer">
          <mat-divider></mat-divider>
          <a mat-list-item (click)="logout()">
            <mat-icon matListItemIcon>logout</mat-icon>
            <span matListItemTitle>Logout</span>
          </a>
        </div>
      </mat-sidenav>

      <!-- Main content -->
      <mat-sidenav-content class="main-content">
        <!-- Toolbar -->
        <mat-toolbar color="primary" class="toolbar">
          <button mat-icon-button (click)="sidenav.toggle()" *ngIf="isHandset$ | async">
            <mat-icon>menu</mat-icon>
          </button>
          
          <span class="page-title">{{ pageTitle }}</span>
          
          <span class="toolbar-spacer"></span>

          <!-- User info -->
          <div class="user-info" *ngIf="currentUser$ | async as user">
            <mat-icon>person</mat-icon>
            <span class="user-email">{{ user.email }}</span>
          </div>

          <!-- Theme toggle -->
          <button mat-icon-button (click)="toggleTheme()" matTooltip="Toggle dark mode">
            <mat-icon>{{ (isDarkMode$ | async) ? 'light_mode' : 'dark_mode' }}</mat-icon>
          </button>

          <!-- Notifications -->
          <button mat-icon-button matTooltip="Notifications" [matBadge]="notificationCount" matBadgeColor="warn" [matBadgeHidden]="notificationCount === 0">
            <mat-icon>notifications</mat-icon>
          </button>
        </mat-toolbar>

        <!-- Page content with animation -->
        <main class="page-content" [@fadeAnimation]="outlet.isActivated ? outlet.activatedRoute : ''">
          <router-outlet #outlet="outlet"></router-outlet>
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .sidenav-container {
      height: 100vh;
    }

    .sidenav {
      width: 250px;
      background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
    }

    .sidenav.dark-theme {
      background: linear-gradient(180deg, #121212 0%, #1e1e1e 100%);
    }

    .sidenav-header {
      padding: 20px;
      text-align: center;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .logo {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      color: white;
      font-size: 1.5rem;
      font-weight: 500;
    }

    .logo mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
    }

    .sidenav mat-nav-list {
      padding-top: 10px;
    }

    .sidenav mat-nav-list a {
      color: rgba(255,255,255,0.8);
      margin: 5px 10px;
      border-radius: 8px;
    }

    .sidenav mat-nav-list a:hover {
      background: rgba(255,255,255,0.1);
    }

    .sidenav mat-nav-list a.active {
      background: rgba(255,255,255,0.2);
      color: white;
    }

    .sidenav-footer {
      position: absolute;
      bottom: 0;
      width: 100%;
    }

    .sidenav-footer mat-divider {
      border-color: rgba(255,255,255,0.1);
    }

    .sidenav-footer a {
      color: rgba(255,255,255,0.7);
    }

    .toolbar {
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .toolbar-spacer {
      flex: 1 1 auto;
    }

    .page-title {
      margin-left: 10px;
      font-size: 1.2rem;
    }

    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-right: 15px;
      padding: 5px 15px;
      background: rgba(255,255,255,0.1);
      border-radius: 20px;
    }

    .user-email {
      font-size: 0.9rem;
    }

    .main-content {
      background: #f5f5f5;
      min-height: 100vh;
    }

    .dark-theme .main-content {
      background: #303030;
    }

    .page-content {
      padding: 20px;
      max-width: 1400px;
      margin: 0 auto;
    }

    @media (max-width: 768px) {
      .user-email {
        display: none;
      }

      .page-content {
        padding: 15px;
      }

      .user-info {
        padding: 5px 10px;
      }
    }
  `],
  animations: [
    trigger('fadeAnimation', [
      transition('* <=> *', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class LayoutComponent implements OnInit, OnDestroy {
  @ViewChild('sidenav') sidenav!: MatSidenav;

  private destroy$ = new Subject<void>();

  isHandset$: Observable<boolean>;
  isDarkMode$: Observable<boolean>;
  currentUser$: Observable<any>;

  pageTitle = 'Dashboard';
  notificationCount = 3;

  constructor(
    private breakpointObserver: BreakpointObserver,
    private router: Router,
    private authService: AuthService,
    private themeService: ThemeService
  ) {
    this.isHandset$ = this.breakpointObserver.observe(Breakpoints.Handset)
      .pipe(
        map(result => result.matches),
        shareReplay()
      );

    this.isDarkMode$ = this.themeService.isDarkMode$;
    this.currentUser$ = this.authService.currentUser$;
  }

  ngOnInit(): void {
    // Update page title based on route
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      takeUntil(this.destroy$)
    ).subscribe((event: any) => {
      this.updatePageTitle(event.urlAfterRedirects);
    });

    // Set initial title
    this.updatePageTitle(this.router.url);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private updatePageTitle(url: string): void {
    const titles: { [key: string]: string } = {
      '/dashboard': 'Dashboard',
      '/calculator': 'Pricing Calculator',
      '/offers': 'Offers List',
      '/companies': 'Companies'
    };
    this.pageTitle = titles[url] || 'AI Pricing System';
  }

  closeSidenavOnMobile(): void {
    this.isHandset$.pipe(takeUntil(this.destroy$)).subscribe(isHandset => {
      if (isHandset && this.sidenav) {
        this.sidenav.close();
      }
    });
  }

  toggleTheme(): void {
    this.themeService.toggleTheme();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
