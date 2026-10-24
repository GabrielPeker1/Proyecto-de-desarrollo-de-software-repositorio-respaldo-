import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UbicacionCreate {
  provincia: string;
  departamento: string;
  ciudad: string;
  calle: string;
  numero: string;
  piso?: string;
  zona_aproximada?: string;
}

@Injectable({ providedIn: 'root' })
export class UbicacionService {
  private baseUrl = '/api/ubicaciones';

  constructor(private http: HttpClient) {}

  create(data: UbicacionCreate): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, data);
  }

  delete(id: number): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}/`);
  }

  getDepartamentos(provincia: string): Observable<any> {
    const params = new HttpParams().set('provincia', provincia);
    return this.http.get<any>('/api/departamentos/', { params });
  }

  getLocalidades(provincia: string, departamento: string): Observable<any> {
    const params = new HttpParams().set('provincia', provincia).set('departamento', departamento);
    return this.http.get<any>('/api/localidades/', { params });
  }
}

/**
 * Maneja los tres desplegables encadenados Provincia -> Departamento -> Localidad.
 * Lo usan el registro y el perfil. La localidad se guarda en "ciudad".
 */
export class SelectorUbicacion {
  provincia = '';
  departamento = '';
  ciudad = '';
  departamentos: string[] = [];
  localidades: string[] = [];
  cargandoDepartamentos = false;
  cargandoLocalidades = false;
  error = '';

  constructor(private servicio: UbicacionService, private alCambiar: () => void) {}

  get completa(): boolean {
    return Boolean(this.provincia && this.departamento && this.ciudad);
  }

  /** Carga una ubicación ya guardada y deja seleccionados sus valores si existen en el catálogo. */
  cargar(provincia: string, departamento: string, ciudad: string): void {
    this.provincia = provincia;
    this.elegirProvincia(departamento, ciudad);
  }

  elegirProvincia(departamentoPreferido = '', ciudadPreferida = ''): void {
    this.departamento = '';
    this.ciudad = '';
    this.departamentos = [];
    this.localidades = [];
    this.error = '';
    if (!this.provincia) {
      return;
    }
    const provinciaElegida = this.provincia;
    this.cargandoDepartamentos = true;
    this.servicio.getDepartamentos(provinciaElegida).subscribe({
      next: res => {
        // Si cambiaron de provincia mientras llegaba la respuesta, la ignoramos.
        if (provinciaElegida !== this.provincia) {
          return;
        }
        this.cargandoDepartamentos = false;
        this.departamentos = Array.isArray(res?.data) ? res.data : [];
        const departamento = buscarNombre(this.departamentos, departamentoPreferido);
        if (departamento) {
          this.departamento = departamento;
          this.elegirDepartamento(ciudadPreferida);
        }
        this.alCambiar();
      },
      error: err => {
        console.error('No se pudieron cargar los departamentos.', err);
        this.cargandoDepartamentos = false;
        this.error = 'No se pudieron cargar los departamentos. Verificá que el servidor esté activo.';
        this.alCambiar();
      }
    });
  }

  elegirDepartamento(ciudadPreferida = ''): void {
    this.ciudad = '';
    this.localidades = [];
    this.error = '';
    if (!this.provincia || !this.departamento) {
      return;
    }
    const provinciaElegida = this.provincia;
    const departamentoElegido = this.departamento;
    this.cargandoLocalidades = true;
    this.servicio.getLocalidades(provinciaElegida, departamentoElegido).subscribe({
      next: res => {
        if (provinciaElegida !== this.provincia || departamentoElegido !== this.departamento) {
          return;
        }
        this.cargandoLocalidades = false;
        this.localidades = Array.isArray(res?.data) ? res.data : [];
        this.ciudad = buscarNombre(this.localidades, ciudadPreferida);
        this.alCambiar();
      },
      error: err => {
        console.error('No se pudieron cargar las localidades.', err);
        this.cargandoLocalidades = false;
        this.error = 'No se pudieron cargar las localidades. Verificá que el servidor esté activo.';
        this.alCambiar();
      }
    });
  }
}

/** Busca un nombre en la lista sin importar mayúsculas y devuelve el de la lista ('' si no está). */
export function buscarNombre(lista: string[], nombre: string): string {
  const buscado = (nombre ?? '').trim().toLowerCase();
  return buscado ? lista.find(item => item.toLowerCase() === buscado) ?? '' : '';
}
