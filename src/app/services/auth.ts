import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private usuarioSubject = new BehaviorSubject<any>(null);
  usuario$ = this.usuarioSubject.asObservable();

  constructor(private http: HttpClient) {
    const guardado = localStorage.getItem('usuario');
    // Las sesiones guardadas antes de que existiera el token no sirven:
    // el back ya no responde sin él, así que hay que volver a iniciar sesión.
    if (guardado && this.getToken()) {
      this.usuarioSubject.next(JSON.parse(guardado));
    } else {
      this.logout();
    }
  }

  login(email: string, password: string): Observable<any> {
    return this.http.post<any>('/api/login/', { email, password }).pipe(
      tap(res => {
        // El token se manda en cada pedido a la API (ver interceptors/auth.interceptor.ts).
        localStorage.setItem('token', res.token);
        this.usuarioSubject.next(res.data);
        localStorage.setItem('usuario', JSON.stringify(res.data));
      })
    );
  }

  logout(): void {
    this.usuarioSubject.next(null);
    localStorage.removeItem('usuario');
    localStorage.removeItem('token');
  }

  getToken(): string | null {
    return localStorage.getItem('token');
  }

  getUsuarioActual(): any {
    return this.usuarioSubject.value;
  }

  actualizarUsuarioActual(usuario: any): void {
    this.usuarioSubject.next(usuario);
    localStorage.setItem('usuario', JSON.stringify(usuario));
  }

  estaLogueado(): boolean {
    return !!this.usuarioSubject.value;
  }
}
