import { Routes } from '@angular/router';
import { agricultorGuard } from './core/guards/auth.guard';
import { agronomoGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  // Landing pública
  {
    path: '',
    loadComponent: () =>
      import('./pages/landing/landing.component').then(m => m.LandingComponent),
  },

  // Auth
  {
    path: 'auth',
    children: [
      {
        path: 'login',
        loadComponent: () =>
          import('./features/auth/pages/login/login.component').then(m => m.LoginComponent),
      },
      {
        path: 'registro',
        loadComponent: () =>
          import('./features/auth/pages/registro/registro.component').then(m => m.RegistroComponent),
      },
      {
        path: 'recuperar-password',
        loadComponent: () =>
          import('./features/auth/pages/recuperar-password/recuperar-password.component').then(m => m.RecuperarPasswordComponent),
      },
      {
        path: 'reset-password/:token',
        loadComponent: () =>
          import('./features/auth/pages/reset-password/reset-password.component').then(m => m.ResetPasswordComponent),
      },
      {
        path: 'verificar-correo/:token',
        loadComponent: () =>
          import('./features/auth/pages/verificar-correo/verificar-correo.component').then(m => m.VerificarCorreoComponent),
      },
    ]
  },

  // Agricultor — layout con sidebar
  {
    path: 'app',
    canActivate: [agricultorGuard],
    loadComponent: () =>
      import('./layouts/agricultor-layout/agricultor-layout.component').then(m => m.AgricultorLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/agricultor/dashboard/dashboard.component').then(m => m.DashboardComponent),
      },
      {
        path: 'temporada',
        loadComponent: () =>
          import('./features/agricultor/temporada/temporada.component').then(m => m.TemporadaComponent),
      },
      {
        path: 'climatico',
        loadComponent: () =>
          import('./features/agricultor/climatico/climatico.component').then(m => m.ClimaticoComponent),
      },
      {
        path: 'finanzas',
        loadComponent: () =>
          import('./features/agricultor/finanzas/finanzas.component').then(m => m.FinanzasComponent),
      },
      {
        path: 'reportes',
        loadComponent: () =>
          import('./features/agricultor/reportes/reportes.component').then(m => m.ReportesComponent),
      },
      {
        path: 'mapa',
        loadComponent: () =>
          import('./features/agricultor/mapa/mapa.component').then(m => m.MapaComponent),
      },
      {
        path: 'actividades',
        loadComponent: () =>
          import('./features/agricultor/actividades/actividades.component').then(m => m.ActividadesComponent),
      },
      {
        path: 'recomendaciones',
        loadComponent: () =>
          import('./features/agricultor/recomendaciones/recomendaciones.component').then(m => m.RecomendacionesComponent),
      },
      {
        path: 'mapa',
        loadComponent: () =>
          import('./features/agricultor/mapa/mapa.component').then(m => m.MapaComponent),
      },
      {
        path: 'mapa/nueva-finca',
        loadComponent: () =>
          import('./features/agricultor/mapa/pages/nueva-finca/nueva-finca.component').then(m => m.NuevaFincaComponent),
      },
      {
        path: 'mapa/nuevo-lote/:finca_id',
        loadComponent: () =>
          import('./features/agricultor/mapa/pages/nuevo-lote/nuevo-lote.component').then(m => m.NuevoLoteComponent),
      },
      {
        path: 'mapa/nueva-parcela/:lote_id',
        loadComponent: () =>
          import('./features/agricultor/mapa/pages/nueva-parcela/nueva-parcela.component').then(m => m.NuevaParcelaComponent),
      },
      {
        path: 'temporada',
        loadComponent: () =>
          import('./features/agricultor/temporada/temporada.component').then(m => m.TemporadaComponent),
      },
      {
        path: 'temporada/nueva',
        loadComponent: () =>
          import('./features/agricultor/temporada/pages/nueva-temporada/nueva-temporada.component').then(m => m.NuevaTemporadaComponent),
      },
      {
        path: 'temporada/:id',
        loadComponent: () =>
          import('./features/agricultor/temporada/pages/detalle-temporada/detalle-temporada.component').then(m => m.DetalleTemporadaComponent),
      },
      {
          path: 'actividades',
          loadComponent: () =>
            import('./features/agricultor/actividades/actividades.component').then(m => m.ActividadesComponent),
      },
      {
        path: 'climatico',
        loadComponent: () =>
          import('./features/agricultor/climatico/climatico.component').then(m => m.ClimaticoComponent),
      },
      {
        path: 'finanzas',
        loadComponent: () =>
          import('./features/agricultor/finanzas/finanzas.component').then(m => m.FinanzasComponent),
      },
      {
          path: 'reportes',
          loadComponent: () =>
            import('./features/agricultor/reportes/reportes.component').then(m => m.ReportesComponent),
        },
        {
          path: 'recomendaciones',
          loadComponent: () =>
            import('./features/agricultor/recomendaciones/recomendaciones.component').then(m => m.RecomendacionesComponent),
        },
        {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
    ]
  },
      // Dentro del array de rutas:
    {
      path: 'agronomo',
      canActivate: [agronomoGuard],
      loadComponent: () =>
        import('./layouts/agronomo-layout/agronomo-layout.component').then(m => m.AgronomoLayoutComponent),
      children: [
        {
          path: 'dashboard',
          loadComponent: () =>
            import('./features/agronomo/dashboard/agronomo-dashboard.component').then(m => m.AgronomoDashboardComponent),
        },
        {
          path: 'fincas',
          loadComponent: () =>
            import('./features/agronomo/fincas/agronomo-fincas.component').then(m => m.AgronomoFincasComponent),
        },
        {
          path: 'observaciones',
          loadComponent: () =>
            import('./features/agronomo/observaciones/observaciones.component').then(m => m.ObservacionesComponent),
        },
        {
          path: 'recomendaciones',
          loadComponent: () =>
            import('./features/agronomo/recomendaciones/agronomo-recomendaciones.component').then(m => m.AgronomoRecomendacionesComponent),
        },
        {
          path: 'evaluaciones',
          loadComponent: () =>
            import('./features/agronomo/evaluaciones/evaluaciones.component').then(m => m.EvaluacionesComponent),
        },
        {
          path: '',
          redirectTo: 'dashboard',
          pathMatch: 'full',
        },
      ]
    },
    {
  path: 'admin',
  canActivate: [adminGuard],
  loadComponent: () =>
    import('./layouts/admin-layout/admin-layout.component').then(m => m.AdminLayoutComponent),
  children: [
    {
      path: 'dashboard',
      loadComponent: () =>
        import('./features/admin/dashboard/admin-dashboard.component').then(m => m.AdminDashboardComponent),
    },
    {
      path: 'usuarios',
      loadComponent: () =>
        import('./features/admin/usuarios/admin-usuarios.component').then(m => m.AdminUsuariosComponent),
    },
    {
      path: 'fincas',
      loadComponent: () =>
        import('./features/admin/fincas/admin-fincas.component').then(m => m.AdminFincasComponent),
    },
    {
      path: 'sistema',
      loadComponent: () =>
        import('./features/admin/sistema/admin-sistema.component').then(m => m.AdminSistemaComponent),
    },
    { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  ]
},

  { path: '**', redirectTo: '' },
];