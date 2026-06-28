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

@Injectable({ providedIn: 'root' })
export class SentinelService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = `${environment.apiBaseUrl}/sentinel/query`;

  /**
   * Envia uma mensagem ao agente Sentinel.AI via API Python (trajeto_api).
   * A autenticação GCP é gerenciada pelo servidor Python com ADC.
   */
  query(mensagem: string, contextoLocalizacao?: string): Observable<string> {
    const input = contextoLocalizacao
      ? `${contextoLocalizacao}\n\nPergunta do paciente: ${mensagem}`
      : mensagem;

    return this.http
      .post<{ output: unknown }>(this.endpoint, { input: { input: input } })
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
}
