import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class MensajeService {
  private baseUrl = '/api/mensajes';

  constructor(private http: HttpClient) {}

  getByChat(idChat: number, idUsuario: number): Observable<any> {
    const params = new HttpParams()
      .set('id_chat', idChat)
      .set('id_usuario', idUsuario);
    return this.http.get<any>(`${this.baseUrl}/`, { params });
  }

  create(data: any): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }
}