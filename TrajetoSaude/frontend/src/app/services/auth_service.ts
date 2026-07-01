import { Injectable, PLATFORM_ID, computed, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export type UserRole = 'agente' | 'paciente';

export interface CadastroLocalizacao {
  bairro: string;
  rotaTrabalho: string[];
  descricaoRota: string;
}

export interface PerfilAgente {
  cnes: string;
  coren: string;
  unidade: string;
  cargo: string;
}

export interface AuthUser {
  id: string;
  username: string;
  nome: string;
  role: UserRole;
  cns?: string;
  perfilAgente?: PerfilAgente;
  localizacao?: CadastroLocalizacao;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  tipo: string;
  usuario_id: string;
  nome: string;
}

const STORAGE_KEY = 'fiap-health-auth-user';
const TOKEN_KEY = 'fiap-health-jwt';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly isBrowser = isPlatformBrowser(inject(PLATFORM_ID));
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiBaseUrl}/api/auth`;

  readonly currentUser = signal<AuthUser | null>(this.restaurarSessao());
  readonly isAuthenticated = computed(() => this.currentUser() !== null);
  readonly role = computed(() => this.currentUser()?.role ?? null);

  login(email: string, senha: string): Observable<boolean> {
    return this.http.post<LoginResponse>(`${this.base}/login`, { email, senha }).pipe(
      map((resp) => {
        const user: AuthUser = {
          id: resp.usuario_id,
          username: email,
          nome: resp.nome,
          role: resp.tipo === 'agente_saude' ? 'agente' : 'paciente',
        };
        this.currentUser.set(user);
        this.persistirSessao(user);
        this.salvarToken(resp.access_token);
        return true;
      }),
      catchError(() => of(false))
    );
  }

  register(nome: string, email: string, senha: string, tipo: 'paciente' | 'agente_saude'): Observable<boolean> {
    return this.http.post(`${this.base}/register`, { nome, email, senha, tipo }).pipe(
      map(() => true),
      catchError(() => of(false))
    );
  }

  /** Auto-registra e faz login — usado pelos atalhos de demo. */
  loginOuRegistrar(
    nome: string,
    email: string,
    senha: string,
    tipo: 'paciente' | 'agente_saude'
  ): Observable<boolean> {
    return this.login(email, senha).pipe(
      switchMap((ok) => {
        if (ok) return of(true);
        return this.register(nome, email, senha, tipo).pipe(
          switchMap((registered) => (registered ? this.login(email, senha) : of(false)))
        );
      })
    );
  }

  logout(): void {
    this.currentUser.set(null);
    this.persistirSessao(null);
    this.salvarToken(null);
  }

  getToken(): string | null {
    if (!this.isBrowser) return null;
    return localStorage.getItem(TOKEN_KEY);
  }

  homeRouteFor(role: UserRole): string {
    return role === 'agente' ? '/identificacao' : '/paciente';
  }

  private restaurarSessao(): AuthUser | null {
    if (!this.isBrowser) return null;
    const bruto = localStorage.getItem(STORAGE_KEY);
    if (!bruto) return null;
    try {
      return JSON.parse(bruto) as AuthUser;
    } catch {
      return null;
    }
  }

  private persistirSessao(usuario: AuthUser | null): void {
    if (!this.isBrowser) return;
    if (usuario) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(usuario));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }

  private salvarToken(token: string | null): void {
    if (!this.isBrowser) return;
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  }
}
