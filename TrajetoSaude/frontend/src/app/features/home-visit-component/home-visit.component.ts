import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-home-visit',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './home-visit.component.html',
  styleUrl: './home-visit.component.css',
})
export class HomeVisitComponent {
  private readonly flow = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly justificativa = this.flow.justificativaSelecionada;

  protected reiniciarFluxo(): void {
    this.flow.reiniciarFluxo();
    this.router.navigate(['/identificacao']);
  }
}
