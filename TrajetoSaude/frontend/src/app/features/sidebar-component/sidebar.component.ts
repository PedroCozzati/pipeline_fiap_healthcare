import { Component, computed, inject, signal } from '@angular/core';
import { RouterModule } from '@angular/router';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth_service';

interface NavItem {
  icon: string;
  label: string;
  route: string | null;
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterModule],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.css',
})
export class SidebarComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly expandida = signal(false);
  protected readonly role = this.auth.role;

  protected readonly menuItems = computed<NavItem[]>(() => {
    const role = this.role();
    if (role === 'paciente') {
      return [
        { icon: 'fa-house',             label: 'Início',        route: '/paciente' },
        { icon: 'fa-qrcode',            label: 'Meu Ticket',    route: '/paciente/ticket' },
        { icon: 'fa-clock-rotate-left', label: 'Histórico',     route: '/paciente/historico' },
        { icon: 'fa-bell',              label: 'Notificações',  route: '/paciente/notificacoes' },
        { icon: 'fa-circle-user',       label: 'Perfil',        route: '/paciente/perfil' },
      ];
    }
    return [
      { icon: 'fa-house',             label: 'Início',     route: '/identificacao' },
      { icon: 'fa-clock-rotate-left', label: 'Histórico',  route: '/agente/historico' },
      { icon: 'fa-circle-user',       label: 'Perfil',     route: '/agente/perfil' },
    ];
  });

  protected toggleSidebar(): void {
    this.expandida.update(v => !v);
  }

  protected sair(): void {
    this.auth.logout();
    this.router.navigateByUrl('/login');
  }
}
