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

type Classificacao = 'alto' | 'medio' | 'baixo' | 'pendente';

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

  protected readonly totalAlto  = computed(() =>
    this.atendimentos().filter(a => this.classificacao(a.triagem) === 'alto').length
  );
  protected readonly totalMedio = computed(() =>
    this.atendimentos().filter(a => this.classificacao(a.triagem) === 'medio').length
  );
  protected readonly totalBaixo = computed(() =>
    this.atendimentos().filter(a => this.classificacao(a.triagem) === 'baixo').length
  );

  ngOnInit(): void {
    const uid = this.auth.currentUser()?.id;
    if (!uid) { this.carregando.set(false); this.semDados.set(true); return; }

    this.storage.buscarAgentePorUsuario(uid).subscribe({
      next: (agente) => {
        this.storage.historicoTriagensPorAgente(agente.id).subscribe({
          next: (triagens) => {
            if (triagens.length === 0) { this.semDados.set(true); this.carregando.set(false); return; }

            const buscarPacientes = triagens.map(t =>
              this.storage.buscarPaciente(t.paciente_id!.toString()).pipe(catchError(() => of(null)))
            );

            forkJoin(buscarPacientes).subscribe(pacientes => {
              this.atendimentos.set(triagens.map((t, i) => ({ triagem: t, paciente: pacientes[i] })));
              this.carregando.set(false);
            });
          },
          error: () => { this.carregando.set(false); this.semDados.set(true); },
        });
      },
      error: () => { this.carregando.set(false); this.semDados.set(true); },
    });
  }

  /** Glicemia elevada + risco baixo = categoria intermediária (ticket emitido com prioridade média) */
  protected classificacao(t: TriagemApi): Classificacao {
    if (t.risco_label === 1) return 'alto';
    if (t.risco_label === 0 && t.glicemia != null && t.glicemia >= 126) return 'medio';
    if (t.risco_label === 0) return 'baixo';
    return 'pendente';
  }

  protected formatarData(iso: string): string {
    return new Date(iso).toLocaleDateString('pt-BR');
  }

  protected labelRisco(t: TriagemApi): string {
    const c = this.classificacao(t);
    if (c === 'alto')  return 'Evasão Alta';
    if (c === 'medio') return 'Glicemia Elevada';
    if (c === 'baixo') return 'Evasão Baixa';
    return '—';
  }

  protected resumoDesfecho(t: TriagemApi): string {
    const c = this.classificacao(t);
    if (c === 'alto')  return 'Encaminhado para UBS — prioridade alta';
    if (c === 'medio') return 'Encaminhado para UBS — prioridade média (glicemia elevada)';
    if (c === 'baixo') return 'Agendamento de rotina indicado';
    return 'Sem desfecho registrado';
  }
}
