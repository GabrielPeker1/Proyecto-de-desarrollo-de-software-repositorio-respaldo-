import { Animal } from './animal.model';
import { Usuario } from './usuario.model';

export class Publicacion {
  id_publicacion!: number;
  descripcion?: string;
  fecha_publicacion!: string;
  estado!: 'EN_ADOPCION' | 'EN_PROCESO' | 'ADOPTADO';
  // Heredada del rescatista al crear la publicación (la completa el back).
  provincia?: string;
  departamento?: string;
  localidad?: string;
  animal!: Animal;
  rescatista!: Usuario;
  rescatista_id?: number;
  animal_id?: number;
}