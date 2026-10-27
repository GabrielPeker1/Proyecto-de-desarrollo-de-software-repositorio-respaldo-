import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Publicacion } from '../models/publicacion.model';

@Injectable({ providedIn: 'root' })
export class PublicacionService {
  private baseUrl = '/api/publicaciones';

  constructor(private http: HttpClient) {}

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

  /** Departamentos de la provincia que tienen mascotas en adopción. */
  getDepartamentos(provincia: string): Observable<any> {
    const params = new HttpParams().set('provincia', provincia);
    return this.http.get<any>(`${this.baseUrl}/departamentos/`, { params });
  }

  /** Localidades del departamento que tienen mascotas en adopción. */
  getLocalidades(provincia: string, departamento: string): Observable<any> {
    const params = new HttpParams().set('provincia', provincia).set('departamento', departamento);
    return this.http.get<any>(`${this.baseUrl}/localidades/`, { params });
  }

  get(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}/`);
  }

  create(data: Pick<Publicacion, 'rescatista_id' | 'animal_id'> & Partial<Pick<Publicacion, 'descripcion' | 'estado'>>): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }

  update(id: number, data: any): Observable<any> {
    return this.http.patch<any>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: number, idRescatista: number): Observable<any> {
    const params = new HttpParams().set('id_rescatista', idRescatista);
    return this.http.delete<any>(`${this.baseUrl}/${id}/`, { params });
  }
}