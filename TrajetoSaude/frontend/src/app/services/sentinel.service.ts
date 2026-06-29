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

@Injectable({ providedIn: 'root' })
export class SentinelService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiBaseUrl}/api/sentinel`;

  /**
   * Envia uma mensagem ao agente Sentinel.AI via API Python (trajeto_api).
   * A autenticação GCP é gerenciada pelo servidor Python com ADC.
   */
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
          return of(`Não foi possível contatar a Sentinel.AI: ${detail}`);
        })
      );
  }

  sentinelPaciente(payload: { mensagem: string; localizacao?: unknown; carteira_sus?: string; nome_paciente?: string }): Observable<SentinelAgentePacienteResponse> {
    return this.http.post<SentinelAgentePacienteResponse>(`${this.base}/sentinelai_paciente`, payload);
  }

  sentinelAgente(payload: {
    nome_paciente?: string;
    endereco_paciente?: string;
    local_trabalho?: string;
    rota_trabalho?: string[];
    endereco_hub: string;
    lat_hub?: number;
    lng_hub?: number;
  }): Observable<SentinelAgenteResponse> {
    return this.http.post<SentinelAgenteResponse>(`${this.base}/sentinelai_agente`, payload);
  }
}
