import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { PublicacionService } from '../../services/publicacion';
import { Publicacion } from '../../models/publicacion.model';
import { AuthService } from '../../services/auth';
import { ToastrService } from 'ngx-toastr';
import { PROVINCIAS_ARGENTINAS } from '../../data/provincias';
import { buscarNombre } from '../../services/ubicacion';

@Component({
  selector: 'app-publicacion-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './publicacion-list.html',
  styleUrls: ['./publicacion-list.css']
})
export class PublicacionList implements OnInit {
  publicaciones: Publicacion[] = [];
  eliminandoPublicaciones = new Set<number>();
  readonly provincias = PROVINCIAS_ARGENTINAS;
  // Las listas solo traen lugares que tienen mascotas en adopción.
  departamentos: string[] = [];
  localidades: string[] = [];
  provincia = '';
  departamento = '';
  localidad = '';

  constructor(
    private publicacionService: PublicacionService,
    private changeDetector: ChangeDetectorRef,
    private auth: AuthService,
    private toastr: ToastrService
  ) {}

  ngOnInit(): void {
    // Al adoptante le preseleccionamos siempre su provincia y, si hay publicaciones
    // ahí, también su departamento y su localidad.
    const ubicacion = this.auth.getUsuarioActual()?.ubicacion;
    if (!this.esRescatista && ubicacion?.provincia) {
      this.provincia = ubicacion.provincia;
      this.cambiarProvincia(ubicacion.departamento ?? '', ubicacion.ciudad ?? '');
      return;
    }
    this.cargarPublicaciones();
  }

  get esRescatista(): boolean {
    return String(this.auth.getUsuarioActual()?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'rescatista';
  }

  cargarPublicaciones(): void {
    const usuario = this.auth.getUsuarioActual();
    const filtros = this.esRescatista
      ? { id_rescatista: usuario.id_usuario }
      : { estado: 'EN_ADOPCION', provincia: this.provincia, departamento: this.departamento, localidad: this.localidad };
    this.publicacionService.getAll(filtros).subscribe({
      next: (res) => {
        const data = Array.isArray(res?.data) ? res.data : Array.isArray(res) ? res : [];
        this.publicaciones = data;
        this.changeDetector.detectChanges();
      },
      error: (err) => {
        console.error('No se pudieron cargar las publicaciones.', err);
        this.changeDetector.detectChanges();
      }
    });
  }

  get hayFiltros(): boolean {
    return Boolean(this.provincia || this.departamento || this.localidad);
  }

  // Los "preferidos" son los del adoptante al entrar a Inicio. Mientras haya uno
  // pendiente de preseleccionar, esperamos a tener la lista para cargar una sola vez.
  cambiarProvincia(departamentoPreferido = '', localidadPreferida = ''): void {
    this.departamento = '';
    this.localidad = '';
    this.departamentos = [];
    this.localidades = [];
    if (!this.provincia) {
      this.cargarPublicaciones();
      return;
    }
    if (!departamentoPreferido) {
      this.cargarPublicaciones();
    }
    const provinciaElegida = this.provincia;
    this.publicacionService.getDepartamentos(provinciaElegida).subscribe({
      next: (res) => {
        // Si el usuario cambió de provincia mientras llegaba la respuesta, la ignoramos.
        if (provinciaElegida !== this.provincia) {
          return;
        }
        this.departamentos = Array.isArray(res?.data) ? res.data : [];
        if (departamentoPreferido) {
          // Solo lo seleccionamos si hay publicaciones ahí (si está en la lista).
          this.departamento = buscarNombre(this.departamentos, departamentoPreferido);
          if (this.departamento) {
            this.cambiarDepartamento(localidadPreferida);
          } else {
            this.cargarPublicaciones();
          }
        }
        this.changeDetector.detectChanges();
      },
      error: (err) => {
        console.error('No se pudieron cargar los departamentos.', err);
        this.toastr.error('No se pudieron cargar los departamentos.');
        if (departamentoPreferido) {
          this.cargarPublicaciones();
        }
      }
    });
  }

  cambiarDepartamento(localidadPreferida = ''): void {
    this.localidad = '';
    this.localidades = [];
    if (!this.departamento) {
      this.cargarPublicaciones();
      return;
    }
    if (!localidadPreferida) {
      this.cargarPublicaciones();
    }
    const provinciaElegida = this.provincia;
    const departamentoElegido = this.departamento;
    this.publicacionService.getLocalidades(provinciaElegida, departamentoElegido).subscribe({
      next: (res) => {
        if (provinciaElegida !== this.provincia || departamentoElegido !== this.departamento) {
          return;
        }
        this.localidades = Array.isArray(res?.data) ? res.data : [];
        if (localidadPreferida) {
          this.localidad = buscarNombre(this.localidades, localidadPreferida);
          this.cargarPublicaciones();
        }
        this.changeDetector.detectChanges();
      },
      error: (err) => {
        console.error('No se pudieron cargar las localidades.', err);
        this.toastr.error('No se pudieron cargar las localidades.');
        if (localidadPreferida) {
          this.cargarPublicaciones();
        }
      }
    });
  }

  limpiarFiltros(): void {
    this.provincia = '';
    this.departamento = '';
    this.localidad = '';
    this.departamentos = [];
    this.localidades = [];
    this.cargarPublicaciones();
  }

  eliminarPublicacion(publicacion: Publicacion): void {
    const usuario = this.auth.getUsuarioActual();
    if (!this.esRescatista || !usuario?.id_usuario || this.eliminandoPublicaciones.has(publicacion.id_publicacion)) {
      return;
    }
    if (!window.confirm(`¿Querés eliminar la publicación de ${publicacion.animal?.nombre || 'esta mascota'}?`)) {
      return;
    }

    this.eliminandoPublicaciones.add(publicacion.id_publicacion);
    this.publicacionService.delete(publicacion.id_publicacion, usuario.id_usuario).subscribe({
      next: () => {
        this.publicaciones = this.publicaciones.filter(item => item.id_publicacion !== publicacion.id_publicacion);
        this.eliminandoPublicaciones.delete(publicacion.id_publicacion);
        this.toastr.success('La publicación fue eliminada.');
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo eliminar la publicación.', error);
        this.eliminandoPublicaciones.delete(publicacion.id_publicacion);
        this.toastr.error(error?.error?.data || 'No se pudo eliminar la publicación.');
        this.changeDetector.detectChanges();
      }
    });
  }

  getUbicacionPublicacion(pub: Publicacion): string {
    const localidad = pub?.localidad || 'Sin localidad';
    return pub?.provincia ? `${localidad}, ${pub.provincia}` : localidad;
  }
}