import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-patient-notifications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './patient-notifications.component.html',
  styleUrl: './patient-notifications.component.css',
})
export class PatientNotificationsComponent {
  private readonly flow = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly lembretes = this.flow.lembretes;

  protected voltarInicio(): void {
    this.router.navigate(['/paciente']);
  }
}
