import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Animal, AnimalCreate } from '../models/animal.model';

@Injectable({ providedIn: 'root' })
export class AnimalService {
  private baseUrl = '/api/animales';

  constructor(private http: HttpClient) {}

  getAll(): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/`);
  }

  get(id: number): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/${id}/`);
  }

  create(data: AnimalCreate): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }

  uploadFotos(id: number, archivos: File[]): Observable<any> {
    const formData = new FormData();
    archivos.forEach(archivo => formData.append('imagenes', archivo, archivo.name));
    return this.http.post<any>(`${this.baseUrl}/${id}/fotos/`, formData);
  }

  update(id: number, data: Animal): Observable<any> {
    return this.http.patch<any>(`${this.baseUrl}/${id}/`, data);
  }

  delete(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}/`);
  }
}