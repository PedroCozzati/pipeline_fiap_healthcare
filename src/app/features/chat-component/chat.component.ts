import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService } from '../../services/triage_flow_service';

interface SintomaSugerido {
  titulo: string;
  relato: string;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent {
  private readonly flow = inject(TriageFlowService);
  private readonly router = inject(Router);

  protected readonly sugestoes: SintomaSugerido[] = [
    {
      titulo: 'Sede excessiva e visão embaçada',
      relato: 'Paciente relata muita sede, visão embaçada e cansaço frequente desde o dia 02/04.'
    },
    {
      titulo: 'Dor de cabeça e febre leve',
      relato: 'Paciente relata dor de cabeça constante, febre baixa e mal-estar há dois dias.'
    },
    {
      titulo: 'Falta de ar e palpitações',
      relato: 'Paciente relata falta de ar ao caminhar, palpitações e pressão alta nos últimos registros.'
    }
  ];

  protected readonly paciente = this.flow.pacienteAtual;
  protected readonly relato = signal(this.flow.relato());
  protected readonly enviado = signal(false);

  protected aplicarSugestao(sugestao: SintomaSugerido): void {
    this.relato.set(sugestao.relato);
  }

  protected enviarRelato(): void {
    if (!this.relato().trim()) {
      return;
    }
    this.flow.definirRelato(this.relato());
    this.enviado.set(true);
  }

  protected avancarParaSinaisVitais(): void {
    this.router.navigate(['/vitals']);
  }
}
