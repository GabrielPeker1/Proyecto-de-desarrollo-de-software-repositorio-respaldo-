export class TiposUsuario {
  id_tipo_usuario!: number;
  nombre!: string;
}

export class Ubicacion {
  id_ubicacion!: number;
  provincia!: string;
  departamento?: string;
  ciudad!: string;
  calle?: string;
  numero?: string;
  piso?: string;
  direccion_completa?: string;
  zona_aproximada?: string;
}

export class Usuario {
  id_usuario!: number;
  email!: string;
  nombre_completo!: string;
  telefono?: string;
  descripcion?: string;
  // Si la calle, número y piso se ven en el perfil público (privada por defecto).
  direccion_publica?: boolean;
  estado!: string;
  ubicacion?: Ubicacion;
  zona?: {
    ciudad?: string;
    provincia?: string;
  };
  tipo_usuario!: TiposUsuario;
  password?: string;
  ubicacion_id?: number;
  tipo_usuario_id?: number;
}

export interface UsuarioCreate {
  email: string;
  nombre_completo: string;
  telefono?: string;
  descripcion?: string;
  ubicacion_id: number;
  tipo_usuario_id: number;
  password: string;
}