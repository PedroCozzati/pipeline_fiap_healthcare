import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { ResultadoCheckin, TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-patient-checkin',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './patient-checkin.component.html',
  styleUrl: './patient-checkin.component.css',
})
export class PatientCheckinComponent {
  private readonly flow = inject(TriageFlowService);

  protected readonly ticket = this.flow.ticket;
  protected readonly senhaVirtual = this.flow.senhaVirtual;

  protected readonly resultado = signal<ResultadoCheckin | null>(null);

  protected lerQrCode(): void {
    this.resultado.set(this.flow.realizarCheckin());
  }
}
