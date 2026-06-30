import { Injectable, computed, signal } from '@angular/core';
import { RiskResponse } from './api.service';
import { TicketApi } from './storage.service';

export interface VitalSigns {
  glicemia: number;
  pressaoSistolica: number;
  pressaoDiastolica: number;
  temperatura: number;
}

export type RiskLevel = 'baixo' | 'alto';

export interface UbsOption {
  nome: string;
  endereco: string;
  distanciaMin: number;
  ocupacao: number;
  lotacao: 'normal' | 'critica';
}

export interface HubRegiao {
  nome: string;
  endereco: string;
  distanciaMin: number;
  regioesAtendidas: string[];
}

export interface HubRecomendado extends HubRegiao {
  noTrajeto: boolean;
}

export interface ConsultaHistorico {
  data: string;
  unidade: string;
  motivo: string;
  resultado: string;
}

export interface InternacaoHistorico {
  data: string;
  motivo: string;
  duracaoDias: number;
}

export interface UsoAplicativo {
  cadastradoEm: string;
  ultimoAcesso: string;
  frequenciaUso: 'alta' | 'media' | 'baixa';
  lembretesIgnorados: number;
}

export interface PacienteRegistro {
  nome: string;
  idade: number;
  cns: string;
  rg: string;
  bairro: string;
  /** Endereço residencial completo, usado na consulta de UBS próximas ao agente Sentinel.AI. */
  enderecoCasa?: string;
  rotaTrabalho: string[];
  tempoDeslocamentoMin: number;
  qtdUbs3km: number;
  historicoConsultas: ConsultaHistorico[];
  internacoes: InternacaoHistorico[];
  usoApp: UsoAplicativo;
}

export type DesfechoJustificativa = 'transporte' | 'visita';

export interface JustificativaOption {
  id: string;
  label: string;
  desfecho: DesfechoJustificativa;
}

export type StatusTicket = 'emitido' | 'em_unidade' | 'expirado';
export type PrioridadeTriagem = 'alta' | 'media' | 'baixa';

export interface TicketInfo {
  token: string;
  emitidoEm: Date;
  status: StatusTicket;
  prioridade: PrioridadeTriagem;
  apiId?: string;
  validoAte?: Date;
}

export type ResultadoCheckin = 'sucesso' | 'expirado' | 'sem_ticket';

export interface AtendimentoHistorico {
  data: string;
  local: string;
  tipo: string;
  resultado: string;
}

export interface LembretePaciente {
  titulo: string;
  mensagem: string;
  prazo: string;
  canal: 'whatsapp' | 'app';
}

const VALIDADE_TICKET_HORAS = 24;

const RELATO_PADRAO =
  'Paciente relata muita sede, visão embaçada e cansaço frequente desde o dia 02/04.';

const SINAIS_PADRAO: VitalSigns = {
  glicemia: 142,
  pressaoSistolica: 130,
  pressaoDiastolica: 85,
  temperatura: 37.2,
};

@Injectable({ providedIn: 'root' })
export class TriageFlowService {
  // ── Paciente atual ────────────────────────────────────────────────────────
  readonly pacienteAtual = signal<PacienteRegistro | null>(null);

  /** ID do paciente no backend (UUID). Null quando veio de mock. */
  readonly pacienteApiId = signal<string | null>(null);

  setPacienteAtual(paciente: PacienteRegistro | null): void {
    this.pacienteAtual.set(paciente);
  }

  setPacienteApiId(id: string | null): void {
    this.pacienteApiId.set(id);
  }

  /** Atualiza o tempo de deslocamento informado pelo agente de saúde durante a triagem. */
  definirTempoDeslocamento(minutos: number): void {
    const atual = this.pacienteAtual();
    if (!atual) return;
    this.pacienteAtual.set({ ...atual, tempoDeslocamentoMin: minutos });
  }

  /** Atualiza a quantidade de UBS em 3km assim que a resposta do agente Sentinel.AI chega. */
  definirQtdUbs3km(quantidade: number): void {
    const atual = this.pacienteAtual();
    if (!atual) return;
    this.pacienteAtual.set({ ...atual, qtdUbs3km: quantidade });
  }

  /** Fallback mock — usado quando o paciente não está cadastrado na API. */
  buscarPaciente(documento: string): boolean {
    const normalizado = documento.replace(/\D/g, '');
    const encontrado = BASE_PACIENTES.find(
      (p) => p.cns.replace(/\D/g, '') === normalizado || p.rg.replace(/\D/g, '') === normalizado
    );
    this.pacienteAtual.set(encontrado ?? null);
    this.pacienteApiId.set(null);
    return !!encontrado;
  }

  // ── Relato de sintomas ────────────────────────────────────────────────────
  readonly relato = signal<string>(RELATO_PADRAO);

  definirRelato(texto: string): void {
    this.relato.set(texto.trim().length ? texto : RELATO_PADRAO);
  }

  // ── Sinais vitais ──────────────────────────────────────────────────────────
  readonly sinaisVitais = signal<VitalSigns>({ ...SINAIS_PADRAO });

  definirSinaisVitais(vitais: VitalSigns): void {
    this.sinaisVitais.set(vitais);
  }

  // ── Resultado da predição (API ML) ────────────────────────────────────────
  readonly ultimaPredicao = signal<RiskResponse | null>(null);

  setUltimaPredicao(predicao: RiskResponse | null): void {
    this.ultimaPredicao.set(predicao);
  }

  // ── Fatores de risco (computed) ───────────────────────────────────────────
  readonly fatoresRisco = computed<string[]>(() => {
    const fatores: string[] = [];
    const v = this.sinaisVitais();

    if (v.glicemia >= 126)
      fatores.push(`Glicemia de ${v.glicemia} mg/dL acima do limite de referência (126 mg/dL)`);
    if (v.pressaoSistolica >= 140 || v.pressaoDiastolica >= 90)
      fatores.push(`Pressão arterial ${v.pressaoSistolica}/${v.pressaoDiastolica} mmHg elevada`);
    if (v.temperatura >= 37.8)
      fatores.push(`Temperatura de ${v.temperatura} °C indica febre`);

    const paciente = this.pacienteAtual();
    if (paciente) {
      if (paciente.internacoes.length > 0) {
        const ultima = paciente.internacoes[0];
        fatores.push(`Histórico de internação em ${ultima.data} por "${ultima.motivo}"`);
      }
      const consultaAlterada = paciente.historicoConsultas.find((c) =>
        /pré-diabetes|limítrofe|alterad/i.test(c.resultado)
      );
      if (consultaAlterada)
        fatores.push(`Consulta de ${consultaAlterada.data} já apontava: "${consultaAlterada.resultado}"`);
      if (paciente.usoApp.frequenciaUso === 'baixa')
        fatores.push(
          `Baixo engajamento no app (${paciente.usoApp.lembretesIgnorados} lembretes ignorados)`
        );
    }
    return fatores;
  });

  readonly nivelRisco = computed<RiskLevel>(() => {
    const predicao = this.ultimaPredicao();
    if (predicao) return predicao.risk_label === 1 ? 'alto' : 'baixo';

    const v = this.sinaisVitais();
    const alteradoVitais =
      v.glicemia >= 126 || v.pressaoSistolica >= 140 || v.pressaoDiastolica >= 90 || v.temperatura >= 37.8;
    const paciente = this.pacienteAtual();
    const alertaHistorico =
      !!paciente && (paciente.internacoes.length > 0 || paciente.usoApp.frequenciaUso === 'baixa');
    return alteradoVitais || alertaHistorico ? 'alto' : 'baixo';
  });

  readonly sugestaoCuidado = computed<string>(() =>
    this.nivelRisco() === 'baixo'
      ? 'Sinais dentro da normalidade. Reforce hidratação, sono regular e reavaliação da glicemia em 90 dias.'
      : 'Pergunte sobre o histórico familiar e reforce a necessidade de acompanhamento contínuo do paciente.'
  );

  // ── Diretório de hubs (fallback local) ────────────────────────────────────
  private readonly diretorioHubs: HubRegiao[] = [
    { nome: 'UBS Jardim Ipanema', endereco: 'Rua das Acácias, 210 — Jardim Ipanema', distanciaMin: 14, regioesAtendidas: ['Jardim Ipanema'] },
    { nome: 'Hub de Saúde — Terminal Barra Funda', endereco: 'Av. Auro Soares de Moura Andrade, 564 — Barra Funda', distanciaMin: 19, regioesAtendidas: ['Vila Esperança'] },
    { nome: 'UBS Vila Esperança', endereco: 'Av. Brasil, 880 — Vila Esperança', distanciaMin: 22, regioesAtendidas: ['Vila Esperança'] },
    { nome: 'Hub de Saúde — Terminal da Luz', endereco: 'Praça da Luz, s/n — Luz', distanciaMin: 24, regioesAtendidas: ['Centro'] },
    { nome: 'UBS Parque das Flores', endereco: 'Rua dos Lírios, 75 — Parque das Flores', distanciaMin: 35, regioesAtendidas: ['Parque das Flores'] },
  ];

  hubsProximos(bairro: string, rotaTrabalho: string[]): HubRecomendado[] {
    const regioesDoCadastro = [bairro, ...rotaTrabalho];
    return this.diretorioHubs
      .map((hub) => ({ ...hub, noTrajeto: hub.regioesAtendidas.some((r) => regioesDoCadastro.includes(r)) }))
      .sort((a, b) => (a.noTrajeto !== b.noTrajeto ? (a.noTrajeto ? -1 : 1) : a.distanciaMin - b.distanciaMin));
  }

  // ── Logística urbana (fallback local) ────────────────────────────────────
  private readonly ubsMaisProxima = { nome: 'UBS Jardim Ipanema', endereco: 'Rua das Acácias, 210 — Jardim Ipanema', distanciaMin: 14 };
  private readonly ubsAlternativa = { nome: 'UBS Vila Esperança', endereco: 'Av. Brasil, 880 — Vila Esperança', distanciaMin: 22 };

  readonly demandaDePico = computed<boolean>(() => {
    const v = this.sinaisVitais();
    return v.glicemia >= 180 || v.pressaoSistolica >= 160;
  });

  readonly logistica = computed(() => {
    const pico = this.demandaDePico();
    const maisProxima: UbsOption = { ...this.ubsMaisProxima, lotacao: pico ? 'critica' : 'normal', ocupacao: pico ? 94 : 56 };
    const alternativa: UbsOption = { ...this.ubsAlternativa, lotacao: 'normal', ocupacao: 63 };
    const recomendada = pico ? alternativa : maisProxima;
    return { maisProxima, alternativa, recomendada, desviada: pico, tempoEstimado: `≈ ${recomendada.distanciaMin} min de deslocamento` };
  });

  readonly ubsIndicada = signal<{ nome: string; endereco: string; lat?: number; lon?: number } | null>(null);

  definirUbsIndicada(ubs: { nome: string; endereco: string; lat?: number; lon?: number } | null): void {
    this.ubsIndicada.set(ubs);
  }

  // ── Prioridade da triagem ─────────────────────────────────────────────────
  readonly prioridadeTriagem = signal<PrioridadeTriagem>('alta');

  setPrioridade(p: PrioridadeTriagem): void {
    this.prioridadeTriagem.set(p);
  }

  // ── Justificativas de exceção ────────────────────────────────────────────
  readonly justificativas: JustificativaOption[] = [
    { id: 'sem-transporte', label: 'Paciente sem meio de transporte disponível', desfecho: 'transporte' },
    { id: 'horario', label: 'Incompatibilidade de horário com a unidade indicada', desfecho: 'transporte' },
    { id: 'recusa-paciente', label: 'Paciente recusa o deslocamento até a unidade', desfecho: 'visita' },
  ];

  readonly justificativaSelecionada = signal<JustificativaOption | null>(null);

  selecionarJustificativa(justificativa: JustificativaOption | null): void {
    this.justificativaSelecionada.set(justificativa);
  }

  readonly modalAlternativo = {
    nome: 'Van do transporte sanitário municipal',
    previsaoChegada: '≈ 15 min',
    observacao: 'Embarque organizado no ponto de apoio mais próximo da residência do paciente.',
  };

  // ── Ticket ────────────────────────────────────────────────────────────────
  readonly ticket = signal<TicketInfo | null>(null);

  emitirTicket(): void {
    const token = `SUS-${Math.floor(100000 + Math.random() * 900000)}`;
    this.ticket.set({ token, emitidoEm: new Date(), status: 'emitido', prioridade: this.prioridadeTriagem() });
  }

  /** Define o ticket a partir da resposta real da API de storage. */
  setTicketFromApi(apiTicket: TicketApi): void {
    this.ticket.set({
      token: `SUS-${apiTicket.id.slice(0, 6).toUpperCase()}`,
      emitidoEm: new Date(apiTicket.created_at),
      status: 'emitido',
      prioridade: this.prioridadeTriagem(),
      apiId: apiTicket.id,
      validoAte: new Date(apiTicket.valido_ate),
    });
  }

  reiniciarFluxo(): void {
    this.pacienteAtual.set(null);
    this.pacienteApiId.set(null);
    this.ultimaPredicao.set(null);
    this.relato.set(RELATO_PADRAO);
    this.sinaisVitais.set({ ...SINAIS_PADRAO });
    this.justificativaSelecionada.set(null);
    this.ubsIndicada.set(null);
    this.prioridadeTriagem.set('alta');
    this.ticket.set(null);
    this.senhaVirtual.set(null);
  }

  // ── Check-in no totem ────────────────────────────────────────────────────
  readonly senhaVirtual = signal<string | null>(null);

  simularTokenExpirado(): void {
    const atual = this.ticket();
    if (!atual) return;
    const emitidoEm = new Date(atual.emitidoEm.getTime() - (VALIDADE_TICKET_HORAS + 1) * 60 * 60 * 1000);
    this.ticket.set({ ...atual, emitidoEm, status: 'expirado' });
    this.senhaVirtual.set(null);
  }

  realizarCheckin(): ResultadoCheckin {
    const atual = this.ticket();
    if (!atual) return 'sem_ticket';

    const validoAte = atual.validoAte ?? new Date(atual.emitidoEm.getTime() + VALIDADE_TICKET_HORAS * 60 * 60 * 1000);
    if (new Date() > validoAte || atual.status === 'expirado') {
      this.ticket.set({ ...atual, status: 'expirado' });
      this.senhaVirtual.set(null);
      return 'expirado';
    }

    const senha = `H-${String(Math.floor(1 + Math.random() * 99)).padStart(2, '0')}`;
    this.senhaVirtual.set(senha);
    this.ticket.set({ ...atual, status: 'em_unidade' });
    return 'sucesso';
  }

  // ── Histórico e lembretes ────────────────────────────────────────────────
  private readonly historicoAnterior: AtendimentoHistorico[] = [
    { data: '18/06/2026', local: 'HUB de Saúde — Terminal Pirituba', tipo: 'Triagem rápida', resultado: 'Pressão arterial 138/88 mmHg — limítrofe' },
  ];

  readonly historicoAtendimentos = computed<AtendimentoHistorico[]>(() => {
    const ticket = this.ticket();
    const historico = [...this.historicoAnterior];
    if (ticket?.status === 'em_unidade') {
      historico.unshift({
        data: ticket.emitidoEm.toLocaleDateString('pt-BR'),
        local: this.logistica().recomendada.nome,
        tipo: 'Triagem rápida no hub de saúde',
        resultado: `Risco classificado como ${this.nivelRisco() === 'alto' ? 'alto' : 'baixo'} — senha ${this.senhaVirtual()}`,
      });
    }
    return historico;
  });

  readonly lembretes = computed<LembretePaciente[]>(() => {
    const lembretes: LembretePaciente[] = [];
    if (this.ticket()?.status === 'em_unidade') {
      lembretes.push({
        titulo: 'Compareça à UBS do seu bairro',
        mensagem: `A triagem do hub classificou seu risco como ${this.nivelRisco() === 'alto' ? 'ALTO' : 'baixo'}. Procure a UBS indicada para uma avaliação completa.`,
        prazo: this.nivelRisco() === 'alto' ? 'em até 7 dias' : 'em até 30 dias',
        canal: 'whatsapp',
      });
    }
    lembretes.push({
      titulo: 'Atualize seus dados de cadastro',
      mensagem: 'Confirme se o seu endereço e a sua rota de trabalho continuam corretos.',
      prazo: 'sem urgência',
      canal: 'app',
    });
    return lembretes;
  });
}

// ── Base mock de fallback (CNS demo) ─────────────────────────────────────────
const BASE_PACIENTES: PacienteRegistro[] = [
  {
    nome: 'Maria Souza', idade: 52, cns: '700123456789012', rg: '34.567.890-1',
    bairro: 'Jaraguá', rotaTrabalho: ['Jaraguá', 'Vila Esperança', 'Centro'],
    tempoDeslocamentoMin: 90, qtdUbs3km: 1,
    historicoConsultas: [
      { data: '15/01/2026', unidade: 'UBS Jardim Ipanema', motivo: 'Consulta de rotina', resultado: 'Glicemia de jejum 118 mg/dL — pré-diabetes' },
      { data: '02/09/2025', unidade: 'UBS Jardim Ipanema', motivo: 'Consulta de rotina', resultado: 'Pressão arterial 138/88 mmHg — limítrofe' },
    ],
    internacoes: [{ data: '20/03/2024', motivo: 'Crise hiperglicêmica', duracaoDias: 2 }],
    usoApp: { cadastradoEm: '10/01/2024', ultimoAcesso: '08/06/2026', frequenciaUso: 'baixa', lembretesIgnorados: 4 },
  },
  {
    nome: 'João Pereira', idade: 38, cns: '700987654321098', rg: '12.345.678-9',
    bairro: 'Santana', rotaTrabalho: ['Santana', 'Centro'],
    tempoDeslocamentoMin: 45, qtdUbs3km: 3,
    historicoConsultas: [
      { data: '22/04/2026', unidade: 'Hub de Saúde Centro', motivo: 'Consulta de rotina', resultado: 'Sinais vitais dentro da normalidade' },
    ],
    internacoes: [],
    usoApp: { cadastradoEm: '05/05/2025', ultimoAcesso: '07/06/2026', frequenciaUso: 'alta', lembretesIgnorados: 0 },
  },
];
