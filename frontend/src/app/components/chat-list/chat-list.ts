import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ChatService } from '../../services/chat';
import { AuthService } from '../../services/auth';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-chat-list',
  templateUrl: './chat-list.html',
  styleUrl: './chat-list.css',
})
export class ChatList implements OnInit {
  chats: any[] = [];
  busqueda = '';
  cargando = true;
  errorCarga = false;

  constructor(
    private chatService: ChatService,
    private auth: AuthService,
    private changeDetector: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const usuario = this.auth.getUsuarioActual();
    if (!usuario?.id_usuario) {
      this.cargando = false;
      return;
    }

    this.chatService.getAll(usuario.id_usuario).subscribe({
      next: response => {
        this.chats = Array.isArray(response?.data) ? response.data : [];
        this.cargando = false;
        this.changeDetector.detectChanges();
      },
      error: error => {
        console.error('No se pudieron cargar las conversaciones.', error);
        this.errorCarga = true;
        this.cargando = false;
        this.changeDetector.detectChanges();
      }
    });
  }

  get conversacionesFiltradas(): any[] {
    const query = this.busqueda.trim().toLocaleLowerCase();
    if (!query) {
      return this.chats;
    }

    return this.chats.filter(chat => {
      const persona = this.personaDelChat(chat);
      const animal = chat.solicitud?.animal ?? '';
      return `${persona.nombre_completo} ${animal}`.toLocaleLowerCase().includes(query);
    });
  }

  personaDelChat(chat: any): any {
    const usuarioId = this.auth.getUsuarioActual()?.id_usuario;
    const participantes = chat?.participantes ?? {};
    return String(participantes.adoptante?.id_usuario) === String(usuarioId)
      ? participantes.rescatista ?? {}
      : participantes.adoptante ?? {};
  }

  fechaCorta(value?: string): string {
    if (!value) {
      return '';
    }
    return new Intl.DateTimeFormat('es', { day: '2-digit', month: '2-digit' }).format(new Date(value));
  }
}
