import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule, Location } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
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
  imports: [CommonModule],
  templateUrl: './perfil-publico.html',
  styleUrl: './perfil-publico.css',
})
export class PerfilPublicoComponent implements OnInit {
  perfil: PerfilPublico | null = null;
  cargando = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private usuarios: UsuarioService,
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

  volver(): void {
    this.location.back();
  }
}
