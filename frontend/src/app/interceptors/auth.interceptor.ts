import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth';

/**
 * Pasa por todos los pedidos HTTP de la app:
 * 1) Si hay sesión, agrega "Authorization: Bearer <token>" a los pedidos a la API,
 *    así el back sabe quién los hace.
 * 2) Si la API responde 401 (token vencido o inválido), cierra la sesión y
 *    manda al login.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const toastr = inject(ToastrService);

  const token = auth.getToken();
  const esApi = req.url.startsWith('/api/');
  const pedido = token && esApi
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(pedido).pipe(
    catchError((error: HttpErrorResponse) => {
      // El 401 del login es "contraseña incorrecta", no una sesión vencida.
      const esLogin = req.url.startsWith('/api/login/');
      if (error.status === 401 && esApi && !esLogin && auth.estaLogueado()) {
        auth.logout();
        // El back explica el motivo (sesión vencida, cuenta suspendida, dada de baja...).
        const motivo = error.error?.detail ?? error.error?.data;
        toastr.warning(typeof motivo === 'string' ? motivo : 'Tu sesión venció. Iniciá sesión de nuevo.');
        router.navigate(['/login'], { queryParams: { returnUrl: router.url } });
      }
      return throwError(() => error);
    })
  );
};
