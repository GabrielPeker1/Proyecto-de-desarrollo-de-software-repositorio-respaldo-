import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Alerta {
  id_alerta: number;
  tipo: 'ADVERTENCIA' | 'SUSPENSION' | 'STRIKE';
  mensaje: string;
  fecha_alerta: string;
  leida: boolean;
}

/** Avisos que le manda un moderador al usuario (advertencias, suspensiones y strikes). */
@Injectable({ providedIn: 'root' })
export class AlertaService {
  private baseUrl = '/api/alertas';

  constructor(private http: HttpClient) {}

  getNoLeidas(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/`, { params: { leida: 'false' } });
  }

  marcarLeida(id: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/leida/`, {});
  }
}
