import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { TriageFlowService } from '../../services/triage_flow_service';
import { SentinelService } from '../../services/sentinel.service';

@Component({
  selector: 'app-vitals',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vitals.component.html',
  styleUrl: './vitals.component.css',
})
export class VitalsComponent implements OnInit {
  private readonly flow     = inject(TriageFlowService);
  private readonly sentinel = inject(SentinelService);
  private readonly router   = inject(Router);

  protected readonly relato   = this.flow.relato;
  protected readonly paciente = this.flow.pacienteAtual;

  protected readonly glicemia = signal(this.flow.sinaisVitais().glicemia);
  protected readonly tempoDeslocamento = signal(this.flow.pacienteAtual()?.tempoDeslocamentoMin ?? 0);
  protected readonly carregandoUbs = signal(false);

  ngOnInit(): void {
    // Consulta o agente Sentinel.AI em segundo plano para confirmar a quantidade
    // de UBS em 3km; até a resposta chegar (ou se falhar), mantém o valor mock.
    const paciente = this.paciente();
    const endereco = paciente?.enderecoCasa ?? (paciente?.bairro ? `${paciente.bairro}, São Paulo - SP` : undefined);
    if (!endereco) return;

    this.carregandoUbs.set(true);
    this.sentinel.ubsRaioCasa({ endereco_casa: endereco }).pipe(
      catchError(() => of({ items: [] }))
    ).subscribe((r) => {
      this.carregandoUbs.set(false);
      if (r.items.length > 0) this.flow.definirQtdUbs3km(r.items.length);
    });
  }

  protected analisar(): void {
    // Preserva os outros campos com os valores padrão já existentes
    const atual = this.flow.sinaisVitais();
    this.flow.definirSinaisVitais({ ...atual, glicemia: this.glicemia() });
    this.flow.definirTempoDeslocamento(this.tempoDeslocamento());
    this.router.navigate(['/results']);
  }
}
