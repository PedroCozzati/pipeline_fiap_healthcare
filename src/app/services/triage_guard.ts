import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { TriageFlowService } from './triage_flow_service';

/** Garante que o agente identificou o paciente (CNS/RG) antes de iniciar a triagem. */
export const pacienteIdentificadoGuard: CanActivateFn = () => {
  const flow = inject(TriageFlowService);
  const router = inject(Router);

  if (flow.pacienteAtual()) {
    return true;
  }
  return router.parseUrl('/identificacao');
};
