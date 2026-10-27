import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth';

export const authenticatedOnlyGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.getUsuarioActual()?.id_usuario) {
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  }
  return true;
};

export const rescuerOnlyGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const usuario = auth.getUsuarioActual();
  const rol = String(usuario?.tipo_usuario?.nombre ?? '').toLocaleLowerCase();

  if (!usuario?.id_usuario) {
    return router.createUrlTree(['/login'], { queryParams: { returnUrl: state.url } });
  }
  if (rol !== 'rescatista') {
    return router.createUrlTree(['/publicaciones']);
  }
  return true;
};
