import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';
import { Solicitud } from '../models/solicitud.model';

@Injectable({ providedIn: 'root' })
export class SolicitudService {
  private baseUrl = '/api/solicitudes';
  private actualizacionesSubject = new Subject<void>();
  actualizaciones$ = this.actualizacionesSubject.asObservable();

  constructor(private http: HttpClient) {}

  notificarActualizacion(): void {
    this.actualizacionesSubject.next();
  }

  getAll(filtros?: any): Observable<any> {
    let params = new HttpParams();
    if (filtros) {
      Object.keys(filtros).forEach(k => {
        if (filtros[k] !== null && filtros[k] !== undefined && filtros[k] !== '') {
          params = params.set(k, filtros[k]);
        }
      });
    }
    return this.http.get<any>(`${this.baseUrl}/`, { params });
  }

  get(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}/`);
  }

  create(data: Pick<Solicitud, 'adoptante_id' | 'publicacion_id'>): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }

  aceptar(id: number, idRescatista: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/aceptar/`, {
      id_rescatista: idRescatista
    });
  }

  rechazar(id: number, idRescatista: number, motivo: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/rechazar/`, {
      id_rescatista: idRescatista,
      motivo_rechazo: motivo
    });
  }

  delete(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}/`);
  }
}