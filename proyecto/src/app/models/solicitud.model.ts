import { Usuario } from './usuario.model';
import { Publicacion } from './publicacion.model';

export class Solicitud {
  id_solicitud!: number;
  fecha_solicitud!: string;
  estado!: 'PENDIENTE' | 'ACEPTADA' | 'RECHAZADA';
  motivo_rechazo?: string;
  adoptante!: Usuario;
  publicacion!: Publicacion;
  id_chat?: number;
  adoptante_id?: number;
  publicacion_id?: number;
}