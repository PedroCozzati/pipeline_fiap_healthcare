import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

interface RiskResult {
  risk_probability: number;
  risk_label: number;
  risk_label_texto: string;
  features_usadas: Record<string, number>;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <h1>Trajeto Saúde</h1>
      <p class="status">Gateway: {{ apiUrl }} — status: {{ gatewayStatus }}</p>

      <form (ngSubmit)="predict()">
        <label for="idade">Idade</label>
        <input id="idade" type="number" [(ngModel)]="form.Idade" name="idade" required>

        <label for="tempo">Tempo de deslocamento (min)</label>
        <input id="tempo" type="number" [(ngModel)]="form.Tempo_Deslocamento_Min" name="tempo" required>

        <label for="ubs">UBS num raio de 3 km</label>
        <input id="ubs" type="number" [(ngModel)]="form.Qtd_UBS_Origem_3km" name="ubs" required>

        <label for="glicemia">Glicemia aferida (mg/dL)</label>
        <input id="glicemia" type="number" [(ngModel)]="form.Glicemia_Aferida" name="glicemia" required>

        <button type="submit" [disabled]="loading">Calcular risco</button>
      </form>

      <p class="error" *ngIf="error">{{ error }}</p>

      <div class="result" *ngIf="result">
        <strong>{{ result.risk_label_texto }}</strong>
        <p>Probabilidade: {{ result.risk_probability | percent:'1.0-1' }}</p>
      </div>
    </div>
  `,
})
export class AppComponent {
  private http = inject(HttpClient);

  apiUrl = (window as any).__env?.API_URL ?? 'http://localhost:8000';
  gatewayStatus = 'verificando...';
  loading = false;
  error = '';
  result: RiskResult | null = null;

  form = {
    Idade: 45,
    Tempo_Deslocamento_Min: 90,
    Qtd_UBS_Origem_3km: 2,
    Glicemia_Aferida: 130,
  };

  constructor() {
    this.http.get<{ status: string }>(`${this.apiUrl}/health`).subscribe({
      next: (data) => (this.gatewayStatus = data.status),
      error: () => (this.gatewayStatus = 'indisponível'),
    });
  }

  predict(): void {
    this.loading = true;
    this.error = '';
    this.result = null;

    this.http.post<RiskResult>(`${this.apiUrl}/api/prediction/risk`, this.form).subscribe({
      next: (data) => {
        this.result = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err?.error?.detail ?? 'Falha ao consultar predição.';
        this.loading = false;
      },
    });
  }
}
