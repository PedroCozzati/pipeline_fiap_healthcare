import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth_service';
import { StorageService, TriagemApi } from '../../services/storage.service';

@Component({
  selector: 'app-patient-history',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './patient-history.component.html',
  styleUrl: './patient-history.component.css',
})
export class PatientHistoryComponent implements OnInit {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);

  protected readonly triagens   = signal<TriagemApi[]>([]);
  protected readonly carregando = signal(true);
  protected readonly semDados   = signal(false);

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); this.semDados.set(true); return; }

    this.storage.buscarPacientePorUsuario(uid).subscribe({
      next: (paciente) => {
        this.storage.historicoTriagens(paciente.id).subscribe({
          next: (list) => {
            this.triagens.set(list);
            this.semDados.set(list.length === 0);
            this.carregando.set(false);
          },
          error: () => { this.carregando.set(false); this.semDados.set(true); },
        });
      },
      error: () => { this.carregando.set(false); this.semDados.set(true); },
    });
  }

  protected formatarData(iso: string): string {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  protected resumoVitais(t: TriagemApi): string {
    const partes: string[] = [];
    if (t.glicemia != null) partes.push(`Glicemia: ${t.glicemia} mg/dL`);
    if (t.pressao_sistolica != null && t.pressao_diastolica != null)
      partes.push(`PA: ${t.pressao_sistolica}/${t.pressao_diastolica} mmHg`);
    return partes.join(' · ') || '—';
  }

  protected labelRisco(t: TriagemApi): string {
    if (t.risco_label === 1) return `Alto risco${t.risco_probabilidade != null ? ' · ' + Math.round(t.risco_probabilidade * 100) + '%' : ''}`;
    if (t.risco_label === 0) return `Baixo risco${t.risco_probabilidade != null ? ' · ' + Math.round(t.risco_probabilidade * 100) + '%' : ''}`;
    return 'Sem classificação';
  }

  protected classeRisco(t: TriagemApi): string {
    if (t.risco_label === 1) return 'risco-alto';
    if (t.risco_label === 0) return 'risco-baixo';
    return 'risco-neutro';
  }
}
