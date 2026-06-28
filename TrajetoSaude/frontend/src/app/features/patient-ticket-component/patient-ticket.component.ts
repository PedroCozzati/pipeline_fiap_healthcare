import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-patient-ticket',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './patient-ticket.component.html',
  styleUrl: './patient-ticket.component.css',
})
export class PatientTicketComponent {
  private readonly flow = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly ticket = this.flow.ticket;

  protected readonly ubsNome     = () => this.flow.ubsIndicada()?.nome     ?? this.flow.logistica().recomendada.nome;
  protected readonly ubsEndereco = () => this.flow.ubsIndicada()?.endereco ?? this.flow.logistica().recomendada.endereco;

  protected readonly rotaUrl = computed(() => {
    const ubs = this.flow.ubsIndicada();
    if (ubs?.lat && ubs?.lon) {
      return `https://www.google.com/maps/search/?api=1&query=${ubs.lat},${ubs.lon}`;
    }
    const endereco = ubs?.endereco ?? this.flow.logistica().recomendada.endereco;
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(endereco)}`;
  });

  protected simularTokenExpirado(): void {
    this.flow.simularTokenExpirado();
  }

  protected aproximarDoTotem(): void {
    this.router.navigate(['/paciente/checkin']);
  }
}
