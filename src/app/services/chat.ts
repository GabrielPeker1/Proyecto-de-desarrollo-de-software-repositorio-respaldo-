import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private baseUrl = '/api/chats';

  constructor(private http: HttpClient) {}

  getAll(idUsuario?: number): Observable<any> {
    let params = new HttpParams();
    if (idUsuario) params = params.set('id_usuario', idUsuario);
    return this.http.get<any>(`${this.baseUrl}/`, { params });
  }

  get(id: number, idUsuario: number): Observable<any> {
    const params = new HttpParams().set('id_usuario', idUsuario);
    return this.http.get<any>(`${this.baseUrl}/${id}/`, { params });
  }
}