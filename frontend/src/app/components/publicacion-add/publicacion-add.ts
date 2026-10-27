import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ToastrService } from 'ngx-toastr';
import { AnimalCreate } from '../../models/animal.model';
import { AnimalService } from '../../services/animal';
import { AuthService } from '../../services/auth';
import { PublicacionService } from '../../services/publicacion';

@Component({
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  selector: 'app-publicacion-add',
  templateUrl: './publicacion-add.html',
  styleUrl: './publicacion-add.css',
})
export class PublicacionAdd implements OnDestroy {
  nombre = '';
  especie = '';
  especieOtra = '';
  raza = '';
  edad: number | null = null;
  sexo = '';
  peso: number | null = null;
  vacunas = '';
  descripcion = '';
  castrado = false;
  compatibleNinos = false;
  compatibleOtrosAnimales = false;
  desparasitado = false;
  tieneMicrochip = false;
  entrenamientoBasico = false;
  fotosSeleccionadas: { archivo: File; vistaPrevia: string }[] = [];
  publicando = false;
  confirmarDescartar = false;

  constructor(
    private animalService: AnimalService,
    private publicacionService: PublicacionService,
    private auth: AuthService,
    private router: Router,
    private toastr: ToastrService
  ) {}

  get usuarioAutenticado(): boolean {
    return Boolean(this.auth.getUsuarioActual()?.id_usuario);
  }

  seleccionarFotos(event: Event): void {
    const input = event.target as HTMLInputElement;
    const archivos = Array.from(input.files ?? []);
    const lugaresDisponibles = 5 - this.fotosSeleccionadas.length;

    if (archivos.length > lugaresDisponibles) {
      this.toastr.warning('Podés agregar hasta 5 fotos.');
    }

    for (const archivo of archivos.slice(0, lugaresDisponibles)) {
      if (!archivo.type.startsWith('image/')) {
        this.toastr.warning(`${archivo.name} no es un archivo de imagen.`);
        continue;
      }
      if (archivo.size > 5 * 1024 * 1024) {
        this.toastr.warning(`${archivo.name} supera el tamaño máximo de 5 MB.`);
        continue;
      }
      this.fotosSeleccionadas.push({
        archivo,
        vistaPrevia: URL.createObjectURL(archivo)
      });
    }
    input.value = '';
  }

  quitarFoto(index: number): void {
    const [foto] = this.fotosSeleccionadas.splice(index, 1);
    if (foto) {
      URL.revokeObjectURL(foto.vistaPrevia);
    }
  }

  ngOnDestroy(): void {
    this.fotosSeleccionadas.forEach(foto => URL.revokeObjectURL(foto.vistaPrevia));
  }

  publicar(): void {
    const usuario = this.auth.getUsuarioActual();
    if (!usuario?.id_usuario) {
      this.toastr.warning('Iniciá sesión para publicar un animal.');
      this.router.navigate(['/login']);
      return;
    }
    if (this.publicando) {
      return;
    }
    // La publicación hereda la ubicación del rescatista: si le falta el departamento
    // (cuentas creadas antes de que existiera), no lo dejamos empezar.
    if (!usuario.ubicacion?.departamento || !usuario.ubicacion?.ciudad) {
      this.toastr.warning('Completá tu departamento y localidad en Mi Perfil antes de publicar.');
      return;
    }
    if (
      this.fotosSeleccionadas.length === 0 ||
      !this.nombre.trim() ||
      !this.especie ||
      (this.especie === 'Otro' && !this.especieOtra.trim()) ||
      !this.raza.trim() ||
      this.edad === null ||
      !Number.isFinite(this.edad) ||
      this.edad < 0 ||
      !this.sexo ||
      this.peso === null ||
      !Number.isFinite(this.peso) ||
      this.peso < 0 ||
      !this.vacunas.trim() ||
      !this.descripcion.trim()
    ) {
      this.toastr.warning('Completá todos los campos obligatorios y agregá al menos una foto.');
      return;
    }

    const animal: AnimalCreate = {
      nombre: this.nombre.trim(),
      // Si eligió "Otro", guardamos lo que escribió (ej: "Conejo") en lugar de "Otro".
      especie: this.especie === 'Otro' ? this.especieOtra.trim() : this.especie,
      raza: this.raza.trim(),
      edad: String(this.edad),
      sexo: this.sexo,
      peso: this.peso,
      vacunas_administradas: this.vacunas.trim(),
      castrado: this.castrado,
      compatible_ninos: this.compatibleNinos,
      compatible_otros_animales: this.compatibleOtrosAnimales,
      desparasitado: this.desparasitado,
      tiene_microchip: this.tieneMicrochip,
      entrenamiento_basico: this.entrenamientoBasico,
    };

    this.publicando = true;
    this.animalService.create(animal).subscribe({
      next: (response) => {
        const idAnimal = response?.data?.id_animal;
        if (!idAnimal) {
          this.publicando = false;
          this.toastr.error('El servidor no devolvió el identificador del animal.');
          return;
        }

        this.subirFotosYPublicar(idAnimal, usuario.id_usuario);
      },
      error: (error) => {
        this.publicando = false;
        this.toastr.error(this.mensajeError(error));
      }
    });
  }

  private subirFotosYPublicar(idAnimal: number, idRescatista: number): void {
    if (this.fotosSeleccionadas.length === 0) {
      this.crearPublicacion(idAnimal, idRescatista);
      return;
    }

    this.animalService.uploadFotos(idAnimal, this.fotosSeleccionadas.map(foto => foto.archivo)).subscribe({
      next: () => this.crearPublicacion(idAnimal, idRescatista),
      error: error => {
        console.error('No se pudieron cargar las fotos del animal.', error);
        this.limpiarAnimalTrasError(idAnimal, error, 'No se pudieron cargar las fotos');
      }
    });
  }

  private crearPublicacion(idAnimal: number, idRescatista: number): void {
    this.publicacionService.create({
      animal_id: idAnimal,
      rescatista_id: idRescatista,
      descripcion: this.descripcion.trim(),
      estado: 'EN_ADOPCION'
    }).subscribe({
      next: () => {
        this.toastr.success('La publicación quedó creada.');
        this.router.navigate(['/publicaciones']);
      },
      error: error => {
        console.error('No se pudo crear la publicación.', error);
        this.limpiarAnimalTrasError(idAnimal, error, 'No se pudo publicar');
      }
    });
  }

  private limpiarAnimalTrasError(idAnimal: number, error: any, motivo: string): void {
    this.animalService.delete(idAnimal).subscribe({
      next: () => {
        this.publicando = false;
        this.toastr.error(`${motivo}: ${this.mensajeError(error)}`);
      },
      error: cleanupError => {
        console.error('No se pudo limpiar el animal y sus fotos tras fallar la publicación.', cleanupError);
        this.publicando = false;
        this.toastr.error(
          `${motivo}: ${this.mensajeError(error)}. El animal se guardó, pero no se pudo limpiar el registro; contactá al equipo.`
        );
      }
    });
  }

  confirmarSalida(): void {
    this.confirmarDescartar = false;
    this.router.navigate(['/publicaciones']);
  }

  solicitarDescartar(event: Event): void {
    event.preventDefault();
    this.confirmarDescartar = true;
  }

  private mensajeError(error: any): string {
    const data = error?.error?.data;
    if (typeof data === 'string') {
      return data;
    }
    if (data && typeof data === 'object') {
      return Object.values(data).flat().join(' ') || 'No se pudo guardar la publicación.';
    }
    return 'No se pudo guardar la publicación. Revisá la conexión con el servidor.';
  }
}
