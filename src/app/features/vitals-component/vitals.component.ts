import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

@Component({
  selector: 'app-vitals',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vitals.component.html',
  styleUrl: './vitals.component.css',
})
export class VitalsComponent {
  private readonly flow   = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly relato   = this.flow.relato;
  protected readonly paciente = this.flow.pacienteAtual;

  protected readonly glicemia = signal(this.flow.sinaisVitais().glicemia);

  protected analisar(): void {
    // Preserva os outros campos com os valores padrão já existentes
    const atual = this.flow.sinaisVitais();
    this.flow.definirSinaisVitais({ ...atual, glicemia: this.glicemia() });
    this.router.navigate(['/results']);
  }
}
