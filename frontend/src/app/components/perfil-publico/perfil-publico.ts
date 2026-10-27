import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AuthService } from '../../services/auth';
import { Bloqueo, BloqueoService } from '../../services/bloqueo';
import { CATEGORIAS_REPORTE, ReporteService } from '../../services/reporte';
import { UsuarioService } from '../../services/usuario';

interface PerfilPublico {
  id_usuario: number;
  nombre_completo: string;
  tipo_usuario: string;
  provincia: string;
  departamento: string | null;
  ciudad: string;
  // Solo viene en el perfil de los rescatistas.
  descripcion?: string | null;
  // Solo vienen si el usuario hizo pública su dirección.
  calle?: string | null;
  numero?: string | null;
  piso?: string | null;
}

/**
 * Perfil de otro usuario, de solo lectura. El adoptante ve el del rescatista
 * desde una publicación y el rescatista ve el del adoptante desde sus solicitudes.
 * El back decide qué datos manda: nunca email, teléfono ni dirección.
 */
@Component({
  selector: 'app-perfil-publico',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './perfil-publico.html',
  styleUrl: './perfil-publico.css',
})
export class PerfilPublicoComponent implements OnInit {
  perfil: PerfilPublico | null = null;
  cargando = true;
  error = '';

  // Bloqueo con el otro usuario
  bloqueoHecho: Bloqueo | null = null;
  meBloquearon = false;
  // Arranca en true: el botón no se puede usar hasta saber si ya está bloqueado.
  procesandoBloqueo = true;

  // Formulario de reporte
  reportando = false;
  readonly categorias = CATEGORIAS_REPORTE;
  categoriaReporte = '';
  motivoReporte = '';
  enviandoReporte = false;

  constructor(
    private route: ActivatedRoute,
    private usuarios: UsuarioService,
    private reportes: ReporteService,
    private bloqueos: BloqueoService,
    private auth: AuthService,
    private toastr: ToastrService,
    private location: Location,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.usuarios.getPerfilPublico(id).subscribe({
      next: res => {
        this.perfil = res?.data ?? null;
        this.cargando = false;
        this.changeDetector.detectChanges();
        if (this.puedeVerReportar) {
          this.cargarBloqueos();
        }
      },
      error: err => {
        console.error('No se pudo cargar el perfil.', err);
        this.error = err?.status === 404 ? 'Este usuario no existe.' : 'No se pudo cargar el perfil.';
        this.cargando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  get esRescatista(): boolean {
    return this.perfil?.tipo_usuario?.toLowerCase() === 'rescatista';
  }

  /** No se puede reportar a uno mismo ni a un moderador. */
  get puedeVerReportar(): boolean {
    return !!this.perfil
      && this.perfil.id_usuario !== this.auth.getUsuarioActual()?.id_usuario
      && this.perfil.tipo_usuario?.toLowerCase() !== 'moderador';
  }

  private get idOtroUsuario(): number | undefined {
    return this.perfil?.id_usuario;
  }

  private cargarBloqueos(): void {
    this.bloqueos.getMios().subscribe({
      next: res => {
        const lista: Bloqueo[] = Array.isArray(res?.data) ? res.data : [];
        const yo = this.auth.getUsuarioActual()?.id_usuario;
        const otro = this.idOtroUsuario;
        this.bloqueoHecho = yo && otro ? BloqueoService.buscarHecho(lista, yo, otro) : null;
        this.meBloquearon = !!yo && !!otro && BloqueoService.meBloqueo(lista, yo, otro);
        this.procesandoBloqueo = false;
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudieron cargar los bloqueos.', error);
        this.procesandoBloqueo = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  alternarBloqueo(nombre: string): void {
    const otro = this.idOtroUsuario;
    if (!otro || this.procesandoBloqueo) {
      return;
    }
    const bloqueo = this.bloqueoHecho;
    if (!bloqueo && !window.confirm(
      `¿Querés bloquear a ${nombre}? No van a poder mandarse mensajes ni solicitudes, `
      + 'y no vas a ver sus publicaciones. Podés desbloquearlo cuando quieras.')) {
      return;
    }
    this.procesandoBloqueo = true;
    const pedido = bloqueo ? this.bloqueos.desbloquear(bloqueo.id_bloqueo) : this.bloqueos.bloquear(otro);
    pedido.subscribe({
      next: res => {
        this.bloqueoHecho = bloqueo ? null : res?.data ?? null;
        this.toastr.success(bloqueo ? `Desbloqueaste a ${nombre}.` : `Bloqueaste a ${nombre}.`);
        this.procesandoBloqueo = false;
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudo cambiar el bloqueo.', error);
        const data = error?.error?.data;
        this.toastr.error(typeof data === 'string' ? data : 'No se pudo completar la acción.');
        // Puede que el estado de la pantalla no coincida con el real (ej: ya estaba bloqueado).
        this.cargarBloqueos();
      }
    });
  }

  /** Con 3 strikes por reportar sin motivo, el back bloquea los reportes. */
  get reportesBloqueados(): boolean {
    return this.auth.getUsuarioActual()?.puede_reportar === false;
  }

  enviarReporte(): void {
    const motivo = this.motivoReporte.trim();
    if (!this.perfil || !this.categoriaReporte || !motivo || this.enviandoReporte) {
      return;
    }
    this.enviandoReporte = true;
    this.reportes.reportar(this.perfil.id_usuario, this.categoriaReporte, motivo).subscribe({
      next: () => {
        this.toastr.success('Reporte enviado. Un moderador lo va a revisar.');
        this.reportando = false;
        this.motivoReporte = '';
        this.categoriaReporte = '';
        this.enviandoReporte = false;
        this.changeDetector.detectChanges();
      },
      error: err => {
        console.error('No se pudo enviar el reporte.', err);
        const mensaje = err?.error?.data;
        this.toastr.error(typeof mensaje === 'string' ? mensaje : 'No se pudo enviar el reporte.');
        this.enviandoReporte = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  volver(): void {
    this.location.back();
  }
}
