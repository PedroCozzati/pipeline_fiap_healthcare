import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

// ── Predição de risco ─────────────────────────────────────────────────────────
export interface RiskRequest {
  Idade: number;
  Tempo_Deslocamento_Min: number;
  Qtd_UBS_Origem_3km: number;
  Glicemia_Aferida: number;
}

export interface RiskResponse {
  risk_probability: number;
  risk_label: number;
  risk_label_texto: string;
  features_usadas: Record<string, number>;
}

// ── Deslocamento (UBS no raio de 3km + tempo estimado) ─────────────────────────
export interface DeslocamentoRequest {
  lat_residencia: number;
  lng_residencia: number;
  lat_trabalho?: number;
  lng_trabalho?: number;
}

export interface DeslocamentoResponse {
  qtd_ubs_3km: number | null;
  tempo_deslocamento_min: number;
  fonte_ubs: 'geo_real' | 'indisponivel';
}

// ── UBS mais próximas ─────────────────────────────────────────────────────────
export interface UbsItem {
  nm_equipamento: string;
  tx_endereco_equipamento: string;
  nm_bairro_equipamento: string;
  latitude: number;
  longitude: number;
  distance_km: number;
}

export interface RouteUbsItem extends UbsItem {
  distance_to_current_km: number;
  distance_to_work_km: number;
  route_score: number;
}

export interface NearestUbsResponse {
  current_location: { latitude: number; longitude: number; location_query: string; matched_by: string };
  nearest_ubs: UbsItem[];
  work_location?: Record<string, unknown>;
  route_ubs?: RouteUbsItem[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiBaseUrl;

  predictRisk(payload: RiskRequest): Observable<RiskResponse> {
    return this.http.post<RiskResponse>(`${this.base}/api/prediction/risk`, payload);
  }

  calcularDeslocamento(payload: DeslocamentoRequest): Observable<DeslocamentoResponse> {
    return this.http.post<DeslocamentoResponse>(`${this.base}/api/prediction/deslocamento`, payload);
  }

  nearestUbs(currentLocation: string, workLocation?: string, limit = 5): Observable<NearestUbsResponse> {
    let params = new HttpParams()
      .set('current_location', currentLocation)
      .set('limit', String(limit));
    if (workLocation) {
      params = params.set('work_location', workLocation);
    }
    return this.http.get<NearestUbsResponse>(`${this.base}/api/prediction/nearest_ubs`, { params });
  }
}
