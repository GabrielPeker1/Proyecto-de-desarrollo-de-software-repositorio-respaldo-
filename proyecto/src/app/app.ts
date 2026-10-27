import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './services/auth';
import { NavigationEnd, Router } from '@angular/router';
import { SolicitudService } from './services/solicitud';
import { filter } from 'rxjs';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App implements OnInit {
  solicitudesPendientes = 0;

  constructor(
    private auth: AuthService,
    private router: Router,
    private solicitudes: SolicitudService
  ) {}

  ngOnInit(): void {
    this.cargarSolicitudesPendientes();
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => this.cargarSolicitudesPendientes());
    this.solicitudes.actualizaciones$.subscribe(() => this.cargarSolicitudesPendientes());
  }

  get usuario() { return this.auth.getUsuarioActual(); }

  get fotoPerfil(): string {
    const idUsuario = this.usuario?.id_usuario;
    if (!idUsuario) {
      return '';
    }
    try {
      return localStorage.getItem(`perfil-foto-${idUsuario}`) || '';
    } catch (error) {
      console.error('No se pudo leer la foto de perfil del usuario.', error);
      return '';
    }
  }

  get esRescatista(): boolean {
    return String(this.usuario?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'rescatista';
  }

  private cargarSolicitudesPendientes(): void {
    const usuario = this.usuario;
    const esRescatista = String(usuario?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'rescatista';
    if (!usuario?.id_usuario || !esRescatista) {
      this.solicitudesPendientes = 0;
      return;
    }

    this.solicitudes.getAll({ id_rescatista: usuario.id_usuario }).subscribe({
      next: response => {
        const solicitudes = Array.isArray(response?.data) ? response.data : [];
        this.solicitudesPendientes = solicitudes.filter(
          (solicitud: { estado?: string }) => solicitud.estado === 'PENDIENTE'
        ).length;
      },
      error: error => {
        console.error('No se pudieron cargar las notificaciones de solicitudes.', error);
        this.solicitudesPendientes = 0;
      }
    });
  }

  cerrarSesion(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}