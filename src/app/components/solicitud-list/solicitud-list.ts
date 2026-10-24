import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';
import { SolicitudService } from '../../services/solicitud';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-solicitud-list',
  templateUrl: './solicitud-list.html',
  styleUrl: './solicitud-list.css',
})
export class SolicitudList implements OnInit {
  solicitudes: any[] = [];
  estadoFiltro = 'TODAS';
  cargando = true;
  errorCarga = false;
  solicitudRechazo: any = null;
  motivoRechazo = '';
  procesandoId: number | null = null;

  constructor(
    private solicitudesService: SolicitudService,
    private auth: AuthService,
    private router: Router,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.cargarSolicitudes();
  }

  get esRescatista(): boolean {
    return String(this.auth.getUsuarioActual()?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'rescatista';
  }

  get tituloLista(): string {
    return this.esRescatista ? 'Solicitudes de Adopción' : 'Mis solicitudes';
  }

  get solicitudesVisibles(): any[] {
    return this.estadoFiltro === 'TODAS'
      ? this.solicitudes
      : this.solicitudes.filter(solicitud => solicitud.estado === this.estadoFiltro);
  }

  cargarSolicitudes(): void {
    const usuario = this.auth.getUsuarioActual();
    if (!usuario?.id_usuario) {
      this.cargando = false;
      return;
    }

    const filtros = this.esRescatista
      ? { id_rescatista: usuario.id_usuario }
      : { id_adoptante: usuario.id_usuario };

    this.solicitudesService.getAll(filtros).subscribe({
      next: response => {
        this.solicitudes = Array.isArray(response?.data) ? response.data : [];
        this.cargando = false;
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudieron cargar las solicitudes.', error);
        this.errorCarga = true;
        this.cargando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  aceptar(solicitud: any): void {
    const idRescatista = this.auth.getUsuarioActual()?.id_usuario;
    if (!idRescatista || !this.esRescatista) {
      this.toastr.error('Solo el rescatista propietario puede aceptar esta solicitud.');
      return;
    }
    this.procesandoId = solicitud.id_solicitud;
    this.solicitudesService.aceptar(solicitud.id_solicitud, idRescatista).subscribe({
      next: response => {
        solicitud.estado = 'ACEPTADA';
        solicitud.id_chat = response?.data?.chat?.id_chat;
        this.procesandoId = null;
        this.solicitudesService.notificarActualizacion();
        this.toastr.success('Solicitud aceptada. Ya pueden coordinar por el chat.');
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo aceptar la solicitud.', error);
        this.toastr.error(this.errorMessage(error));
        this.procesandoId = null;
        this.changeDetector.detectChanges();
      }
    });
  }

  abrirRechazo(solicitud: any): void {
    this.solicitudRechazo = solicitud;
    this.motivoRechazo = '';
  }

  rechazar(): void {
    const solicitud = this.solicitudRechazo;
    const motivo = this.motivoRechazo.trim();
    if (!solicitud || !motivo || this.procesandoId !== null) {
      return;
    }
    const idRescatista = this.auth.getUsuarioActual()?.id_usuario;
    if (!idRescatista || !this.esRescatista) {
      this.toastr.error('Solo el rescatista propietario puede rechazar esta solicitud.');
      return;
    }

    this.procesandoId = solicitud.id_solicitud;
    this.solicitudesService.rechazar(solicitud.id_solicitud, idRescatista, motivo).subscribe({
      next: () => {
        solicitud.estado = 'RECHAZADA';
        solicitud.motivo_rechazo = motivo;
        this.solicitudRechazo = null;
        this.procesandoId = null;
        this.solicitudesService.notificarActualizacion();
        this.toastr.success('La solicitud fue rechazada.');
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo rechazar la solicitud.', error);
        this.toastr.error(this.errorMessage(error));
        this.procesandoId = null;
        this.changeDetector.detectChanges();
      }
    });
  }

  abrirChat(solicitud: any): void {
    if (solicitud.id_chat) {
      this.router.navigate(['/chats', solicitud.id_chat]);
    }
  }

  nombreMascota(solicitud: any): string {
    return solicitud.publicacion?.animal?.nombre ?? 'Mascota';
  }

  fotoMascota(solicitud: any): string {
    return solicitud.publicacion?.animal?.fotos?.[0]?.url_foto
      ?? 'https://placehold.co/160x200?text=Sin+foto';
  }

  ubicacion(solicitud: any): string {
    const zona = solicitud.publicacion?.rescatista?.zona;
    if (!zona) {
      return 'Ubicación no disponible';
    }
    return [zona.ciudad, zona.provincia].filter(Boolean).join(', ');
  }

  private errorMessage(error: any): string {
    const message = error?.error?.data;
    return typeof message === 'string' ? message : 'No se pudo completar la acción.';
  }
}
