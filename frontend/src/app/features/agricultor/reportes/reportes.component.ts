import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.scss'
})
export class ReportesComponent implements OnInit {

  cargando     = signal(true);
  descargando  = signal<string | null>(null);
  error        = signal('');

  temporadas   = signal<any[]>([]);
  temporadaId  = signal('');
  tpId         = signal('');

  constructor(private api: ApiService) {}

  ngOnInit() { this.cargarTemporadas(); }

  cargarTemporadas() {
    this.api.get<any>('/temporadas/historial').subscribe({
      next: (res) => {
        const lista = res.temporadas || [];
        this.temporadas.set(lista);
        const activa = lista.find((t: any) => t.estado === 'activa') || lista[0];
        if (activa) {
          this.temporadaId.set(activa.id);
          this.cargarTpId(activa.id);
        }
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false),
    });
  }

  cargarTpId(temporadaId: string) {
    this.api.get<any>(`/financiero/temporadas/${temporadaId}/rentabilidad`).subscribe({
      next: (res) => {
        if (res.parcelas?.length > 0) {
          this.tpId.set(res.parcelas[0].temporada_parcela_id || '');
        }
      },
      error: () => {},
    });
  }

  descargarFicha() {
    if (!this.tpId()) {
      this.error.set('No hay parcela vinculada a esta temporada.');
      return;
    }

    this.descargando.set('ficha');
    this.error.set('');

    // Descargar el PDF directamente
    const url = `http://localhost:5000/api/v1/reportes/temporada-parcela/${this.tpId()}/ficha-tecnica`;
    const token = localStorage.getItem('access_token');

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Error al generar el reporte');
      return res.blob();
    })
    .then(blob => {
      const url  = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href     = url;
      link.download = `ficha-tecnica-${this.temporadaActual?.nombre || 'temporada'}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
      this.descargando.set(null);
    })
    .catch(() => {
      this.descargando.set(null);
      this.error.set('Error al generar el PDF. Intenta de nuevo.');
    });
  }

  cambiarTemporada(id: string) {
    this.temporadaId.set(id);
    this.tpId.set('');
    this.cargarTpId(id);
  }

  get temporadaActual(): any {
    return this.temporadas().find(t => t.id === this.temporadaId());
  }
}