import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';
import { AccionReporte, ReporteService, textoCategoria } from '../../services/reporte';
import { UsuarioService } from '../../services/usuario';
import { PublicacionService } from '../../services/publicacion';

type Pestana = 'pendientes' | 'resueltos' | 'sancionados';
type AccionResolucion = Exclude<AccionReporte, 'revisar'>;

/**
 * Panel del moderador (/moderacion o /administracion).
 * Si no hay un moderador logueado muestra su propio login. Las cuentas de
 * moderador no se crean desde el registro: ver "python manage.py crear_moderador".
 */
@Component({
  selector: 'app-moderacion',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './moderacion.html',
  styleUrl: './moderacion.css'
})
export class Moderacion implements OnInit {
  readonly maxStrikes = 3;
  readonly opcionesDias = [1, 3, 7, 15, 30, 0];

  // Login
  email = '';
  password = '';
  ingresando = false;
  errorLogin = '';

  // Panel
  pestana: Pestana = 'pendientes';
  reportes: any[] = [];
  sancionados: any[] = [];
  cargando = false;

  // Resolución abierta (una a la vez)
  reporteAbierto: number | null = null;
  accion: AccionResolucion | null = null;
  mensaje = '';
  dias = 7;
  nota = '';
  enviando = false;

  // Reportes con la conversación desplegada
  evidenciaAbierta = new Set<number>();
  eliminandoPublicaciones = new Set<number>();
  readonly textoCategoria = textoCategoria;

  constructor(
    private auth: AuthService,
    private reporteService: ReporteService,
    private usuarioService: UsuarioService,
    private publicacionService: PublicacionService,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    if (this.esModerador) {
      this.cargar();
    }
  }

  get esModerador(): boolean {
    return this.auth.esModerador();
  }

  ingresar(): void {
    if (this.ingresando) {
      return;
    }
    this.ingresando = true;
    this.errorLogin = '';
    this.auth.login(this.email.trim(), this.password).subscribe({
      next: () => {
        this.ingresando = false;
        this.password = '';
        if (!this.auth.esModerador()) {
          // Una cuenta común no entra al panel, aunque la contraseña sea correcta.
          this.auth.logout();
          this.errorLogin = 'Esta cuenta no tiene permisos de moderación.';
        } else {
          this.toastr.success('Sesión de moderador iniciada.');
          this.cargar();
        }
        this.changeDetector.detectChanges();
      },
      error: error => {
        const mensaje = error?.error?.data;
        this.errorLogin = typeof mensaje === 'string' ? mensaje : 'No se pudo iniciar sesión.';
        this.ingresando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  cambiarPestana(pestana: Pestana): void {
    this.pestana = pestana;
    this.cerrarResolucion();
    this.cargar();
  }

  cargar(): void {
    this.cargando = true;
    const pedido = this.pestana === 'sancionados'
      ? this.usuarioService.getSancionados()
      : this.reporteService.getAll(this.pestana === 'pendientes' ? { pendientes: true } : {});
    pedido.subscribe({
      next: res => {
        const datos = Array.isArray(res?.data) ? res.data : [];
        if (this.pestana === 'sancionados') {
          this.sancionados = datos;
        } else if (this.pestana === 'resueltos') {
          this.reportes = datos.filter((r: any) => r.estado === 'ACEPTADO' || r.estado === 'RECHAZADO');
        } else {
          this.reportes = datos;
        }
        this.cargando = false;
        this.changeDetector.detectChanges();
      },
      error: err => {
        console.error('No se pudo cargar el panel de moderación.', err);
        this.toastr.error('No se pudieron cargar los datos.');
        this.cargando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  abrirResolucion(reporte: any, accion: AccionResolucion): void {
    this.reporteAbierto = reporte.id_reporte;
    this.accion = accion;
    this.mensaje = '';
    this.nota = '';
    this.dias = 7;
    // Marcamos el reporte "en revisión" para que otro moderador sepa que alguien lo está mirando.
    if (reporte.estado === 'PENDIENTE') {
      this.reporteService.gestionar(reporte.id_reporte, 'revisar').subscribe({
        next: res => {
          reporte.estado = res?.data?.estado ?? reporte.estado;
          this.changeDetector.detectChanges();
        },
        error: err => console.error('No se pudo marcar el reporte en revisión.', err)
      });
    }
  }

  cerrarResolucion(): void {
    this.reporteAbierto = null;
    this.accion = null;
  }

  get puedeConfirmar(): boolean {
    return !this.enviando && (this.accion !== 'advertir' || !!this.mensaje.trim());
  }

  confirmar(reporte: any): void {
    if (!this.accion || !this.puedeConfirmar) {
      return;
    }
    this.enviando = true;
    this.reporteService.gestionar(reporte.id_reporte, this.accion, {
      mensaje: this.mensaje.trim() || undefined,
      // En el strike el backend solo usa los días si es el que bloquea los reportes.
      dias: this.accion === 'suspender' || this.accion === 'strike' ? Number(this.dias) : undefined,
      nota: this.nota.trim() || undefined
    }).subscribe({
      next: () => {
        this.toastr.success('Reporte resuelto.');
        this.enviando = false;
        this.cerrarResolucion();
        this.cargar();
      },
      error: err => {
        const mensaje = err?.error?.data;
        this.toastr.error(typeof mensaje === 'string' ? mensaje : 'No se pudo resolver el reporte.');
        this.enviando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  quitarSancion(usuario: any, accion: 'levantar-suspension' | 'reiniciar-strikes'): void {
    this.usuarioService.quitarSancion(usuario.id_usuario, accion).subscribe({
      next: () => {
        this.toastr.success(accion === 'levantar-suspension' ? 'Suspensión levantada.' : 'Strikes reiniciados.');
        this.cargar();
      },
      error: err => {
        const mensaje = err?.error?.data;
        this.toastr.error(typeof mensaje === 'string' ? mensaje : 'No se pudo quitar la sanción.');
      }
    });
  }

  eliminarPublicacion(reporte: any): void {
    const id = reporte.id_publicacion;
    const usuario = this.auth.getUsuarioActual();
    if (!id || !usuario?.id_usuario || this.eliminandoPublicaciones.has(id)) {
      return;
    }
    if (!window.confirm(`¿Eliminar la publicación de ${reporte.publicacion?.animal?.nombre || 'esta mascota'}? No se puede deshacer.`)) {
      return;
    }
    this.eliminandoPublicaciones.add(id);
    // El backend deja borrar a un moderador aunque no sea el dueño (lo saca del token).
    this.publicacionService.delete(id, usuario.id_usuario).subscribe({
      next: () => {
        this.toastr.success('Publicación eliminada.');
        this.eliminandoPublicaciones.delete(id);
        // Otros reportes pueden apuntar a la misma publicación.
        for (const r of this.reportes) {
          if (r.id_publicacion === id) {
            r.publicacion_existe = false;
            r.id_publicacion = null;
          }
        }
        this.changeDetector.detectChanges();
      },
      error: err => {
        const mensaje = err?.error?.data;
        this.toastr.error(typeof mensaje === 'string' ? mensaje : 'No se pudo eliminar la publicación.');
        this.eliminandoPublicaciones.delete(id);
        this.changeDetector.detectChanges();
      }
    });
  }

  alternarEvidencia(idReporte: number): void {
    if (this.evidenciaAbierta.has(idReporte)) {
      this.evidenciaAbierta.delete(idReporte);
    } else {
      this.evidenciaAbierta.add(idReporte);
    }
  }

  estaSuspendido(usuario: any): boolean {
    return !!usuario.suspendido_hasta && new Date(usuario.suspendido_hasta) > new Date();
  }

  textoDias(dias: number): string {
    if (dias === 0) {
      return 'Baja definitiva';
    }
    return dias === 1 ? '1 día' : `${dias} días`;
  }

  textoResolucion(resolucion: string | null): string {
    switch (resolucion) {
      case 'IGNORADO': return 'Ignorado';
      case 'ADVERTENCIA': return 'Advertencia enviada';
      case 'SUSPENSION': return 'Usuario suspendido';
      case 'STRIKE': return 'Strike al reportador';
      default: return '—';
    }
  }
}
