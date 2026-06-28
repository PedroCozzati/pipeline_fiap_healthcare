import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { switchMap } from 'rxjs';
import { TriageFlowService } from '../../services/triage_flow_service';
import { StorageService } from '../../services/storage.service';

@Component({
  selector: 'app-ticket',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './ticket.component.html',
  styleUrl: './ticket.component.css',
})
export class TicketComponent implements OnInit {
  private readonly flow    = inject(TriageFlowService);
  private readonly storage = inject(StorageService);
  private readonly router  = inject(Router);

  protected readonly ticket      = this.flow.ticket;
  protected readonly carregando  = signal(false);
  protected readonly ubsNome     = () => this.flow.ubsIndicada()?.nome     ?? this.flow.logistica().recomendada.nome;
  protected readonly ubsEndereco = () => this.flow.ubsIndicada()?.endereco ?? this.flow.logistica().recomendada.endereco;

  ngOnInit(): void {
    const pacienteId = this.flow.pacienteApiId();

    if (pacienteId) {
      this.criarTicketViaApi(pacienteId);
    } else if (!this.ticket()) {
      this.flow.emitirTicket();
    }
  }

  private criarTicketViaApi(pacienteId: string): void {
    this.carregando.set(true);
    const vitais   = this.flow.sinaisVitais();
    const predicao = this.flow.ultimaPredicao();
    const ubs      = this.flow.ubsIndicada() ?? this.flow.logistica().recomendada;

    this.storage.criarTriagem({
      paciente_id:         pacienteId,
      glicemia:            vitais.glicemia,
      pressao_sistolica:   vitais.pressaoSistolica,
      pressao_diastolica:  vitais.pressaoDiastolica,
      risco_probabilidade: predicao?.risk_probability,
      risco_label:         predicao?.risk_label,
    }).pipe(
      switchMap((triagem) =>
        this.storage.criarTicket({
          paciente_id:       pacienteId,
          triagem_id:        triagem.id,
          ubs_encaminhamento: `${ubs.nome} — ${ubs.endereco}`,
        })
      )
    ).subscribe({
      next: (ticket) => {
        this.flow.setTicketFromApi(ticket);
        this.carregando.set(false);
      },
      error: () => {
        this.flow.emitirTicket();
        this.carregando.set(false);
      },
    });
  }

  protected dispararWhatsApp(): void {
    this.flow.dispararWhatsApp();
  }

  protected reiniciarFluxo(): void {
    this.flow.reiniciarFluxo();
    this.router.navigate(['/identificacao']);
  }
}
