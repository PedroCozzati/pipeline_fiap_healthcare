import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { TriageFlowService } from '../../services/triage_flow_service';
import { SentinelService, SentinelAgentePayload } from '../../services/sentinel.service';

type UbsAgente = { name: string; description?: string; address: string; cep?: string };

@Component({
  selector: 'app-map',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './map.component.html',
  styleUrl: './map.component.css',
})
export class MapComponent implements OnInit {
  private readonly flow     = inject(TriageFlowService);
  private readonly sentinel = inject(SentinelService);
  private readonly router   = inject(Router);

  protected readonly carregando  = signal(true);
  protected readonly ubsLista    = signal<UbsAgente[]>([]);
  protected readonly recomendada = signal<UbsAgente | null>(null);
  protected readonly apiErro     = signal<string | null>(null);

  protected readonly mapUrl = () => {
    const ubs = this.recomendada();
    if (!ubs) return '#';
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(ubs.address)}`;
  };

  ngOnInit(): void {
    const paciente = this.flow.pacienteAtual();
    if (!paciente) { this.carregando.set(false); return; }

    const payload: SentinelAgentePayload = {
      localizacao_atual: `${paciente.bairro}, São Paulo - SP`,
      rota_trabalho:     paciente.rotaTrabalho,
      local_trabalho:    paciente.rotaTrabalho.at(-1),
      endereco_casa:     `${paciente.bairro}, São Paulo - SP`,
    };
    this.sentinel.sentinelAgente(payload).pipe(
      catchError(() => of(null))
    ).subscribe(res => {
      this.carregando.set(false);

      if (!res || !res.items.length) {
        this.apiErro.set('Agente Sentinel.AI indisponível. Exibindo dados locais.');
        const mock = this.flow.logistica();
        const fallback: UbsAgente = {
          name:    mock.recomendada.nome,
          address: mock.recomendada.endereco,
        };
        this.recomendada.set(fallback);
        this.ubsLista.set([fallback]);
        return;
      }

      this.ubsLista.set(res.items);
      this.recomendada.set(res.items[0]);
    });
  }

  protected selecionarUbs(ubs: UbsAgente): void {
    this.recomendada.set(ubs);
  }

  protected avancarParaValidacao(): void {
    const rec = this.recomendada();
    if (rec) {
      this.flow.definirUbsIndicada({ nome: rec.name, endereco: rec.address });
    }
    this.router.navigate(['/validacao']);
  }
}
