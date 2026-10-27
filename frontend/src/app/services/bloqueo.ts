import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Bloqueo {
  id_bloqueo: number;
  fecha_bloqueo: string;
  estado: 'ACTIVO' | 'ANULADO';
  usuario_bloqueador: { id_usuario: number; nombre_completo: string; tipo_usuario: string };
  usuario_bloqueado: { id_usuario: number; nombre_completo: string; tipo_usuario: string };
}

/**
 * Bloquear a otro usuario: no se pueden mandar mensajes ni solicitudes entre
 * los dos y no se ven sus publicaciones. No hace falta reportarlo.
 */
@Injectable({ providedIn: 'root' })
export class BloqueoService {
  private baseUrl = '/api/bloqueos';

  constructor(private http: HttpClient) {}

  /** Los bloqueos donde participa el usuario del token (los que hizo y los que recibió). */
  getMios(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/`);
  }

  /** El que bloquea sale del token. */
  bloquear(idUsuario: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, { usuario_bloqueado_id: idUsuario });
  }

  desbloquear(idBloqueo: number): Observable<any> {
    return this.http.patch<any>(`${this.baseUrl}/${idBloqueo}/`, { estado: 'ANULADO' });
  }

  /** El bloqueo activo que yo le hice a otro usuario, si existe. */
  static buscarHecho(bloqueos: Bloqueo[], yo: number, otro: number): Bloqueo | null {
    return bloqueos.find(b => b.estado === 'ACTIVO'
      && b.usuario_bloqueador.id_usuario === yo && b.usuario_bloqueado.id_usuario === otro) ?? null;
  }

  /** True si el otro usuario me bloqueó a mí. */
  static meBloqueo(bloqueos: Bloqueo[], yo: number, otro: number): boolean {
    return bloqueos.some(b => b.estado === 'ACTIVO'
      && b.usuario_bloqueador.id_usuario === otro && b.usuario_bloqueado.id_usuario === yo);
  }
}
