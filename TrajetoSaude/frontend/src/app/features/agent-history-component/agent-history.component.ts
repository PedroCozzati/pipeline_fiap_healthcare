import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth_service';
import { StorageService, TriagemApi, PacienteApi } from '../../services/storage.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface AtendimentoView {
  triagem: TriagemApi;
  paciente: PacienteApi | null;
}

@Component({
  selector: 'app-agent-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './agent-history.component.html',
  styleUrl: './agent-history.component.css',
})
export class AgentHistoryComponent implements OnInit {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);

  protected readonly atendimentos = signal<AtendimentoView[]>([]);
  protected readonly carregando   = signal(true);
  protected readonly semDados     = signal(false);

  protected readonly totalAlto  = computed(() => this.atendimentos().filter(a => a.triagem.risco_label === 1).length);
  protected readonly totalBaixo = computed(() => this.atendimentos().filter(a => a.triagem.risco_label === 0).length);

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); this.semDados.set(true); return; }

    this.storage.buscarAgentePorUsuario(uid).subscribe({
      next: (agente) => {
        this.storage.historicoTriagensPorAgente(agente.id).subscribe({
          next: (triagens) => {
            if (triagens.length === 0) { this.semDados.set(true); this.carregando.set(false); return; }

            // Busca dados dos pacientes em paralelo
            const buscarPacientes = triagens.map(t =>
              this.storage.buscarPaciente(t.paciente_id!.toString()).pipe(catchError(() => of(null)))
            );

            forkJoin(buscarPacientes).subscribe(pacientes => {
              const views = triagens.map((t, i) => ({ triagem: t, paciente: pacientes[i] }));
              this.atendimentos.set(views);
              this.carregando.set(false);
            });
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

  protected labelRisco(t: TriagemApi): string {
    if (t.risco_label === 1) return 'Alto';
    if (t.risco_label === 0) return 'Baixo';
    return '—';
  }

  protected resumoDesfecho(t: TriagemApi): string {
    if (t.risco_label === 1) return 'Encaminhado para UBS via ticket';
    if (t.risco_label === 0) return t.glicemia != null && t.glicemia >= 126
      ? 'Cuidados preventivos — glicemia elevada'
      : 'Agendamento de rotina indicado';
    return 'Sem desfecho registrado';
  }
}
