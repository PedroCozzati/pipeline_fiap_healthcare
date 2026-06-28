import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth_service';
import { StorageService, PacienteApi } from '../../services/storage.service';

@Component({
  selector: 'app-patient-profile',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './patient-profile.component.html',
  styleUrl: './patient-profile.component.css',
})
export class PatientProfileComponent implements OnInit {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);

  protected readonly usuario    = this.auth.currentUser;
  protected readonly perfil     = signal<PacienteApi | null>(null);
  protected readonly carregando = signal(true);

  protected readonly rotaFormatada = () => {
    const p = this.perfil();
    if (!p?.rota_trabalho) return '—';
    try {
      const rota: string[] = JSON.parse(p.rota_trabalho);
      return rota.join(' → ');
    } catch { return p.rota_trabalho; }
  };

  protected readonly idadeFormatada = () => {
    const p = this.perfil();
    if (!p?.data_nascimento) return '—';
    const anos = Math.floor((Date.now() - new Date(p.data_nascimento).getTime()) / (365.25 * 24 * 60 * 60 * 1000));
    return `${anos} anos`;
  };

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); return; }

    this.storage.buscarPacientePorUsuario(uid).subscribe({
      next: (p) => { this.perfil.set(p); this.carregando.set(false); },
      error: ()  => this.carregando.set(false),
    });
  }
}
