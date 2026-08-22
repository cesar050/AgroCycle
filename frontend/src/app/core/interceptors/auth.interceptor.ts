import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../../features/auth/services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  // Si la petición ya trae su propio Authorization (ej. token temporal 2FA), respétalo
  if (req.headers.has('Authorization')) {
    return next(req);
  }

  const authService = inject(AuthService);
  const token = authService.token;
  if (token) {
    const reqConToken = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
    return next(reqConToken);
  }
  return next(req);
};