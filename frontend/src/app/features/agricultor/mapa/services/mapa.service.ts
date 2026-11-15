import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from '../../../../core/services/api.service';

@Injectable({ providedIn: 'root' })
export class MapaService {

  constructor(private api: ApiService) {}

  // Fincas
  listarFincas(): Observable<any> {
    return this.api.get('/fincas');
  }

  registrarFinca(datos: any): Observable<any> {
    return this.api.post('/fincas', datos);
  }

  editarFinca(fincaId: string, datos: any): Observable<any> {
    return this.api.put(`/fincas/${fincaId}`, datos);
  }

  eliminarFinca(fincaId: string): Observable<any> {
    return this.api.delete(`/fincas/${fincaId}`);
  }

  obtenerMapaFinca(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/mapa`);
  }

  // Lotes
  listarLotes(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/lotes`);
  }

  registrarLote(fincaId: string, datos: any): Observable<any> {
    return this.api.post(`/fincas/${fincaId}/lotes`, datos);
  }

  obtenerLote(loteId: string): Observable<any> {
    return this.api.get(`/lotes/${loteId}`);
  }

  editarLote(loteId: string, datos: any): Observable<any> {
    return this.api.put(`/lotes/${loteId}`, datos);
  }

  eliminarLote(loteId: string): Observable<any> {
    return this.api.delete(`/lotes/${loteId}`);
  }

  // Parcelas
  listarParcelas(loteId: string): Observable<any> {
    return this.api.get(`/lotes/${loteId}/parcelas`);
  }

  registrarParcela(loteId: string, datos: any): Observable<any> {
    return this.api.post(`/lotes/${loteId}/parcelas`, datos);
  }

  obtenerParcela(parcelaId: string): Observable<any> {
    return this.api.get(`/parcelas/${parcelaId}`);
  }

  editarParcela(parcelaId: string, datos: any): Observable<any> {
    return this.api.put(`/parcelas/${parcelaId}`, datos);
  }

  eliminarParcela(parcelaId: string): Observable<any> {
    return this.api.delete(`/parcelas/${parcelaId}`);
  }

  // Catálogos
  listarTiposSuelo(): Observable<any> {
    return this.api.get('/tipos-suelo');
  }

  // Topografía
  grillaTopo(parcelaId: string): Observable<any> {
    return this.api.get(`/parcelas/${parcelaId}/grilla-topografica`);
  }

  obtenerTopografiaFinca(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/mapa/topografia`);
  }

  obtenerHumedadFinca(fincaId: string): Observable<any> {
    return this.api.get(`/fincas/${fincaId}/mapa/humedad`);
  }

  obtenerNdviFinca(fincaId: string, fecha?: string): Observable<Blob> {
    return this.api.getBlob(`/fincas/${fincaId}/mapa/ndvi`, { fecha });
  }
}