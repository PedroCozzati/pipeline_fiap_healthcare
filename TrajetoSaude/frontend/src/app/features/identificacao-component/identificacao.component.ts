import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { TriageFlowService, PacienteRegistro } from '../../services/triage_flow_service';
import { StorageService, PacienteApi } from '../../services/storage.service';
import { ApiService } from '../../services/api.service';

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
  private readonly api     = inject(ApiService);
  private readonly router  = inject(Router);

  protected readonly sugestoes: PacienteSugerido[] = [
    { titulo: 'Maria Souza — CNS de exemplo', documento: '700123456789012' },
    { titulo: 'João Pereira — CNS de exemplo', documento: '700987654321098' },
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
        this.mapearDaApi(api).subscribe((paciente) => {
          this.flow.setPacienteAtual(paciente);
          this.flow.setPacienteApiId(api.id);
          this.resultadoBusca.set('encontrado');
          this.carregando.set(false);
        });
      },
      error: () => {
        // Fallback: busca no mock local (pacientes de demonstração)
        const encontrado = this.flow.buscarPaciente(sus);
        this.resultadoBusca.set(encontrado ? 'encontrado' : 'nao_encontrado');
        this.carregando.set(false);
      },
    });
  }

  protected iniciarTriagem(): void {
    this.router.navigateByUrl('/chat');
  }

  /** Valores padrão usados quando o paciente não tem coordenadas/endereço cadastrados ou os serviços falham. */
  private static readonly TEMPO_DESLOCAMENTO_PADRAO = 60;
  /** Mock: usado até a tela de triagem confirmar a contagem real via Vitta.AI (ou se a consulta falhar). */
  private static readonly QTD_UBS_3KM_PADRAO = 1;

  private mapearDaApi(api: PacienteApi): Observable<PacienteRegistro> {
    const nascimento = api.data_nascimento ? new Date(api.data_nascimento) : null;
    const idade = nascimento
      ? Math.floor((Date.now() - nascimento.getTime()) / (365.25 * 24 * 60 * 60 * 1000))
      : 0;

    let rotaTrabalho: string[] = [];
    if (api.rota_trabalho) {
      try { rotaTrabalho = JSON.parse(api.rota_trabalho); } catch { rotaTrabalho = [api.rota_trabalho]; }
    }

    const base: PacienteRegistro = {
      nome: api.nome,
      idade,
      cns: api.carteira_sus,
      rg: '',
      bairro: api.cidade ?? api.endereco ?? '',
      enderecoCasa: [api.endereco, api.cidade, api.estado].filter(Boolean).join(', ') || undefined,
      rotaTrabalho,
      tempoDeslocamentoMin: IdentificacaoComponent.TEMPO_DESLOCAMENTO_PADRAO,
      // Mock inicial; a tela de triagem busca o valor real no Vitta.AI em segundo plano
      // (a busca do paciente não pode ficar travada esperando a IA responder).
      qtdUbs3km: IdentificacaoComponent.QTD_UBS_3KM_PADRAO,
      historicoConsultas: [],
      internacoes: [],
      usoApp: {
        cadastradoEm: api.created_at.slice(0, 10),
        ultimoAcesso: api.created_at.slice(0, 10),
        frequenciaUso: 'media',
        lembretesIgnorados: 0,
      },
    };

    // Tempo de deslocamento é apenas uma sugestão inicial: o agente de saúde
    // confirma/ajusta o valor exato durante a triagem (tela "vitals").
    if (api.lat_residencia == null || api.lng_residencia == null) {
      return of(base);
    }

    return this.api.calcularDeslocamento({
      lat_residencia: api.lat_residencia,
      lng_residencia: api.lng_residencia,
      lat_trabalho: api.lat_trabalho,
      lng_trabalho: api.lng_trabalho,
    }).pipe(
      map((r) => ({
        ...base,
        tempoDeslocamentoMin: r.tempo_deslocamento_min > 0 ? r.tempo_deslocamento_min : base.tempoDeslocamentoMin,
      })),
      catchError(() => of(base))
    );
  }
}
