import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { switchMap, of } from 'rxjs';
import { AuthService, UserRole } from '../../services/auth_service';
import { StorageService } from '../../services/storage.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

interface AtalhoLogin {
  rotulo: string;
  email: string;
  senha: string;
  nome: string;
  tipo: 'paciente' | 'agente_saude';
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly auth    = inject(AuthService);
  private readonly storage = inject(StorageService);
  private readonly http    = inject(HttpClient);
  private readonly router  = inject(Router);

  protected readonly atalhos: AtalhoLogin[] = [
    { rotulo: 'Agente de Saúde (demo)', email: 'agente@demo.trajeto', senha: '123456', nome: 'Camila Rocha', tipo: 'agente_saude' },
    { rotulo: 'Paciente (demo)',         email: 'paciente@demo.trajeto', senha: '123456', nome: 'Maria Souza', tipo: 'paciente' },
  ];

  // ── modo ──────────────────────────────────────────────────────────────────
  protected readonly modo = signal<'login' | 'cadastro'>('login');

  // ── campos login ──────────────────────────────────────────────────────────
  protected readonly email = signal('');
  protected readonly senha = signal('');

  // ── campos cadastro (comuns) ──────────────────────────────────────────────
  protected readonly cadNome  = signal('');
  protected readonly cadEmail = signal('');
  protected readonly cadSenha = signal('');
  protected readonly cadTipo  = signal<'paciente' | 'agente_saude'>('paciente');

  // ── campos agente ─────────────────────────────────────────────────────────
  protected readonly cadCoren       = signal('');
  protected readonly corenValido    = signal<boolean | null>(null);
  protected readonly corenMensagem  = signal('');
  protected readonly validandoCoren = signal(false);

  // ── campos paciente ───────────────────────────────────────────────────────
  protected readonly cadSus           = signal('');
  protected readonly cadNascimento    = signal('');
  protected readonly cadEndereco      = signal('');
  protected readonly cadCidade        = signal('');
  protected readonly cadEstado        = signal('SP');
  protected readonly cadCep           = signal('');
  protected readonly cadLocalTrabalho = signal('');
  /** Bairros/trechos da rota separados por vírgula */
  protected readonly cadRotaTrabalho  = signal('');

  // ── estado ────────────────────────────────────────────────────────────────
  protected readonly erro       = signal('');
  protected readonly sucesso    = signal('');
  protected readonly carregando = signal(false);

  constructor() {
    const papel = this.auth.role();
    if (papel) this.router.navigateByUrl(this.auth.homeRouteFor(papel));
  }

  protected alternarModo(): void {
    this.erro.set(''); this.sucesso.set('');
    this.modo.set(this.modo() === 'login' ? 'cadastro' : 'login');
  }

  // ── Login ─────────────────────────────────────────────────────────────────
  protected entrar(): void {
    if (!this.email().trim() || !this.senha()) return;
    this.erro.set(''); this.carregando.set(true);
    this.auth.login(this.email().trim(), this.senha()).subscribe((ok) => {
      this.carregando.set(false);
      if (!ok) { this.erro.set('E-mail ou senha inválidos.'); return; }
      this.navegarParaHome();
    });
  }

  protected aplicarAtalho(atalho: AtalhoLogin): void {
    this.email.set(atalho.email); this.senha.set(atalho.senha);
    this.erro.set(''); this.carregando.set(true);
    this.auth.loginOuRegistrar(atalho.nome, atalho.email, atalho.senha, atalho.tipo).subscribe((ok) => {
      this.carregando.set(false);
      if (!ok) { this.erro.set('Falha ao entrar com conta demo.'); return; }
      this.navegarParaHome();
    });
  }

  // ── Validação COREN ───────────────────────────────────────────────────────
  protected validarCoren(): void {
    const numero = this.cadCoren().trim();
    if (!numero) return;
    this.validandoCoren.set(true);
    this.corenValido.set(null);
    this.corenMensagem.set('');

    this.http.post<{ valid: boolean; nome: string | null; situacao: string | null }>(
      `${environment.apiBaseUrl}/api/auth/validate-coren`,
      { numero }
    ).subscribe({
      next: (r) => {
        this.validandoCoren.set(false);
        this.corenValido.set(r.valid);
        this.corenMensagem.set(r.situacao ?? (r.valid ? 'Registro válido.' : 'Registro não encontrado.'));
      },
      error: () => {
        this.validandoCoren.set(false);
        this.corenValido.set(null);
        this.corenMensagem.set('Não foi possível validar. Verifique o número.');
      },
    });
  }

  // ── Cadastro ──────────────────────────────────────────────────────────────
  protected cadastrar(): void {
    if (!this.cadNome().trim() || !this.cadEmail().trim() || !this.cadSenha()) return;

    if (this.cadTipo() === 'agente_saude' && this.corenValido() !== true) {
      this.erro.set('Valide o CPF / COREN antes de continuar.'); return;
    }
    if (this.cadTipo() === 'paciente' && !this.cadSus().trim()) {
      this.erro.set('Informe a Carteira do SUS.'); return;
    }

    this.erro.set(''); this.sucesso.set(''); this.carregando.set(true);

    this.auth.register(this.cadNome().trim(), this.cadEmail().trim(), this.cadSenha(), this.cadTipo())
      .pipe(
        switchMap((ok) => {
          if (!ok) return of(null);
          return this.auth.login(this.cadEmail().trim(), this.cadSenha());
        }),
        switchMap((logado) => {
          if (!logado) return of(null);
          const usuarioId = this.auth.currentUser()?.id ?? '';
          const nome      = this.cadNome().trim();

          if (this.cadTipo() === 'agente_saude') {
            return this.storage.criarAgente({
              usuario_id:            usuarioId,
              nome,
              registro_profissional: this.cadCoren().trim(),
              especialidade:         'Agente de Saúde',
            });
          } else {
            const rota = this.cadRotaTrabalho().split(',').map(s => s.trim()).filter(Boolean);
            return this.storage.criarPaciente({
              usuario_id:       usuarioId,
              nome,
              carteira_sus:     this.cadSus().trim(),
              data_nascimento:  this.cadNascimento() || undefined,
              endereco:         this.cadEndereco().trim() || undefined,
              cidade:           this.cadCidade().trim() || undefined,
              estado:           this.cadEstado().trim() || undefined,
              cep:              this.cadCep().trim() || undefined,
              local_trabalho:   this.cadLocalTrabalho().trim() || undefined,
              rota_trabalho:    rota.length ? JSON.stringify(rota) : undefined,
            });
          }
        })
      )
      .subscribe({
        next: (perfil) => {
          this.carregando.set(false);
          if (!perfil) { this.erro.set('Falha no cadastro. E-mail já pode estar em uso.'); return; }
          this.navegarParaHome();
        },
        error: () => {
          this.carregando.set(false);
          this.erro.set('Erro ao criar perfil. Tente novamente.');
        },
      });
  }

  private navegarParaHome(): void {
    this.router.navigateByUrl(this.auth.homeRouteFor(this.auth.role() as UserRole));
  }
}
