import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Usuario, UsuarioCreate } from '../models/usuario.model';

export type UsuarioUpdate = Partial<Usuario> & {
  provincia?: string;
  departamento?: string;
  ciudad?: string;
  zona_aproximada?: string;
  calle?: string;
  numero?: string;
  piso?: string | null;
};

@Injectable({ providedIn: 'root' })
export class UsuarioService {
  private baseUrl = '/api/usuarios';

  constructor(private http: HttpClient) {}

  getAll(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/`);
  }

  get(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}/`);
  }

  /** Perfil de otro usuario: solo nombre, ubicación y (si es rescatista) descripción. */
  getPerfilPublico(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}/perfil-publico/`);
  }

  create(data: UsuarioCreate): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }

  update(id: number, data: UsuarioUpdate): Observable<any> {
    return this.http.patch<any>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}/`);
  }

  /** Solo para moderadores: el back identifica al moderador por su token. */
  darDeBaja(id: number): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/baja/`, {});
  }

  cambiarPassword(id: number, passwordActual: string, passwordNuevo: string): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/${id}/cambiar-password/`, {
      password_actual: passwordActual,
      password_nueva: passwordNuevo
    });
  }
}