import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { JustificativaOption, TriageFlowService } from '../../services/triage_flow_service';

type ModoValidacao = 'inicial' | 'menu-justificativas' | 'modal-recalculado';

@Component({
  selector: 'app-validation',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './validation.component.html',
  styleUrl: './validation.component.css',
})
export class ValidationComponent {
  private readonly flow = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly logistica    = this.flow.logistica;
  protected readonly ubsIndicada  = this.flow.ubsIndicada;
  protected readonly ubsNome      = () => this.flow.ubsIndicada()?.nome     ?? this.flow.logistica().recomendada.nome;
  protected readonly ubsEndereco  = () => this.flow.ubsIndicada()?.endereco ?? this.flow.logistica().recomendada.endereco;
  protected readonly justificativas = this.flow.justificativas;
  protected readonly modalAlternativo = this.flow.modalAlternativo;
  protected readonly justificativaSelecionada = this.flow.justificativaSelecionada;

  protected readonly modo = signal<ModoValidacao>('inicial');

  protected confirmarEEmitirTicket(): void {
    this.flow.emitirTicket();
    this.router.navigate(['/ticket']);
  }

  protected abrirMenuDeJustificativas(): void {
    this.modo.set('menu-justificativas');
  }

  protected escolherJustificativa(justificativa: JustificativaOption): void {
    this.flow.selecionarJustificativa(justificativa);
    this.modo.set(justificativa.desfecho === 'transporte' ? 'modal-recalculado' : 'inicial');

    if (justificativa.desfecho === 'visita') {
      this.router.navigate(['/visita-domiciliar']);
    }
  }

  protected confirmarModalRecalculado(): void {
    this.flow.emitirTicket();
    this.router.navigate(['/ticket']);
  }

  protected voltarParaValidacao(): void {
    this.flow.selecionarJustificativa(null);
    this.modo.set('inicial');
  }
}
