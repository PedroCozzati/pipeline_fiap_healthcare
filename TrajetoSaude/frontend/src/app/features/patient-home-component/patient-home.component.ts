import { Component, ElementRef, OnInit, ViewChild, computed, effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';
import { AuthService } from '../../services/auth_service';
import { SentinelService, MensagemChat, SentinelPacientePayload } from '../../services/sentinel.service';
import { MarkdownPipe } from '../../shared/markdown.pipe';

@Component({
  selector: 'app-patient-home',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, MarkdownPipe],
  templateUrl: './patient-home.component.html',
  styleUrl: './patient-home.component.css',
})
export class PatientHomeComponent implements OnInit {
  private readonly flow = inject(TriageFlowService);
  private readonly auth = inject(AuthService);
  private readonly sentinel = inject(SentinelService);
  private readonly router = inject(Router);

  @ViewChild('mensagensEl') private mensagensEl!: ElementRef<HTMLElement>;

  protected readonly nome = () => this.auth.currentUser()?.nome ?? 'paciente';
  protected readonly ticket = this.flow.ticket;
  protected readonly logistica = this.flow.logistica;

  protected readonly localizacao = computed(() => this.auth.currentUser()?.localizacao ?? null);

  protected readonly mensagens = signal<MensagemChat[]>([]);
  protected readonly inputTexto = signal('');
  protected readonly aguardandoResposta = signal(false);

  constructor() {
    effect(() => {
      this.mensagens(); // rastreia mudanças
      setTimeout(() => {
        const el = this.mensagensEl?.nativeElement;
        if (el) el.scrollTop = el.scrollHeight;
      }, 0);
    });
  }

  ngOnInit(): void {
    this.mensagens.set([
      {
        papel: 'ai',
        texto: `Olá, ${this.nome()}! Sou a Sentinel.AI. Posso te ajudar a encontrar uma unidade de saúde próxima ou acompanhar seu atendimento.`,
      },
    ]);
  }

  protected enviarMensagem(texto?: string): void {
    const msg = (texto ?? this.inputTexto()).trim();
    if (!msg || this.aguardandoResposta()) return;

    this.inputTexto.set('');
    this.mensagens.update(m => [...m, { papel: 'user', texto: msg }]);
    this.mensagens.update(m => [...m, { papel: 'ai', texto: '', carregando: true }]);
    this.aguardandoResposta.set(true);

    const user = this.auth.currentUser();
    const loc  = this.localizacao();

    const payload: SentinelPacientePayload = {
      mensagem:      msg,
      nome_paciente: user?.nome,
      endereco_atual: loc?.bairro ? `${loc.bairro}, São Paulo - SP` : undefined,
      endereco_casa:  loc?.bairro ? `${loc.bairro}, São Paulo - SP` : undefined,
      rota_trabalho:  loc?.rotaTrabalho,
      local_trabalho: loc?.rotaTrabalho?.at(-1),
    };

    this.sentinel.sentinelPaciente(payload).subscribe(resp => {
      this.aguardandoResposta.set(false);
      const resposta = typeof resp.output === 'string' ? resp.output : JSON.stringify(resp.output);
      this.mensagens.update(m => [...m.slice(0, -1), { papel: 'ai', texto: resposta }]);
    });
  }

  protected verTicket(): void {
    this.router.navigate(['/paciente/ticket']);
  }
}
