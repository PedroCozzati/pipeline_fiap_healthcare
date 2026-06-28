import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth_service';
import { StorageService, AgenteApi } from '../../services/storage.service';

@Component({
  selector: 'app-agent-profile',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './agent-profile.component.html',
  styleUrl: './agent-profile.component.css',
})
export class AgentProfileComponent implements OnInit {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);

  protected readonly usuario    = this.auth.currentUser;
  protected readonly perfil     = signal<AgenteApi | null>(null);
  protected readonly carregando = signal(true);

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); return; }

    this.storage.buscarAgentePorUsuario(uid).subscribe({
      next: (a) => { this.perfil.set(a); this.carregando.set(false); },
      error: ()  => this.carregando.set(false),
    });
  }
}
