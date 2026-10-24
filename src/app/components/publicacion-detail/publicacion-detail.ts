import { Component, HostListener, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef } from '@angular/core';
import { PublicacionService } from '../../services/publicacion';
import { SolicitudService } from '../../services/solicitud';
import { AuthService } from '../../services/auth';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-publicacion-detail',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './publicacion-detail.html',
  styleUrls: ['./publicacion-detail.css']
})
export class PublicacionDetail implements OnInit {
  publicacion: any;
  imagenPrincipal = '';
  visorAbierto = false;
  cargandoSolicitud = false;
  enviandoSolicitud = false;
  eliminandoPublicacion = false;
  solicitudExistente = false;
  estadoSolicitud = '';

  constructor(
    private route: ActivatedRoute,
    private publicacionService: PublicacionService,
    private solicitudService: SolicitudService,
    private auth: AuthService,
    private toastr: ToastrService,
    private router: Router,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.publicacionService.get(id).subscribe(res => {
      this.publicacion = res.data;
      const fotos = this.publicacion.animal?.fotos || [];
      this.imagenPrincipal = fotos[0]?.url_foto || 'https://placehold.co/600x400';
      if (this.esAdoptante) {
        this.cargarSolicitudExistente();
      }
      this.changeDetector.detectChanges();
    });
  }

  // ---- Visor de fotos en pantalla completa ----
  get fotos(): string[] {
    return (this.publicacion?.animal?.fotos || []).map((foto: any) => foto.url_foto);
  }

  get indiceFoto(): number {
    return this.fotos.indexOf(this.imagenPrincipal);
  }

  abrirVisor(): void {
    // El placeholder de "sin foto" no se amplía.
    if (this.fotos.length > 0) {
      this.visorAbierto = true;
    }
  }

  cerrarVisor(): void {
    this.visorAbierto = false;
  }

  cambiarFoto(paso: number): void {
    const total = this.fotos.length;
    if (total > 1) {
      // El % hace que de la última vuelva a la primera y al revés.
      this.imagenPrincipal = this.fotos[(this.indiceFoto + paso + total) % total];
    }
  }

  @HostListener('document:keydown', ['$event'])
  teclaVisor(event: KeyboardEvent): void {
    if (!this.visorAbierto) {
      return;
    }
    if (event.key === 'Escape') {
      this.cerrarVisor();
    } else if (event.key === 'ArrowRight') {
      this.cambiarFoto(1);
    } else if (event.key === 'ArrowLeft') {
      this.cambiarFoto(-1);
    }
  }

  get esAdoptante(): boolean {
    return String(this.auth.getUsuarioActual()?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'adoptante';
  }

  get esRescatistaPropietario(): boolean {
    const usuario = this.auth.getUsuarioActual();
    return String(usuario?.tipo_usuario?.nombre ?? '').toLocaleLowerCase() === 'rescatista'
      && usuario?.id_usuario === this.publicacion?.rescatista?.id_usuario;
  }

  get sinSesion(): boolean {
    return !this.auth.getUsuarioActual()?.id_usuario;
  }

  get returnUrl(): string {
    return this.router.url;
  }

  solicitarAdopcion(): void {
    const u = this.auth.getUsuarioActual();
    if (!u?.id_usuario) {
      this.router.navigate(['/login'], {
        queryParams: { returnUrl: this.router.url }
      });
      return;
    }
    if (!this.esAdoptante) {
      this.toastr.warning('Solo las cuentas adoptantes pueden enviar solicitudes.');
      return;
    }
    if (this.enviandoSolicitud || this.solicitudExistente || !this.publicacion) {
      return;
    }

    this.enviandoSolicitud = true;
    this.solicitudService.create({
      adoptante_id: u.id_usuario,
      publicacion_id: this.publicacion.id_publicacion
    }).subscribe({
      next: () => {
        this.solicitudExistente = true;
        this.estadoSolicitud = 'PENDIENTE';
        this.enviandoSolicitud = false;
        this.toastr.success('Solicitud enviada');
        // Sin esto el botón se queda en "Enviando solicitud..." aunque ya se haya enviado.
        this.changeDetector.detectChanges();
      },
      error: (e) => {
        console.error('No se pudo enviar la solicitud de adopción.', e);
        this.toastr.error(e.error?.data || 'No se pudo enviar la solicitud.');
        this.enviandoSolicitud = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  eliminarPublicacion(): void {
    const usuario = this.auth.getUsuarioActual();
    if (!this.esRescatistaPropietario || !usuario?.id_usuario || !this.publicacion || this.eliminandoPublicacion) {
      return;
    }
    if (!window.confirm(`¿Querés eliminar la publicación de ${this.publicacion.animal?.nombre || 'esta mascota'}?`)) {
      return;
    }

    this.eliminandoPublicacion = true;
    this.publicacionService.delete(this.publicacion.id_publicacion, usuario.id_usuario).subscribe({
      next: () => {
        this.toastr.success('La publicación fue eliminada.');
        this.router.navigate(['/publicaciones']);
      },
      error: error => {
        console.error('No se pudo eliminar la publicación.', error);
        this.toastr.error(error?.error?.data || 'No se pudo eliminar la publicación.');
        this.eliminandoPublicacion = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  private cargarSolicitudExistente(): void {
    const usuario = this.auth.getUsuarioActual();
    if (!usuario?.id_usuario || !this.publicacion) {
      return;
    }

    this.cargandoSolicitud = true;
    this.solicitudService.getAll({ id_adoptante: usuario.id_usuario }).subscribe({
      next: response => {
        const solicitudes = Array.isArray(response?.data) ? response.data : [];
        const existente = solicitudes.find(
          (solicitud: { publicacion?: { id_publicacion?: number } }) =>
            solicitud.publicacion?.id_publicacion === this.publicacion.id_publicacion
        );
        this.solicitudExistente = Boolean(existente);
        this.estadoSolicitud = existente?.estado ?? '';
        this.cargandoSolicitud = false;
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo comprobar si ya existe una solicitud para esta publicación.', error);
        this.cargandoSolicitud = false;
        this.toastr.error('No se pudo comprobar tu solicitud. Intentá recargar la página.');
        this.changeDetector.detectChanges();
      }
    });
  }
}