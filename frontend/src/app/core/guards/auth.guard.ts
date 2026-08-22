import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../../features/auth/services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.estaAutenticado) {
    router.navigate(['/auth/login']);
    return false;
  }
  return true;
};

export const agricultorGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.estaAutenticado) {
    router.navigate(['/auth/login']);
    return false;
  }

  if (!auth.esAgricultor && !auth.esAdmin) {
    router.navigate(['/']);
    return false;
  }

  return true;
};

export const agronomoGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.estaAutenticado) {
    router.navigate(['/auth/login']);
    return false;
  }

  if (!auth.esAgronomo && !auth.esAdmin) {
    router.navigate(['/']);
    return false;
  }

  return true;
};

export const adminGuard: CanActivateFn = () => {
  const auth   = inject(AuthService);
  const router = inject(Router);

  if (!auth.estaAutenticado) {
    router.navigate(['/auth/login']);
    return false;
  }

  if (!auth.esAdmin) {
    router.navigate(['/']);
    return false;
  }

  return true;
};