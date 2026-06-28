import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, UserRole } from './auth_service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated()) {
    return true;
  }
  return router.parseUrl('/login');
};

export function roleGuard(esperado: UserRole): CanActivateFn {
  return () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    const papel = auth.role();
    if (papel === esperado) {
      return true;
    }
    if (papel === null) {
      return router.parseUrl('/login');
    }
    return router.parseUrl(auth.homeRouteFor(papel));
  };
}
