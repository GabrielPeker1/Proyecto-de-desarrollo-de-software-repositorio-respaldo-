import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { interval, Subscription } from 'rxjs';
import { ChatService } from '../../services/chat';
import { MensajeService } from '../../services/mensaje';
import { AuthService } from '../../services/auth';
import { Bloqueo, BloqueoService } from '../../services/bloqueo';
import { ReportarDialogo } from '../reportar-dialogo/reportar-dialogo';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ReportarDialogo],
  selector: 'app-chat-detail',
  templateUrl: './chat-detail.html',
  styleUrl: './chat-detail.css',
})
export class ChatDetail implements OnInit, OnDestroy {
  @ViewChild('messageList') private messageList?: ElementRef<HTMLElement>;

  chat: any;
  mensajes: any[] = [];
  texto = '';
  cargando = true;
  enviando = false;
  errorCarga = false;
  reportando = false;
  // Bloqueo con el otro usuario
  bloqueoHecho: Bloqueo | null = null;
  meBloquearon = false;
  // Arranca en true: el botón no se puede usar hasta saber si ya está bloqueado.
  procesandoBloqueo = true;
  private polling?: Subscription;
  private idChat = 0;

  constructor(
    private route: ActivatedRoute,
    private chatService: ChatService,
    private mensajeService: MensajeService,
    public auth: AuthService,
    private bloqueos: BloqueoService,
    private toastr: ToastrService,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.idChat = Number(this.route.snapshot.paramMap.get('id'));
    const idUsuario = this.auth.getUsuarioActual()?.id_usuario;
    if (!Number.isInteger(this.idChat) || this.idChat < 1 || !idUsuario) {
      this.cargando = false;
      this.errorCarga = true;
      return;
    }

    this.chatService.get(this.idChat, idUsuario).subscribe({
      next: response => {
        this.chat = response?.data;
        this.changeDetector.detectChanges();
        this.cargarBloqueos();
        this.cargarMensajes();
        this.polling = interval(5000).subscribe(() => this.cargarMensajes(false));
      },
      error: error => {
        console.error('No se pudo cargar esta conversación.', error);
        this.errorCarga = true;
        this.cargando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  ngOnDestroy(): void {
    this.polling?.unsubscribe();
  }

  get persona(): any {
    const yo = this.auth.getUsuarioActual()?.id_usuario;
    const partes = this.chat?.participantes ?? {};
    return String(partes.adoptante?.id_usuario) === String(yo)
      ? partes.rescatista ?? {}
      : partes.adoptante ?? {};
  }

  get soyAdoptante(): boolean {
    return String(this.chat?.participantes?.adoptante?.id_usuario)
      === String(this.auth.getUsuarioActual()?.id_usuario);
  }

  private get idOtroUsuario(): number | undefined {
    return this.persona?.id_usuario;
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

  abrirReporte(): void {
    if (this.reportesBloqueados) {
      this.toastr.warning('Tu herramienta de reportes está bloqueada por reportes sin motivo.');
      return;
    }
    this.reportando = true;
  }

  cargarMensajes(showSpinner = true): void {
    const idUsuario = this.auth.getUsuarioActual()?.id_usuario;
    if (!idUsuario) {
      this.cargando = false;
      this.errorCarga = true;
      return;
    }
    if (showSpinner) {
      this.cargando = true;
    }
    this.mensajeService.getByChat(this.idChat, idUsuario).subscribe({
      next: response => {
        this.mensajes = Array.isArray(response?.data) ? response.data : [];
        this.cargando = false;
        this.errorCarga = false;
        this.changeDetector.detectChanges();
        setTimeout(() => this.scrollToBottom(), 0);
      },
      error: error => {
        console.error('No se pudieron cargar los mensajes.', error);
        this.cargando = false;
        this.errorCarga = true;
        this.changeDetector.detectChanges();
      }
    });
  }

  enviar(): void {
    const contenido = this.texto.trim();
    const emisorId = this.auth.getUsuarioActual()?.id_usuario;
    if (!contenido || !emisorId || this.enviando) {
      return;
    }

    this.enviando = true;
    this.mensajeService.create({
      chat_id: this.idChat,
      emisor_id: emisorId,
      contenido
    }).subscribe({
      next: response => {
        if (response?.data) {
          this.mensajes = [...this.mensajes, response.data];
        }
        this.texto = '';
        this.enviando = false;
        this.changeDetector.detectChanges();
        setTimeout(() => this.scrollToBottom(), 0);
      },
      error: error => {
        console.error('No se pudo enviar el mensaje.', error);
        const data = error?.error?.data;
        this.toastr.error(typeof data === 'string' ? data : 'No se pudo enviar el mensaje.');
        this.enviando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  fecha(value: string): string {
    return new Intl.DateTimeFormat('es', { hour: '2-digit', minute: '2-digit' }).format(new Date(value));
  }

  private scrollToBottom(): void {
    const container = this.messageList?.nativeElement;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }
}
