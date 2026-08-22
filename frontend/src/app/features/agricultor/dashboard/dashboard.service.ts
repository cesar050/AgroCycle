import { Injectable } from '@angular/core';
import { Observable, forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { ApiService } from '../../../core/services/api.service';

export interface DashboardData {
  temporada: any;
  temporadaParcela: any;
  estimacion: any;
  clima: any;
  financiero: any;
  actividades: any[];
  tieneFinca: boolean;
}

@Injectable({ providedIn: 'root' })
export class DashboardService {

  constructor(private api: ApiService) {}

    cargarDashboard(): Observable<DashboardData | null> {
    return this.api.get<any>('/temporadas/historial').pipe(
        map(res => res),
        catchError(() => of(null))
    );
    }

  cargarTemporadaActiva(): Observable<any> {
    return this.api.get<any>('/temporadas/activa').pipe(
      catchError(() => of(null))
    );
  }

  cargarEstimacion(temporadaParcelaId: string): Observable<any> {
    return this.api.get<any>(
      `/estimacion/temporada-parcela/${temporadaParcelaId}/estimaciones`
    ).pipe(catchError(() => of(null)));
  }

  cargarFinanciero(temporadaId: string): Observable<any> {
    return this.api.get<any>(
      `/financiero/temporadas/${temporadaId}/rentabilidad`
    ).pipe(catchError(() => of(null)));
  }

  cargarFincas(): Observable<any> {
    return this.api.get<any>('/fincas').pipe(
      catchError(() => of({ fincas: [] }))
    );
  }
}