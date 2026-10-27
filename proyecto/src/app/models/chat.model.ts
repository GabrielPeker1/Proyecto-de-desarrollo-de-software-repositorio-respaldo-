export class Mensaje {
  id_mensaje!: number;
  contenido!: string;
  fecha_envio!: string;
  emisor!: { id_usuario: number; nombre_completo: string };
  chat_id?: number;
  emisor_id?: number;
}

export class Chat {
  id_chat!: number;
  fecha_creacion!: string;
  solicitud!: any;
  participantes!: any;
  ultimo_mensaje?: Mensaje;
  solicitud_id?: number;
}