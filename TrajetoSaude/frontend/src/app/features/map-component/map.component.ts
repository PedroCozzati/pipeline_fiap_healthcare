import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { TriageFlowService } from '../../services/triage_flow_service';
import { ApiService, UbsItem, RouteUbsItem } from '../../services/api.service';

export type UbsDisplay = (UbsItem | RouteUbsItem) & { distancia: string; recomendada: boolean };

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map.component.html',
  styleUrl: './map.component.css',
})
export class MapComponent implements OnInit {
  private readonly flow   = inject(TriageFlowService);
  private readonly api    = inject(ApiService);
  private readonly router = inject(Router);

  protected readonly carregando  = signal(true);
  protected readonly ubsLista    = signal<UbsDisplay[]>([]);
  protected readonly recomendada = signal<UbsDisplay | null>(null);
  protected readonly usouRota    = signal(false);
  protected readonly apiErro     = signal<string | null>(null);

  protected readonly mapUrl = () => {
    const ubs = this.recomendada();
    if (!ubs) return '#';
    return `https://www.google.com/maps/search/?api=1&query=${ubs.latitude},${ubs.longitude}`;
  };

  ngOnInit(): void {
    const paciente = this.flow.pacienteAtual();
    if (!paciente) { this.carregando.set(false); return; }

    const bairro = paciente.bairro;
    const trabalho = paciente.rotaTrabalho.at(-1);

    this.api.nearestUbs(bairro, trabalho, 5).pipe(
      catchError(() => of(null))
    ).subscribe(res => {
      this.carregando.set(false);

      if (!res) {
        this.apiErro.set('API de geolocalização indisponível. Exibindo dados locais.');
        // fallback: use mock logistica
        const mock = this.flow.logistica();
        const fallback: UbsDisplay = {
          nm_equipamento: mock.recomendada.nome,
          tx_endereco_equipamento: mock.recomendada.endereco,
          nm_bairro_equipamento: '',
          latitude: 0, longitude: 0, distance_km: 0,
          distancia: `${mock.recomendada.distanciaMin} min`,
          recomendada: true,
        };
        this.recomendada.set(fallback);
        this.ubsLista.set([fallback]);
        return;
      }

      const fonte = res.route_ubs?.length ? res.route_ubs : res.nearest_ubs;
      this.usouRota.set(!!res.route_ubs?.length);

      const lista: UbsDisplay[] = fonte.map((u, i) => ({
        ...u,
        distancia: `${(u.distance_km ?? (u as RouteUbsItem).distance_to_current_km ?? 0).toFixed(1)} km`,
        recomendada: i === 0,
      }));

      this.ubsLista.set(lista);
      this.recomendada.set(lista[0] ?? null);
    });
  }

  protected avancarParaValidacao(): void {
    const rec = this.recomendada();
    if (rec) {
      this.flow.definirUbsIndicada({
        nome:     rec.nm_equipamento,
        endereco: rec.tx_endereco_equipamento,
        lat:      rec.latitude || undefined,
        lon:      rec.longitude || undefined,
      });
    }
    this.router.navigate(['/validacao']);
  }
}
