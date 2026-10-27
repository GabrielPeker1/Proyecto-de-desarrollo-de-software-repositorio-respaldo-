import { Component, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from './services/auth';
import { NavigationEnd, Router } from '@angular/router';
import { SolicitudService } from './services/solicitud';
import { Alerta, AlertaService } from './services/alerta';
import { UsuarioService } from './services/usuario';
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
  // Avisos del moderador que el usuario todavía no vio. Se muestran de a uno.
  alertas: Alerta[] = [];

  constructor(
    private auth: AuthService,
    private router: Router,
    private solicitudes: SolicitudService,
    private alertaService: AlertaService,
    private usuarios: UsuarioService
  ) {}

  ngOnInit(): void {
    this.cargarSolicitudesPendientes();
    this.cargarAlertas();
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd)
    ).subscribe(() => {
      this.cargarSolicitudesPendientes();
      this.cargarAlertas();
    });
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

  get esModerador(): boolean {
    return this.auth.esModerador();
  }

  get alertaActual(): Alerta | null {
    return this.alertas[0] ?? null;
  }

  get tituloAlerta(): string {
    switch (this.alertaActual?.tipo) {
      case 'SUSPENSION': return 'Tu cuenta fue suspendida';
      case 'STRIKE': return 'Recibiste un strike';
      default: return 'Advertencia de un moderador';
    }
  }

  private cargarAlertas(): void {
    const usuario = this.usuario;
    if (!usuario?.id_usuario || this.esModerador) {
      this.alertas = [];
      return;
    }
    this.alertaService.getNoLeidas().subscribe({
      next: response => {
        this.alertas = Array.isArray(response?.data) ? response.data : [];
        // Un strike puede bloquearle los reportes: refrescamos sus datos guardados.
        if (this.alertas.some(alerta => alerta.tipo === 'STRIKE')) {
          this.usuarios.get(usuario.id_usuario).subscribe({
            next: res => res?.data && this.auth.actualizarUsuarioActual(res.data),
            error: error => console.error('No se pudieron actualizar los datos del usuario.', error)
          });
        }
      },
      error: error => console.error('No se pudieron cargar las alertas.', error)
    });
  }

  cerrarAlerta(): void {
    const alerta = this.alertaActual;
    if (!alerta) {
      return;
    }
    this.alertas = this.alertas.slice(1);
    this.alertaService.marcarLeida(alerta.id_alerta).subscribe({
      error: error => console.error('No se pudo marcar la alerta como leída.', error)
    });
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