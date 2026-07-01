import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth_service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.css',
})
export class HeaderComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly currentUser = this.auth.currentUser;

  protected readonly papelLabel = (): string =>
    this.currentUser()?.role === 'agente' ? 'Agente de Saúde' : 'Paciente';

  protected sair(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
