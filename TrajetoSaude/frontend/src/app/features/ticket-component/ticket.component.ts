import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { switchMap, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { AuthService } from '../../services/auth_service';
import { TriageFlowService } from '../../services/triage_flow_service';
import { StorageService } from '../../services/storage.service';
import QRCode from 'qrcode';

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
  private readonly auth    = inject(AuthService);
  private readonly router  = inject(Router);

  protected readonly ticket      = this.flow.ticket;
  protected readonly carregando  = signal(false);
  protected readonly qrDataUrl   = signal<string>('');
  protected readonly ubsNome     = () => this.flow.ubsIndicada()?.nome     ?? this.flow.logistica().recomendada.nome;
  protected readonly ubsEndereco = () => this.flow.ubsIndicada()?.endereco ?? this.flow.logistica().recomendada.endereco;
  protected readonly prioridade  = this.flow.prioridadeTriagem;

  protected readonly labelPrioridade = () => {
    const p = this.prioridade();
    if (p === 'alta')  return 'Alta';
    if (p === 'media') return 'Média';
    return 'Baixa';
  };

  protected readonly classePrioridade = () => {
    const p = this.prioridade();
    if (p === 'alta')  return 'badge-prioridade alta';
    if (p === 'media') return 'badge-prioridade media';
    return 'badge-prioridade baixa';
  };

  ngOnInit(): void {
    const pacienteId = this.flow.pacienteApiId();

    if (pacienteId) {
      this.criarTicketViaApi(pacienteId);
    } else if (!this.ticket()) {
      this.flow.emitirTicket();
      this.gerarQrCode();
    } else {
      this.gerarQrCode();
    }
  }

  private criarTicketViaApi(pacienteId: string): void {
    this.carregando.set(true);
    const vitais   = this.flow.sinaisVitais();
    const predicao = this.flow.ultimaPredicao();
    const ubs      = this.flow.ubsIndicada() ?? this.flow.logistica().recomendada;
    const usuarioId = this.auth.currentUser()?.id;

    const criarTriagem = (agenteId?: string) => this.storage.criarTriagem({
      paciente_id:         pacienteId,
      agente_id:           agenteId,
      glicemia:            vitais.glicemia,
      pressao_sistolica:   vitais.pressaoSistolica,
      pressao_diastolica:  vitais.pressaoDiastolica,
      risco_probabilidade: predicao?.risk_probability,
      risco_label:         predicao?.risk_label,
    });

    const triagem$ = usuarioId
      ? this.storage.buscarAgentePorUsuario(usuarioId).pipe(
          catchError(() => of(null)),
          switchMap((agente) => criarTriagem(agente?.id))
        )
      : criarTriagem();

    triagem$.pipe(
      switchMap((triagem) =>
        this.storage.criarTicket({
          paciente_id:        pacienteId,
          triagem_id:         triagem.id,
          ubs_encaminhamento: `${ubs.nome} — ${ubs.endereco}`,
        })
      )
    ).subscribe({
      next: (ticket) => {
        this.flow.setTicketFromApi(ticket);
        this.carregando.set(false);
        this.gerarQrCode();
      },
      error: () => {
        this.flow.emitirTicket();
        this.carregando.set(false);
        this.gerarQrCode();
      },
    });
  }

  private async gerarQrCode(): Promise<void> {
    const t        = this.ticket();
    const paciente = this.flow.pacienteAtual();
    const cns      = paciente?.cns ?? 'SEM-CNS';
    const ubs      = this.ubsNome();
    const prior    = this.flow.prioridadeTriagem();
    const token    = t?.token ?? 'SEM-TOKEN';

    const conteudo = `${token}|${ubs}|${cns}|${prior}`;

    try {
      const url = await QRCode.toDataURL(conteudo, {
        width: 220,
        margin: 2,
        color: { dark: '#1a1a2e', light: '#ffffff' },
        errorCorrectionLevel: 'M',
      });
      this.qrDataUrl.set(url);
    } catch {
      // silently fail — ticket ainda é exibido sem QR
    }
  }

  protected reiniciarFluxo(): void {
    this.flow.reiniciarFluxo();
    this.router.navigate(['/identificacao']);
  }
}
