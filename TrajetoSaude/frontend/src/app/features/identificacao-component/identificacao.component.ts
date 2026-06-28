import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { TriageFlowService, PacienteRegistro } from '../../services/triage_flow_service';
import { StorageService, PacienteApi } from '../../services/storage.service';

interface PacienteSugerido {
  titulo: string;
  documento: string;
}

type ResultadoBusca = 'pendente' | 'encontrado' | 'nao_encontrado';

@Component({
  selector: 'app-identificacao',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './identificacao.component.html',
  styleUrl: './identificacao.component.css',
})
export class IdentificacaoComponent {
  private readonly flow    = inject(TriageFlowService);
  private readonly storage = inject(StorageService);
  private readonly router  = inject(Router);

  protected readonly sugestoes: PacienteSugerido[] = [
    { titulo: 'Maria Souza — CNS demo', documento: '700123456789012' },
    { titulo: 'João Pereira — CNS demo', documento: '700987654321098' },
  ];

  protected readonly documento      = signal('');
  protected readonly resultadoBusca = signal<ResultadoBusca>('pendente');
  protected readonly carregando     = signal(false);
  protected readonly paciente       = this.flow.pacienteAtual;

  protected aplicarSugestao(sugestao: PacienteSugerido): void {
    this.documento.set(sugestao.documento);
  }

  protected buscarPaciente(): void {
    const sus = this.documento().replace(/\D/g, '');
    if (!sus) return;

    this.carregando.set(true);
    this.resultadoBusca.set('pendente');

    this.storage.buscarPacientePorSus(sus).subscribe({
      next: (api) => {
        this.flow.setPacienteAtual(this.mapearDaApi(api));
        this.flow.setPacienteApiId(api.id);
        this.resultadoBusca.set('encontrado');
        this.carregando.set(false);
      },
      error: () => {
        // Fallback para dados mock (demo sem banco populado)
        const encontrado = this.flow.buscarPaciente(sus);
        this.resultadoBusca.set(encontrado ? 'encontrado' : 'nao_encontrado');
        this.carregando.set(false);
      },
    });
  }

  protected iniciarTriagem(): void {
    this.router.navigate(['/chat']);
  }

  private mapearDaApi(api: PacienteApi): PacienteRegistro {
    const nascimento = api.data_nascimento ? new Date(api.data_nascimento) : null;
    const idade = nascimento
      ? Math.floor((Date.now() - nascimento.getTime()) / (365.25 * 24 * 60 * 60 * 1000))
      : 0;

    let rotaTrabalho: string[] = [];
    if (api.rota_trabalho) {
      try { rotaTrabalho = JSON.parse(api.rota_trabalho); } catch { rotaTrabalho = [api.rota_trabalho]; }
    }

    return {
      nome: api.nome,
      idade,
      cns: api.carteira_sus,
      rg: '',
      bairro: api.cidade ?? api.endereco ?? '',
      rotaTrabalho,
      tempoDeslocamentoMin: 60,
      qtdUbs3km: 2,
      historicoConsultas: [],
      internacoes: [],
      usoApp: {
        cadastradoEm: api.created_at.slice(0, 10),
        ultimoAcesso: api.created_at.slice(0, 10),
        frequenciaUso: 'media',
        lembretesIgnorados: 0,
      },
    };
  }
}
