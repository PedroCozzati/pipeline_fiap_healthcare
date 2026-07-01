import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-preventive-care',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './preventive-care.component.html',
  styleUrl: './preventive-care.component.css',
})
export class PreventiveCareComponent {
  private readonly flow   = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly sugestao      = this.flow.sugestaoCuidado;
  protected readonly vitais        = this.flow.sinaisVitais;
  protected readonly paciente      = this.flow.pacienteAtual;
  protected readonly fatoresRisco  = this.flow.fatoresRisco;

  /** Glicemia ≥ 126 mesmo com risco de evasão baixo → alerta clínico */
  protected readonly glicemiaElevada = () => this.flow.sinaisVitais().glicemia >= 126;

  protected reiniciarFluxo(): void {
    this.flow.reiniciarFluxo();
    this.router.navigate(['/identificacao']);
  }
}
