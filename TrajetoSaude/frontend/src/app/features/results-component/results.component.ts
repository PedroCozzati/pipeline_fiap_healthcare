import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { catchError, of } from 'rxjs';
import { TriageFlowService } from '../../services/triage_flow_service';
import { ApiService, RiskResponse } from '../../services/api.service';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './results.component.html',
  styleUrl: './results.component.css',
})
export class ResultsComponent implements OnInit {
  private readonly flow   = inject(TriageFlowService);
  private readonly api    = inject(ApiService);
  private readonly router = inject(Router);

  protected readonly relato       = this.flow.relato;
  protected readonly vitais       = this.flow.sinaisVitais;
  protected readonly paciente     = this.flow.pacienteAtual;
  protected readonly sugestao     = this.flow.sugestaoCuidado;
  protected readonly fatoresRisco = this.flow.fatoresRisco;

  protected readonly carregando = signal(true);
  protected readonly apiRisk    = signal<RiskResponse | null>(null);
  protected readonly apiErro    = signal<string | null>(null);

  protected readonly nivelRisco = () =>
    this.apiRisk()
      ? (this.apiRisk()!.risk_label === 1 ? 'alto' : 'baixo')
      : this.flow.nivelRisco();

  protected readonly probabilidadeFormatada = () => {
    const r = this.apiRisk();
    return r ? Math.round(r.risk_probability * 100) : null;
  };

  /**
   * Glicemia ≥ 126 mg/dL (critério ADA para diabetes) exige encaminhamento
   * à UBS mesmo quando o modelo classifica risco de evasão como baixo.
   */
  protected readonly glicemiaElevada = () => this.flow.sinaisVitais().glicemia >= 126;

  /**
   * Risco alto → acompanhamento contínuo obrigatório (encaminha para logística).
   * Risco baixo + glicemia elevada → preventivo com alerta de UBS.
   * Risco baixo + glicemia ok → cuidados preventivos simples.
   */
  protected decidirFluxo(): void {
    if (this.nivelRisco() === 'alto') {
      this.flow.setPrioridade('alta');
      this.router.navigate(['/map']);
    } else if (this.glicemiaElevada()) {
      this.flow.setPrioridade('media');
      this.router.navigate(['/map']);
    } else {
      this.flow.setPrioridade('baixa');
      this.router.navigate(['/cuidados-preventivos']);
    }
  }

  ngOnInit(): void {
    const paciente = this.flow.pacienteAtual();
    const vitais   = this.flow.sinaisVitais();

    this.api.predictRisk({
      Idade:                  paciente?.idade                ?? 50,
      Tempo_Deslocamento_Min: paciente?.tempoDeslocamentoMin ?? 60,
      Qtd_UBS_Origem_3km:     paciente?.qtdUbs3km            ?? 2,
      Glicemia_Aferida:       vitais.glicemia,
    }).pipe(
      catchError(() => of(null))
    ).subscribe((r) => {
      this.apiRisk.set(r);
      this.flow.setUltimaPredicao(r);
      if (!r) this.apiErro.set('API indisponível — usando classificação local.');
      this.carregando.set(false);
    });
  }
}
