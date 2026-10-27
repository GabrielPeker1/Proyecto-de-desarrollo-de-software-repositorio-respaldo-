import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

/** Acciones del moderador sobre un reporte (ver GestionarReporteView en el back). */
export type AccionReporte = 'revisar' | 'ignorar' | 'advertir' | 'suspender' | 'strike';

/** Las mismas categorías que Reportes.CATEGORIAS en el back. */
export const CATEGORIAS_REPORTE = [
  { valor: 'INSULTOS', texto: 'Insultos o lenguaje ofensivo' },
  { valor: 'ACOSO', texto: 'Acoso' },
  { valor: 'ESTAFA', texto: 'Posible estafa' },
  { valor: 'SPAM', texto: 'Spam' },
  { valor: 'CONTENIDO_INAPROPIADO', texto: 'Contenido inapropiado' },
  { valor: 'OTRO', texto: 'Otro' },
];

export function textoCategoria(valor: string): string {
  return CATEGORIAS_REPORTE.find(c => c.valor === valor)?.texto ?? 'Otro';
}

export interface DatosResolucion {
  mensaje?: string;
  dias?: number;
  nota?: string;
}

@Injectable({ providedIn: 'root' })
export class ReporteService {
  private baseUrl = '/api/reportes';

  constructor(private http: HttpClient) {}

  /**
   * El que reporta sale del token: solo se manda a quién y por qué.
   * Con idPublicacion el reporte es sobre esa publicación (el back usa a su rescatista como reportado).
   */
  reportar(idUsuarioReportado: number, categoria: string, motivo: string,
           idPublicacion: number | null = null): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, {
      usuario_reportado_id: idUsuarioReportado,
      categoria,
      motivo,
      publicacion_id: idPublicacion
    });
  }

  /** El moderador ve todos; el resto solo los que hizo. */
  getAll(filtros?: { pendientes?: boolean; estado?: string }): Observable<any> {
    let params = new HttpParams();
    if (filtros?.pendientes) {
      params = params.set('pendientes', 'true');
    }
    if (filtros?.estado) {
      params = params.set('estado', filtros.estado);
    }
    return this.http.get<any>(`${this.baseUrl}/`, { params });
  }

  /** Solo moderadores. */
  gestionar(id: number, accion: AccionReporte, datos: DatosResolucion = {}): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/${accion}/`, datos);
  }
}
