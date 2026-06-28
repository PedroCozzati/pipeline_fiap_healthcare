import { Routes } from '@angular/router';
import { authGuard, roleGuard } from './services/auth_guard';
import { pacienteIdentificadoGuard } from './services/triage_guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./features/login-component/login.component').then((m) => m.LoginComponent)
  },

  // ---- Fluxo do agente de saúde -------------------------------------------
  {
    path: 'identificacao',
    canActivate: [authGuard, roleGuard('agente')],
    loadComponent: () =>
      import('./features/identificacao-component/identificacao.component').then((m) => m.IdentificacaoComponent)
  },
  {
    path: 'chat',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () => import('./features/chat-component/chat.component').then((m) => m.ChatComponent)
  },
  {
    path: 'vitals',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () => import('./features/vitals-component/vitals.component').then((m) => m.VitalsComponent)
  },
  {
    path: 'results',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () => import('./features/results-component/results.component').then((m) => m.ResultsComponent)
  },
  {
    path: 'cuidados-preventivos',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () =>
      import('./features/preventive-care-component/preventive-care.component').then((m) => m.PreventiveCareComponent)
  },
  {
    path: 'map',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () => import('./features/map-component/map.component').then((m) => m.MapComponent)
  },
  {
    path: 'validacao',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () =>
      import('./features/validation-component/validation.component').then((m) => m.ValidationComponent)
  },
  {
    path: 'visita-domiciliar',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () =>
      import('./features/home-visit-component/home-visit.component').then((m) => m.HomeVisitComponent)
  },
  {
    path: 'ticket',
    canActivate: [authGuard, roleGuard('agente'), pacienteIdentificadoGuard],
    loadComponent: () => import('./features/ticket-component/ticket.component').then((m) => m.TicketComponent)
  },

  // ---- Páginas do agente de saúde -----------------------------------------
  {
    path: 'agente/historico',
    canActivate: [authGuard, roleGuard('agente')],
    loadComponent: () =>
      import('./features/agent-history-component/agent-history.component').then((m) => m.AgentHistoryComponent)
  },
  {
    path: 'agente/perfil',
    canActivate: [authGuard, roleGuard('agente')],
    loadComponent: () =>
      import('./features/agent-profile-component/agent-profile.component').then((m) => m.AgentProfileComponent)
  },

  // ---- Fluxo do paciente ---------------------------------------------------
  {
    path: 'paciente',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-home-component/patient-home.component').then((m) => m.PatientHomeComponent)
  },
  {
    path: 'paciente/ticket',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-ticket-component/patient-ticket.component').then((m) => m.PatientTicketComponent)
  },
  {
    path: 'paciente/checkin',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-checkin-component/patient-checkin.component').then((m) => m.PatientCheckinComponent)
  },
  {
    path: 'paciente/historico',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-history-component/patient-history.component').then((m) => m.PatientHistoryComponent)
  },
  {
    path: 'paciente/notificacoes',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-notifications-component/patient-notifications.component').then((m) => m.PatientNotificationsComponent)
  },
  {
    path: 'paciente/perfil',
    canActivate: [authGuard, roleGuard('paciente')],
    loadComponent: () =>
      import('./features/patient-profile-component/patient-profile.component').then((m) => m.PatientProfileComponent)
  }
];
