import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface MensagemChat {
  papel: 'user' | 'ai';
  texto: string;
  carregando?: boolean;
}

export interface SentinelAgenteResponse {
  items: Array<{ name: string; description?: string; address: string; cep?: string }>;
  output_raw?: string;
}

export interface SentinelAgentePacienteResponse {
  output: string | Record<string, unknown> | null;
  contexto_enviado?: string;
}

export interface SentinelPacientePayload {
  mensagem: string;
  nome_paciente?: string;
  carteira_sus?: string;
  endereco_atual?: string;
  endereco_casa?: string;
  local_trabalho?: string;
  rota_trabalho?: string[];
}

export interface SentinelAgentePayload {
  localizacao_atual: string;
  rota_trabalho?: string[];
  local_trabalho?: string;
  endereco_casa?: string;
}

export interface UbsRaioCasaPayload {
  endereco_casa: string;
}

/** Resposta do agente dedicado sentinel_ai_ubs_per_3km (retorna inteiro direto). */
export interface UbsRaioCasaResponse {
  qtd_ubs: number | null;
  output_raw?: string | null;
}

@Injectable({ providedIn: 'root' })
export class SentinelService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiBaseUrl}/api/sentinel`;

  /** Consulta genérica legada — mantida para compatibilidade. */
  query(mensagem: string, contextoLocalizacao?: string): Observable<string> {
    const input = contextoLocalizacao
      ? `${contextoLocalizacao}\n\nPergunta do paciente: ${mensagem}`
      : mensagem;

    return this.http
      .post<{ output: unknown }>(`${this.base}/query`, { input: { input: input } })
      .pipe(
        map((r) => {
          const out = r?.output;
          if (typeof out === 'string') return out;
          if (out && typeof (out as Record<string, unknown>)['output'] === 'string')
            return (out as Record<string, unknown>)['output'] as string;
          return JSON.stringify(out);
        }),
        catchError((err) => {
          const detail = err?.error?.detail ?? err?.message ?? 'erro desconhecido';
          return of(`Não foi possível contatar a Vitta.AI: ${detail}`);
        })
      );
  }

  sentinelPaciente(payload: SentinelPacientePayload): Observable<SentinelAgentePacienteResponse> {
    return this.http.post<SentinelAgentePacienteResponse>(
      `${this.base}/sentinelai_paciente`,
      payload
    ).pipe(
      catchError((err) => {
        const detail = err?.error?.detail ?? err?.message ?? 'erro desconhecido';
        return of({ output: `Não foi possível contatar a Vitta.AI: ${detail}`, contexto_enviado: undefined });
      })
    );
  }

  sentinelAgente(payload: SentinelAgentePayload): Observable<SentinelAgenteResponse> {
    return this.http.post<SentinelAgenteResponse>(`${this.base}/sentinelai_agente`, payload);
  }

  /** Pergunta ao agente Sentinel (sentinel_ai_ubs_per_3km) quantas UBS existem num raio de 3km da residência do paciente. Retorna inteiro diretamente. */
  ubsRaioCasa(payload: UbsRaioCasaPayload): Observable<UbsRaioCasaResponse> {
    return this.http.post<UbsRaioCasaResponse>(`${this.base}/ubs_raio_casa`, payload).pipe(
      catchError(() => of({ qtd_ubs: null } as UbsRaioCasaResponse))
    );
  }
}
