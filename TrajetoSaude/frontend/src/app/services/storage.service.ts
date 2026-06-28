import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface PacienteApi {
  id: string;
  usuario_id: string;
  nome: string;
  carteira_sus: string;
  data_nascimento?: string;
  endereco?: string;
  cidade?: string;
  estado?: string;
  cep?: string;
  lat_residencia?: number;
  lng_residencia?: number;
  local_trabalho?: string;
  lat_trabalho?: number;
  lng_trabalho?: number;
  rota_trabalho?: string;
  created_at: string;
}

export interface AgenteApi {
  id: string;
  usuario_id: string;
  nome: string;
  registro_profissional?: string;
  especialidade?: string;
  ubs_vinculada?: string;
  created_at: string;
}

export interface TriagemCreate {
  paciente_id: string;
  agente_id?: string;
  glicemia?: number;
  pressao_sistolica?: number;
  pressao_diastolica?: number;
  risco_probabilidade?: number;
  risco_label?: number;
}

export interface TriagemApi extends TriagemCreate {
  id: string;
  created_at: string;
}

export interface TicketCreate {
  paciente_id: string;
  triagem_id: string;
  ubs_encaminhamento: string;
}

export interface TicketApi {
  id: string;
  paciente_id: string;
  triagem_id: string;
  ubs_encaminhamento: string;
  status: string;
  valido_ate: string;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class StorageService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiBaseUrl}/api/storage`;

  buscarPacientePorSus(carteiraSus: string): Observable<PacienteApi> {
    return this.http.get<PacienteApi>(`${this.base}/pacientes/sus/${carteiraSus}`);
  }

  buscarPacientePorUsuario(usuarioId: string): Observable<PacienteApi> {
    return this.http.get<PacienteApi>(`${this.base}/pacientes/usuario/${usuarioId}`);
  }

  buscarAgentePorUsuario(usuarioId: string): Observable<AgenteApi> {
    return this.http.get<AgenteApi>(`${this.base}/agentes/usuario/${usuarioId}`);
  }

  historicoTriagensPorAgente(agenteId: string): Observable<TriagemApi[]> {
    return this.http.get<TriagemApi[]>(`${this.base}/triagens/agente/${agenteId}`);
  }

  buscarPaciente(pacienteId: string): Observable<PacienteApi> {
    return this.http.get<PacienteApi>(`${this.base}/pacientes/${pacienteId}`);
  }

  criarPaciente(payload: Partial<PacienteApi>): Observable<PacienteApi> {
    return this.http.post<PacienteApi>(`${this.base}/pacientes`, payload);
  }

  atualizarPaciente(id: string, payload: Partial<PacienteApi>): Observable<PacienteApi> {
    return this.http.patch<PacienteApi>(`${this.base}/pacientes/${id}`, payload);
  }

  criarAgente(payload: { usuario_id: string; nome: string; registro_profissional?: string; especialidade?: string; ubs_vinculada?: string }): Observable<unknown> {
    return this.http.post(`${this.base}/agentes`, payload);
  }

  criarTriagem(payload: TriagemCreate): Observable<TriagemApi> {
    return this.http.post<TriagemApi>(`${this.base}/triagens`, payload);
  }

  atualizarPredicao(triagemId: string, prob: number, label: number): Observable<TriagemApi> {
    const params = new HttpParams()
      .set('risco_probabilidade', String(prob))
      .set('risco_label', String(label));
    return this.http.patch<TriagemApi>(`${this.base}/triagens/${triagemId}/predicao`, {}, { params });
  }

  historicoTriagens(pacienteId: string): Observable<TriagemApi[]> {
    return this.http.get<TriagemApi[]>(`${this.base}/triagens/paciente/${pacienteId}`);
  }

  criarTicket(payload: TicketCreate): Observable<TicketApi> {
    return this.http.post<TicketApi>(`${this.base}/tickets`, payload);
  }

  buscarTicket(ticketId: string): Observable<TicketApi> {
    return this.http.get<TicketApi>(`${this.base}/tickets/${ticketId}`);
  }

  utilizarTicket(ticketId: string): Observable<TicketApi> {
    return this.http.post<TicketApi>(`${this.base}/tickets/${ticketId}/utilizar`, {});
  }
}
